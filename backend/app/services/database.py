import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings


def psycopg_url() -> str:
    url = get_settings().database_url
    # API runtime uses SQLAlchemy-style URLs in config; psycopg expects plain
    # postgres scheme, so normalize once at connection entry.
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


_DEBUG_LOG = Path(__file__).resolve().parents[3] / ".cursor" / "debug-ce83c2.log"


def _agent_log(hypothesis_id: str, message: str, data: dict) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "ce83c2",
            "hypothesisId": hypothesis_id,
            "location": "database.py:get_connection",
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _DEBUG_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    # `with get_connection()` ensures commit/rollback and connection cleanup
    # are consistently handled by psycopg context manager semantics.
    try:
        with psycopg.connect(
            psycopg_url(),
            row_factory=dict_row,
            connect_timeout=8,
            options="-c statement_timeout=8000",
        ) as conn:
            yield conn
    except Exception as exc:
        host = "unknown"
        try:
            host = psycopg_url().split("@")[1].split("/")[0]
        except (IndexError, ValueError):
            pass
        _agent_log(
            "H1",
            "db_connect_failed",
            {"host": host, "error_type": type(exc).__name__, "error": str(exc)[:240]},
        )
        raise
