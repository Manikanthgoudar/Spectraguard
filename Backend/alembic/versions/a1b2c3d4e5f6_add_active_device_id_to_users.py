"""add_active_device_id_to_users

Revision ID: a1b2c3d4e5f6
Revises: 17c8bb04bab1
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '17c8bb04bab1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('active_device_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'active_device_id')
