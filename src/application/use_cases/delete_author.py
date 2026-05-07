"""
DeleteAuthorUseCase
===================
Use case: permanently delete an author from the library.

Orchestration:
  1. Verify the author exists (raise AuthorNotFoundError if not).
  2. Verify no books still reference this author (raise AuthorHasBooksError).
  3. Delete the author.
"""

from __future__ import annotations

from src.application.dtos.author_dtos import DeleteAuthorInputDTO
from src.domain.exceptions.domain_exceptions import (
    AuthorHasBooksError,
    AuthorNotFoundError,
)
from src.domain.repositories.author_repository import AuthorRepository


class DeleteAuthorUseCase:
    """Permanently remove an author who is not referenced by any books."""

    def __init__(self, author_repository: AuthorRepository) -> None:
        self._author_repository = author_repository

    async def execute(self, dto: DeleteAuthorInputDTO) -> None:
        """
        Raises:
            AuthorNotFoundError: if the author does not exist.
            AuthorHasBooksError: if one or more books reference this author.
        """
        if not await self._author_repository.exists(dto.author_id):
            raise AuthorNotFoundError(dto.author_id)

        book_count = await self._author_repository.count_books_by_author(
            dto.author_id
        )
        if book_count > 0:
            raise AuthorHasBooksError(
                author_id=dto.author_id, book_count=book_count
            )

        await self._author_repository.delete(dto.author_id)
