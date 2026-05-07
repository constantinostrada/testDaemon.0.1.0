"""
Book Entity
===========
Central domain entity representing a book in the library.

Invariants enforced at construction and mutation time:
  - title must be non-empty.
  - author_ids must contain at least one id, with no duplicates.
  - isbn must be a valid ISBN-10 or ISBN-13 (delegated to ISBN value object).
  - status transitions must follow the allowed lifecycle.

Rules (domain layer):
  - Zero third-party imports.
  - No ORM decorators.
  - No HTTP types.
  - Raises DomainException subclasses on invariant violations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.domain.exceptions.domain_exceptions import (
    BookAuthorsRequiredError,
    InvalidBookStatusTransitionError,
)
from src.domain.value_objects.book_status import BookStatus
from src.domain.value_objects.isbn import ISBN


class Book:
    """
    Aggregate root representing a physical or digital book in the library.

    Identity is provided by a UUID string (`id`). Authorship is modelled
    as a list of references to Author aggregate roots — Book holds the
    ids only, and the application layer hydrates Author entities when
    output is requested.
    """

    def __init__(
        self,
        *,
        id: str,
        title: str,
        author_ids: list[str],
        isbn: ISBN,
        status: BookStatus = BookStatus.UNREAD,
        year_published: int | None = None,
        description: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._validate_title(title)
        normalised_author_ids = self._validate_author_ids(author_ids)

        self._id = id
        self._title = title.strip()
        self._author_ids = normalised_author_ids
        self._isbn = isbn
        self._status = status
        self._year_published = year_published
        self._description = description
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or self._created_at

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        title: str,
        author_ids: list[str],
        isbn: ISBN,
        year_published: int | None = None,
        description: str | None = None,
    ) -> "Book":
        """Create a new book with a fresh UUID and UNREAD status."""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            author_ids=author_ids,
            isbn=isbn,
            status=BookStatus.UNREAD,
            year_published=year_published,
            description=description,
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
    def author_ids(self) -> list[str]:
        return list(self._author_ids)

    @property
    def isbn(self) -> ISBN:
        return self._isbn

    @property
    def status(self) -> BookStatus:
        return self._status

    @property
    def year_published(self) -> int | None:
        return self._year_published

    @property
    def description(self) -> str | None:
        return self._description

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
        self._updated_at = datetime.now(timezone.utc)

    def update_metadata(
        self,
        *,
        title: str | None = None,
        author_ids: list[str] | None = None,
        year_published: int | None = None,
        description: str | None = None,
    ) -> None:
        """Update mutable metadata fields. None values are left unchanged."""
        if title is not None:
            self._validate_title(title)
            self._title = title.strip()
        if author_ids is not None:
            self._author_ids = self._validate_author_ids(author_ids)
        if year_published is not None:
            self._year_published = year_published
        if description is not None:
            self._description = description
        self._updated_at = datetime.now(timezone.utc)

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
    def _validate_author_ids(author_ids: list[str]) -> list[str]:
        if not author_ids:
            raise BookAuthorsRequiredError()
        seen: set[str] = set()
        normalised: list[str] = []
        for raw_id in author_ids:
            if not isinstance(raw_id, str) or not raw_id.strip():
                raise ValueError("Book author id must be a non-empty string.")
            cleaned = raw_id.strip()
            if cleaned in seen:
                continue
            seen.add(cleaned)
            normalised.append(cleaned)
        return normalised
