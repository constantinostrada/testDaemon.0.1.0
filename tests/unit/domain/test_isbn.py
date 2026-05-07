"""
Unit tests for the ISBN value object.
"""

import pytest

from src.domain.exceptions.domain_exceptions import InvalidISBNError
from src.domain.value_objects.isbn import ISBN


class TestISBN:
    # ------------------------------------------------------------------
    # Valid ISBN-13
    # ------------------------------------------------------------------

    def test_valid_isbn13_digits_only(self) -> None:
        isbn = ISBN("9780132350884")
        assert isbn.value == "9780132350884"

    def test_valid_isbn13_with_hyphens(self) -> None:
        isbn = ISBN("978-0-13-235088-4")
        assert isbn.value == "9780132350884"

    # ------------------------------------------------------------------
    # Valid ISBN-10
    # ------------------------------------------------------------------

    def test_valid_isbn10(self) -> None:
        isbn = ISBN("0132350882")
        assert isbn.value == "0132350882"

    def test_valid_isbn10_with_x_check_digit(self) -> None:
        # ISBN-10 with X as check digit
        isbn = ISBN("047191738X")
        assert isbn.value == "047191738X"

    # ------------------------------------------------------------------
    # Equality / hashing
    # ------------------------------------------------------------------

    def test_equality_same_value(self) -> None:
        a = ISBN("9780132350884")
        b = ISBN("978-0-13-235088-4")
        assert a == b

    def test_inequality_different_isbns(self) -> None:
        a = ISBN("9780132350884")
        b = ISBN("9783161484100")
        assert a != b

    def test_hashable_can_be_used_in_set(self) -> None:
        a = ISBN("9780132350884")
        b = ISBN("978-0-13-235088-4")
        assert len({a, b}) == 1

    # ------------------------------------------------------------------
    # Invalid inputs
    # ------------------------------------------------------------------

    def test_too_short_raises(self) -> None:
        with pytest.raises(InvalidISBNError):
            ISBN("123")

    def test_wrong_check_digit_raises(self) -> None:
        with pytest.raises(InvalidISBNError):
            ISBN("9780132350885")  # last digit changed

    def test_letters_in_isbn13_raises(self) -> None:
        with pytest.raises(InvalidISBNError):
            ISBN("978013235088A")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidISBNError):
            ISBN("")
