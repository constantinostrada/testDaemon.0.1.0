"""
CreateAuthorUseCase
===================
Use case: register a new author in the library.

Orchestration steps:
  1. Check that no author with the same full_name already exists.
  2. Build the Author domain entity (validation lives in the entity).
  3. Persist via the repository interface.
  4. Return an AuthorOutputDTO.

Rules (application layer):
  - Imports only from domain/ and application/.
  - No SQL, HTTP, or I/O.
"""

from __future__ import annotations

from src.application.dtos.author_dtos import (
    AuthorOutputDTO,
    CreateAuthorInputDTO,
)
from src.application.mappers.author_mapper import AuthorMapper
from src.domain.entities.author import Author
from src.domain.exceptions.domain_exceptions import DuplicateAuthorError
from src.domain.repositories.author_repository import AuthorRepository


class CreateAuthorUseCase:
    """Register a new author in the library."""

    def __init__(self, author_repository: AuthorRepository) -> None:
        self._author_repository = author_repository

    async def execute(self, dto: CreateAuthorInputDTO) -> AuthorOutputDTO:
        """
        Execute the use case.

        Raises:
            InvalidAuthorError: if domain validation fails.
            DuplicateAuthorError: if an author with the same full_name exists.
        """
        existing = await self._author_repository.get_by_full_name(dto.full_name)
        if existing is not None:
            raise DuplicateAuthorError(dto.full_name)

        author = Author.create(
            full_name=dto.full_name,
            bio=dto.bio,
            date_of_birth=dto.date_of_birth,
        )

        await self._author_repository.save(author)

        return AuthorMapper.to_output_dto(author)
