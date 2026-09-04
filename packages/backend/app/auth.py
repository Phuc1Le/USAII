"""Who is calling, and how they proved it.

Two ways in, and which one applies depends on the account:

  - An account with no password is anonymous. It is identified by the X-User-Id
    header the client generated for itself. This is identification only — the
    client asserts who it is and the backend believes it.
  - An account with a password can only be reached with a signed token. The
    header stops working for it the moment credentials are attached, so signing
    up cannot leave a way in that skips the password.

That rule is what lets login be added to a running app: drafts made before
anyone registered keep working, real accounts are protected immediately, and
there is never a window where both are true of the same account.
"""

from datetime import datetime, timedelta, timezone
import logging

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from app.database import get_db

logger = logging.getLogger(__name__)

MAX_CLIENT_KEY_LENGTH = 200
# Used only when JWT_SECRET is unset, so local development runs without setup.
# Tokens signed with it are worthless anywhere else, which is the point.
_DEV_SECRET = "dev-only-insecure-secret"


def _signing_secret() -> str:
    return JWT_SECRET or _DEV_SECRET


# ── passwords ─────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Turn a password into something safe to store.

    bcrypt is deliberately slow and salts every hash, so two people with the
    same password get different stored values and guessing is expensive. The
    salt is part of the output, which is why verify_password needs no second
    column to check against.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # stored value isn't a valid bcrypt hash — treat as a failed login
        # rather than a crash
        return False


# ── tokens ────────────────────────────────────────────────────────

def create_access_token(user: models.User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),          # subject: who the token is about
        "iat": now,                   # issued at
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),   # expiry
    }
    return jwt.encode(payload, _signing_secret(), algorithm=JWT_ALGORITHM)


def _user_id_from_token(token: str) -> int:
    try:
        payload = jwt.decode(token, _signing_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — please sign in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    subject = payload.get("sub")
    try:
        return int(subject)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


# ── identifying the caller ────────────────────────────────────────

def _user_from_client_key(db: Session, key: str) -> models.User:
    user = db.query(models.User).filter(models.User.client_key == key).first()
    if user:
        return user

    # first time we've seen this key: create the user it stands for
    user = models.User(client_key=key, display_name=key[:12])
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # two requests from the same new client raced; uq_users_client_key made
        # one of them lose, and the winner's row is the one we want
        db.rollback()
        return db.query(models.User).filter(models.User.client_key == key).one()

    db.refresh(user)
    return user


def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise HTTPException(status_code=401, detail="Authorization must be 'Bearer <token>'")
        user = db.query(models.User).filter(models.User.id == _user_id_from_token(token.strip())).first()
        if not user:
            # the account was deleted after the token was handed out
            raise HTTPException(status_code=401, detail="Invalid token")
        return user

    key = (x_user_id or "").strip()
    if not key:
        raise HTTPException(
            status_code=401,
            detail="Not signed in — send an Authorization header, or an X-User-Id for an anonymous session.",
        )
    if len(key) > MAX_CLIENT_KEY_LENGTH:
        # the key is client-supplied and goes straight into an indexed column;
        # cap it rather than letting an arbitrarily long value through
        raise HTTPException(status_code=400, detail="X-User-Id is too long")

    user = _user_from_client_key(db, key)
    if user.password_hash:
        # This account has credentials, so the header no longer speaks for it —
        # otherwise anyone who learned the client_key could bypass the password.
        raise HTTPException(
            status_code=401,
            detail="This account has a password — sign in to continue.",
        )
    return user
