"""
AuthorRepository Interface
==========================
Abstract repository interface for Author persistence.

This interface defines WHAT operations are available — not HOW they
are implemented. Concrete implementations live in infrastructure/.

Rules (domain layer):
  - No ORM, SQL, or I/O imports.
  - Methods are async to allow any concrete implementation.
  - Returns domain entities, never raw DB rows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.author import Author


class AuthorRepository(ABC):
    """Abstract interface for Author persistence operations."""

    @abstractmethod
    async def save(self, author: Author) -> None:
        """
        Persist a new author.

        Raises:
            DuplicateAuthorError: if an author with the same full_name already exists.
        """
        ...

    @abstractmethod
    async def get_by_id(self, author_id: str) -> Author | None:
        """Return the Author with the given id, or None if not found."""
        ...

    @abstractmethod
    async def get_by_full_name(self, full_name: str) -> Author | None:
        """Return the Author whose normalised full_name matches, or None."""
        ...

    @abstractmethod
    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Author]:
        """Return a paginated list of all authors."""
        ...

    @abstractmethod
    async def list_by_ids(self, author_ids: list[str]) -> list[Author]:
        """Return all authors whose ids appear in the given list."""
        ...

    @abstractmethod
    async def update(self, author: Author) -> None:
        """
        Persist changes to an existing author.

        Raises:
            AuthorNotFoundError: if the author does not exist.
        """
        ...

    @abstractmethod
    async def delete(self, author_id: str) -> None:
        """
        Remove an author from the repository.

        Raises:
            AuthorNotFoundError: if no author with the given id exists.
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """Return the total number of authors."""
        ...

    @abstractmethod
    async def exists(self, author_id: str) -> bool:
        """Return True if the author with the given id exists."""
        ...

    @abstractmethod
    async def count_books_by_author(self, author_id: str) -> int:
        """Return the number of books that reference this author."""
        ...
