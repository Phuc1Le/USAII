"""unique (step_id, order_index) on tasks

Tasks are generated lazily the first time a step's task list is read. Two
concurrent reads both saw an empty list and both inserted a full set, leaving
duplicated tasks. The constraint makes the second insert fail instead, and the
route falls back to whichever set landed first.

Revision ID: c3d4e5f60718
Revises: b2c3d4e5f607
Create Date: 2026-08-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f60718'
down_revision: Union[str, None] = 'b2c3d4e5f607'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch mode: SQLite cannot ALTER TABLE ADD CONSTRAINT, so Alembic rebuilds
    # the table. On PostgreSQL this compiles down to a plain ALTER TABLE.
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.create_unique_constraint('uq_tasks_step_order', ['step_id', 'order_index'])


def downgrade() -> None:
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.drop_constraint('uq_tasks_step_order', type_='unique')
