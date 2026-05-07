"""
ListBooksUseCase
================
Use case: list all books in the library, with optional status filtering
and cursor-based pagination.

Rules (application layer):
  - Imports only from domain/ and application/.
  - Returns a ListBooksOutputDTO, never raw entities.
"""

from __future__ import annotations

from src.application.dtos.book_dtos import (
    ListBooksInputDTO,
    ListBooksOutputDTO,
)
from src.application.mappers.book_mapper import BookMapper
from src.domain.repositories.author_repository import AuthorRepository
from src.domain.repositories.book_repository import BookRepository
from src.domain.value_objects.book_status import BookStatus


class ListBooksUseCase:
    """Return a paginated list of books, optionally filtered by status."""

    def __init__(
        self,
        book_repository: BookRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self._book_repository = book_repository
        self._author_repository = author_repository

    async def execute(self, dto: ListBooksInputDTO) -> ListBooksOutputDTO:
        """
        Raises:
            ValueError: if status_filter is an unrecognised status string.
        """
        status_filter: BookStatus | None = None
        if dto.status_filter is not None:
            status_filter = BookStatus(dto.status_filter)

        books = await self._book_repository.list_all(
            status_filter=status_filter,
            limit=dto.limit,
            offset=dto.offset,
        )
        total = await self._book_repository.count(status_filter=status_filter)

        # Hydrate every author referenced by any book on this page in one shot.
        all_author_ids: list[str] = []
        seen: set[str] = set()
        for book in books:
            for aid in book.author_ids:
                if aid not in seen:
                    seen.add(aid)
                    all_author_ids.append(aid)
        authors = (
            await self._author_repository.list_by_ids(all_author_ids)
            if all_author_ids
            else []
        )

        return ListBooksOutputDTO(
            books=[BookMapper.to_output_dto(b, authors) for b in books],
            total=total,
            limit=dto.limit,
            offset=dto.offset,
        )
