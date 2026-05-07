"""
Unit tests for the BookStatus value object.
"""

from src.domain.value_objects.book_status import BookStatus


class TestBookStatusTransitions:
    def test_unread_can_go_to_reading(self) -> None:
        assert BookStatus.UNREAD.can_transition_to(BookStatus.READING) is True

    def test_unread_cannot_go_to_read(self) -> None:
        assert BookStatus.UNREAD.can_transition_to(BookStatus.READ) is False

    def test_reading_can_go_to_read(self) -> None:
        assert BookStatus.READING.can_transition_to(BookStatus.READ) is True

    def test_reading_can_go_back_to_unread(self) -> None:
        assert BookStatus.READING.can_transition_to(BookStatus.UNREAD) is True

    def test_read_has_no_transitions(self) -> None:
        assert BookStatus.READ.can_transition_to(BookStatus.UNREAD) is False
        assert BookStatus.READ.can_transition_to(BookStatus.READING) is False


class TestBookStatusValues:
    def test_string_values(self) -> None:
        assert BookStatus.UNREAD.value == "unread"
        assert BookStatus.READING.value == "reading"
        assert BookStatus.READ.value == "read"

    def test_from_string(self) -> None:
        assert BookStatus("reading") == BookStatus.READING
