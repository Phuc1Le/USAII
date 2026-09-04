# packages/backend/app/backfill_embeddings.py
#
# One-off backfill for Decision.embedding: computes embeddings for every
# decision row where the column is still NULL.
#
#     python -m app.backfill_embeddings        # from packages/backend, venv active
#
# PostgreSQL + pgvector required (the embedding column is not created on
# SQLite). Safe to re-run: rows with a non-NULL embedding are skipped.

import time

from sqlalchemy import select, func

from app import models
from app.database import engine, session_scope
from app import agent_client


def backfill(batch_size: int = 10, sleep_seconds: float = 0.2) -> int:
    if engine.dialect.name != "postgresql":
        print(
            f"skipping backfill: pgvector requires postgresql (dialect={engine.dialect.name})"
        )
        return 0

    total = 0
    while True:
        with session_scope() as db:
            rows = (
                db.execute(
                    select(models.Decision)
                    .where(models.Decision.embedding.is_(None))
                    .order_by(models.Decision.id)
                    .limit(batch_size)
                )
                .scalars()
                .all()
            )
            if not rows:
                break
            for decision in rows:
                try:
                    embedding = agent_client.embed_text(decision.content)
                except Exception as exc:
                    print(f"  [error] decision {decision.id}: {exc}")
                    continue
                db.execute(
                    models.Decision.__table__.update()
                    .where(models.Decision.id == decision.id)
                    .values(embedding=embedding)
                )
                db.commit()
                total += 1
                print(f"  embedded decision {decision.id}")
        time.sleep(sleep_seconds)

    return total


if __name__ == "__main__":
    with session_scope() as db:
        pending = db.query(func.count(models.Decision.id)).filter(
            models.Decision.embedding.is_(None)
        ).scalar()
        print(f"decisions missing embeddings: {pending}")
    done = backfill()
    print(f"backfill complete: {done} rows embedded")
