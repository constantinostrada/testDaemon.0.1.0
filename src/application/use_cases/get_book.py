"""
GetBookUseCase
==============
Use case: retrieve a single book by its ID.

Rules (application layer):
  - Imports only from domain/ and application/.
  - Returns a DTO, never a raw entity.
"""

from __future__ import annotations

from src.application.dtos.book_dtos import BookOutputDTO, GetBookInputDTO
from src.application.mappers.book_mapper import BookMapper
from src.domain.exceptions.domain_exceptions import BookNotFoundError
from src.domain.repositories.book_repository import BookRepository


class GetBookUseCase:
    """Retrieve a single book by its unique ID."""

    def __init__(self, book_repository: BookRepository) -> None:
        self._book_repository = book_repository

    async def execute(self, dto: GetBookInputDTO) -> BookOutputDTO:
        """
        Execute the use case.

        Args:
            dto: GetBookInputDTO with the target book_id.

        Returns:
            BookOutputDTO for the found book.

        Raises:
            BookNotFoundError: if no book with the given ID exists.
        """
        book = await self._book_repository.get_by_id(dto.book_id)
        if book is None:
            raise BookNotFoundError(dto.book_id)

        return BookMapper.to_output_dto(book)
