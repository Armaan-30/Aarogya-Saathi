from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
import hashlib
import json
import secrets
from fastapi import FastAPI, Depends, File, Form, UploadFile, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy import select, func, update
from . import config
from .db import Base, engine, get_db, migrate_schema, User, LoginSession, CaregiverGrant, AccessAudit, CareTaskEvent, Document, DocumentFile, CarePlan, CareTask, DocumentProcessing, AnalysisCache, TranslationCache, DocumentChatMessage
from .schemas import Review, TaskUpdate, TranslationRequest, DemoRequest, SpeechRequest, SpeechResponse, DocumentChatRequest, DocumentChatHistory, AuthRegister, AuthLogin, AuthStatus, UserResponse, CaregiverInviteRequest, CaregiverAcceptRequest, CaregiverResponse, CaregiverInviteResponse, CaregiverPatientResponse, CaregiverDashboardResponse
from .schemas import HealthResponse, DocumentResponse, DemoCaseResponse, ReviewResponse, CarePlanResponse, TaskResponse, TranslationResponse
from .services.document_extractor import extract, ocr_available, MAX_SIZE, validate_file
from .services.analysis_service import CASES, sample_path, demo_analysis
from .services.gemini_service import analyze, require_live
from .services.pipeline_service import process, request_key, request_lock, PIPELINE_VERSION
from .services.verification_service import verify
from .services.translation_service import translate
from .services.speech_service import synthesize
from .services.indian_medicine_info import approved_uses
from .services.document_chat_service import ask_document
from .services.auth_service import get_current_user, hash_password, verify_password, issue_session, revoke_session, normalize_email, token_hash
from .services.recovery_plan_service import care_task_json

@asynccontextmanager
async def lifespan(app):
    migrate_schema()
    yield

app = FastAPI(title='AarogyaSaathi AI', version='1.0.0', lifespan=lifespan, description='Synthetic-data hackathon prototype. Patient review is not clinical verification.')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173'], allow_credentials=True, allow_methods=['GET','POST','PATCH','DELETE'], allow_headers=['Content-Type','Authorization'])

@app.exception_handler(Exception)
async def unexpected(request, exc):
    return JSONResponse(status_code=500, content={'detail':'Something went wrong. Please try again. No unreviewed instructions were added to a plan.'})

def get_or_404(db, model, id):
    row = db.get(model, id)
    if not row: raise HTTPException(404, 'Record not found.')
    return row

def current_doc(db, user, id, action='read'):
    doc = get_or_404(db, Document, id)
    if doc.owner_id == user.id:
        db.add(AccessAudit(actor_id=user.id, patient_id=user.id, document_id=doc.id, action=action))
        db.commit()
        return doc, None
    if not doc.owner_id:
        raise HTTPException(404, 'Record not found.')
    grant = db.scalar(select(CaregiverGrant).where(CaregiverGrant.patient_id == doc.owner_id,
        CaregiverGrant.caregiver_id == user.id, CaregiverGrant.status == 'active'))
    if not grant:
        raise HTTPException(404, 'Record not found.')
    db.add(AccessAudit(actor_id=user.id, patient_id=doc.owner_id, document_id=doc.id, action=action))
    db.commit()
    return doc, grant

def current_plan(db, user, id, action='read'):
    care_plan = get_or_404(db, CarePlan, id)
    doc, grant = current_doc(db, user, care_plan.document_id, action)
    return care_plan, doc, grant

def care_plan_data(db, user, row, doc):
    tasks = db.scalars(select(CareTask).where(CareTask.plan_id == row.id)).all()
    items = doc.result['items']
    return {'id':row.id, 'document':document_json(doc, db), 'decisions':row.decisions,
        'tasks':[care_task_json(t) for t in tasks],
        'clarifications':[i for i in items if row.decisions[i['id']] == 'clarify'],
        'warnings':[i for i in items if i['kind'] == 'warning' and row.decisions[i['id']] == 'reviewed']}

