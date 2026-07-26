"""add embedding column to decisions

Revision ID: 9d3996724e5e
Revises: b495b358d1c0
Create Date: 2026-07-26 17:21:20.741715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '9d3996724e5e'
down_revision: Union[str, None] = 'b495b358d1c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Prerequisite: a superuser must run this first on the database:
    #   CREATE EXTENSION IF NOT EXISTS vector;
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        op.add_column('decisions', sa.Column('embedding', Vector(768), nullable=True))


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        op.drop_column('decisions', 'embedding')
