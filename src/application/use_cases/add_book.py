"""
AddBookUseCase
==============
Use case: add a new book to the library.

Orchestration steps:
  1. Parse and validate the ISBN via the domain value object.
  2. Check for duplicate ISBN in the repository.
  3. Create a new Book entity.
  4. Persist via the repository interface.
  5. Return a BookOutputDTO.

Rules (application layer):
  - Imports only from domain/ and application/.
  - No SQL, HTTP, or I/O.
  - Single public method: execute(dto).
"""

from __future__ import annotations

from src.application.dtos.book_dtos import AddBookInputDTO, BookOutputDTO
from src.application.mappers.book_mapper import BookMapper
from src.domain.entities.book import Book
from src.domain.exceptions.domain_exceptions import DuplicateBookError
from src.domain.repositories.book_repository import BookRepository
from src.domain.value_objects.isbn import ISBN


class AddBookUseCase:
    """Add a new book to the library catalogue."""

    def __init__(self, book_repository: BookRepository) -> None:
        self._book_repository = book_repository

    async def execute(self, dto: AddBookInputDTO) -> BookOutputDTO:
        """
        Execute the use case.

        Args:
            dto: AddBookInputDTO carrying the book details.

        Returns:
            BookOutputDTO representing the newly created book.

        Raises:
            InvalidISBNError: if the isbn string is not a valid ISBN.
            DuplicateBookError: if a book with the same ISBN already exists.
        """
        # 1. Parse & validate ISBN (domain raises InvalidISBNError on failure)
        isbn = ISBN(dto.isbn)

        # 2. Guard against duplicates
        existing = await self._book_repository.get_by_isbn(isbn)
        if existing is not None:
            raise DuplicateBookError(isbn.value)

        # 3. Create domain entity
        book = Book.create(
            title=dto.title,
            authors=dto.authors,
            isbn=isbn,
            genre=dto.genre,
            year_published=dto.year_published,
        )

        # 4. Persist
        await self._book_repository.save(book)

        # 5. Return DTO — never expose raw domain entities
        return BookMapper.to_output_dto(book)
