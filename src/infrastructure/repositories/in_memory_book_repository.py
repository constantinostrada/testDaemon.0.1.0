"""
InMemoryBookRepository
======================
In-memory implementation of the BookRepository domain interface.

Backed by a Python dict keyed by book id, plus a secondary ISBN index
for O(1) duplicate detection. Methods are async to satisfy the
interface contract; there is no real I/O.

Rules (infrastructure layer):
  - Implements a domain interface.
  - No business logic.
  - No external services.
"""

from __future__ import annotations

from src.domain.entities.book import Book
from src.domain.exceptions.domain_exceptions import (
    BookNotFoundError,
    DuplicateBookError,
)
from src.domain.repositories.book_repository import BookRepository
from src.domain.value_objects.book_status import BookStatus
from src.domain.value_objects.isbn import ISBN


class InMemoryBookRepository(BookRepository):
    """Async in-memory implementation of BookRepository."""

    def __init__(self) -> None:
        self._books: dict[str, Book] = {}
        self._isbn_to_id: dict[str, str] = {}

    # ------------------------------------------------------------------
    # BookRepository implementation
    # ------------------------------------------------------------------

    async def save(self, book: Book) -> None:
        """Persist a new book. Raises DuplicateBookError on ISBN clash."""
        if book.isbn.value in self._isbn_to_id:
            raise DuplicateBookError(book.isbn.value)
        self._books[book.id] = book
        self._isbn_to_id[book.isbn.value] = book.id

    async def get_by_id(self, book_id: str) -> Book | None:
        return self._books.get(book_id)

    async def get_by_isbn(self, isbn: ISBN) -> Book | None:
        book_id = self._isbn_to_id.get(isbn.value)
        if book_id is None:
            return None
        return self._books.get(book_id)

    async def list_all(
        self,
        *,
        status_filter: BookStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Book]:
        books = list(self._books.values())
        if status_filter is not None:
            books = [b for b in books if b.status == status_filter]
        books.sort(key=lambda b: b.created_at, reverse=True)
        return books[offset : offset + limit]

    async def update(self, book: Book) -> None:
        if book.id not in self._books:
            raise BookNotFoundError(book.id)
        existing = self._books[book.id]
        if existing.isbn.value != book.isbn.value:
            self._isbn_to_id.pop(existing.isbn.value, None)
            self._isbn_to_id[book.isbn.value] = book.id
        self._books[book.id] = book

    async def delete(self, book_id: str) -> None:
        existing = self._books.pop(book_id, None)
        if existing is None:
            raise BookNotFoundError(book_id)
        self._isbn_to_id.pop(existing.isbn.value, None)

    async def count(self, *, status_filter: BookStatus | None = None) -> int:
        if status_filter is None:
            return len(self._books)
        return sum(1 for b in self._books.values() if b.status == status_filter)

    async def search(
        self,
        *,
        title_query: str | None = None,
        author_query: str | None = None,
        year_published: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Book], int]:
        title_needle = title_query.casefold() if title_query else None
        author_needle = author_query.casefold() if author_query else None

        def matches(book: Book) -> bool:
            if title_needle is not None and title_needle not in book.title.casefold():
                return False
            if author_needle is not None and not any(
                author_needle in a.casefold() for a in book.authors
            ):
                return False
            if year_published is not None and book.year_published != year_published:
                return False
            return True

        matched = [b for b in self._books.values() if matches(b)]
        matched.sort(key=lambda b: b.created_at, reverse=True)
        return matched[offset : offset + limit], len(matched)
