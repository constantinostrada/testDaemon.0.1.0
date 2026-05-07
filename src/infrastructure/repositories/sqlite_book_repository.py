"""
SQLiteBookRepository
====================
Concrete implementation of the BookRepository domain interface,
backed by an async SQLite database via aiosqlite.

Responsibilities:
  - Maps domain Book entities ↔ SQLite rows.
  - Manages the many-to-many `book_authors` join table alongside the
    `books` row when saving / updating.
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
        """Insert a new book row + its join rows. Raises via UNIQUE constraint."""
        sql_book = """
            INSERT INTO books
                (id, title, isbn, status, year_published, description,
                 created_at, updated_at)
            VALUES
                (:id, :title, :isbn, :status, :year_published, :description,
                 :created_at, :updated_at)
        """
        async with self._db.connection() as conn:
            await conn.execute(sql_book, self._to_book_row(book))
            await conn.executemany(
                "INSERT INTO book_authors (book_id, author_id) VALUES (?, ?)",
                [(book.id, aid) for aid in book.author_ids],
            )
            await conn.commit()
        logger.debug("Saved book %s (isbn=%s)", book.id, book.isbn.value)

    async def get_by_id(self, book_id: str) -> Book | None:
        async with self._db.connection() as conn:
            async with conn.execute(
                "SELECT * FROM books WHERE id = :id", {"id": book_id}
            ) as cursor:
                row = await cursor.fetchone()
            if row is None:
                return None
            author_ids = await self._fetch_author_ids(conn, book_id)
        return self._to_entity(row, author_ids)

    async def get_by_isbn(self, isbn: ISBN) -> Book | None:
        async with self._db.connection() as conn:
            async with conn.execute(
                "SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn.value}
            ) as cursor:
                row = await cursor.fetchone()
            if row is None:
                return None
            author_ids = await self._fetch_author_ids(conn, row["id"])
        return self._to_entity(row, author_ids)

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
            if not rows:
                return []
            author_ids_by_book = await self._fetch_author_ids_for_books(
                conn, [row["id"] for row in rows]
            )
        return [
            self._to_entity(row, author_ids_by_book.get(row["id"], []))
            for row in rows
        ]

    async def update(self, book: Book) -> None:
        sql_book = """
            UPDATE books
            SET title          = :title,
                isbn           = :isbn,
                status         = :status,
                year_published = :year_published,
                description    = :description,
                updated_at     = :updated_at
            WHERE id = :id
        """
        async with self._db.connection() as conn:
            cursor = await conn.execute(sql_book, self._to_book_row(book))
            if cursor.rowcount == 0:
                await conn.rollback()
                raise BookNotFoundError(book.id)
            # Replace join rows atomically: delete then re-insert in same txn.
            await conn.execute(
                "DELETE FROM book_authors WHERE book_id = ?", (book.id,)
            )
            await conn.executemany(
                "INSERT INTO book_authors (book_id, author_id) VALUES (?, ?)",
                [(book.id, aid) for aid in book.author_ids],
            )
            await conn.commit()
        logger.debug("Updated book %s", book.id)

    async def delete(self, book_id: str) -> None:
        # ON DELETE CASCADE on book_authors.book_id removes join rows.
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

    async def list_by_author(self, author_id: str) -> list[Book]:
        sql = """
            SELECT b.*
            FROM books b
            INNER JOIN book_authors ba ON ba.book_id = b.id
            WHERE ba.author_id = :author_id
            ORDER BY b.created_at DESC
        """
        async with self._db.connection() as conn:
            async with conn.execute(sql, {"author_id": author_id}) as cursor:
                rows = await cursor.fetchall()
            if not rows:
                return []
            author_ids_by_book = await self._fetch_author_ids_for_books(
                conn, [row["id"] for row in rows]
            )
        return [
            self._to_entity(row, author_ids_by_book.get(row["id"], []))
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _fetch_author_ids(
        conn: aiosqlite.Connection, book_id: str
    ) -> list[str]:
        sql = (
            "SELECT author_id FROM book_authors WHERE book_id = :book_id "
            "ORDER BY rowid"
        )
        async with conn.execute(sql, {"book_id": book_id}) as cursor:
            rows = await cursor.fetchall()
        return [row["author_id"] for row in rows]

    @staticmethod
    async def _fetch_author_ids_for_books(
        conn: aiosqlite.Connection, book_ids: list[str]
    ) -> dict[str, list[str]]:
        if not book_ids:
            return {}
        placeholders = ",".join("?" for _ in book_ids)
        sql = (
            f"SELECT book_id, author_id FROM book_authors "
            f"WHERE book_id IN ({placeholders}) ORDER BY rowid"
        )
        async with conn.execute(sql, tuple(book_ids)) as cursor:
            rows = await cursor.fetchall()
        result: dict[str, list[str]] = {bid: [] for bid in book_ids}
        for row in rows:
            result[row["book_id"]].append(row["author_id"])
        return result

    @staticmethod
    def _to_book_row(book: Book) -> dict[str, object]:
        """Convert a Book entity to a flat dict for the books-table binding."""
        return {
            "id": book.id,
            "title": book.title,
            "isbn": book.isbn.value,
            "status": book.status.value,
            "year_published": book.year_published,
            "description": book.description,
            "created_at": book.created_at.isoformat(),
            "updated_at": book.updated_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: aiosqlite.Row, author_ids: list[str]) -> Book:
        """Reconstruct a Book domain entity from a books row + its join rows."""
        return Book(
            id=row["id"],
            title=row["title"],
            author_ids=author_ids,
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
