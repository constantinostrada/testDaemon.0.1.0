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
from src.domain.repositories.book_repository import BookRepository
from src.domain.value_objects.book_status import BookStatus


class ListBooksUseCase:
    """Return a paginated list of books, optionally filtered by status."""

    def __init__(self, book_repository: BookRepository) -> None:
        self._book_repository = book_repository

    async def execute(self, dto: ListBooksInputDTO) -> ListBooksOutputDTO:
        """
        Execute the use case.

        Args:
            dto: ListBooksInputDTO with pagination and optional filter params.

        Returns:
            ListBooksOutputDTO containing the page of books and total count.

        Raises:
            ValueError: if status_filter is an unrecognised status string.
        """
        # Resolve optional status filter
        status_filter: BookStatus | None = None
        if dto.status_filter is not None:
            status_filter = BookStatus(dto.status_filter)   # raises ValueError if invalid

        # Fetch page and total in parallel-friendly fashion (two awaits)
        books = await self._book_repository.list_all(
            status_filter=status_filter,
            limit=dto.limit,
            offset=dto.offset,
        )
        total = await self._book_repository.count(status_filter=status_filter)

        return ListBooksOutputDTO(
            books=[BookMapper.to_output_dto(b) for b in books],
            total=total,
            limit=dto.limit,
            offset=dto.offset,
        )
