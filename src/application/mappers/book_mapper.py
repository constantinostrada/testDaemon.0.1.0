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
from src.application.mappers.author_mapper import AuthorMapper
from src.domain.entities.author import Author
from src.domain.entities.book import Book


class BookMapper:
    """Stateless mapper: Book entity ↔ BookOutputDTO."""

    @staticmethod
    def to_output_dto(book: Book, authors: list[Author]) -> BookOutputDTO:
        """
        Convert a Book entity (plus its hydrated Author entities) to a DTO.

        ``authors`` is provided by the calling use case after looking up the
        author ids referenced by the book. Order is preserved to match
        ``book.author_ids``; missing authors are silently skipped (the use
        case is responsible for verifying referential integrity beforehand).
        """
        authors_by_id = {a.id: a for a in authors}
        ordered_authors = [
            authors_by_id[aid] for aid in book.author_ids if aid in authors_by_id
        ]

        return BookOutputDTO(
            id=book.id,
            title=book.title,
            authors=[AuthorMapper.to_output_dto(a) for a in ordered_authors],
            isbn=book.isbn.value,
            status=book.status.value,
            year_published=book.year_published,
            description=book.description,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
