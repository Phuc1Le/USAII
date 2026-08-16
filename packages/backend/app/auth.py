"""Who is calling.

This is identification, not authentication: the client asserts who it is with the
X-User-Id header and the backend takes its word for it. That is enough to keep one
person's projects out of another person's list, and it is NOT enough to keep a
determined person out of someone else's data — anyone can send another key.

When real login lands, only `get_current_user` changes: it reads the subject of a
verified token instead of a header. Everything that filters by `user.id` stays as is.
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

MAX_CLIENT_KEY_LENGTH = 200


def get_current_user(
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    key = (x_user_id or "").strip()
    if not key:
        raise HTTPException(
            status_code=400,
            detail="Missing X-User-Id header — the client must send a stable id it generated.",
        )
    if len(key) > MAX_CLIENT_KEY_LENGTH:
        # the key is client-supplied and goes straight into an indexed column;
        # cap it rather than letting an arbitrarily long value through
        raise HTTPException(status_code=400, detail="X-User-Id is too long")

    user = db.query(models.User).filter(models.User.client_key == key).first()
    if user:
        return user

    # first time we've seen this key: create the user it stands for
    user = models.User(client_key=key, display_name=key[:12])
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # two requests from the same new client raced; uq_users_client_key made one
        # of them lose, and the winner's row is the one we want
        db.rollback()
        user = db.query(models.User).filter(models.User.client_key == key).one()
        return user

    db.refresh(user)
    return user
