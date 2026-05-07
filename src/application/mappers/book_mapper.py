"""
BookMapper
==========
Converts between domain entities and application DTOs.

Rules (application layer):
  - May import from domain/.
  - Returns DTOs, never entities.
  - No infrastructure or HTTP imports.
"""

from __future__ import annotations

from src.application.dtos.book_dtos import BookOutputDTO
from src.domain.entities.book import Book


class BookMapper:
    """Stateless mapper: Book entity ↔ BookOutputDTO."""

    @staticmethod
    def to_output_dto(book: Book) -> BookOutputDTO:
        """Convert a Book domain entity to a serialisable output DTO."""
        return BookOutputDTO(
            id=book.id,
            title=book.title,
            authors=book.authors,
            isbn=book.isbn.value,
            genre=book.genre,
            status=book.status.value,
            year_published=book.year_published,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
