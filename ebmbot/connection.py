import sqlite3

from . import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS job (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,
    args TEXT,
    slack_channel TEXT,
    thread_ts TEXT,
    start_after DATETIME,
    started_at DATETIME
);

CREATE TABLE IF NOT EXISTS suppression (
    id INTEGER PRIMARY KEY,
    job_type TEXT NOT NULL,
    start_at DATETIME,
    end_at DATETIME
);
"""


def get_connection():
    """Return connection to database, ensuring tables exist."""

    def dict_factory(cursor, row):
        return {col[0]: row[ix] for ix, col in enumerate(cursor.description)}

    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = dict_factory
    conn.executescript(SCHEMA)
    return conn
