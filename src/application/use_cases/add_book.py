"""
AddBookUseCase
==============
Use case: add a new book to the library.

Orchestration steps:
  1. Parse and validate the ISBN via the domain value object.
  2. Validate that every referenced author exists.
  3. Check for duplicate ISBN in the repository.
  4. Create a new Book entity (which enforces at-least-one-author).
  5. Persist via the repository interface.
  6. Return a BookOutputDTO with the hydrated Author list.

Rules (application layer):
  - Imports only from domain/ and application/.
  - No SQL, HTTP, or I/O.
  - Single public method: execute(dto).
"""

from __future__ import annotations

from src.application.dtos.book_dtos import AddBookInputDTO, BookOutputDTO
from src.application.mappers.book_mapper import BookMapper
from src.domain.entities.book import Book
from src.domain.exceptions.domain_exceptions import (
    AuthorNotFoundError,
    DuplicateBookError,
)
from src.domain.repositories.author_repository import AuthorRepository
from src.domain.repositories.book_repository import BookRepository
from src.domain.value_objects.isbn import ISBN


class AddBookUseCase:
    """Add a new book to the library catalogue."""

    def __init__(
        self,
        book_repository: BookRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self._book_repository = book_repository
        self._author_repository = author_repository

    async def execute(self, dto: AddBookInputDTO) -> BookOutputDTO:
        """
        Raises:
            InvalidISBNError: if the isbn string is not a valid ISBN.
            BookAuthorsRequiredError: if author_ids is empty.
            AuthorNotFoundError: if any referenced author does not exist.
            DuplicateBookError: if a book with the same ISBN already exists.
        """
        isbn = ISBN(dto.isbn)

        await self._verify_authors_exist(dto.author_ids)

        existing = await self._book_repository.get_by_isbn(isbn)
        if existing is not None:
            raise DuplicateBookError(isbn.value)

        book = Book.create(
            title=dto.title,
            author_ids=dto.author_ids,
            isbn=isbn,
            year_published=dto.year_published,
            description=dto.description,
        )

        await self._book_repository.save(book)

        authors = await self._author_repository.list_by_ids(book.author_ids)
        return BookMapper.to_output_dto(book, authors)

    async def _verify_authors_exist(self, author_ids: list[str]) -> None:
        if not author_ids:
            return  # Domain entity will raise BookAuthorsRequiredError.
        found = await self._author_repository.list_by_ids(author_ids)
        found_ids = {a.id for a in found}
        for aid in author_ids:
            if aid not in found_ids:
                raise AuthorNotFoundError(aid)
