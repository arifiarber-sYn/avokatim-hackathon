"""One-off backfill (D-033): encrypt plaintext TOTP secrets already in the DB.
Idempotent — encrypted values (enc:v1: prefix) are skipped.
Run:  cd backend && .venv/bin/python scripts/encrypt_totp_secrets.py
"""
import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import _TOTP_ENC_PREFIX, protect_totp_secret  # noqa: E402


async def main() -> None:
    async with SessionLocal() as db:
        users = (
            (await db.execute(select(User).where(User.totp_secret.is_not(None))))
            .scalars()
            .all()
        )
        changed = 0
        for user in users:
            if user.totp_secret.startswith(_TOTP_ENC_PREFIX):
                continue
            user.totp_secret = protect_totp_secret(user.totp_secret)
            changed += 1
        await db.commit()
        print(f"users with TOTP: {len(users)}, encrypted now: {changed}")


asyncio.run(main())
