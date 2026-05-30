"""add poster columns

Revision ID: be7b8029410f
Revises: 55e4c873240e
Create Date: 2026-05-30 04:07:14.730540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be7b8029410f'
down_revision: Union[str, Sequence[str], None] = '55e4c873240e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('movies', sa.Column('poster_path', sa.Text(), nullable=True))
    op.add_column('movies', sa.Column('blurhash', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('movies', 'blurhash')
    op.drop_column('movies', 'poster_path')
