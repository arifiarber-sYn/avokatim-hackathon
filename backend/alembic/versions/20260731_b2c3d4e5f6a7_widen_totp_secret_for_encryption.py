"""Widen users.totp_secret so Fernet-encrypted values fit (D-033).

The backfill that encrypts existing plaintext secrets runs separately
(scripts/encrypt_totp_secrets.py) so the migration stays crypto-free.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-31
"""
import sqlalchemy as sa

from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "totp_secret",
        existing_type=sa.String(64),
        type_=sa.String(255),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "totp_secret",
        existing_type=sa.String(255),
        type_=sa.String(64),
        existing_nullable=True,
    )
