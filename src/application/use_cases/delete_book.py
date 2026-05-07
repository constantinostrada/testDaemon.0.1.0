"""
DeleteBookUseCase
=================
Use case: permanently remove a book from the library.

Rules (application layer):
  - Imports only from domain/ and application/.
  - Returns None on success (idiomatic delete).
"""

from __future__ import annotations

from src.application.dtos.book_dtos import DeleteBookInputDTO
from src.domain.exceptions.domain_exceptions import BookNotFoundError
from src.domain.repositories.book_repository import BookRepository


class DeleteBookUseCase:
    """Permanently remove a book from the library catalogue."""

    def __init__(self, book_repository: BookRepository) -> None:
        self._book_repository = book_repository

    async def execute(self, dto: DeleteBookInputDTO) -> None:
        """
        Execute the use case.

        Args:
            dto: DeleteBookInputDTO with the target book_id.

        Returns:
            None

        Raises:
            BookNotFoundError: if no book with the given ID exists.
        """
        book = await self._book_repository.get_by_id(dto.book_id)
        if book is None:
            raise BookNotFoundError(dto.book_id)

        await self._book_repository.delete(dto.book_id)
