"""
UpdateBookStatusUseCase
=======================
Use case: transition a book's reading status.

Orchestration steps:
  1. Load the book (raises BookNotFoundError if missing).
  2. Parse the requested status into a BookStatus enum value.
  3. Delegate the transition to the domain entity (raises
     InvalidBookStatusTransitionError if the move is forbidden).
  4. Persist the updated entity.
  5. Return the updated BookOutputDTO.

Rules (application layer):
  - Imports only from domain/ and application/.
  - Business rule (allowed transitions) is enforced inside Book.update_status().
"""

from __future__ import annotations

from src.application.dtos.book_dtos import BookOutputDTO, UpdateBookStatusInputDTO
from src.application.mappers.book_mapper import BookMapper
from src.domain.exceptions.domain_exceptions import BookNotFoundError
from src.domain.repositories.book_repository import BookRepository
from src.domain.value_objects.book_status import BookStatus


class UpdateBookStatusUseCase:
    """Transition a book's reading status following domain lifecycle rules."""

    def __init__(self, book_repository: BookRepository) -> None:
        self._book_repository = book_repository

    async def execute(self, dto: UpdateBookStatusInputDTO) -> BookOutputDTO:
        """
        Execute the use case.

        Args:
            dto: UpdateBookStatusInputDTO with book_id and new_status.

        Returns:
            Updated BookOutputDTO.

        Raises:
            BookNotFoundError: if no book with the given ID exists.
            ValueError: if new_status is not a recognised BookStatus value.
            InvalidBookStatusTransitionError: if the transition is not allowed.
        """
        # 1. Load
        book = await self._book_repository.get_by_id(dto.book_id)
        if book is None:
            raise BookNotFoundError(dto.book_id)

        # 2. Parse requested status (ValueError if unknown)
        new_status = BookStatus(dto.new_status)

        # 3. Domain entity enforces transition rules
        book.update_status(new_status)

        # 4. Persist
        await self._book_repository.update(book)

        # 5. Return DTO
        return BookMapper.to_output_dto(book)
