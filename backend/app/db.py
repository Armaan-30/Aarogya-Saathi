from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine, String, Text, JSON, Boolean, ForeignKey, LargeBinary, UniqueConstraint, inspect, text as sql_text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import DATABASE_URL

class Base(DeclarativeBase):
    pass

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).isoformat()

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(default=now)

class LoginSession(Base):
    __tablename__ = 'login_sessions'
    token_hash: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    expires_at: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(default=now)

class CaregiverGrant(Base):
    __tablename__ = 'caregiver_grants'
    __table_args__ = (UniqueConstraint('patient_id', 'caregiver_id'),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    caregiver_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True, nullable=True)
    invite_email: Mapped[str] = mapped_column(String)
    invite_hash: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    invite_expires_at: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default='pending')
    can_complete_tasks: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(default=now)
    revoked_at: Mapped[str | None] = mapped_column(String, nullable=True)

class AccessAudit(Base):
    __tablename__ = 'access_audit'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    document_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(default=now)

class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    filename: Mapped[str]
    text: Mapped[str] = mapped_column(Text)
    result: Mapped[dict] = mapped_column(JSON)
    mode: Mapped[str]
    model: Mapped[str]
    extraction: Mapped[str]
    sample_id: Mapped[str | None]
    created_at: Mapped[str] = mapped_column(default=now)

class DocumentFile(Base):
    __tablename__ = 'document_files'
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'), primary_key=True)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    media_type: Mapped[str]

class CarePlan(Base):
    __tablename__ = 'care_plans'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'), unique=True)
    decisions: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)

class DocumentProcessing(Base):
    __tablename__ = 'document_processing'
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'), primary_key=True)
    details: Mapped[dict] = mapped_column(JSON)

class AnalysisCache(Base):
    __tablename__ = 'analysis_cache'
    key: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'))

class TranslationCache(Base):
    __tablename__ = 'translation_cache'
    key: Mapped[str] = mapped_column(String, primary_key=True)
    result: Mapped[dict] = mapped_column(JSON)

class DocumentChatMessage(Base):
    __tablename__ = 'document_chat_messages'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'), index=True)
    role: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(default=now)

class CareTaskEvent(Base):
    __tablename__ = 'care_task_events'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    task_id: Mapped[str] = mapped_column(ForeignKey('care_tasks.id'), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(default=now)

class CareTask(Base):
    __tablename__ = 'care_tasks'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    plan_id: Mapped[str] = mapped_column(ForeignKey('care_plans.id'))
    item: Mapped[dict] = mapped_column(JSON)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
Session = sessionmaker(engine)

def get_db():
    with Session() as session:
        yield session

def migrate_schema():
    """Apply additive SQLite changes while preserving existing user records."""
    Base.metadata.create_all(engine)
    columns = {col['name'] for col in inspect(engine).get_columns('documents')}
    if 'owner_id' not in columns:
        with engine.begin() as connection:
            connection.execute(sql_text('ALTER TABLE documents ADD COLUMN owner_id VARCHAR REFERENCES users(id)'))
    with engine.begin() as connection:
        connection.execute(sql_text('CREATE INDEX IF NOT EXISTS ix_documents_owner_id ON documents (owner_id)'))
