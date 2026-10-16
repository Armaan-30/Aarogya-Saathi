from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Item(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str
    kind: Literal['medicine', 'instruction', 'follow_up', 'warning']
    category: Literal['medicine', 'follow_up', 'precaution', 'diet', 'activity', 'warning', 'other'] | None = None
    title: str
    wording: str
    source: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    timing: str | None = None
    date: str | None = None
    uncertain: bool = False
    concerns: list[str] = Field(default_factory=list)
    professional_verification_required: bool = False

class Analysis(BaseModel):
    model_config = ConfigDict(extra='forbid')
    document_type: str
    summary: str
    items: list[Item]
    uncertainties: list[str] = Field(default_factory=list)

class Review(BaseModel):
    decisions: dict[str, Literal['reviewed', 'clarify']]

class TaskUpdate(BaseModel):
    completed: bool

class AuthRegister(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    invite_code: str | None = Field(default=None, min_length=20, max_length=200)

class AuthLogin(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)

class AuthStatus(BaseModel):
    setup_required: bool

class UserResponse(BaseModel):
    id: str
    email: str

class CaregiverInviteRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    can_complete_tasks: bool = True

class CaregiverAcceptRequest(BaseModel):
    invite_code: str = Field(min_length=20, max_length=200)

class CaregiverResponse(BaseModel):
    id: str
    email: str
    status: Literal['active', 'revoked']
    can_complete_tasks: bool
    created_at: str

class CaregiverInviteResponse(BaseModel):
    id: str
    email: str
    invite_code: str
    expires_at: str

class ReminderStatus(BaseModel):
    state: Literal['completed', 'today', 'upcoming', 'overdue', 'date_only', 'unscheduled']
    scheduled_for: str | None = None

class TranslationRequest(BaseModel):
    language: Literal['en', 'hi', 'mr']

class SpeechRequest(BaseModel):
    language: Literal['hi', 'mr']
    text: str = Field(min_length=1, max_length=5000)

class SpeechResponse(BaseModel):
    language: Literal['hi', 'mr']
    mime_type: Literal['audio/wav'] = 'audio/wav'
    audio_base64: str

class DocumentChatRequest(BaseModel):
    document_id: str = Field(min_length=1, max_length=36)
    question: str = Field(min_length=2, max_length=1200)
    language: Literal['en', 'hi', 'mr'] = 'en'

class DocumentChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=4000)
    citations: list[str] = Field(default_factory=list)
    created_at: str

class DocumentChatHistory(BaseModel):
    document_id: str
    document_name: str
    messages: list[DocumentChatMessage]

class ChatCitation(BaseModel):
    quote: str = Field(min_length=1, max_length=500)

class ChatAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=3000)
    citations: list[ChatCitation] = Field(default_factory=list, max_length=4)

class Translation(BaseModel):
    explanation: str

class DemoRequest(BaseModel):
    mode: Literal['demo', 'live'] = 'demo'

class VisionTranscription(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(max_length=40000)
    unreadable_regions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class ProcessingInfo(BaseModel):
    document_mode: Literal['printed', 'handwritten'] = 'printed'
    methods: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unreadable_regions: list[str] = Field(default_factory=list)
    preprocessing: list[str] = Field(default_factory=list)
    vision_model: str | None = None
    image_input_verified: bool = False
    provenance: str = 'Source text requires patient review.'

class HealthResponse(BaseModel):
    status: str
    ai_configured: bool
    model: str
    demo_mode: bool
    free_tier_confirmed: bool
    ocr_available: bool

class DocumentResponse(BaseModel):
    id: str
    filename: str
    extracted_text: str
    analysis: Analysis
    mode: Literal['demo', 'live']
    model: str
    extraction: str
    sample_id: str | None
    created_at: str
    processing: ProcessingInfo = Field(default_factory=ProcessingInfo)
    reused: bool = False

class DemoCaseResponse(BaseModel):
    id: str
    title: str
    description: str
    filename: str
    url: str
    document_mode: Literal['printed', 'handwritten'] = 'printed'

class ReviewResponse(BaseModel):
    plan_id: str
    status: Literal['Patient Reviewed']

class TaskResponse(BaseModel):
    id: str
    completed: bool

class CareTaskResponse(TaskResponse):
    item: Item
    reminder: ReminderStatus = Field(default_factory=lambda: ReminderStatus(state='unscheduled'))

class CarePlanResponse(BaseModel):
    id: str
    document: DocumentResponse
    decisions: dict[str, Literal['reviewed', 'clarify']]
    tasks: list[CareTaskResponse]
    clarifications: list[Item]
    warnings: list[Item]

class CaregiverPatientResponse(BaseModel):
    patient_email: str
    can_complete_tasks: bool
    plans: list[CarePlanResponse]

class CaregiverDashboardResponse(BaseModel):
    patients: list[CaregiverPatientResponse]

class TranslationResponse(Translation):
    language: Literal['en', 'hi', 'mr']
    mode: Literal['demo', 'live']
