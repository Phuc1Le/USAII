"""add email and password_hash to users

Registration attaches credentials to the user row that already exists for the
caller's client_key, so nobody loses the projects they made before signing up.
Both columns stay nullable: a row is created on a visitor's first request and
has no credentials until they choose to register.

Revision ID: e5f607182930
Revises: d4e5f6071829
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f607182930'
down_revision: Union[str, None] = 'd4e5f6071829'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('password_hash', sa.String(), nullable=True))

    # Unique, but on a nullable column: SQL treats NULLs as distinct from each
    # other, so every anonymous user can have no email while two accounts can
    # never share one.
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_email', table_name='users')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('password_hash')
        batch_op.drop_column('email')
