"""add embedding column to decisions for sqlite

The postgres-only migration 9d3996724e5e created the column on PostgreSQL
but skipped SQLite, so the model's Vector(768) column had no table backing on
SQLite and every decision INSERT failed. pgvector's Vector type works on
SQLite for storage, so add the column there too.

Revision ID: a1b2c3d4e5f6
Revises: 9156c80a53ec
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9156c80a53ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == 'sqlite':
        op.add_column('decisions', sa.Column('embedding', Vector(768), nullable=True))


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == 'sqlite':
        op.drop_column('decisions', 'embedding')
