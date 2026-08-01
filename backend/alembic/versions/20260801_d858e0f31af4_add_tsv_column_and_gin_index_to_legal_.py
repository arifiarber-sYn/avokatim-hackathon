"""add tsv column and GIN index to legal_corpus_chunks

Hybrid legal retrieval (D-042): BM25-style full-text search next to the
pgvector cosine search, fused with Reciprocal Rank Fusion in rag.py.
The tsvector uses the `german` config for German documents (stemming,
compound-friendly) and `simple` for everything else (Albanian has no
built-in config). Backfills existing chunks from the parent doc language.

Revision ID: d858e0f31af4
Revises: 39eb3d97a67c
Create Date: 2026-08-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd858e0f31af4'
down_revision = '39eb3d97a67c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "legal_corpus_chunks", sa.Column("tsv", postgresql.TSVECTOR(), nullable=True)
    )
    op.execute(
        """
        UPDATE legal_corpus_chunks c
        SET tsv = to_tsvector(
            CASE WHEN d.language = 'de' THEN 'german' ELSE 'simple' END::regconfig,
            c.text
        )
        FROM legal_corpus_docs d
        WHERE d.id = c.doc_id
        """
    )
    op.create_index(
        "ix_legal_corpus_chunks_tsv",
        "legal_corpus_chunks",
        ["tsv"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_legal_corpus_chunks_tsv", table_name="legal_corpus_chunks")
    op.drop_column("legal_corpus_chunks", "tsv")
