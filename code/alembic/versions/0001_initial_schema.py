"""Initial schema — bronze, silver, gold tables.

Revision ID: 0001
Revises:
Create Date: 2026-04-20
"""

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("""
        CREATE TABLE IF NOT EXISTS bronze (
            id              TEXT PRIMARY KEY,
            soort           TEXT NOT NULL,
            datum           DATE,
            onderwerp       TEXT,
            vergaderjaar    TEXT,
            content_type    TEXT,
            stream_tag      TEXT NOT NULL,
            raw_text        TEXT,
            raw_file_path   TEXT,
            ingested_at     TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS silver (
            id              SERIAL PRIMARY KEY,
            doc_id          TEXT NOT NULL REFERENCES bronze(id),
            chunk_index     INTEGER NOT NULL,
            chunk_text      TEXT NOT NULL,
            profile_version TEXT NOT NULL,
            created_at      TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS gold (
            id                  SERIAL PRIMARY KEY,
            doc_id              TEXT NOT NULL REFERENCES bronze(id),
            chunk_index         INTEGER NOT NULL,
            norm_frame          JSONB NOT NULL,
            completeness_score  INTEGER NOT NULL CHECK (completeness_score BETWEEN 0 AND 8),
            stream_tag          TEXT NOT NULL,
            confirmed           BOOLEAN,
            timestamp           TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    from alembic import op
    op.execute("DROP TABLE IF EXISTS gold")
    op.execute("DROP TABLE IF EXISTS silver")
    op.execute("DROP TABLE IF EXISTS bronze")
