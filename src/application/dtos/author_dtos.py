"""
Author DTOs (Data Transfer Objects)
====================================
Plain data classes used as input/output contracts for author use cases.

Rules (application layer):
  - No domain entities leak through these boundaries.
  - No ORM / HTTP / third-party imports.
  - Use Python dataclasses to stay dependency-free at this layer.
    (Pydantic validation sits in the interfaces layer.)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Input DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CreateAuthorInputDTO:
    """Input contract for the CreateAuthorUseCase."""

    full_name: str
    bio: str | None = None
    date_of_birth: date | None = None


@dataclass(frozen=True)
class UpdateAuthorInputDTO:
    """Input contract for the UpdateAuthorUseCase."""

    author_id: str
    full_name: str | None = None
    bio: str | None = None
    date_of_birth: date | None = None


@dataclass(frozen=True)
class DeleteAuthorInputDTO:
    """Input contract for the DeleteAuthorUseCase."""

    author_id: str


@dataclass(frozen=True)
class GetAuthorInputDTO:
    """Input contract for the GetAuthorUseCase."""

    author_id: str


@dataclass(frozen=True)
class ListAuthorsInputDTO:
    """Input contract for the ListAuthorsUseCase."""

    limit: int = 50
    offset: int = 0


# ---------------------------------------------------------------------------
# Output DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorOutputDTO:
    """Output contract — a serialisable snapshot of an Author entity."""

    id: str
    full_name: str
    bio: str | None
    date_of_birth: date | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ListAuthorsOutputDTO:
    """Paginated list result from ListAuthorsUseCase."""

    authors: list[AuthorOutputDTO]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return (self.offset + self.limit) < self.total
