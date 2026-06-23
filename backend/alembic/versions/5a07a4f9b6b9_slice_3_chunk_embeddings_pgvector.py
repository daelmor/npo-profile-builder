"""slice 3: chunk embeddings (pgvector)

Revision ID: 5a07a4f9b6b9
Revises: 54afb9967965
Create Date: 2026-06-23 01:05:12.900786

"""
from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5a07a4f9b6b9'
down_revision: str | None = '54afb9967965'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "source_chunks",
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
    )
    # Approximate-nearest-neighbour index for cosine similarity search.
    op.execute(
        "CREATE INDEX ix_source_chunks_embedding "
        "ON source_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_index("ix_source_chunks_embedding", table_name="source_chunks")
    op.drop_column("source_chunks", "embedding")
