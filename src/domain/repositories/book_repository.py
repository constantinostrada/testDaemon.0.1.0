"""
BookRepository Interface
========================
Abstract repository interface for Book persistence.

This interface defines WHAT operations are available — not HOW they
are implemented. Concrete implementations live in infrastructure/.

Rules (domain layer):
  - No ORM, SQL, or I/O imports.
  - Methods are async to allow any concrete implementation (SQLite, Postgres…).
  - Returns domain entities, never raw DB rows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.book import Book
from src.domain.value_objects.book_status import BookStatus
from src.domain.value_objects.isbn import ISBN


class BookRepository(ABC):
    """Abstract interface for Book persistence operations."""

    @abstractmethod
    async def save(self, book: Book) -> None:
        """
        Persist a new book.

        Raises:
            DuplicateBookError: if a book with the same ISBN already exists.
        """
        ...

    @abstractmethod
    async def get_by_id(self, book_id: str) -> Book | None:
        """Return the Book with the given id, or None if not found."""
        ...

    @abstractmethod
    async def get_by_isbn(self, isbn: ISBN) -> Book | None:
        """Return the Book with the given ISBN, or None if not found."""
        ...

    @abstractmethod
    async def list_all(
        self,
        *,
        status_filter: BookStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Book]:
        """
        Return a paginated list of all books, optionally filtered by status.

        Args:
            status_filter: when provided, only books with this status are returned.
            limit:  maximum number of books to return (default 50).
            offset: number of books to skip for pagination (default 0).
        """
        ...

    @abstractmethod
    async def update(self, book: Book) -> None:
        """
        Persist changes to an existing book.

        Raises:
            BookNotFoundError: if the book does not exist.
        """
        ...

    @abstractmethod
    async def delete(self, book_id: str) -> None:
        """
        Remove a book from the repository.

        Raises:
            BookNotFoundError: if no book with the given id exists.
        """
        ...

    @abstractmethod
    async def count(self, *, status_filter: BookStatus | None = None) -> int:
        """Return the total number of books, optionally filtered by status."""
        ...
