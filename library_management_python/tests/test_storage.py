"""CSV 저장 및 불러오기 기능을 검증하는 테스트."""

import csv

import pytest

from models import Book
from storage import CSV_FIELDNAMES, StorageError, load_books, save_books


def make_books() -> list[Book]:
    """저장·불러오기 테스트용 도서 목록을 생성한다."""

    available_book = Book(
        book_id="B0001",
        title="파이썬, 제대로 배우기",
        author="김철수",
        publisher="전자출판사",
        year=2025,
    )
    borrowed_book = Book(
        book_id="B0002",
        title="C++ Programming",
        author="홍길동",
        publisher="한빛출판사",
        year=2024,
        is_borrowed=True,
        borrower="김건태",
        borrowed_date="2026-08-04",
    )
    return [available_book, borrowed_book]


def test_save_books_writes_utf8_csv_with_fixed_header(tmp_path) -> None:
    """공통 헤더와 UTF-8 한글 데이터가 CSV 파일에 저장되어야 한다."""

    file_path = tmp_path / "books.csv"

    saved_count = save_books(make_books(), file_path)

    assert saved_count == 2

    with file_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.reader(csv_file))

    assert tuple(rows[0]) == CSV_FIELDNAMES
    assert rows[1][1] == "파이썬, 제대로 배우기"
    assert rows[2][5:] == ["true", "김건태", "2026-08-04"]


def test_save_books_creates_parent_directory(tmp_path) -> None:
    """저장 폴더가 없으면 자동으로 생성해야 한다."""

    file_path = tmp_path / "data" / "demo" / "books.csv"

    save_books(make_books(), file_path)

    assert file_path.exists()


def test_saved_books_can_be_loaded_without_data_loss(tmp_path) -> None:
    """한글, 쉼표, 대출 상태를 포함한 모든 필드가 복원되어야 한다."""

    books = make_books()
    file_path = tmp_path / "books.csv"
    save_books(books, file_path)

    loaded_books = load_books(file_path)

    assert loaded_books == books
    assert loaded_books[0] is not books[0]


def test_missing_file_returns_empty_list(tmp_path) -> None:
    """CSV 파일이 없어도 오류 없이 빈 목록으로 시작해야 한다."""

    assert load_books(tmp_path / "missing.csv") == []


def test_empty_file_returns_empty_list(tmp_path) -> None:
    """빈 CSV 파일은 빈 도서 목록으로 처리해야 한다."""

    file_path = tmp_path / "books.csv"
    file_path.write_text("", encoding="utf-8")

    assert load_books(file_path) == []


def test_damaged_rows_are_skipped_while_valid_rows_are_loaded(tmp_path) -> None:
    """일부 행이 손상되어도 정상 행은 계속 불러와야 한다."""

    file_path = tmp_path / "books.csv"
    file_path.write_text(
        "\n".join(
            [
                ",".join(CSV_FIELDNAMES),
                "B0001,정상 도서,김철수,전자출판사,2025,false,,",
                "B0002,잘못된 연도,홍길동,한빛출판사,not-year,false,,",
                "B0003,잘못된 대출 상태,박영희,미래출판사,2024,yes,,",
                "B0004,정상 대출 도서,이민수,기술출판사,2023,true,김건태,2026-08-04",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.warns(RuntimeWarning) as warning_records:
        loaded_books = load_books(file_path)

    assert [book.book_id for book in loaded_books] == ["B0001", "B0004"]
    assert len(warning_records) == 2


def test_duplicate_book_ids_are_skipped_case_insensitively(tmp_path) -> None:
    """CSV 내부의 중복 ID는 첫 번째 도서만 유지해야 한다."""

    file_path = tmp_path / "books.csv"
    file_path.write_text(
        "\n".join(
            [
                ",".join(CSV_FIELDNAMES),
                "B0001,첫 번째 도서,김철수,전자출판사,2025,false,,",
                "b0001,중복 도서,홍길동,한빛출판사,2024,false,,",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.warns(RuntimeWarning, match="중복된 도서 번호"):
        loaded_books = load_books(file_path)

    assert [book.title for book in loaded_books] == ["첫 번째 도서"]


def test_invalid_header_raises_storage_error(tmp_path) -> None:
    """공통 CSV 헤더가 아닌 파일은 명확한 오류로 거부해야 한다."""

    file_path = tmp_path / "books.csv"
    file_path.write_text("id,name\nB0001,Python", encoding="utf-8")

    with pytest.raises(StorageError, match="CSV 헤더가 올바르지 않습니다"):
        load_books(file_path)
