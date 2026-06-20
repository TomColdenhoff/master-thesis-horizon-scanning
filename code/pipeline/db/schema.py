"""PostgreSQL schema definitions for all three stores.

Run create_all() once to initialise the database before the pipeline runs.
"""

from pipeline.db.connection import transaction

_BRONZE = """
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
);
"""

_SILVER = """
CREATE TABLE IF NOT EXISTS silver (
    id              SERIAL PRIMARY KEY,
    doc_id          TEXT NOT NULL REFERENCES bronze(id),
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    profile_version TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

_GOLD = """
CREATE TABLE IF NOT EXISTS gold (
    id                  SERIAL PRIMARY KEY,
    doc_id              TEXT NOT NULL REFERENCES bronze(id),
    chunk_index         INTEGER NOT NULL,
    norm_frame          JSONB NOT NULL,
    reasoning           TEXT,
    completeness_score  INTEGER NOT NULL CHECK (completeness_score BETWEEN 0 AND 8),
    stream_tag          TEXT NOT NULL,
    confirmed           BOOLEAN,
    timestamp           TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


def create_all() -> None:
    """Create all tables if they do not exist."""
    with transaction() as conn:
        cur = conn.cursor()
        cur.execute(_BRONZE)
        cur.execute(_SILVER)
        cur.execute(_GOLD)
