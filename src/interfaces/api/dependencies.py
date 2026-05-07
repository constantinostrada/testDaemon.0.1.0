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
from src.application.use_cases.create_author import CreateAuthorUseCase
from src.application.use_cases.delete_author import DeleteAuthorUseCase
from src.application.use_cases.delete_book import DeleteBookUseCase
from src.application.use_cases.get_author import GetAuthorUseCase
from src.application.use_cases.get_book import GetBookUseCase
from src.application.use_cases.list_authors import ListAuthorsUseCase
from src.application.use_cases.list_books import ListBooksUseCase
from src.application.use_cases.update_author import UpdateAuthorUseCase
from src.application.use_cases.update_book import UpdateBookUseCase
from src.application.use_cases.update_book_status import UpdateBookStatusUseCase
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.database.sqlite_client import SQLiteClient
from src.infrastructure.repositories.sqlite_author_repository import (
    SQLiteAuthorRepository,
)
from src.infrastructure.repositories.sqlite_book_repository import (
    SQLiteBookRepository,
)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def provide_settings() -> Settings:
    return get_settings()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _create_db_client(db_path: str) -> SQLiteClient:
    return SQLiteClient(db_path=db_path)


def provide_db_client(
    settings: Annotated[Settings, Depends(provide_settings)],
) -> SQLiteClient:
    return _create_db_client(settings.database_url)


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


def provide_book_repository(
    db_client: Annotated[SQLiteClient, Depends(provide_db_client)],
) -> SQLiteBookRepository:
    return SQLiteBookRepository(db_client=db_client)


def provide_author_repository(
    db_client: Annotated[SQLiteClient, Depends(provide_db_client)],
) -> SQLiteAuthorRepository:
    return SQLiteAuthorRepository(db_client=db_client)


# ---------------------------------------------------------------------------
# Book Use Cases
# ---------------------------------------------------------------------------


def provide_add_book_use_case(
    book_repo: Annotated[SQLiteBookRepository, Depends(provide_book_repository)],
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> AddBookUseCase:
    return AddBookUseCase(
        book_repository=book_repo, author_repository=author_repo
    )


def provide_get_book_use_case(
    book_repo: Annotated[SQLiteBookRepository, Depends(provide_book_repository)],
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> GetBookUseCase:
    return GetBookUseCase(
        book_repository=book_repo, author_repository=author_repo
    )


def provide_list_books_use_case(
    book_repo: Annotated[SQLiteBookRepository, Depends(provide_book_repository)],
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> ListBooksUseCase:
    return ListBooksUseCase(
        book_repository=book_repo, author_repository=author_repo
    )


def provide_update_book_use_case(
    book_repo: Annotated[SQLiteBookRepository, Depends(provide_book_repository)],
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> UpdateBookUseCase:
    return UpdateBookUseCase(
        book_repository=book_repo, author_repository=author_repo
    )


def provide_update_book_status_use_case(
    book_repo: Annotated[SQLiteBookRepository, Depends(provide_book_repository)],
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> UpdateBookStatusUseCase:
    return UpdateBookStatusUseCase(
        book_repository=book_repo, author_repository=author_repo
    )


def provide_delete_book_use_case(
    book_repo: Annotated[SQLiteBookRepository, Depends(provide_book_repository)],
) -> DeleteBookUseCase:
    return DeleteBookUseCase(book_repository=book_repo)


# ---------------------------------------------------------------------------
# Author Use Cases
# ---------------------------------------------------------------------------


def provide_create_author_use_case(
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> CreateAuthorUseCase:
    return CreateAuthorUseCase(author_repository=author_repo)


def provide_get_author_use_case(
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> GetAuthorUseCase:
    return GetAuthorUseCase(author_repository=author_repo)


def provide_list_authors_use_case(
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> ListAuthorsUseCase:
    return ListAuthorsUseCase(author_repository=author_repo)


def provide_update_author_use_case(
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> UpdateAuthorUseCase:
    return UpdateAuthorUseCase(author_repository=author_repo)


def provide_delete_author_use_case(
    author_repo: Annotated[
        SQLiteAuthorRepository, Depends(provide_author_repository)
    ],
) -> DeleteAuthorUseCase:
    return DeleteAuthorUseCase(author_repository=author_repo)
