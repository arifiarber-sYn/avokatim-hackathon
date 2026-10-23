"""Enable Row-Level Security on all tenant-scoped tables (D-033).

Policy design (differs from a pure per-org SaaS): AvokatIM has legitimate
cross-tenant reads — the public lawyer directory, landing stats, background
reminder loops and the /platform admin. The policy is therefore DEFAULT-OPEN:
with no app.tenant_id setting the table behaves exactly as before. As soon as
deps.get_current_user pins the session to a tenant (set_config transaction-
local), Postgres itself refuses rows of any other tenant — defense in depth
against a forgotten WHERE clause in authenticated lawyer endpoints.

The app connects as the non-superuser role avokatim_app (NOBYPASSRLS);
FORCE RLS keeps even the owner role subject to the policies.

Revision ID: a1b2c3d4e5f6
Revises: ae0a6921092d
Create Date: 2026-07-31
"""
import sqlalchemy as sa

from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "ae0a6921092d"
branch_labels = None
depends_on = None

# nullif(..., '') everywhere: after a transaction-local set_config reverts,
# the GUC reads as '' (not NULL), and Postgres does NOT short-circuit OR —
# a bare ''::uuid cast in the second arm would raise. nullif makes both arms
# evaluation-safe while keeping the uuid comparison index-friendly.
# "tenant_id IS NULL" rows are platform-shared data (global document
# templates, platform-level audit events) and stay visible to everyone.
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
    for table in _tenant_tables(conn):
        conn.execute(sa.text(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"'))
        conn.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        conn.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