def document_json(doc, db, reused=False):
    metadata = db.get(DocumentProcessing, doc.id)
    return {'id':doc.id, 'filename':doc.filename, 'extracted_text':doc.text, 'analysis':doc.result, 'mode':doc.mode, 'model':doc.model, 'extraction':doc.extraction, 'sample_id':doc.sample_id, 'created_at':doc.created_at, 'processing':metadata.details if metadata else {}, 'reused':reused}

def save_doc(db, filename, text, method, result, mode, sample_id=None, content=None, processing=None, cache_key=None, owner_id=None):
    doc = Document(owner_id=owner_id, filename=filename, text=text, result=result.model_dump(), mode=mode, model=config.MODEL if mode == 'live' else 'Prerecorded fixture', extraction=method, sample_id=sample_id)
    db.add(doc); db.flush()
    if processing:
        db.add(DocumentProcessing(document_id=doc.id, details=processing.model_dump()))
    if cache_key:
        db.add(AnalysisCache(key=cache_key, document_id=doc.id))
    if content:
        media_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'image/png' if filename.lower().endswith('.png') else 'image/jpeg'
        db.add(DocumentFile(document_id=doc.id, content=content, media_type=media_type))
    db.commit(); db.refresh(doc)
    return document_json(doc, db)

def live_document(db, data, filename, document_mode, user, sample_id=None):
    mime = validate_file(data, filename)
    if document_mode == 'handwritten' and mime == 'application/pdf':
        raise HTTPException(415, 'Handwritten mode accepts PNG or JPEG images. Upload a photo of the prescription.')
    require_live()
    key = request_key(data, document_mode, mime, user.id)
    # This local prototype runs one API worker. Locks coalesce concurrent requests.
    with request_lock(key):
        cached = db.get(AnalysisCache, key)
        if cached:
            return document_json(get_or_404(db, Document, cached.document_id), db, reused=True)
        text, method, result, info = process(data, filename, document_mode, analyze)
        return save_doc(db, filename, text, method, result, 'live', sample_id,
                        content=data, processing=info, cache_key=key, owner_id=user.id)

def auth_cookie(response, raw_token):
    response.set_cookie('aarogya_session', raw_token, httponly=True,
        secure=config.SESSION_COOKIE_SECURE, samesite='strict', path='/api',
        max_age=config.SESSION_TTL_HOURS * 3600)

@app.get('/api/auth/status', response_model=AuthStatus)
def auth_status(db=Depends(get_db)):
    return {'setup_required': db.scalar(select(func.count()).select_from(User)) == 0}

@app.post('/api/auth/register', response_model=UserResponse)
def register(request: AuthRegister, response: Response, db=Depends(get_db)):
    email = normalize_email(request.email)
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, 'An account with this email already exists. Sign in instead.')
    is_first = db.scalar(select(func.count()).select_from(User)) == 0
    if request.invite_code:
        grant = db.scalar(select(CaregiverGrant).where(CaregiverGrant.invite_hash == token_hash(request.invite_code), CaregiverGrant.status == 'pending'))
        if not grant or not grant.invite_expires_at or datetime.fromisoformat(grant.invite_expires_at) <= datetime.now(timezone.utc):
            raise HTTPException(400, 'Caregiver invitation is invalid or expired.')
        if normalize_email(grant.invite_email) != email:
            raise HTTPException(403, 'Use the email address the patient invited.')
    user = User(email=email, password_hash=hash_password(request.password))
    db.add(user); db.flush()
    if is_first:
        # Existing local records remain intact and are assigned to the operator's first account.
        db.execute(update(Document).where(Document.owner_id.is_(None)).values(owner_id=user.id))
    if request.invite_code:
        grant.caregiver_id = user.id
        grant.status = 'active'
        grant.invite_hash = None
        grant.invite_expires_at = None
        db.add(AccessAudit(actor_id=user.id, patient_id=grant.patient_id, action='caregiver_invitation_accepted'))
    raw = issue_session(db, user)
    auth_cookie(response, raw)
    return {'id': user.id, 'email': user.email}

