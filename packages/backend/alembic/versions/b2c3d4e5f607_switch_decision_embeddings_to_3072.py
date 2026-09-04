"""switch decision embeddings to gemini-embedding-001 (3072 dims)

The embedding model changed from text-embedding-004 (768 dims) to
gemini-embedding-001 (3072 dims). The column must be resized, and any
existing 768-dim vectors are incompatible with the new model's queries,
so they are cleared (re-embed via app.backfill_embeddings).

Revision ID: b2c3d4e5f607
Revises: a1b2c3d4e5f6
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f607'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        # 768-dim vectors can't be cast to 3072; drop them and re-embed via backfill
        op.execute("UPDATE decisions SET embedding = NULL")
        op.execute("ALTER TABLE decisions ALTER COLUMN embedding TYPE vector(3072)")


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        op.execute("UPDATE decisions SET embedding = NULL")
        op.execute("ALTER TABLE decisions ALTER COLUMN embedding TYPE vector(768)")
