"""
Domain Exceptions
=================
Custom exception hierarchy for the domain layer.

Rules:
  - All exceptions inherit from DomainException.
  - No imports from outside domain/.
  - Carry only primitive data — no infrastructure or HTTP concepts.
"""


class DomainException(Exception):
    """Base class for all domain exceptions."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"


class BookNotFoundError(DomainException):
    """Raised when a requested Book does not exist in the repository."""

    def __init__(self, book_id: str) -> None:
        super().__init__(f"Book with id '{book_id}' was not found.")
        self.book_id = book_id


class InvalidISBNError(DomainException):
    """Raised when an ISBN string fails format validation."""

    def __init__(self, raw_isbn: str) -> None:
        super().__init__(
            f"'{raw_isbn}' is not a valid ISBN-10 or ISBN-13. "
            "Provide digits only (hyphens are stripped automatically)."
        )
        self.raw_isbn = raw_isbn


class DuplicateBookError(DomainException):
    """Raised when attempting to add a book whose ISBN is already registered."""

    def __init__(self, isbn: str) -> None:
        super().__init__(f"A book with ISBN '{isbn}' already exists in the library.")
        self.isbn = isbn


class InvalidBookStatusTransitionError(DomainException):
    """Raised when a status transition is not permitted by domain rules."""

    def __init__(self, current: str, requested: str) -> None:
        super().__init__(
            f"Cannot transition book status from '{current}' to '{requested}'."
        )
        self.current = current
        self.requested = requested


class AuthorNotFoundError(DomainException):
    """Raised when a requested Author does not exist in the repository."""

    def __init__(self, author_id: str) -> None:
        super().__init__(f"Author with id '{author_id}' was not found.")
        self.author_id = author_id


class DuplicateAuthorError(DomainException):
    """Raised when attempting to create an author whose full_name is already registered."""

    def __init__(self, full_name: str) -> None:
        super().__init__(
            f"An author named '{full_name}' already exists in the library."
        )
        self.full_name = full_name


class AuthorHasBooksError(DomainException):
    """Raised when attempting to delete an author still referenced by one or more books."""

    def __init__(self, author_id: str, book_count: int) -> None:
        super().__init__(
            f"Author '{author_id}' cannot be deleted because {book_count} "
            "book(s) still reference them."
        )
        self.author_id = author_id
        self.book_count = book_count


class InvalidAuthorError(DomainException):
    """Raised when an Author field fails domain validation."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"Invalid author {field}: {reason}")
        self.field = field
        self.reason = reason


class BookAuthorsRequiredError(DomainException):
    """Raised when a book is created or updated without at least one author."""

    def __init__(self) -> None:
        super().__init__("A book must have at least one author.")
