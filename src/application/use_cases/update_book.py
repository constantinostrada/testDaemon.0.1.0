"""
UpdateBookUseCase
=================
Use case: update mutable metadata of an existing book — including its
associated authors.

Orchestration:
  1. Load the book (raises BookNotFoundError if missing).
  2. If author_ids are being changed, verify every referenced author exists.
  3. Delegate the mutation to the entity (domain validation lives there).
  4. Persist and return the updated DTO with hydrated authors.
"""

from __future__ import annotations

from src.application.dtos.book_dtos import BookOutputDTO, UpdateBookInputDTO
from src.application.mappers.book_mapper import BookMapper
from src.domain.exceptions.domain_exceptions import (
    AuthorNotFoundError,
    BookNotFoundError,
)
from src.domain.repositories.author_repository import AuthorRepository
from src.domain.repositories.book_repository import BookRepository


class UpdateBookUseCase:
    """Update a book's mutable metadata (title, authors, year, description)."""

    def __init__(
        self,
        book_repository: BookRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self._book_repository = book_repository
        self._author_repository = author_repository

    async def execute(self, dto: UpdateBookInputDTO) -> BookOutputDTO:
        """
        Raises:
            BookNotFoundError: if the book does not exist.
            AuthorNotFoundError: if a referenced author does not exist.
            BookAuthorsRequiredError: if author_ids becomes empty.
            InvalidBookError: if domain validation fails.
        """
        book = await self._book_repository.get_by_id(dto.book_id)
        if book is None:
            raise BookNotFoundError(dto.book_id)

        if dto.author_ids is not None:
            await self._verify_authors_exist(dto.author_ids)

        book.update_metadata(
            title=dto.title,
            author_ids=dto.author_ids,
            year_published=dto.year_published,
            description=dto.description,
        )

        await self._book_repository.update(book)

        authors = await self._author_repository.list_by_ids(book.author_ids)
        return BookMapper.to_output_dto(book, authors)

    async def _verify_authors_exist(self, author_ids: list[str]) -> None:
        if not author_ids:
            return  # Domain entity will raise BookAuthorsRequiredError.
        found = await self._author_repository.list_by_ids(author_ids)
        found_ids = {a.id for a in found}
        for aid in author_ids:
            if aid not in found_ids:
                raise AuthorNotFoundError(aid)
