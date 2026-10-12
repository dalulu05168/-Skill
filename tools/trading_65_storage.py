"""Durable storage for the 65-person *simulated* ledger.

Local development keeps the original JSON file behavior. Hosted free instances
must set P004_TRADE_DATABASE_URL to a PostgreSQL database; losing contact with
that database fails closed and never silently switches to ephemeral files.
"""
from __future__ import annotations
import json
import os

from trading_65 import (
    fresh_state,
    read_state as read_local_state,
    validate_state,
    write_state as write_local_state,
)

TABLE = "p004_trading65_ledger"
KEY = "canonical_65_v1"


def _database_url():
    return os.environ.get("P004_TRADE_DATABASE_URL", "").strip()


def is_durable():
    return bool(_database_url())


def _connect():
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("PostgreSQL driver unavailable; install requirements-trading-free.txt") from exc
    return psycopg.connect(_database_url(), connect_timeout=20, sslmode="require")


def _ensure_table(connection):
    connection.execute(
        "CREATE TABLE IF NOT EXISTS " + TABLE + " ("
        "ledger_key TEXT PRIMARY KEY, payload JSONB NOT NULL, "
        "revision INTEGER NOT NULL CHECK (revision >= 0), "
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)")


def read_trade_state(path):
    if not is_durable():
        return read_local_state(path)
    with _connect() as conn:
        _ensure_table(conn)
        cur = conn.execute(
            "SELECT payload::text FROM " + TABLE + " WHERE ledger_key = %s", (KEY,))
        record = cur.fetchone()
    return validate_state(json.loads(record[0])) if record else fresh_state()


def write_trade_state(path, state):
    validate_state(state)
    if not is_durable():
        return write_local_state(path, state)
    revision = int(state["revision"])
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    with _connect() as conn:
        _ensure_table(conn)
        if revision > 0:
            updated = conn.execute(
                "UPDATE " + TABLE +
                " SET payload = %s::jsonb, revision = %s, updated_at = CURRENT_TIMESTAMP "
                "WHERE ledger_key = %s AND revision = %s",
                (payload, revision, KEY, revision - 1))
            if updated.rowcount == 1:
                return
        # First action only. Existing ledger cannot be overwritten by a stale
        # instance, and a conflict is surfaced to the user rather than lost.
        inserted = conn.execute(
            "INSERT INTO " + TABLE + " (ledger_key, payload, revision) "
            "VALUES (%s, %s::jsonb, %s) ON CONFLICT (ledger_key) DO NOTHING",
            (KEY, payload, revision))
        if inserted.rowcount != 1:
            raise ValueError("账本版本已变化，操作未保存。请刷新后重试。")


def check_connection():
    if not is_durable():
        return False
    with _connect() as conn:
        _ensure_table(conn)
        return conn.execute("SELECT 1").fetchone()[0] == 1
