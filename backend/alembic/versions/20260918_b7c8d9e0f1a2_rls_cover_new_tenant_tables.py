"""Re-apply Row-Level Security across tenant tables (audit 2026-09-18).

Five tables added after the original RLS wave (a1b2c3d4e5f6) were created
without policies: email_suggestions, deadline_suggestions, notifications,
passkey_credentials, api_tokens (found by scripts/isolation_check.py).
This migration re-runs the same discovery + DEFAULT-OPEN policy over every
table with a tenant_id column, so it both fixes the five and future-proofs
a re-run. Policy semantics identical to a1b2c3d4e5f6 (see its docstring).

Revision ID: b7c8d9e0f1a2
Revises: f5a6b7c8d9e0
Create Date: 2026-09-18
"""
import sqlalchemy as sa

from alembic import op

revision = "b7c8d9e0f1a2"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None

# The five tables this revision is about — downgrade only reverts these,
# leaving the original wave (a1b2c3d4e5f6) intact.
_NEW_TABLES = [
    "email_suggestions",
    "deadline_suggestions",
    "notifications",
    "passkey_credentials",
    "api_tokens",
]

_POLICY = """
CREATE POLICY tenant_isolation ON "{table}"
    USING (
        nullif(current_setting('app.tenant_id', true), '') IS NULL
        OR tenant_id IS NULL
        OR tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
    )
    WITH CHECK (
        nullif(current_setting('app.tenant_id', true), '') IS NULL
        OR tenant_id IS NULL
        OR tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
    )
"""


def _tenant_tables(conn) -> list[str]:
    return (
        conn.execute(
            sa.text(
                "select table_name from information_schema.columns "
                "where table_schema = 'public' and column_name = 'tenant_id' "
                "order by table_name"
            )
        )
        .scalars()
        .all()
    )


def upgrade() -> None:
    conn = op.get_bind()
    for table in _tenant_tables(conn):
        conn.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        conn.execute(sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
        conn.execute(sa.text(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"'))
        conn.execute(sa.text(_POLICY.format(table=table)))


def downgrade() -> None:
    conn = op.get_bind()
    for table in _NEW_TABLES:
        conn.execute(sa.text(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"'))
        conn.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        conn.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
