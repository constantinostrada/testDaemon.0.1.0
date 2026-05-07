"""
Book Entity
===========
Central domain entity representing a book in the library catalog.

Invariants enforced at construction and mutation time:
  - title must be non-empty.
  - authors must be a non-empty list with each name non-empty.
  - isbn must be a valid ISBN-10 or ISBN-13 (delegated to ISBN value object).
  - genre must be non-empty.
  - status transitions must follow the allowed lifecycle.

Rules (domain layer):
  - Zero third-party imports.
  - No ORM decorators.
  - No HTTP types.
  - Raises DomainException subclasses on invariant violations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.domain.exceptions.domain_exceptions import (
    InvalidBookStatusTransitionError,
)
from src.domain.value_objects.book_status import BookStatus
from src.domain.value_objects.isbn import ISBN


class Book:
    """
    Aggregate root representing a book in the library catalog.

    Identity is provided by a UUID string (`id`).
    """

    def __init__(
        self,
        *,
        id: str,
        title: str,
        authors: list[str],
        isbn: ISBN,
        genre: str,
        status: BookStatus = BookStatus.UNREAD,
        year_published: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._validate_title(title)
        self._validate_authors(authors)
        self._validate_genre(genre)

        self._id = id
        self._title = title.strip()
        self._authors = [a.strip() for a in authors]
        self._isbn = isbn
        self._genre = genre.strip()
        self._status = status
        self._year_published = year_published
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or self._created_at

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        title: str,
        authors: list[str],
        isbn: ISBN,
        genre: str,
        year_published: int | None = None,
    ) -> Book:
        """Create a new book with a fresh UUID and UNREAD status."""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            authors=authors,
            isbn=isbn,
            genre=genre,
            status=BookStatus.UNREAD,
            year_published=year_published,
        )

    # ------------------------------------------------------------------
    # Properties (read-only)
    # ------------------------------------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def authors(self) -> list[str]:
        return list(self._authors)

    @property
    def isbn(self) -> ISBN:
        return self._isbn

    @property
    def genre(self) -> str:
        return self._genre

    @property
    def status(self) -> BookStatus:
        return self._status

    @property
    def year_published(self) -> int | None:
        return self._year_published

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # ------------------------------------------------------------------
    # Domain behaviour
    # ------------------------------------------------------------------

    def update_status(self, new_status: BookStatus) -> None:
        """
        Transition the book to a new reading status.

        Raises:
            InvalidBookStatusTransitionError: when the transition is not allowed.
        """
        if not self._status.can_transition_to(new_status):
            raise InvalidBookStatusTransitionError(
                current=self._status.value,
                requested=new_status.value,
            )
        self._status = new_status
        self._updated_at = datetime.now(UTC)

    def update_metadata(
        self,
        *,
        title: str | None = None,
        authors: list[str] | None = None,
        genre: str | None = None,
        year_published: int | None = None,
    ) -> None:
        """Update mutable metadata fields. None values are left unchanged."""
        if title is not None:
            self._validate_title(title)
            self._title = title.strip()
        if authors is not None:
            self._validate_authors(authors)
            self._authors = [a.strip() for a in authors]
        if genre is not None:
            self._validate_genre(genre)
            self._genre = genre.strip()
        if year_published is not None:
            self._year_published = year_published
        self._updated_at = datetime.now(UTC)

    # ------------------------------------------------------------------
    # Equality / hashing — identity based
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return (
            f"Book(id={self._id!r}, title={self._title!r}, "
            f"isbn={self._isbn!r}, status={self._status!r})"
        )

    # ------------------------------------------------------------------
    # Private validators
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise ValueError("Book title must not be empty.")

    @staticmethod
    def _validate_authors(authors: list[str]) -> None:
        if not authors:
            raise ValueError("Book must have at least one author.")
        for author in authors:
            if not author or not author.strip():
                raise ValueError("Book author names must not be empty.")

    @staticmethod
    def _validate_genre(genre: str) -> None:
        if not genre or not genre.strip():
            raise ValueError("Book genre must not be empty.")
