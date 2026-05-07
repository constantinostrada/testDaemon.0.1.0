"""
SQLiteAuthorRepository
======================
Concrete implementation of the AuthorRepository domain interface,
backed by an async SQLite database via aiosqlite.

Responsibilities:
  - Maps domain Author entities ↔ SQLite rows.
  - Wraps DB-level errors as domain exceptions.
  - Never leaks aiosqlite types or SQL strings into application/domain.

Rules (infrastructure layer):
  - Implements a domain interface.
  - No business logic.
  - Reads from/writes to DB only.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

import aiosqlite

from src.domain.entities.author import Author
from src.domain.exceptions.domain_exceptions import AuthorNotFoundError
from src.domain.repositories.author_repository import AuthorRepository
from src.infrastructure.database.sqlite_client import SQLiteClient

logger = logging.getLogger(__name__)


class SQLiteAuthorRepository(AuthorRepository):
    """Async SQLite-backed implementation of AuthorRepository."""

    def __init__(self, db_client: SQLiteClient) -> None:
        self._db = db_client

    # ------------------------------------------------------------------
    # AuthorRepository implementation
    # ------------------------------------------------------------------

    async def save(self, author: Author) -> None:
        """Insert a new author row. UNIQUE(full_name) maps to DuplicateAuthorError."""
        sql = """
            INSERT INTO authors
                (id, full_name, bio, date_of_birth, created_at, updated_at)
            VALUES
                (:id, :full_name, :bio, :date_of_birth, :created_at, :updated_at)
        """
        async with self._db.connection() as conn:
            await conn.execute(sql, self._to_row(author))
            await conn.commit()
        logger.debug("Saved author %s (full_name=%s)", author.id, author.full_name)

    async def get_by_id(self, author_id: str) -> Author | None:
        sql = "SELECT * FROM authors WHERE id = :id"
        async with self._db.connection() as conn:
            async with conn.execute(sql, {"id": author_id}) as cursor:
                row = await cursor.fetchone()
        return self._to_entity(row) if row else None

    async def get_by_full_name(self, full_name: str) -> Author | None:
        sql = "SELECT * FROM authors WHERE full_name = :full_name"
        async with self._db.connection() as conn:
            async with conn.execute(
                sql, {"full_name": full_name.strip()}
            ) as cursor:
                row = await cursor.fetchone()
        return self._to_entity(row) if row else None

    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Author]:
        sql = (
            "SELECT * FROM authors "
            "ORDER BY full_name ASC LIMIT :limit OFFSET :offset"
        )
        async with self._db.connection() as conn:
            async with conn.execute(
                sql, {"limit": limit, "offset": offset}
            ) as cursor:
                rows = await cursor.fetchall()
        return [self._to_entity(row) for row in rows]

    async def list_by_ids(self, author_ids: list[str]) -> list[Author]:
        if not author_ids:
            return []
        placeholders = ",".join("?" for _ in author_ids)
        sql = f"SELECT * FROM authors WHERE id IN ({placeholders})"
        async with self._db.connection() as conn:
            async with conn.execute(sql, tuple(author_ids)) as cursor:
                rows = await cursor.fetchall()
        return [self._to_entity(row) for row in rows]

    async def update(self, author: Author) -> None:
        sql = """
            UPDATE authors
            SET full_name     = :full_name,
                bio           = :bio,
                date_of_birth = :date_of_birth,
                updated_at    = :updated_at
            WHERE id = :id
        """
        async with self._db.connection() as conn:
            cursor = await conn.execute(sql, self._to_row(author))
            await conn.commit()
            if cursor.rowcount == 0:
                raise AuthorNotFoundError(author.id)
        logger.debug("Updated author %s", author.id)

    async def delete(self, author_id: str) -> None:
        sql = "DELETE FROM authors WHERE id = :id"
        async with self._db.connection() as conn:
            cursor = await conn.execute(sql, {"id": author_id})
            await conn.commit()
            if cursor.rowcount == 0:
                raise AuthorNotFoundError(author_id)
        logger.debug("Deleted author %s", author_id)

    async def count(self) -> int:
        sql = "SELECT COUNT(*) FROM authors"
        async with self._db.connection() as conn:
            async with conn.execute(sql) as cursor:
                row = await cursor.fetchone()
        return int(row[0]) if row else 0

    async def exists(self, author_id: str) -> bool:
        sql = "SELECT 1 FROM authors WHERE id = :id LIMIT 1"
        async with self._db.connection() as conn:
            async with conn.execute(sql, {"id": author_id}) as cursor:
                row = await cursor.fetchone()
        return row is not None

    async def count_books_by_author(self, author_id: str) -> int:
        sql = "SELECT COUNT(*) FROM book_authors WHERE author_id = :author_id"
        async with self._db.connection() as conn:
            async with conn.execute(
                sql, {"author_id": author_id}
            ) as cursor:
                row = await cursor.fetchone()
        return int(row[0]) if row else 0

    # ------------------------------------------------------------------
    # Private mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(author: Author) -> dict[str, object]:
        return {
            "id": author.id,
            "full_name": author.full_name,
            "bio": author.bio,
            "date_of_birth": (
                author.date_of_birth.isoformat()
                if author.date_of_birth is not None
                else None
            ),
            "created_at": author.created_at.isoformat(),
            "updated_at": author.updated_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: aiosqlite.Row) -> Author:
        dob_raw = row["date_of_birth"]
        dob = date.fromisoformat(dob_raw) if dob_raw else None
        return Author(
            id=row["id"],
            full_name=row["full_name"],
            bio=row["bio"],
            date_of_birth=dob,
            created_at=datetime.fromisoformat(row["created_at"]).replace(
                tzinfo=timezone.utc
            ),
            updated_at=datetime.fromisoformat(row["updated_at"]).replace(
                tzinfo=timezone.utc
            ),
        )
