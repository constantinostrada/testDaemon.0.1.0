"""
GetAuthorUseCase
================
Use case: retrieve a single author by its ID.
"""

from __future__ import annotations

from src.application.dtos.author_dtos import AuthorOutputDTO, GetAuthorInputDTO
from src.application.mappers.author_mapper import AuthorMapper
from src.domain.exceptions.domain_exceptions import AuthorNotFoundError
from src.domain.repositories.author_repository import AuthorRepository


class GetAuthorUseCase:
    """Retrieve a single author by its unique ID."""

    def __init__(self, author_repository: AuthorRepository) -> None:
        self._author_repository = author_repository

    async def execute(self, dto: GetAuthorInputDTO) -> AuthorOutputDTO:
        """
        Raises:
            AuthorNotFoundError: if no author with the given ID exists.
        """
        author = await self._author_repository.get_by_id(dto.author_id)
        if author is None:
            raise AuthorNotFoundError(dto.author_id)

        return AuthorMapper.to_output_dto(author)
