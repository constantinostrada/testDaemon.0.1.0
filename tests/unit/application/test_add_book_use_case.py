"""
Unit tests for AddBookUseCase.

The BookRepository is mocked so no real DB is needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dtos.book_dtos import AddBookInputDTO, BookOutputDTO
from src.application.use_cases.add_book import AddBookUseCase
from src.domain.exceptions.domain_exceptions import DuplicateBookError, InvalidISBNError


@pytest.fixture()
def mock_repo() -> AsyncMock:
    """A mock BookRepository."""
    repo = AsyncMock()
    repo.get_by_isbn.return_value = None   # no duplicate by default
    repo.save.return_value = None
    return repo


@pytest.fixture()
def use_case(mock_repo: AsyncMock) -> AddBookUseCase:
    return AddBookUseCase(book_repository=mock_repo)


class TestAddBookUseCase:
    async def test_adds_book_successfully(
        self, use_case: AddBookUseCase, mock_repo: AsyncMock
    ) -> None:
        dto = AddBookInputDTO(
            title="Clean Code",
            authors=["Robert C. Martin"],
            isbn="9780132350884",
            genre="Software Engineering",
            year_published=2008,
        )
        result = await use_case.execute(dto)

        assert result.title == "Clean Code"
        assert result.authors == ["Robert C. Martin"]
        assert result.isbn == "9780132350884"
        assert result.genre == "Software Engineering"
        assert result.status == "unread"
        mock_repo.save.assert_awaited_once()

    async def test_supports_multiple_authors(
        self, use_case: AddBookUseCase
    ) -> None:
        dto = AddBookInputDTO(
            title="Design Patterns",
            authors=["Erich Gamma", "Richard Helm", "Ralph Johnson", "John Vlissides"],
            isbn="9780201633610",
            genre="Software Engineering",
        )
        result = await use_case.execute(dto)
        assert result.authors == [
            "Erich Gamma",
            "Richard Helm",
            "Ralph Johnson",
            "John Vlissides",
        ]

    async def test_invalid_isbn_raises(self, use_case: AddBookUseCase) -> None:
        dto = AddBookInputDTO(
            title="Book",
            authors=["Author"],
            isbn="000000000",  # too short / wrong check
            genre="Fiction",
        )
        with pytest.raises(InvalidISBNError):
            await use_case.execute(dto)

    async def test_duplicate_isbn_raises(
        self, use_case: AddBookUseCase, mock_repo: AsyncMock
    ) -> None:
        # Simulate an existing book with the same ISBN
        existing_book = MagicMock()
        mock_repo.get_by_isbn.return_value = existing_book

        dto = AddBookInputDTO(
            title="Any Title",
            authors=["Any Author"],
            isbn="9780132350884",
            genre="Fiction",
        )
        with pytest.raises(DuplicateBookError):
            await use_case.execute(dto)

        mock_repo.save.assert_not_awaited()

    async def test_output_dto_does_not_expose_domain_entity(
        self, use_case: AddBookUseCase
    ) -> None:
        dto = AddBookInputDTO(
            title="Domain-Driven Design",
            authors=["Eric Evans"],
            isbn="9780321125217",
            genre="Software Engineering",
        )
        result = await use_case.execute(dto)
        assert isinstance(result, BookOutputDTO)
