"""Add gold_discarded table to skip reprocessing low-scoring chunks.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-27
"""

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("""
        CREATE TABLE IF NOT EXISTS gold_discarded (
            id          SERIAL PRIMARY KEY,
            doc_id      TEXT NOT NULL REFERENCES bronze(id),
            chunk_index INTEGER NOT NULL,
            score       INTEGER NOT NULL,
            discarded_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (doc_id, chunk_index)
        )
    """)


def downgrade() -> None:
    from alembic import op
    op.execute("DROP TABLE IF EXISTS gold_discarded")
