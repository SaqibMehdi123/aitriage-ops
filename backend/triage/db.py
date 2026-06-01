"""Database access layer: a shared connection pool plus an org-scoped helper.

Multi-tenancy rule (TRD): *every* query against a tenant table is scoped to the
caller's organization at the data layer — never relying on the UI to filter.
`OrgScopedDb` enforces this by refusing to build a query without an
organization_id and by always appending `organization_id = %s` and
`deleted_at IS NULL` to reads and the org filter to writes.

The pool is sync (psycopg 3); it is shared by both the FastAPI API (sync
endpoints run in a threadpool) and the Celery worker.
"""
from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import get_settings

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()

# Tables that are NOT tenant-scoped (no organization_id column).
_GLOBAL_TABLES = {"organizations", "users", "schema_migrations"}


def get_pool() -> ConnectionPool:
    """Lazily open a process-wide connection pool."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                settings = get_settings()
                _pool = ConnectionPool(
                    conninfo=settings.database_url,
                    min_size=1,
                    max_size=10,
                    kwargs={"row_factory": dict_row},
                    open=True,
                )
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    """Borrow a connection from the pool. Commits on success, rolls back on error."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def _identifier(name: str) -> str:
    """Guard against SQL injection via table/column names — allow simple idents only."""
    if not name.replace("_", "").isalnum():
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return name


class OrgScopedDb:
    """Tenant-scoped CRUD helpers bound to a single organization_id.

    Construct one per request/task from the authenticated context. Generic
    enough for foundation CRUD; feature modules can drop to raw SQL via
    `connection()` when they need joins or vector search, but should still
    include the organization_id filter explicitly.
    """

    def __init__(self, organization_id: str):
        if not organization_id:
            raise ValueError("OrgScopedDb requires a non-empty organization_id")
        self.org_id = str(organization_id)

    # -- reads -------------------------------------------------------------
    def fetch_all(
        self,
        table: str,
        where: dict[str, Any] | None = None,
        *,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        table = _identifier(table)
        clauses, params = self._base_filter(table, where, include_deleted)
        sql = f"SELECT * FROM {table} WHERE {' AND '.join(clauses)}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += " LIMIT %s OFFSET %s"
            params += [limit, offset]
        with connection() as conn:
            return conn.execute(sql, params).fetchall()  # type: ignore[return-value]

    def fetch_one(
        self, table: str, where: dict[str, Any] | None = None, *, include_deleted: bool = False
    ) -> dict[str, Any] | None:
        rows = self.fetch_all(table, where, limit=1, include_deleted=include_deleted)
        return rows[0] if rows else None

    def count(self, table: str, where: dict[str, Any] | None = None) -> int:
        table = _identifier(table)
        clauses, params = self._base_filter(table, where, include_deleted=False)
        sql = f"SELECT count(*) AS n FROM {table} WHERE {' AND '.join(clauses)}"
        with connection() as conn:
            row = conn.execute(sql, params).fetchone()
        return int(row["n"]) if row else 0

    # -- writes ------------------------------------------------------------
    def insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        table = _identifier(table)
        data = dict(values)
        if table not in _GLOBAL_TABLES:
            data.setdefault("organization_id", self.org_id)
        cols = [_identifier(c) for c in data]
        placeholders = ", ".join(["%s"] * len(cols))
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) "
            f"VALUES ({placeholders}) RETURNING *"
        )
        with connection() as conn:
            return conn.execute(sql, list(data.values())).fetchone()  # type: ignore[return-value]

    def update(self, table: str, row_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
        table = _identifier(table)
        sets = ", ".join(f"{_identifier(c)} = %s" for c in values)
        params = list(values.values()) + [row_id]
        sql = f"UPDATE {table} SET {sets} WHERE id = %s"
        if table not in _GLOBAL_TABLES:
            sql += " AND organization_id = %s"
            params.append(self.org_id)
        sql += " RETURNING *"
        with connection() as conn:
            return conn.execute(sql, params).fetchone()  # type: ignore[return-value]

    def soft_delete(self, table: str, row_id: str) -> bool:
        table = _identifier(table)
        params: list[Any] = [row_id]
        sql = f"UPDATE {table} SET deleted_at = now() WHERE id = %s AND deleted_at IS NULL"
        if table not in _GLOBAL_TABLES:
            sql += " AND organization_id = %s"
            params.append(self.org_id)
        with connection() as conn:
            cur = conn.execute(sql, params)
            return cur.rowcount > 0

    # -- internals ---------------------------------------------------------
    def _base_filter(
        self, table: str, where: dict[str, Any] | None, include_deleted: bool
    ) -> tuple[list[str], list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if table not in _GLOBAL_TABLES:
            clauses.append("organization_id = %s")
            params.append(self.org_id)
        if not include_deleted:
            clauses.append("deleted_at IS NULL")
        for col, val in (where or {}).items():
            clauses.append(f"{_identifier(col)} = %s")
            params.append(val)
        if not clauses:
            clauses.append("TRUE")
        return clauses, params
