"""
Unit tests for UpdateBookStatusUseCase.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.application.dtos.book_dtos import UpdateBookStatusInputDTO
from src.application.use_cases.update_book_status import UpdateBookStatusUseCase
from src.domain.entities.book import Book
from src.domain.exceptions.domain_exceptions import (
    BookNotFoundError,
    InvalidBookStatusTransitionError,
)
from src.domain.value_objects.isbn import ISBN


def _make_book() -> Book:
    return Book.create(
        title="Refactoring",
        author="Martin Fowler",
        isbn=ISBN("9780134757599"),
    )


@pytest.fixture()
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.update.return_value = None
    return repo


@pytest.fixture()
def use_case(mock_repo: AsyncMock) -> UpdateBookStatusUseCase:
    return UpdateBookStatusUseCase(book_repository=mock_repo)


class TestUpdateBookStatusUseCase:
    async def test_updates_status_successfully(
        self, use_case: UpdateBookStatusUseCase, mock_repo: AsyncMock
    ) -> None:
        book = _make_book()
        mock_repo.get_by_id.return_value = book

        dto = UpdateBookStatusInputDTO(book_id=book.id, new_status="reading")
        result = await use_case.execute(dto)

        assert result.status == "reading"
        mock_repo.update.assert_awaited_once()

    async def test_not_found_raises(
        self, use_case: UpdateBookStatusUseCase, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_id.return_value = None
        dto = UpdateBookStatusInputDTO(book_id="non-existent", new_status="reading")
        with pytest.raises(BookNotFoundError):
            await use_case.execute(dto)

    async def test_invalid_transition_raises(
        self, use_case: UpdateBookStatusUseCase, mock_repo: AsyncMock
    ) -> None:
        book = _make_book()  # status = UNREAD
        mock_repo.get_by_id.return_value = book

        dto = UpdateBookStatusInputDTO(book_id=book.id, new_status="read")  # skip reading
        with pytest.raises(InvalidBookStatusTransitionError):
            await use_case.execute(dto)

    async def test_invalid_status_string_raises(
        self, use_case: UpdateBookStatusUseCase, mock_repo: AsyncMock
    ) -> None:
        book = _make_book()
        mock_repo.get_by_id.return_value = book

        dto = UpdateBookStatusInputDTO(book_id=book.id, new_status="borrowed")
        with pytest.raises(ValueError):
            await use_case.execute(dto)