@app.post('/api/auth/login', response_model=UserResponse)
def login(request: AuthLogin, response: Response, db=Depends(get_db)):
    email = normalize_email(request.email)
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(401, 'Email or password is incorrect.')
    raw = issue_session(db, user)
    auth_cookie(response, raw)
    return {'id': user.id, 'email': user.email}

@app.get('/api/auth/me', response_model=UserResponse)
def auth_me(user: User = Depends(get_current_user)):
    return {'id': user.id, 'email': user.email}

@app.post('/api/auth/logout')
def logout(request: Request, response: Response, db=Depends(get_db), user: User = Depends(get_current_user)):
    revoke_session(db, request.cookies.get('aarogya_session'))
    response.delete_cookie('aarogya_session', path='/api', httponly=True,
        secure=config.SESSION_COOKIE_SECURE, samesite='strict')
    return {'status':'signed_out'}

@app.get('/api/health', response_model=HealthResponse)
def health():
    return {'status':'ok','ai_configured':bool(config.API_KEY),'model':config.MODEL,'demo_mode':config.DEMO_MODE,'free_tier_confirmed':config.FREE_TIER,'ocr_available':ocr_available()}

@app.get('/api/demo/cases', response_model=list[DemoCaseResponse])
def cases():
    return [{'id':id, 'title':v[0], 'description':v[1], 'filename':v[2], 'url':f'/api/demo/cases/{id}/file', 'document_mode':'handwritten' if id in ('handwritten', 'blurry') else 'printed'} for id,v in CASES.items()]

@app.get('/api/demo/cases/{id}/file')
def sample_file(id: str): return FileResponse(sample_path(id), filename=sample_path(id).name)

