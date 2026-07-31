from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.config import settings

# The app connects as the non-superuser role (database_app_url) so Postgres
# Row-Level Security applies; Alembic/scripts keep the owner role via
# database_url (D-033).
engine = create_async_engine(
    settings.database_app_url or settings.database_url, pool_pre_ping=True
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ---------- RLS tenant context (D-033) ----------
# The policies are default-open: with no app.tenant_id set, queries behave as
# before (public directory, background loops, platform admin all read across
# tenants). Once a session is scoped to a tenant, Postgres itself refuses
# rows of other tenants — defense in depth against a forgotten WHERE clause.

_RLS_INFO_KEY = "rls_tenant_id"
# set_config(..., true) is transaction-local, so the setting can never leak
# through the connection pool; the listener below re-arms it for every new
# transaction on a scoped session.
_SET_TENANT_SQL = text("select set_config('app.tenant_id', :tid, true)")


@event.listens_for(Session, "after_begin")
def _apply_rls_tenant(session: Session, transaction, connection) -> None:
    tid = session.info.get(_RLS_INFO_KEY)
    if tid:
        connection.execute(_SET_TENANT_SQL, {"tid": tid})


async def scope_session_to_tenant(db: AsyncSession, tenant_id) -> None:
    """Pin every subsequent transaction of this session to one tenant at the
    database level. Called from deps.get_current_user after authentication."""
    db.sync_session.info[_RLS_INFO_KEY] = str(tenant_id)
    # the current transaction is already open (after_begin has fired), so
    # apply the setting to it directly as well
    await db.execute(_SET_TENANT_SQL, {"tid": str(tenant_id)})


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
