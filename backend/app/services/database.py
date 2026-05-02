from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings


def psycopg_url() -> str:
    url = get_settings().database_url
    # API runtime uses SQLAlchemy-style URLs in config; psycopg expects plain
    # postgres scheme, so normalize once at connection entry.
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    # `with get_connection()` ensures commit/rollback and connection cleanup
    # are consistently handled by psycopg context manager semantics.
    with psycopg.connect(psycopg_url(), row_factory=dict_row) as conn:
        yield conn
