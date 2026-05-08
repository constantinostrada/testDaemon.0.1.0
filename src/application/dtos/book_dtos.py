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

from dataclasses import dataclass
from datetime import datetime

# ---------------------------------------------------------------------------
# Input DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AddBookInputDTO:
    """Input contract for the AddBookUseCase."""

    title: str
    authors: list[str]      # one or more author names
    isbn: str               # raw string — validated by the domain ISBN value object
    genre: str
    year_published: int | None = None


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


@dataclass(frozen=True)
class SearchBooksInputDTO:
    """Input contract for the SearchBooksUseCase.

    All criteria are optional; non-None criteria are combined with AND
    semantics in the use case. Matching rules (substring vs exact) are
    decided at the domain/repository contract level — see ADR
    `docs/decisions/0001-search-matching.md`.
    """

    title_query: str | None = None
    author_query: str | None = None
    year_published: int | None = None
    limit: int = 50
    offset: int = 0


# ---------------------------------------------------------------------------
# Output DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BookOutputDTO:
    """Output contract — a serialisable snapshot of a Book entity."""

    id: str
    title: str
    authors: list[str]
    isbn: str
    genre: str
    status: str
    year_published: int | None
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
