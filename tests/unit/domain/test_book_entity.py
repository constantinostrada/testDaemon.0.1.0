"""
Unit tests for the Book entity.
"""

import pytest

from src.domain.entities.book import Book
from src.domain.exceptions.domain_exceptions import InvalidBookStatusTransitionError
from src.domain.value_objects.book_status import BookStatus
from src.domain.value_objects.isbn import ISBN


def make_book(**kwargs: object) -> Book:
    """Helper: create a Book with sensible defaults."""
    defaults: dict[str, object] = {
        "title": "Clean Code",
        "authors": ["Robert C. Martin"],
        "isbn": ISBN("9780132350884"),
        "genre": "Software Engineering",
    }
    defaults.update(kwargs)
    return Book.create(**defaults)  # type: ignore[arg-type]


class TestBookCreation:
    def test_creates_with_unread_status(self) -> None:
        book = make_book()
        assert book.status == BookStatus.UNREAD

    def test_assigns_unique_id(self) -> None:
        a = make_book()
        b = make_book()
        assert a.id != b.id

    def test_strips_title_whitespace(self) -> None:
        book = make_book(title="  Refactoring  ")
        assert book.title == "Refactoring"

    def test_empty_title_raises(self) -> None:
        with pytest.raises(ValueError, match="title"):
            make_book(title="   ")

    def test_empty_authors_list_raises(self) -> None:
        with pytest.raises(ValueError, match="author"):
            make_book(authors=[])

    def test_blank_author_name_raises(self) -> None:
        with pytest.raises(ValueError, match="author"):
            make_book(authors=["Valid", "  "])

    def test_empty_genre_raises(self) -> None:
        with pytest.raises(ValueError, match="genre"):
            make_book(genre="   ")

    def test_supports_multiple_authors(self) -> None:
        book = make_book(authors=["Erich Gamma", "Richard Helm", "Ralph Johnson"])
        assert book.authors == ["Erich Gamma", "Richard Helm", "Ralph Johnson"]

    def test_authors_property_returns_defensive_copy(self) -> None:
        book = make_book(authors=["A", "B"])
        authors = book.authors
        authors.append("Mutation")
        assert book.authors == ["A", "B"]


class TestBookStatusTransitions:
    def test_unread_to_reading_allowed(self) -> None:
        book = make_book()
        book.update_status(BookStatus.READING)
        assert book.status == BookStatus.READING

    def test_reading_to_read_allowed(self) -> None:
        book = make_book()
        book.update_status(BookStatus.READING)
        book.update_status(BookStatus.READ)
        assert book.status == BookStatus.READ

    def test_reading_back_to_unread_allowed(self) -> None:
        book = make_book()
        book.update_status(BookStatus.READING)
        book.update_status(BookStatus.UNREAD)
        assert book.status == BookStatus.UNREAD

    def test_unread_directly_to_read_forbidden(self) -> None:
        book = make_book()
        with pytest.raises(InvalidBookStatusTransitionError):
            book.update_status(BookStatus.READ)

    def test_read_is_terminal(self) -> None:
        book = make_book()
        book.update_status(BookStatus.READING)
        book.update_status(BookStatus.READ)
        with pytest.raises(InvalidBookStatusTransitionError):
            book.update_status(BookStatus.UNREAD)

    def test_update_status_changes_updated_at(self) -> None:
        book = make_book()
        original = book.updated_at
        book.update_status(BookStatus.READING)
        assert book.updated_at >= original


class TestBookEquality:
    def test_same_id_equal(self) -> None:
        book = make_book()
        clone = Book(
            id=book.id,
            title="Different Title",
            authors=["Other Author"],
            isbn=ISBN("9780132350884"),
            genre="Other Genre",
        )
        assert book == clone

    def test_different_ids_not_equal(self) -> None:
        a = make_book()
        b = make_book()
        assert a != b
