"""
FastAPI Dependency Injection
============================
Wires infrastructure implementations to use case constructors.

This module is the ONLY place in the codebase where infrastructure classes
are instantiated and injected into application use cases.

Rules:
  - Infrastructure is allowed to be imported HERE (interfaces layer is the
    composition root).
  - Use cases are constructed with concrete repository implementations.
  - The rest of the interface layer (controllers) receives use-case instances
    via FastAPI's Depends() mechanism.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.application.use_cases.add_book import AddBookUseCase
from src.application.use_cases.delete_book import DeleteBookUseCase
from src.application.use_cases.get_book import GetBookUseCase
from src.application.use_cases.list_books import ListBooksUseCase
from src.application.use_cases.search_books import SearchBooksUseCase
from src.application.use_cases.update_book_status import UpdateBookStatusUseCase
from src.domain.repositories.book_repository import BookRepository
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.repositories.in_memory_book_repository import (
    InMemoryBookRepository,
)

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def provide_settings() -> Settings:
    return get_settings()


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _book_repository_singleton() -> InMemoryBookRepository:
    return InMemoryBookRepository()


def provide_book_repository() -> BookRepository:
    return _book_repository_singleton()


# ---------------------------------------------------------------------------
# Use Cases
# ---------------------------------------------------------------------------


def provide_add_book_use_case(
    repo: Annotated[BookRepository, Depends(provide_book_repository)],
) -> AddBookUseCase:
    return AddBookUseCase(book_repository=repo)


def provide_get_book_use_case(
    repo: Annotated[BookRepository, Depends(provide_book_repository)],
) -> GetBookUseCase:
    return GetBookUseCase(book_repository=repo)


def provide_list_books_use_case(
    repo: Annotated[BookRepository, Depends(provide_book_repository)],
) -> ListBooksUseCase:
    return ListBooksUseCase(book_repository=repo)


def provide_update_book_status_use_case(
    repo: Annotated[BookRepository, Depends(provide_book_repository)],
) -> UpdateBookStatusUseCase:
    return UpdateBookStatusUseCase(book_repository=repo)


def provide_delete_book_use_case(
    repo: Annotated[BookRepository, Depends(provide_book_repository)],
) -> DeleteBookUseCase:
    return DeleteBookUseCase(book_repository=repo)


def provide_search_books_use_case(
    repo: Annotated[BookRepository, Depends(provide_book_repository)],
) -> SearchBooksUseCase:
    return SearchBooksUseCase(book_repository=repo)
