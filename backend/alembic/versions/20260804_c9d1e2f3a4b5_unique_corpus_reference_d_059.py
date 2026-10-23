"""Unique (jurisdiction, reference, region) on legal_corpus_docs (D-059 F2).

Before growing the DE corpus to 100k+ decisions, duplicates must be
impossible at the DB level — importers dedup in memory today, which breaks
on concurrent/resumed runs. A partial unique index (reference IS NOT NULL)
with COALESCE(region, '') so federal docs (region NULL) also collide.
Pre-existing duplicates are removed first, keeping the oldest doc
(chunks cascade via FK).

Revision ID: c9d1e2f3a4b5
Revises: b701cbe9cae5
Create Date: 2026-08-04
"""
from alembic import op

revision = "c9d1e2f3a4b5"
down_revision = "b701cbe9cae5"
branch_labels = None
depends_on = None

INDEX_NAME = "uq_legal_corpus_docs_jur_ref_region"


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM legal_corpus_docs d
        USING (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY jurisdiction_id, reference, COALESCE(region, '')
                ORDER BY created_at ASC, id
            ) AS rn
            FROM legal_corpus_docs
            WHERE reference IS NOT NULL
        ) x
        WHERE d.id = x.id AND x.rn > 1
        """
    )
    op.execute(
        f"""
        CREATE UNIQUE INDEX {INDEX_NAME}
        ON legal_corpus_docs (jurisdiction_id, reference, COALESCE(region, ''))
        WHERE reference IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
