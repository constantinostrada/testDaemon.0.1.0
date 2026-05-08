"""
SearchBooksUseCase
==================
Use case: search the catalogue by combining optional criteria — keyword
in title, keyword in author, and/or exact publication year. All
provided criteria are combined with AND semantics.

Matching policy (decision register)
-----------------------------------
Textual fields (title, author) use **case-insensitive substring**
matching, so end users can find a book by any fragment of the title or
author name without worrying about capitalisation, accents notwithstanding.
The `year_published` criterion is matched **exactly**, because a year is
a precise value where substring semantics would be confusing
(e.g. "199" matching every book from 1990–1999).

This decision is recorded in three accessible places so the team and
future agents can find it without re-deriving it:

  1. This docstring (the use-case-level contract).
  2. The endpoint OpenAPI description on `GET /api/v1/books/search`.
  3. The architecture decision record at
     `docs/decisions/0001-search-matching.md`.

When the criteria match no books, the use case returns an empty
`ListBooksOutputDTO` with `total == 0` — never an error.

Rules (application layer):
  - Imports only from domain/ and application/.
  - Returns a ListBooksOutputDTO, never raw entities.
"""

from __future__ import annotations

from src.application.dtos.book_dtos import (
    ListBooksOutputDTO,
    SearchBooksInputDTO,
)
from src.application.mappers.book_mapper import BookMapper
from src.domain.repositories.book_repository import BookRepository


class SearchBooksUseCase:
    """Search the catalogue with combinable, AND-ed criteria."""

    def __init__(self, book_repository: BookRepository) -> None:
        self._book_repository = book_repository

    async def execute(self, dto: SearchBooksInputDTO) -> ListBooksOutputDTO:
        """
        Execute the search.

        Args:
            dto: SearchBooksInputDTO with optional title/author/year and
                 pagination params.

        Returns:
            ListBooksOutputDTO with the matching page and the total number
            of matches across the whole catalogue. Empty result is a
            normal outcome, not an error.
        """
        title_query = _clean(dto.title_query)
        author_query = _clean(dto.author_query)

        books, total = await self._book_repository.search(
            title_query=title_query,
            author_query=author_query,
            year_published=dto.year_published,
            limit=dto.limit,
            offset=dto.offset,
        )

        return ListBooksOutputDTO(
            books=[BookMapper.to_output_dto(b) for b in books],
            total=total,
            limit=dto.limit,
            offset=dto.offset,
        )


def _clean(value: str | None) -> str | None:
    """Treat blank/whitespace strings as 'no criterion'."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
