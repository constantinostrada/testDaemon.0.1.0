"""
BookStatus Value Object
=======================
Immutable enumeration representing the reading lifecycle of a book.

Allowed transitions (enforced by the domain entity, not here):

    UNREAD → READING → READ
    READING → UNREAD   (put back on shelf)

Rules (domain layer):
  - No third-party imports.
  - Immutable; equality by value.
"""

from __future__ import annotations

from enum import Enum


class BookStatus(str, Enum):
    """Represents where a book sits in the reader's lifecycle."""

    UNREAD = "unread"
    READING = "reading"
    READ = "read"

    # ------------------------------------------------------------------
    # Allowed transitions map
    # ------------------------------------------------------------------

    @classmethod
    def allowed_transitions(cls) -> dict["BookStatus", set["BookStatus"]]:
        """Return the set of valid next-states for each status."""
        return {
            cls.UNREAD: {cls.READING},
            cls.READING: {cls.READ, cls.UNREAD},
            cls.READ: set(),  # terminal state — no further transitions
        }

    def can_transition_to(self, next_status: "BookStatus") -> bool:
        """Return True if transitioning from *self* to *next_status* is allowed."""
        return next_status in self.allowed_transitions().get(self, set())

    def __str__(self) -> str:
        return self.value
