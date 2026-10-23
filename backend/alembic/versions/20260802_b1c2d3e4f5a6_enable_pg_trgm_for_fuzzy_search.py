"""Enable pg_trgm for typo-tolerant global search (D-054 F5)

Revision ID: b1c2d3e4f5a6
Revises: 722e96516f77
Create Date: 2026-08-02

"""
from alembic import op

revision = "b1c2d3e4f5a6"
down_revision = "722e96516f77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # GIN trigram indexes on the hottest fuzzy-search columns
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_matters_title_trgm "
        "ON matters USING gin (lower(title) gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_contacts_display_name_trgm "
        "ON contacts USING gin (lower(display_name) gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_deadlines_title_trgm "
        "ON deadlines USING gin (lower(title) gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_deadlines_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_contacts_display_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_matters_title_trgm")
    # Extension left in place (other objects may rely on it)
