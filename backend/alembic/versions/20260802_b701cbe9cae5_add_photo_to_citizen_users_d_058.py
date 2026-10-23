"""Add photo to citizen_users (D-058)

Revision ID: b701cbe9cae5
Revises: b1c2d3e4f5a6
Create Date: 2026-08-02 13:31:01.351549

"""
from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


revision = 'b701cbe9cae5'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Profile photo as a data URL, fetched server-side from the OAuth
    # provider. (The trigram-index drops autogenerate suggested are wrong —
    # those indexes are managed by the fuzzy-search migration, not models.)
    op.add_column('citizen_users', sa.Column('photo', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('citizen_users', 'photo')
