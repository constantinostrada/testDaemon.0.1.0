"""
BookAvailabilityService — Domain Service
========================================
Encapsulates business logic that spans multiple entities or that does not
naturally belong on a single entity.

This service determines whether a book can be "checked out" (i.e. is in
UNREAD or READ status and not currently being read).

Rules (domain layer):
  - No third-party imports.
  - No I/O, no logging frameworks.
  - Receives domain objects; returns domain results.
"""

from __future__ import annotations

from src.domain.entities.book import Book
from src.domain.value_objects.book_status import BookStatus


class BookAvailabilityService:
    """
    Domain service for computing book availability in the library.

    A book is considered *available* (ready to be picked up) when its
    status is UNREAD.  A book that is currently READING is considered
    *in use*.  A READ book is *archived*.
    """

    def is_available(self, book: Book) -> bool:
        """Return True if the book is on the shelf and ready to read."""
        return book.status == BookStatus.UNREAD

    def is_in_progress(self, book: Book) -> bool:
        """Return True if the book is currently being read."""
        return book.status == BookStatus.READING

    def is_archived(self, book: Book) -> bool:
        """Return True if the book has been fully read."""
        return book.status == BookStatus.READ

    def availability_summary(self, books: list[Book]) -> dict[str, int]:
        """
        Return a count summary of books by availability category.

        Example return value::

            {"available": 4, "in_progress": 1, "archived": 7}
        """
        available = sum(1 for b in books if self.is_available(b))
        in_progress = sum(1 for b in books if self.is_in_progress(b))
        archived = sum(1 for b in books if self.is_archived(b))
        return {
            "available": available,
            "in_progress": in_progress,
            "archived": archived,
        }
