"""add users table and projects.user_id

Projects had no owner, so GET /projects returned everyone's projects to everyone.
This adds the ownership column in the three phases a NOT NULL column always needs
on a table that already has rows: add it nullable, fill it in, then tighten it.

Revision ID: d4e5f6071829
Revises: c3d4e5f60718
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6071829'
down_revision: Union[str, None] = 'c3d4e5f60718'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# projects that predate ownership are handed to this user rather than deleted
LEGACY_USER_NAME = 'local-dev'
LEGACY_CLIENT_KEY = 'legacy-local-dev'


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_key', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        # a unique constraint already creates the index it needs to enforce itself,
        # so no separate create_index here
        sa.UniqueConstraint('client_key', name='uq_users_client_key'),
    )

    # Phase 1: nullable, because the rows that already exist have no value to put here
    with op.batch_alter_table('projects') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))

    # Phase 2: give every existing project an owner
    connection = op.get_bind()
    orphan_count = connection.execute(
        sa.text('SELECT COUNT(*) FROM projects')
    ).scalar_one()

    if orphan_count:
        connection.execute(
            sa.text('INSERT INTO users (client_key, display_name) VALUES (:key, :name)'),
            {'key': LEGACY_CLIENT_KEY, 'name': LEGACY_USER_NAME},
        )
        legacy_user_id = connection.execute(
            sa.text('SELECT id FROM users WHERE client_key = :key'),
            {'key': LEGACY_CLIENT_KEY},
        ).scalar_one()
        connection.execute(
            sa.text('UPDATE projects SET user_id = :user_id WHERE user_id IS NULL'),
            {'user_id': legacy_user_id},
        )

    # Phase 3: now that no row is empty, the column can be required. The foreign key
    # is added here too — SQLite can only do that inside a batch (table rebuild).
    with op.batch_alter_table('projects') as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key('fk_projects_user_id', 'users', ['user_id'], ['id'])
        batch_op.create_index('ix_projects_user_id', ['user_id'])


def downgrade() -> None:
    with op.batch_alter_table('projects') as batch_op:
        batch_op.drop_index('ix_projects_user_id')
        batch_op.drop_constraint('fk_projects_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
    op.drop_table('users')
