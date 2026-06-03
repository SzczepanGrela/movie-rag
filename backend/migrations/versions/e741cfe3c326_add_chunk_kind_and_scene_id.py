"""add chunk kind and scene_id

Revision ID: e741cfe3c326
Revises: be7b8029410f
Create Date: 2026-06-04 00:19:02.423713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e741cfe3c326'
down_revision: Union[str, Sequence[str], None] = 'be7b8029410f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chunks",
        sa.Column("kind", sa.Text(), nullable=False, server_default="plot"),
    )
    op.alter_column("chunks", "source_text_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("chunks", sa.Column("scene_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_chunks_scene_id", "chunks", "scenes", ["scene_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index(
        "ux_chunks_scene_id",
        "chunks",
        ["scene_id"],
        unique=True,
        postgresql_where=sa.text("scene_id IS NOT NULL"),
    )
    # Pre-migration every chunk has a source_text_id (column was NOT NULL), so the
    # join reaches all rows; the server_default covers any future NULL-source row.
    op.execute(
        """
        UPDATE chunks c SET kind = CASE s.source
            WHEN 'wikipedia' THEN 'plot'
            WHEN 'tmdb_overview' THEN 'overview'
            ELSE 'plot' END
        FROM source_texts s WHERE s.id = c.source_text_id
        """
    )


def downgrade() -> None:
    op.drop_index("ux_chunks_scene_id", table_name="chunks")
    op.drop_constraint("fk_chunks_scene_id", "chunks", type_="foreignkey")
    op.drop_column("chunks", "scene_id")
    op.execute("DELETE FROM chunks WHERE source_text_id IS NULL")
    op.alter_column("chunks", "source_text_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("chunks", "kind")
