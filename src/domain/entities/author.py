"""
Author Entity
=============
Domain entity representing the author of one or more books.

Invariants enforced at construction and mutation time:
  - full_name must be non-empty (after stripping).
  - bio, when provided, must not be only whitespace.
  - date_of_birth, when provided, must be a real date (validated by caller type).

Rules (domain layer):
  - Zero third-party imports.
  - No ORM decorators.
  - No HTTP types.
  - Raises DomainException subclasses on invariant violations.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from src.domain.exceptions.domain_exceptions import InvalidAuthorError


class Author:
    """
    Aggregate root representing an author who may be referenced by many books.

    Identity is provided by a UUID string (`id`).
    """

    def __init__(
        self,
        *,
        id: str,
        full_name: str,
        bio: str | None = None,
        date_of_birth: date | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._validate_full_name(full_name)
        normalised_bio = self._normalise_bio(bio)

        self._id = id
        self._full_name = full_name.strip()
        self._bio = normalised_bio
        self._date_of_birth = date_of_birth
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or self._created_at

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        full_name: str,
        bio: str | None = None,
        date_of_birth: date | None = None,
    ) -> "Author":
        """Create a new author with a fresh UUID."""
        return cls(
            id=str(uuid.uuid4()),
            full_name=full_name,
            bio=bio,
            date_of_birth=date_of_birth,
        )

    # ------------------------------------------------------------------
    # Properties (read-only)
    # ------------------------------------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def bio(self) -> str | None:
        return self._bio

    @property
    def date_of_birth(self) -> date | None:
        return self._date_of_birth

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # ------------------------------------------------------------------
    # Domain behaviour
    # ------------------------------------------------------------------

    def update_metadata(
        self,
        *,
        full_name: str | None = None,
        bio: str | None = None,
        date_of_birth: date | None = None,
    ) -> None:
        """Update mutable metadata fields. None values are left unchanged."""
        if full_name is not None:
            self._validate_full_name(full_name)
            self._full_name = full_name.strip()
        if bio is not None:
            self._bio = self._normalise_bio(bio)
        if date_of_birth is not None:
            self._date_of_birth = date_of_birth
        self._updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Equality / hashing — identity based
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Author):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"Author(id={self._id!r}, full_name={self._full_name!r})"

    # ------------------------------------------------------------------
    # Private validators
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_full_name(full_name: str) -> None:
        if not full_name or not full_name.strip():
            raise InvalidAuthorError(
                field="full_name", reason="must not be empty"
            )

    @staticmethod
    def _normalise_bio(bio: str | None) -> str | None:
        if bio is None:
            return None
        stripped = bio.strip()
        return stripped or None
