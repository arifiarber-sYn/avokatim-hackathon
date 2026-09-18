"""List visible lawyer profiles joined with their user (read-only, for the demo send)."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text  # noqa: E402
from app.config import settings  # noqa: E402

eng = create_engine(settings.database_url)
q = """
SELECT lp.id::text AS profile_id,
       u.email,
       u.full_name,
       u.role,
       u.is_active AS user_active,
       lp.is_visible,
       lp.verification_status,
       lp.is_founder,
       t.name AS tenant_name
FROM lawyer_profiles lp
JOIN users u ON u.id = lp.user_id
LEFT JOIN tenants t ON t.id = lp.tenant_id
WHERE lp.is_visible = true
ORDER BY u.email
"""
with eng.connect() as c:
    rows = [dict(r._mapping) for r in c.execute(text(q))]

print(json.dumps({"count": len(rows), "rows": rows}, ensure_ascii=False, indent=2))
