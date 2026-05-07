"""
Domain Exceptions
=================
Custom exception hierarchy for the domain layer.

Rules:
  - All exceptions inherit from DomainException.
  - No imports from outside domain/.
  - Carry only primitive data — no infrastructure or HTTP concepts.
"""


class DomainException(Exception):  # noqa: N818
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
