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

_CREATE_AUTHORS_TABLE = """
CREATE TABLE IF NOT EXISTS authors (
    id             TEXT PRIMARY KEY,
    full_name      TEXT NOT NULL UNIQUE,
    bio            TEXT,
    date_of_birth  TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
"""

_CREATE_AUTHOR_NAME_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_authors_full_name ON authors (full_name);
"""

# Join table linking books and authors (many-to-many).
# ON DELETE CASCADE on book_id ensures join rows go away with the book; we
# deliberately do NOT cascade on author_id — the use case enforces that an
# author with linked books cannot be deleted (raises AuthorHasBooksError).
_CREATE_BOOK_AUTHORS_TABLE = """
CREATE TABLE IF NOT EXISTS book_authors (
    book_id   TEXT NOT NULL,
    author_id TEXT NOT NULL,
    PRIMARY KEY (book_id, author_id),
    FOREIGN KEY (book_id)   REFERENCES books(id)   ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id)
);
"""

_CREATE_BOOK_AUTHORS_AUTHOR_INDEX = """
CREATE INDEX IF NOT EXISTS idx_book_authors_author_id
    ON book_authors (author_id);
"""

_CREATE_BOOK_AUTHORS_BOOK_INDEX = """
CREATE INDEX IF NOT EXISTS idx_book_authors_book_id
    ON book_authors (book_id);
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
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute(_CREATE_BOOKS_TABLE)
            await conn.execute(_CREATE_ISBN_INDEX)
            await conn.execute(_CREATE_AUTHORS_TABLE)
            await conn.execute(_CREATE_AUTHOR_NAME_INDEX)
            await conn.execute(_CREATE_BOOK_AUTHORS_TABLE)
            await conn.execute(_CREATE_BOOK_AUTHORS_AUTHOR_INDEX)
            await conn.execute(_CREATE_BOOK_AUTHORS_BOOK_INDEX)
            await conn.commit()
        logger.info("Database initialised successfully.")

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Yield a connection with row_factory + FK enforcement pre-configured."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys = ON")
            yield conn
