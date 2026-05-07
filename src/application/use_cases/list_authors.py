"""
ListAuthorsUseCase
==================
Use case: list all authors with cursor-based pagination.
"""

from __future__ import annotations

from src.application.dtos.author_dtos import (
    ListAuthorsInputDTO,
    ListAuthorsOutputDTO,
)
from src.application.mappers.author_mapper import AuthorMapper
from src.domain.repositories.author_repository import AuthorRepository


class ListAuthorsUseCase:
    """Return a paginated list of authors."""

    def __init__(self, author_repository: AuthorRepository) -> None:
        self._author_repository = author_repository

    async def execute(self, dto: ListAuthorsInputDTO) -> ListAuthorsOutputDTO:
        authors = await self._author_repository.list_all(
            limit=dto.limit, offset=dto.offset
        )
        total = await self._author_repository.count()

        return ListAuthorsOutputDTO(
            authors=[AuthorMapper.to_output_dto(a) for a in authors],
            total=total,
            limit=dto.limit,
            offset=dto.offset,
        )
