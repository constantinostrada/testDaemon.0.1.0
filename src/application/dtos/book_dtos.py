"""
Book DTOs (Data Transfer Objects)
==================================
Plain data classes used as input/output contracts for use cases.

Rules (application layer):
  - No domain entities leak through these boundaries.
  - No ORM / HTTP / third-party imports.
  - Use Python dataclasses to stay dependency-free at this layer.
    (Pydantic validation sits in the interfaces layer.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


# ---------------------------------------------------------------------------
# Input DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AddBookInputDTO:
    """Input contract for the AddBookUseCase."""

    title: str
    author: str
    isbn: str               # raw string — validated by the domain ISBN value object
    year_published: int | None = None
    description: str | None = None


@dataclass(frozen=True)
class ListBooksInputDTO:
    """Input contract for the ListBooksUseCase."""

    status_filter: str | None = None   # maps to BookStatus enum in use case
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class UpdateBookStatusInputDTO:
    """Input contract for the UpdateBookStatusUseCase."""

    book_id: str
    new_status: str   # maps to BookStatus enum in use case


@dataclass(frozen=True)
class DeleteBookInputDTO:
    """Input contract for the DeleteBookUseCase."""

    book_id: str


@dataclass(frozen=True)
class GetBookInputDTO:
    """Input contract for the GetBookUseCase."""

    book_id: str


# ---------------------------------------------------------------------------
# Output DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BookOutputDTO:
    """Output contract — a serialisable snapshot of a Book entity."""

    id: str
    title: str
    author: str
    isbn: str
    status: str
    year_published: int | None
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ListBooksOutputDTO:
    """Paginated list result from ListBooksUseCase."""

    books: list[BookOutputDTO]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return (self.offset + self.limit) < self.total
