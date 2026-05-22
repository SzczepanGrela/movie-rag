"""create chunks table with pgvector

Revision ID: e659f1b857ca
Revises: 61d6b7fba916
Create Date: 2026-05-22 22:54:39.649473

"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e659f1b857ca'
down_revision: Union[str, Sequence[str], None] = '61d6b7fba916'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('chunks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_text_id', sa.Integer(), nullable=False),
    sa.Column('movie_id', sa.Integer(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('token_count', sa.Integer(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['movie_id'], ['movies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_text_id'], ['source_texts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_text_id', 'chunk_index')
    )
    op.create_index(op.f('ix_chunks_movie_id'), 'chunks', ['movie_id'], unique=False)
    op.create_index(op.f('ix_chunks_source_text_id'), 'chunks', ['source_text_id'], unique=False)
    op.execute(
        "CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS chunks_embedding_hnsw")
    op.drop_index(op.f('ix_chunks_source_text_id'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_movie_id'), table_name='chunks')
    op.drop_table('chunks')
