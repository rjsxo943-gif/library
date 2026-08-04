"""GUI에서 사용하는 검색·표시·저장 보조 기능을 검증한다."""

from gui_app import book_to_row, load_library, save_library, search_catalog
from library import Library
from models import Book


def make_library() -> Library:
    """GUI 테스트에 사용할 도서관 데이터를 생성한다."""

    library = Library()
    library.add_book(
        Book(
            "B0001",
            "파이썬 기초 입문",
            "김 철 수",
            "한빛출판사",
            2025,
        )
    )
    library.add_book(
        Book(
            "B0002",
            "C++ 프로그래밍",
            "홍길동",
            "전자출판사",
            2024,
            True,
            "김건태",
            "2026-08-04",
        )
    )
    library.add_book(
        Book(
            "B0003",
            "데이터 구조",
            "박영희",
            "미래출판사",
            2023,
        )
    )
    return library


def test_blank_search_returns_all_books() -> None:
    """검색어가 비어 있으면 전체 도서를 표시해야 한다."""

    library = make_library()

    assert search_catalog(library) == library.list_books()


def test_all_search_combines_id_title_and_author_matches() -> None:
    """통합검색은 번호·제목·저자를 모두 검색해야 한다."""

    library = make_library()

    assert [book.book_id for book in search_catalog(library, "파이썬", "전체")] == [
        "B0001"
    ]
    assert [book.book_id for book in search_catalog(library, "홍길동", "전체")] == [
        "B0002"
    ]
    assert [book.book_id for book in search_catalog(library, "b0003", "전체")] == [
        "B0003"
    ]


def test_title_and_author_search_ignore_whitespace() -> None:
    """GUI 검색도 Library의 띄어쓰기 무시 규칙을 사용해야 한다."""

    library = make_library()

    assert [
        book.book_id for book in search_catalog(library, "파이 썬기초", "제목")
    ] == ["B0001"]
    assert [book.book_id for book in search_catalog(library, "김철수", "저자")] == [
        "B0001"
    ]


def test_status_filter_is_applied_after_search() -> None:
    """대출 상태 필터가 검색 결과에 적용되어야 한다."""

    library = make_library()

    assert [
        book.book_id
        for book in search_catalog(library, status_filter="대출 가능")
    ] == ["B0001", "B0003"]
    assert [
        book.book_id for book in search_catalog(library, status_filter="대출 중")
    ] == ["B0002"]


def test_book_to_row_formats_status_and_empty_loan_fields() -> None:
    """GUI 표에 표시할 상태와 빈 대출 정보가 올바르게 변환되어야 한다."""

    row = book_to_row(Book("B0001", "Python", "Kim", "Publisher", 2025))

    assert row == (
        "B0001",
        "Python",
        "Kim",
        "Publisher",
        "2025",
        "대출 가능",
        "-",
        "-",
    )


def test_gui_storage_helpers_preserve_existing_library_data(tmp_path) -> None:
    """GUI 저장·불러오기 보조 함수가 기존 CSV 규격을 유지해야 한다."""

    file_path = tmp_path / "books.csv"
    original = make_library()

    assert save_library(original, file_path) == 3
    loaded = load_library(file_path)

    assert loaded.list_books() == original.list_books()
