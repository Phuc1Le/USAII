from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

_ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def init_db():
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config(str(_ALEMBIC_INI))
    command.upgrade(alembic_cfg, "head")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    """Database session for code that runs outside a request.

    Background tasks can't reuse the request's session — FastAPI closes it
    when the request finishes. This opens and closes its own.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

