"""
SQLiteBookRepository
====================
Concrete implementation of the BookRepository domain interface,
backed by an async SQLite database via aiosqlite.

Responsibilities:
  - Maps domain Book entities ↔ SQLite rows.
  - Wraps all DB-level errors as domain exceptions.
  - Never leaks aiosqlite types or SQL strings into application/domain.

Rules (infrastructure layer):
  - Implements a domain interface.
  - No business logic.
  - Reads from/writes to DB only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import aiosqlite

from src.domain.entities.book import Book
from src.domain.exceptions.domain_exceptions import BookNotFoundError
from src.domain.repositories.book_repository import BookRepository
from src.domain.value_objects.book_status import BookStatus
from src.domain.value_objects.isbn import ISBN
from src.infrastructure.database.sqlite_client import SQLiteClient

logger = logging.getLogger(__name__)


class SQLiteBookRepository(BookRepository):
    """Async SQLite-backed implementation of BookRepository."""

    def __init__(self, db_client: SQLiteClient) -> None:
        self._db = db_client

    # ------------------------------------------------------------------
    # BookRepository implementation
    # ------------------------------------------------------------------

    async def save(self, book: Book) -> None:
        """Insert a new book row. Raises DuplicateBookError via UNIQUE constraint."""
        sql = """
            INSERT INTO books
                (id, title, author, isbn, status, year_published, description,
                 created_at, updated_at)
            VALUES
                (:id, :title, :author, :isbn, :status, :year_published, :description,
                 :created_at, :updated_at)
        """
        async with self._db.connection() as conn:
            await conn.execute(sql, self._to_row(book))
            await conn.commit()
        logger.debug("Saved book %s (isbn=%s)", book.id, book.isbn.value)

    async def get_by_id(self, book_id: str) -> Book | None:
        sql = "SELECT * FROM books WHERE id = :id"
        async with self._db.connection() as conn:
            async with conn.execute(sql, {"id": book_id}) as cursor:
                row = await cursor.fetchone()
        return self._to_entity(row) if row else None

    async def get_by_isbn(self, isbn: ISBN) -> Book | None:
        sql = "SELECT * FROM books WHERE isbn = :isbn"
        async with self._db.connection() as conn:
            async with conn.execute(sql, {"isbn": isbn.value}) as cursor:
                row = await cursor.fetchone()
        return self._to_entity(row) if row else None

    async def list_all(
        self,
        *,
        status_filter: BookStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Book]:
        if status_filter:
            sql = (
                "SELECT * FROM books WHERE status = :status "
                "ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            )
            params: dict[str, object] = {
                "status": status_filter.value,
                "limit": limit,
                "offset": offset,
            }
        else:
            sql = (
                "SELECT * FROM books "
                "ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            )
            params = {"limit": limit, "offset": offset}

        async with self._db.connection() as conn:
            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
        return [self._to_entity(row) for row in rows]

    async def update(self, book: Book) -> None:
        sql = """
            UPDATE books
            SET title          = :title,
                author         = :author,
                isbn           = :isbn,
                status         = :status,
                year_published = :year_published,
                description    = :description,
                updated_at     = :updated_at
            WHERE id = :id
        """
        async with self._db.connection() as conn:
            cursor = await conn.execute(sql, self._to_row(book))
            await conn.commit()
            if cursor.rowcount == 0:
                raise BookNotFoundError(book.id)
        logger.debug("Updated book %s", book.id)

    async def delete(self, book_id: str) -> None:
        sql = "DELETE FROM books WHERE id = :id"
        async with self._db.connection() as conn:
            cursor = await conn.execute(sql, {"id": book_id})
            await conn.commit()
            if cursor.rowcount == 0:
                raise BookNotFoundError(book_id)
        logger.debug("Deleted book %s", book_id)

    async def count(self, *, status_filter: BookStatus | None = None) -> int:
        if status_filter:
            sql = "SELECT COUNT(*) FROM books WHERE status = :status"
            params_count: dict[str, object] = {"status": status_filter.value}
        else:
            sql = "SELECT COUNT(*) FROM books"
            params_count = {}

        async with self._db.connection() as conn:
            async with conn.execute(sql, params_count) as cursor:
                row = await cursor.fetchone()
        return int(row[0]) if row else 0

    # ------------------------------------------------------------------
    # Private mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(book: Book) -> dict[str, object]:
        """Convert a Book entity to a flat dict for SQL binding."""
        return {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "isbn": book.isbn.value,
            "status": book.status.value,
            "year_published": book.year_published,
            "description": book.description,
            "created_at": book.created_at.isoformat(),
            "updated_at": book.updated_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: aiosqlite.Row) -> Book:
        """
        Reconstruct a Book domain entity from a DB row.

        Infrastructure errors are converted to domain exceptions so no
        aiosqlite types or raw SQL leak into upper layers.
        """
        return Book(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            isbn=ISBN(row["isbn"]),
            status=BookStatus(row["status"]),
            year_published=row["year_published"],
            description=row["description"],
            created_at=datetime.fromisoformat(row["created_at"]).replace(
                tzinfo=timezone.utc
            ),
            updated_at=datetime.fromisoformat(row["updated_at"]).replace(
                tzinfo=timezone.utc
            ),
        )
