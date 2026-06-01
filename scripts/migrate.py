#!/usr/bin/env python
"""Minimal forward-only migration runner.

Applies every *.sql file in db/migrations in lexical order, recording each in a
schema_migrations table so re-runs are idempotent. Each file runs in its own
transaction. Reads the DSN from DATABASE_URL (falling back to a localhost dev
default so it works from the host machine against the docker-compose Postgres).

Usage:
    python scripts/migrate.py            # apply all pending migrations
    python scripts/migrate.py --status   # list applied / pending without applying
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "db" / "migrations"
DEFAULT_DSN = "postgresql://triage:triage_dev_pw@localhost:5432/triage"


def get_dsn() -> str:
    dsn = os.environ.get("DATABASE_URL", DEFAULT_DSN)
    # The backend talks to host "postgres" (compose network); from the host
    # machine that name does not resolve, so rewrite to localhost.
    if "@postgres:" in dsn and os.environ.get("IN_DOCKER") != "1":
        dsn = dsn.replace("@postgres:", "@localhost:")
    return dsn


def ensure_table(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename    TEXT PRIMARY KEY,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    conn.commit()


def applied_set(conn: psycopg.Connection) -> set[str]:
    rows = conn.execute("SELECT filename FROM schema_migrations").fetchall()
    return {r[0] for r in rows}


def main() -> int:
    status_only = "--status" in sys.argv
    files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print(f"No migrations found in {MIGRATIONS_DIR}")
        return 1

    with psycopg.connect(get_dsn()) as conn:
        ensure_table(conn)
        done = applied_set(conn)

        pending = [f for f in files if f.name not in done]
        if status_only:
            for f in files:
                mark = "applied" if f.name in done else "PENDING"
                print(f"  [{mark}] {f.name}")
            print(f"\n{len(pending)} pending, {len(done)} applied.")
            return 0

        if not pending:
            print("Database is up to date — no pending migrations.")
            return 0

        for f in pending:
            print(f"Applying {f.name} ...", end=" ", flush=True)
            sql = f.read_text(encoding="utf-8")
            with conn.transaction():
                conn.execute(sql)  # type: ignore[arg-type]
                conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)", (f.name,)
                )
            print("ok")

        print(f"\nApplied {len(pending)} migration(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
