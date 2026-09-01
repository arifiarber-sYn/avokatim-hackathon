"""add tsv column and GIN index to document_chunks

Hybrid retrieval for matter documents (extends D-042): the legal corpus has
had BM25-style full-text search fused with vector search since 2026-08-01,
but matter-document search stayed vector-only. Matter documents are
multilingual (sq/de/sr/...) and carry no language column, so the 'simple'
config (exact words, no stemming) is used — predictable for every language;
the vector leg covers paraphrases.

Revision ID: e4f5a6b7c8d9
Revises: d2e3f4a5b6c7
Create Date: 2026-09-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e4f5a6b7c8d9'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_chunks", sa.Column("tsv", postgresql.TSVECTOR(), nullable=True)
    )
    op.execute("UPDATE document_chunks SET tsv = to_tsvector('simple', text)")
    op.create_index(
        "ix_document_chunks_tsv",
        "document_chunks",
        ["tsv"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_document_chunks_tsv", table_name="document_chunks")
    op.drop_column("document_chunks", "tsv")
