from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import re
import secrets
from fastapi import HTTPException, Request
from sqlalchemy import select
from .. import config
from ..db import LoginSession, User, get_db
from fastapi import Depends

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if not re.fullmatch(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+", value, re.I):
        raise HTTPException(422, 'Enter a valid email address.')
    return value

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f'scrypt$16384$8$1${salt.hex()}${key.hex()}'

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, key_hex = encoded.split('$')
        if scheme != 'scrypt':
            return False
        candidate = hashlib.scrypt(password.encode('utf-8'), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p), dklen=len(bytes.fromhex(key_hex)))
        return hmac.compare_digest(candidate.hex(), key_hex)
    except (ValueError, TypeError):
        return False

def issue_session(db, user: User) -> str:
    raw = secrets.token_urlsafe(40)
    expires = datetime.now(timezone.utc) + timedelta(hours=config.SESSION_TTL_HOURS)
    db.add(LoginSession(token_hash=token_hash(raw), user_id=user.id, expires_at=expires.isoformat()))
    db.commit()
    return raw

def revoke_session(db, raw: str | None) -> None:
    if not raw:
        return
    session = db.get(LoginSession, token_hash(raw))
    if session:
        db.delete(session)
        db.commit()

def get_current_user(request: Request, db=Depends(get_db)) -> User:
    token = request.cookies.get('aarogya_session')
    if not token:
        auth = request.headers.get('authorization', '')
        if auth.lower().startswith('bearer '):
            token = auth[7:].strip()
    if not token:
        raise HTTPException(401, 'Please sign in to access this care record.')
    session = db.get(LoginSession, token_hash(token))
    if not session:
        raise HTTPException(401, 'Your session has expired. Please sign in again.')
    try:
        if datetime.fromisoformat(session.expires_at) <= datetime.now(timezone.utc):
            db.delete(session)
            db.commit()
            raise HTTPException(401, 'Your session has expired. Please sign in again.')
    except ValueError:
        db.delete(session)
        db.commit()
        raise HTTPException(401, 'Your session has expired. Please sign in again.') from None
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, 'Account not found. Please sign in again.')
    return user
