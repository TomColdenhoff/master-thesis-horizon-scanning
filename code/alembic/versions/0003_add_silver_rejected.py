"""Add silver_rejected table to track classifier rejections per profile version.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-26
"""

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("""
        CREATE TABLE IF NOT EXISTS silver_rejected (
            id              SERIAL PRIMARY KEY,
            doc_id          TEXT NOT NULL REFERENCES bronze(id),
            profile_version TEXT NOT NULL,
            reason          TEXT,
            rejected_at     TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (doc_id, profile_version)
        )
    """)


def downgrade() -> None:
    from alembic import op
    op.execute("DROP TABLE IF EXISTS silver_rejected")
