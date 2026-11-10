"""SQLite/PostgreSQL persistence with idempotent upserts and clear backend selection."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg2
except ImportError:  # pragma: no cover - optional runtime dependency
    psycopg2 = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 provider TEXT NOT NULL, dataset TEXT NOT NULL, season INTEGER NOT NULL DEFAULT -1,
 event_key TEXT NOT NULL DEFAULT '', session_key TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL, source_url TEXT NOT NULL DEFAULT '',
 retrieved_at TEXT NOT NULL, payload TEXT NOT NULL,
 UNIQUE(provider, dataset, season, event_key, session_key, status, source_url)
);
CREATE TABLE IF NOT EXISTS sync_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, provider TEXT NOT NULL,
 started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL,
 records INTEGER DEFAULT 0, message TEXT
);
CREATE INDEX IF NOT EXISTS idx_datasets_lookup ON datasets(provider,dataset,season);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    dataset TEXT NOT NULL,
    season INTEGER NOT NULL DEFAULT -1,
    event_key TEXT NOT NULL DEFAULT '',
    session_key TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    source_url TEXT NOT NULL DEFAULT '',
    retrieved_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    UNIQUE(provider, dataset, season, event_key, session_key, status, source_url)
);
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    records INTEGER DEFAULT 0,
    message TEXT
);
CREATE INDEX IF NOT EXISTS idx_datasets_lookup ON datasets(provider,dataset,season);
"""


class F1Repository:
    def __init__(self, path="data/f1_data.sqlite3", connection_url=None):
        self.connection_url = connection_url or os.getenv("F1_DATABASE_URL", "")
        self.backend = "postgresql" if self.connection_url and psycopg2 is not None else "sqlite"
        self.path = Path(path or os.getenv("F1_DATABASE_PATH", "data/f1_data.sqlite3"))
        if self.backend == "sqlite":
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()
        else:
            self._init_postgres()

    def _init_sqlite(self):
        with self.connect() as db:
            db.executescript(SCHEMA)
            db.execute("UPDATE datasets SET season=-1 WHERE season IS NULL")
            db.execute("UPDATE datasets SET event_key='' WHERE event_key IS NULL")
            db.execute("UPDATE datasets SET session_key='' WHERE session_key IS NULL")
            db.execute("UPDATE datasets SET source_url='' WHERE source_url IS NULL")
            db.execute(
                """DELETE FROM datasets WHERE id NOT IN
                (SELECT MIN(id) FROM datasets GROUP BY provider,dataset,season,event_key,session_key,status,source_url)"""
            )
            db.commit()

    def _init_postgres(self):
        if psycopg2 is None:
            raise RuntimeError("psycopg2-binary is required for PostgreSQL support. Install it or unset F1_DATABASE_URL to use SQLite.")
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(POSTGRES_SCHEMA)

    def connect(self):
        if self.backend == "postgresql":
            conn = psycopg2.connect(self.connection_url, connect_timeout=30)
            conn.autocommit = False
            return conn
        db = sqlite3.connect(self.path, timeout=30, isolation_level="DEFERRED")
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def _key(value, fallback):
        return fallback if value is None else value

    def save_dataset(self, provider, dataset, payload, season=None, event_key=None,
                     session_key=None, status="HISTORICAL", source_url=None):
        now = datetime.now(timezone.utc).isoformat()
        encoded = json.dumps(payload, default=str)
        values = (
            provider,
            dataset,
            self._key(season, -1),
            self._key(event_key, ""),
            self._key(session_key, ""),
            status,
            self._key(source_url, ""),
            now,
            encoded,
        )
        if self.backend == "postgresql":
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO datasets
                        (provider,dataset,season,event_key,session_key,status,source_url,retrieved_at,payload)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(provider,dataset,season,event_key,session_key,status,source_url)
                        DO UPDATE SET retrieved_at=EXCLUDED.retrieved_at, payload=EXCLUDED.payload""",
                        values,
                    )
            return len(payload) if isinstance(payload, list) else 1

        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """INSERT INTO datasets
                  (provider,dataset,season,event_key,session_key,status,source_url,retrieved_at,payload)
                  VALUES(?,?,?,?,?,?,?,?,?)
                  ON CONFLICT(provider,dataset,season,event_key,session_key,status,source_url)
                  DO UPDATE SET retrieved_at=excluded.retrieved_at,payload=excluded.payload""",
                values,
            )
        return len(payload) if isinstance(payload, list) else 1

    def latest_datasets(self, limit=100):
        with self.connect() as db:
            if self.backend == "postgresql":
                with db.cursor() as cur:
                    cur.execute(
                        "SELECT provider,dataset,season,status,retrieved_at,source_url,payload FROM datasets ORDER BY retrieved_at DESC LIMIT %s",
                        (limit,),
                    )
                    rows = cur.fetchall()
                    return [
                        {
                            "provider": row[0],
                            "dataset": row[1],
                            "season": row[2],
                            "status": row[3],
                            "retrieved_at": row[4],
                            "source_url": row[5],
                            "payload": row[6],
                        }
                        for row in rows
                    ]
            return [dict(r) for r in db.execute(
                "SELECT provider,dataset,season,status,retrieved_at,source_url,payload FROM datasets ORDER BY retrieved_at DESC LIMIT ?",
                (limit,)).fetchall()]

    def log_sync(self, provider, status, records=0, message=""):
        now = datetime.now(timezone.utc).isoformat()
        if self.backend == "postgresql":
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO sync_logs(provider,started_at,finished_at,status,records,message) VALUES(%s,%s,%s,%s,%s,%s)",
                        (provider, now, now, status, records, str(message)[:1000]),
                    )
            return
        with self.connect() as db:
            db.execute(
                "INSERT INTO sync_logs(provider,started_at,finished_at,status,records,message) VALUES(?,?,?,?,?,?)",
                (provider, now, now, status, records, str(message)[:1000]),
            )

    def counts(self):
        with self.connect() as db:
            if self.backend == "postgresql":
                with db.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM datasets")
                    dataset_count = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM sync_logs")
                    sync_count = cur.fetchone()[0]
                    return {"datasets": dataset_count, "sync_logs": sync_count}
            return {
                "datasets": db.execute("SELECT COUNT(*) FROM datasets").fetchone()[0],
                "sync_logs": db.execute("SELECT COUNT(*) FROM sync_logs").fetchone()[0],
            }
