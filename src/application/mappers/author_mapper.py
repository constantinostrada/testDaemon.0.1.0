"""
AuthorMapper
============
Converts between Author domain entities and application DTOs.

Rules (application layer):
  - May import from domain/.
  - Returns DTOs, never entities.
  - No infrastructure or HTTP imports.
"""

from __future__ import annotations

from src.application.dtos.author_dtos import AuthorOutputDTO
from src.domain.entities.author import Author


class AuthorMapper:
    """Stateless mapper: Author entity ↔ AuthorOutputDTO."""

    @staticmethod
    def to_output_dto(author: Author) -> AuthorOutputDTO:
        """Convert an Author domain entity to a serialisable output DTO."""
        return AuthorOutputDTO(
            id=author.id,
            full_name=author.full_name,
            bio=author.bio,
            date_of_birth=author.date_of_birth,
            created_at=author.created_at,
            updated_at=author.updated_at,
        )
