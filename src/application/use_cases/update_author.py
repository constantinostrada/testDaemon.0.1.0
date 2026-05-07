"""
UpdateAuthorUseCase
===================
Use case: update mutable metadata of an existing author.

Orchestration:
  1. Load the author (raise AuthorNotFoundError if missing).
  2. If full_name is being changed, ensure no other author already has it.
  3. Delegate the mutation to the entity (domain validation lives there).
  4. Persist and return the updated DTO.
"""

from __future__ import annotations

from src.application.dtos.author_dtos import AuthorOutputDTO, UpdateAuthorInputDTO
from src.application.mappers.author_mapper import AuthorMapper
from src.domain.exceptions.domain_exceptions import (
    AuthorNotFoundError,
    DuplicateAuthorError,
)
from src.domain.repositories.author_repository import AuthorRepository


class UpdateAuthorUseCase:
    """Update an author's mutable metadata."""

    def __init__(self, author_repository: AuthorRepository) -> None:
        self._author_repository = author_repository

    async def execute(self, dto: UpdateAuthorInputDTO) -> AuthorOutputDTO:
        """
        Raises:
            AuthorNotFoundError: if the author does not exist.
            DuplicateAuthorError: if renaming would collide with another author.
            InvalidAuthorError: if domain validation fails.
        """
        author = await self._author_repository.get_by_id(dto.author_id)
        if author is None:
            raise AuthorNotFoundError(dto.author_id)

        if dto.full_name is not None and dto.full_name.strip() != author.full_name:
            other = await self._author_repository.get_by_full_name(dto.full_name)
            if other is not None and other.id != author.id:
                raise DuplicateAuthorError(dto.full_name)

        author.update_metadata(
            full_name=dto.full_name,
            bio=dto.bio,
            date_of_birth=dto.date_of_birth,
        )

        await self._author_repository.update(author)

        return AuthorMapper.to_output_dto(author)
