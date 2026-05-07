"""
ISBN Value Object
=================
Immutable value object representing an International Standard Book Number.

Supports ISBN-10 and ISBN-13.  Equality is by normalised value.

Rules (domain layer):
  - Zero third-party imports.
  - Immutable after construction.
  - Raises InvalidISBNError on invalid input — never silently accepts bad data.
"""

from __future__ import annotations

from src.domain.exceptions.domain_exceptions import InvalidISBNError


class ISBN:
    """
    Immutable value object for a validated book ISBN.

    Accepts ISBN-10 (10 digits) or ISBN-13 (13 digits).
    Hyphens and spaces are stripped before validation so that
    '978-3-16-148410-0' and '9783161484100' are equivalent.
    """

    __slots__ = ("_value",)

    def __init__(self, raw: str) -> None:
        normalised = self._normalise(raw)
        self._validate(normalised, raw)
        self._value = normalised

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def value(self) -> str:
        """Return the normalised (digits-only) ISBN string."""
        return self._value

    # ------------------------------------------------------------------
    # Equality / hashing — value object semantics
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ISBN):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"ISBN({self._value!r})"

    def __str__(self) -> str:
        return self._value

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(raw: str) -> str:
        """Strip hyphens, spaces and convert to uppercase (for ISBN-10 check digit X)."""
        return raw.replace("-", "").replace(" ", "").upper()

    @classmethod
    def _validate(cls, normalised: str, original: str) -> None:
        length = len(normalised)
        if length == 10:
            cls._validate_isbn10(normalised, original)
        elif length == 13:
            cls._validate_isbn13(normalised, original)
        else:
            raise InvalidISBNError(original)

    @staticmethod
    def _validate_isbn10(s: str, original: str) -> None:
        """Validate ISBN-10 check digit."""
        total = 0
        for i, ch in enumerate(s):
            if i == 9 and ch == "X":
                digit = 10
            elif ch.isdigit():
                digit = int(ch)
            else:
                raise InvalidISBNError(original)
            total += digit * (10 - i)
        if total % 11 != 0:
            raise InvalidISBNError(original)

    @staticmethod
    def _validate_isbn13(s: str, original: str) -> None:
        """Validate ISBN-13 check digit."""
        if not s.isdigit():
            raise InvalidISBNError(original)
        total = sum(
            int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(s)
        )
        if total % 10 != 0:
            raise InvalidISBNError(original)
