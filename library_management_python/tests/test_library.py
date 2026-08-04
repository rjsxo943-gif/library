"""Library 기본 등록 및 조회 기능을 검증하는 테스트."""

from library import Library
from models import Book


def make_book(book_id: str = "B0001", title: str = "Python 기초") -> Book:
    """테스트에서 반복해서 사용할 Book 객체를 생성한다."""

    return Book(
        book_id=book_id,
        title=title,
        author="김철수",
        publisher="전자출판사",
        year=2025,
    )


def test_new_library_has_empty_book_list() -> None:
    """새 Library의 도서 목록은 비어 있어야 한다."""

    library = Library()

    assert library.list_books() == []


def test_book_can_be_added() -> None:
    """새로운 도서를 정상적으로 등록할 수 있어야 한다."""

    library = Library()
    book = make_book()

    result = library.add_book(book)

    assert result is True
    assert library.list_books() == [book]


def test_books_are_listed_in_registration_order() -> None:
    """전체 조회 결과는 도서가 등록된 순서를 유지해야 한다."""

    library = Library()
    first_book = make_book("B0001", "Python 기초")
    second_book = make_book("B0002", "C++ 기초")

    library.add_book(first_book)
    library.add_book(second_book)

    assert library.list_books() == [first_book, second_book]


def test_duplicate_book_id_is_rejected_case_insensitively() -> None:
    """공백과 영문 대소문자만 다른 중복 도서 번호는 거부해야 한다."""

    library = Library()
    original_book = make_book("B0001")
    duplicate_book = make_book("  b0001  ", "중복 도서")

    assert library.add_book(original_book) is True
    assert library.add_book(duplicate_book) is False
    assert library.list_books() == [original_book]


def test_book_id_is_trimmed_when_added() -> None:
    """등록된 도서 번호의 앞뒤 공백은 제거되어야 한다."""

    library = Library()
    book = make_book("  B0001  ")

    library.add_book(book)

    assert book.book_id == "B0001"


def test_book_can_be_found_by_id_case_insensitively() -> None:
    """ID 검색은 앞뒤 공백과 영문 대소문자를 무시해야 한다."""

    library = Library()
    book = make_book("B0001")
    library.add_book(book)

    result = library.find_book_by_id("  b0001  ")

    assert result is book


def test_find_book_by_unknown_id_returns_none() -> None:
    """존재하지 않는 도서 번호를 검색하면 None을 반환해야 한다."""

    library = Library()
    library.add_book(make_book())

    assert library.find_book_by_id("B9999") is None


def test_empty_book_id_is_rejected() -> None:
    """빈 도서 번호는 등록되지 않아야 한다."""

    library = Library()

    assert library.add_book(make_book("   ")) is False
    assert library.list_books() == []


def test_list_books_returns_a_new_list() -> None:
    """조회 결과 목록을 수정해도 Library 내부 목록은 유지되어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)

    result = library.list_books()
    result.clear()

    assert library.list_books() == [book]
