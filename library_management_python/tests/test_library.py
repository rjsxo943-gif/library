"""Library의 등록·조회·검색·대출·반납 기능을 검증하는 테스트."""

from library import Library
from models import Book


def make_book(
    book_id: str = "B0001",
    title: str = "Python 기초",
    author: str = "김철수",
) -> Book:
    """테스트에서 반복해서 사용할 Book 객체를 생성한다."""

    return Book(
        book_id=book_id,
        title=title,
        author=author,
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


def test_search_by_title_finds_partial_matches_in_registration_order() -> None:
    """제목 일부가 일치하는 모든 도서를 등록 순서대로 반환해야 한다."""

    library = Library()
    first_match = make_book("B0001", "Python 기초")
    second_match = make_book("B0002", "실전 Python")
    non_match = make_book("B0003", "C++ 기초")

    for book in (first_match, second_match, non_match):
        library.add_book(book)

    assert library.search_by_title("Python") == [first_match, second_match]


def test_search_by_title_ignores_case_and_surrounding_spaces() -> None:
    """영문 제목 검색은 검색어의 대소문자와 앞뒤 공백을 무시해야 한다."""

    library = Library()
    book = make_book("B0001", "Clean Code with Python")
    library.add_book(book)

    assert library.search_by_title("  pYtHoN  ") == [book]


def test_search_by_author_finds_partial_korean_name() -> None:
    """저자 이름 일부로 여러 도서를 검색할 수 있어야 한다."""

    library = Library()
    first_match = make_book("B0001", "Python 기초", "김철수")
    second_match = make_book("B0002", "C++ 기초", "김영희")
    non_match = make_book("B0003", "전자공학 개론", "박민수")

    for book in (first_match, second_match, non_match):
        library.add_book(book)

    assert library.search_by_author("김") == [first_match, second_match]


def test_search_by_author_ignores_english_case() -> None:
    """영문 저자 검색은 대소문자를 구분하지 않아야 한다."""

    library = Library()
    book = make_book("B0001", "Python Cookbook", "David Beazley")
    library.add_book(book)

    assert library.search_by_author("BEAZ") == [book]


def test_search_returns_empty_list_when_no_book_matches() -> None:
    """검색 조건에 맞는 도서가 없으면 빈 목록을 반환해야 한다."""

    library = Library()
    library.add_book(make_book())

    assert library.search_by_title("Java") == []
    assert library.search_by_author("홍길동") == []


def test_empty_search_keyword_returns_empty_list() -> None:
    """빈 문자열이나 공백만 있는 검색어는 검색 결과를 만들지 않아야 한다."""

    library = Library()
    library.add_book(make_book())

    assert library.search_by_title("") == []
    assert library.search_by_title("   ") == []
    assert library.search_by_author("") == []
    assert library.search_by_author("   ") == []


def test_book_can_be_borrowed_by_id() -> None:
    """도서 번호로 정상 대출하면 도서 상태와 대출 정보가 변경되어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)

    result = library.borrow_book("  b0001  ", " 김건태 ", " 2026-08-04 ")

    assert result.success is True
    assert result.code == "borrowed"
    assert result.message == "도서 대출이 완료되었습니다."
    assert result.book is book
    assert book.is_borrowed is True
    assert book.borrower == "김건태"
    assert book.borrowed_date == "2026-08-04"


def test_borrow_unknown_book_returns_book_not_found() -> None:
    """존재하지 않는 도서의 대출 요청은 실패해야 한다."""

    library = Library()

    result = library.borrow_book("B9999", "김건태", "2026-08-04")

    assert result.success is False
    assert result.code == "book_not_found"
    assert result.book is None


def test_already_borrowed_book_cannot_be_borrowed_again() -> None:
    """이미 대출 중인 도서는 다시 대출할 수 없어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)
    library.borrow_book("B0001", "김건태", "2026-08-04")

    result = library.borrow_book("B0001", "홍길동", "2026-08-05")

    assert result.success is False
    assert result.code == "already_borrowed"
    assert result.book is book
    assert book.borrower == "김건태"
    assert book.borrowed_date == "2026-08-04"


def test_empty_borrower_is_rejected_without_changing_book() -> None:
    """빈 대출자 이름은 거부되고 도서 상태도 유지되어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)

    result = library.borrow_book("B0001", "   ", "2026-08-04")

    assert result.success is False
    assert result.code == "invalid_borrower"
    assert book.is_available() is True


def test_empty_borrowed_date_is_rejected_without_changing_book() -> None:
    """빈 대출일은 거부되고 도서 상태도 유지되어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)

    result = library.borrow_book("B0001", "김건태", "   ")

    assert result.success is False
    assert result.code == "invalid_borrowed_date"
    assert book.is_available() is True


def test_borrowed_book_can_be_returned_by_id() -> None:
    """대출 중인 도서를 반납하면 대출 정보가 초기화되어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)
    library.borrow_book("B0001", "김건태", "2026-08-04")

    result = library.return_book("  b0001  ")

    assert result.success is True
    assert result.code == "returned"
    assert result.message == "도서 반납이 완료되었습니다."
    assert result.book is book
    assert book.is_available() is True
    assert book.borrower == ""
    assert book.borrowed_date == ""


def test_return_unknown_book_returns_book_not_found() -> None:
    """존재하지 않는 도서의 반납 요청은 실패해야 한다."""

    library = Library()

    result = library.return_book("B9999")

    assert result.success is False
    assert result.code == "book_not_found"
    assert result.book is None


def test_available_book_cannot_be_returned() -> None:
    """대출되지 않은 도서는 반납할 수 없어야 한다."""

    library = Library()
    book = make_book()
    library.add_book(book)

    result = library.return_book("B0001")

    assert result.success is False
    assert result.code == "not_borrowed"
    assert result.book is book
    assert book.is_available() is True
