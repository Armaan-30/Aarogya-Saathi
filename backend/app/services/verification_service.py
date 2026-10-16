from fastapi import HTTPException
from sqlalchemy import select
from ..db import CarePlan, CareTask, DocumentProcessing
from ..schemas import Analysis, ProcessingInfo
from .safety import validate_grounding, apply_processing_safety

def verify(db, doc, decisions):
    result = validate_grounding(Analysis.model_validate(doc.result), doc.text)
    processing = db.get(DocumentProcessing, doc.id)
    if processing:
        result = apply_processing_safety(result, ProcessingInfo.model_validate(processing.details))
    if set(decisions) != {i.id for i in result.items}:
        raise HTTPException(422, 'Review every item before creating a recovery plan.')
    for item in result.items:
        if (item.uncertain or item.professional_verification_required) and decisions[item.id] == 'reviewed':
            raise HTTPException(422, 'Uncertain instructions must be marked for professional clarification.')
    existing = db.scalar(select(CarePlan).where(CarePlan.document_id == doc.id))
    if existing:
        if existing.decisions != decisions: raise HTTPException(409, 'This review is already saved. Start a new analysis to change it.')
        return existing
    plan = CarePlan(document_id=doc.id, decisions=decisions)
    db.add(plan); db.flush()
    for item in result.items:
        if decisions[item.id] == 'reviewed' and item.kind != 'warning':
            db.add(CareTask(plan_id=plan.id, item=item.model_dump(), completed=False))
    db.commit(); db.refresh(plan)
    return plan
