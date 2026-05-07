"""
SQLiteClient
============
Thin async wrapper around aiosqlite that manages connection lifecycle
and schema migrations.

Rules (infrastructure layer):
  - Third-party imports (aiosqlite) are allowed here.
  - No business logic.
  - Reads DATABASE_URL from environment via settings.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

logger = logging.getLogger(__name__)

# DDL — schema definition
_CREATE_BOOKS_TABLE = """
CREATE TABLE IF NOT EXISTS books (
    id             TEXT PRIMARY KEY,
    title          TEXT NOT NULL,
    author         TEXT NOT NULL,
    isbn           TEXT NOT NULL UNIQUE,
    status         TEXT NOT NULL DEFAULT 'unread',
    year_published INTEGER,
    description    TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
"""

_CREATE_ISBN_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_books_isbn ON books (isbn);
"""


class SQLiteClient:
    """
    Manages the SQLite connection and schema.

    Usage::

        client = SQLiteClient(db_path="./library.db")
        await client.initialise()

        async with client.connection() as conn:
            await conn.execute("SELECT 1")
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def initialise(self) -> None:
        """Create tables and indexes if they do not already exist."""
        logger.info("Initialising SQLite database at %s", self._db_path)
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(_CREATE_BOOKS_TABLE)
            await conn.execute(_CREATE_ISBN_INDEX)
            await conn.commit()
        logger.info("Database initialised successfully.")

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Yield a connection with row_factory pre-configured."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn
