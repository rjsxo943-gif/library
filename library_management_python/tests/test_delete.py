"""Library의 안전한 도서 삭제 기능을 검증하는 테스트."""

from library import Library
from models import Book


def make_book(
    book_id: str = "B0001",
    title: str = "Python 기초",
) -> Book:
    """삭제 테스트에 사용할 Book 객체를 생성한다."""

    return Book(
        book_id=book_id,
        title=title,
        author="김철수",
        publisher="전자출판사",
        year=2025,
    )


def test_book_can_be_deleted_by_id() -> None:
    """대출 가능한 도서는 ID로 삭제할 수 있어야 한다."""

    library = Library()
    first_book = make_book("B0001")
    second_book = make_book("B0002", "C++ 기초")
    library.add_book(first_book)
    library.add_book(second_book)

    result = library.delete_book("  b0001  ")

    assert result.success is True
    assert result.code == "deleted"
    assert result.message == "도서 삭제가 완료되었습니다."
    assert result.book is first_book
    assert library.list_books() == [second_book]
    assert library.find_book_by_id("B0001") is None


def test_delete_unknown_book_returns_book_not_found() -> None:
    """존재하지 않는 도서를 삭제하면 기존 목록이 유지되어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)

    result = library.delete_book("B9999")

    assert result.success is False
    assert result.code == "book_not_found"
    assert result.book is None
    assert library.list_books() == [book]


def test_borrowed_book_cannot_be_deleted() -> None:
    """대출 중인 도서는 삭제할 수 없어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)
    library.borrow_book("B0001", "김건태", "2026-08-04")

    result = library.delete_book("B0001")

    assert result.success is False
    assert result.code == "book_is_borrowed"
    assert result.message == "대출 중인 도서는 삭제할 수 없습니다."
    assert result.book is book
    assert library.list_books() == [book]


def test_returned_book_can_be_deleted() -> None:
    """대출 도서를 반납한 뒤에는 삭제할 수 있어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)
    library.borrow_book("B0001", "김건태", "2026-08-04")
    library.return_book("B0001")

    result = library.delete_book("B0001")

    assert result.success is True
    assert result.code == "deleted"
    assert library.list_books() == []
