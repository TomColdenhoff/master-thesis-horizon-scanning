"""Database connection management.

Provides a single connection factory used by all repositories.
Connection parameters are read from environment variables.
"""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extensions import connection as PgConnection
from dotenv import load_dotenv

load_dotenv()


def get_connection() -> PgConnection:
    """Return a new PostgreSQL connection using environment variables."""
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


@contextmanager
def transaction() -> Generator[PgConnection, None, None]:
    """Context manager that yields a connection and commits or rolls back."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