@app.post('/api/demo/cases/{id}/analyze', response_model=DocumentResponse)
def analyze_sample(id: str, request: DemoRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    path = sample_path(id)
    if request.mode == 'demo':
        text, method, result, info = demo_analysis(id)
    else:
        return live_document(db, path.read_bytes(), path.name, 'handwritten' if id in ('handwritten', 'blurry') else 'printed', user, id)
    return save_doc(db, path.name, text, method, result, request.mode, id, content=path.read_bytes(), processing=info, owner_id=user.id)

@app.post('/api/documents/analyze', response_model=DocumentResponse)
def analyze_upload(file: UploadFile = File(...), document_mode: Literal['printed', 'handwritten'] = Form('printed'), db=Depends(get_db), user: User = Depends(get_current_user)):
    data = file.file.read(MAX_SIZE + 1)
    filename = Path((file.filename or 'document').replace('\\','/')).name
    return live_document(db, data, filename, document_mode, user)

@app.get('/api/documents/{id}', response_model=DocumentResponse)
def document(id: str, db=Depends(get_db), user: User = Depends(get_current_user)):
    doc, _ = current_doc(db, user, id)
    return document_json(doc, db)

@app.get('/api/documents/{id}/file')
def original_file(id: str, db=Depends(get_db), user: User = Depends(get_current_user)):
    doc, _ = current_doc(db, user, id, 'download_document')
    original = db.get(DocumentFile, id)
    if not original and doc.sample_id: return FileResponse(sample_path(doc.sample_id))
    if not original: raise HTTPException(404, 'Original document not found.')
    return Response(original.content, media_type=original.media_type, headers={'X-Content-Type-Options':'nosniff','Content-Disposition':'inline'})

@app.post('/api/documents/{id}/verify', response_model=ReviewResponse)
def review(id: str, request: Review, db=Depends(get_db), user: User = Depends(get_current_user)):
    doc, grant = current_doc(db, user, id)
    if grant:
        raise HTTPException(403, 'Only the patient can review instructions and create a care plan.')
    plan = verify(db, doc, request.decisions)
    return {'plan_id':plan.id, 'status':'Patient Reviewed'}

@app.get('/api/care-plans/{id}', response_model=CarePlanResponse)
def plan(id: str, db=Depends(get_db), user: User = Depends(get_current_user)):
    row, doc, _ = current_plan(db, user, id)
    return care_plan_data(db, user, row, doc)

@app.patch('/api/care-plans/{id}/tasks/{task_id}', response_model=TaskResponse)
def task(id: str, task_id: str, request: TaskUpdate, db=Depends(get_db), user: User = Depends(get_current_user)):
    row = get_or_404(db, CareTask, task_id)
    if row.plan_id != id: raise HTTPException(404, 'Task not found in this plan.')
    care_plan, doc, grant = current_plan(db, user, id, 'complete_task' if row.completed != request.completed else 'view_task')
    if grant and (not grant.can_complete_tasks or row.completed == request.completed):
        raise HTTPException(403, 'This caregiver does not have permission to change task completion.')
    row.completed = request.completed; db.commit()
    db.add(CareTaskEvent(task_id=row.id, actor_id=user.id, action='completed' if row.completed else 'reopened'))
    db.commit()
    return {'id':row.id, 'completed':row.completed}

@app.post('/api/documents/{id}/translate', response_model=TranslationResponse)
def translation(id: str, request: TranslationRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    doc, _ = current_doc(db, user, id)
    key = hashlib.sha256(json.dumps([PIPELINE_VERSION, 'translation-v2', config.MODEL, doc.id, doc.result['summary'], request.language], ensure_ascii=False).encode()).hexdigest()
    with request_lock(key):
        cached = db.get(TranslationCache, key)
        if cached: return cached.result
        result = translate(doc, request.language)
        db.add(TranslationCache(key=key, result=result)); db.commit()
        return result

@app.post('/api/documents/{id}/speech', response_model=SpeechResponse)
def speech(id: str, request: SpeechRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    current_doc(db, user, id)
    return synthesize(request.text, request.language)

@app.get('/api/medicines/approved-use')
def medicine_approved_use(name: str = Query(min_length=2, max_length=100), strength: str = Query(default='', max_length=50)):
    return approved_uses(name, strength)

@app.get('/api/chat/history/{document_id}', response_model=DocumentChatHistory)
def document_chat_history(document_id: str, db=Depends(get_db), user: User = Depends(get_current_user)):
    doc, _ = current_doc(db, user, document_id)
    return chat_history_payload(db, doc)

def chat_history_payload(db, doc):
    messages = db.scalars(select(DocumentChatMessage).where(
        DocumentChatMessage.document_id == doc.id
    ).order_by(DocumentChatMessage.created_at, DocumentChatMessage.id).limit(100)).all()
    return {'document_id': doc.id, 'document_name': doc.filename, 'messages': [
        {'role': m.role, 'content': m.content, 'citations': m.citations or [], 'created_at': m.created_at}
        for m in messages
    ]}

@app.post('/api/chat/document', response_model=DocumentChatHistory)
def document_chat(request: DocumentChatRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    doc, _ = current_doc(db, user, request.document_id)
    messages = db.scalars(select(DocumentChatMessage).where(
        DocumentChatMessage.document_id == doc.id
    ).order_by(DocumentChatMessage.created_at, DocumentChatMessage.id).limit(100)).all()
    previous = [{'role': m.role, 'content': m.content, 'citations': m.citations or []} for m in messages[-8:]]
    answer = ask_document(doc, request.question.strip(), request.language, previous)
    db.add(DocumentChatMessage(document_id=doc.id, role='user', content=request.question.strip(), citations=[]))
    db.add(DocumentChatMessage(document_id=doc.id, role='assistant', content=answer['answer'], citations=answer['citations']))
    db.commit()
    return chat_history_payload(db, doc)

@app.post('/api/caregivers/invite', response_model=CaregiverInviteResponse)
def invite_caregiver(request: CaregiverInviteRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    email = normalize_email(request.email)
    if email == user.email:
        raise HTTPException(422, 'You cannot invite your own account as a caregiver.')
    active = db.scalar(select(CaregiverGrant).where(CaregiverGrant.patient_id == user.id,
        CaregiverGrant.invite_email == email, CaregiverGrant.status.in_(['pending','active'])))
    if active:
        raise HTTPException(409, 'An active or pending caregiver invitation already exists for this email.')
    raw = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=48)
    grant = CaregiverGrant(patient_id=user.id, caregiver_id=None, invite_email=email,
        invite_hash=token_hash(raw), invite_expires_at=expires.isoformat(),
        status='pending', can_complete_tasks=request.can_complete_tasks)
    db.add(grant); db.commit(); db.refresh(grant)
    return {'id':grant.id, 'email':email, 'invite_code':raw, 'expires_at':grant.invite_expires_at}

@app.post('/api/caregivers/accept')
def accept_caregiver_invite(request: CaregiverAcceptRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    grant = db.scalar(select(CaregiverGrant).where(CaregiverGrant.invite_hash == token_hash(request.invite_code), CaregiverGrant.status == 'pending'))
    if not grant or not grant.invite_expires_at or datetime.fromisoformat(grant.invite_expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(400, 'Caregiver invitation is invalid or expired.')
    if normalize_email(grant.invite_email) != user.email or grant.patient_id == user.id:
        raise HTTPException(403, 'This invitation was issued to a different account.')
    grant.caregiver_id = user.id; grant.status = 'active'; grant.invite_hash = None; grant.invite_expires_at = None
    db.add(AccessAudit(actor_id=user.id, patient_id=grant.patient_id, action='caregiver_invitation_accepted'))
    db.commit()
    return {'status':'active'}

@app.get('/api/caregivers')
def caregiver_relations(db=Depends(get_db), user: User = Depends(get_current_user)):
    sent = db.scalars(select(CaregiverGrant).where(CaregiverGrant.patient_id == user.id)).all()
    received = db.scalars(select(CaregiverGrant).where(CaregiverGrant.caregiver_id == user.id, CaregiverGrant.status == 'active')).all()
    def relation(grant, email):
        return {'id':grant.id, 'email':email, 'status':grant.status,
            'can_complete_tasks':grant.can_complete_tasks, 'created_at':grant.created_at}
    return {'caregivers':[relation(g, g.invite_email) for g in sent],
        'patients':[relation(g, db.get(User, g.patient_id).email) for g in received]}

@app.delete('/api/caregivers/{grant_id}')
def revoke_caregiver(grant_id: str, db=Depends(get_db), user: User = Depends(get_current_user)):
    grant = db.get(CaregiverGrant, grant_id)
    if not grant or grant.patient_id != user.id:
        raise HTTPException(404, 'Caregiver access not found.')
    if grant.status != 'revoked':
        grant.status = 'revoked'; grant.revoked_at = datetime.now(timezone.utc).isoformat()
        db.add(AccessAudit(actor_id=user.id, patient_id=user.id, action='caregiver_access_revoked'))
        db.commit()
    return {'status':'revoked'}

@app.get('/api/caregivers/dashboard', response_model=CaregiverDashboardResponse)
def caregiver_dashboard(db=Depends(get_db), user: User = Depends(get_current_user)):
    grants = db.scalars(select(CaregiverGrant).where(CaregiverGrant.caregiver_id == user.id,
        CaregiverGrant.status == 'active')).all()
    patients = []
    for grant in grants:
        owner = db.get(User, grant.patient_id)
        docs = db.scalars(select(Document).where(Document.owner_id == grant.patient_id)).all()
        document_ids = [d.id for d in docs]
        rows = db.scalars(select(CarePlan).where(CarePlan.document_id.in_(document_ids))).all() if document_ids else []
        patient_plans = []
        for row in rows:
            plan_row, doc, _ = current_plan(db, user, row.id, 'caregiver_dashboard_view')
            patient_plans.append(care_plan_data(db, user, plan_row, doc))
        patients.append({'patient_email':owner.email if owner else 'Patient account', 'can_complete_tasks':grant.can_complete_tasks, 'plans':patient_plans})
    return {'patients':patients}
