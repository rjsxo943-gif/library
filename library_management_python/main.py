"""도서관리 시스템 Python 콘솔 애플리케이션."""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path
from typing import Iterable

from library import Library, OperationResult
from models import Book
from storage import StorageError, load_books, save_books
from utils import (
    get_current_date,
    get_integer_input,
    get_non_empty_input,
    get_publication_year_input,
    get_yes_no_input,
    normalize_book_id,
)


def get_default_books_file() -> Path:
    """실행 형태에 맞는 기본 books.csv 경로를 반환한다."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().with_name("books.csv")

    return Path(__file__).resolve().with_name("books.csv")


BOOKS_FILE = get_default_books_file()


def print_main_menu() -> None:
    """메인 메뉴를 출력한다."""

    print("\n" + "=" * 40)
    print("           도서관리 시스템")
    print("=" * 40)
    print("1. 도서 등록")
    print("2. 전체 도서 조회")
    print("3. 도서 검색")
    print("4. 도서 대출")
    print("5. 도서 반납")
    print("6. 도서 삭제")
    print("7. 파일 저장")
    print("0. 프로그램 종료")
    print("=" * 40)


def load_library(file_path: str | Path) -> Library:
    """CSV에서 도서를 불러와 Library 객체를 생성한다."""

    library = Library()

    for book in load_books(file_path):
        library.add_book(book)

    return library


def save_library(library: Library, file_path: str | Path) -> bool:
    """현재 도서 목록을 저장하고 성공 여부를 반환한다."""

    try:
        saved_count = save_books(library.list_books(), file_path)
    except StorageError as exc:
        print(f"저장 오류: {exc}")
        return False

    print(f"도서 데이터 {saved_count}권을 저장했습니다.")
    return True


def register_book(library: Library, file_path: str | Path) -> None:
    """사용자 입력을 받아 새 도서를 등록하고 자동 저장한다."""

    print("\n[도서 등록]")
    book_id = normalize_book_id(get_non_empty_input("도서 번호: ", "도서 번호"))

    if library.is_duplicate_id(book_id):
        print("오류: 이미 등록된 도서 번호입니다.")
        return

    title = get_non_empty_input("제목: ", "제목")
    author = get_non_empty_input("저자: ", "저자")
    publisher = get_non_empty_input("출판사: ", "출판사")
    year = get_publication_year_input()

    book = Book(
        book_id=book_id,
        title=title,
        author=author,
        publisher=publisher,
        year=year,
    )

    if not library.add_book(book):
        print("오류: 도서를 등록하지 못했습니다.")
        return

    print("도서가 정상적으로 등록되었습니다.")
    print_book_details(book)
    save_library(library, file_path)


def print_book_details(book: Book) -> None:
    """도서 한 권의 상세 정보를 출력한다."""

    print(f"도서 번호: {book.book_id}")
    print(f"제목: {book.title}")
    print(f"저자: {book.author}")
    print(f"출판사: {book.publisher}")
    print(f"출판 연도: {book.year}")
    print(f"대출 상태: {'대출 중' if book.is_borrowed else '대출 가능'}")
    print(f"대출자: {book.borrower or '-'}")
    print(f"대출일: {book.borrowed_date or '-'}")


def display_books(books: Iterable[Book]) -> None:
    """도서 목록을 한글 폭을 고려한 표 형태로 출력한다."""

    book_list = list(books)

    if not book_list:
        print("등록된 도서가 없습니다.")
        return

    columns = (
        ("도서번호", 10),
        ("제목", 28),
        ("저자", 14),
        ("출판사", 16),
        ("연도", 6),
        ("상태", 10),
        ("대출자", 12),
        ("대출일", 12),
    )
    separator = "-+-".join("-" * width for _, width in columns)
    header = " | ".join(_fit_cell(title, width) for title, width in columns)

    print(separator)
    print(header)
    print(separator)

    for book in book_list:
        values = (
            book.book_id,
            book.title,
            book.author,
            book.publisher,
            str(book.year),
            "대출 중" if book.is_borrowed else "대출 가능",
            book.borrower or "-",
            book.borrowed_date or "-",
        )
        print(
            " | ".join(
                _fit_cell(value, width)
                for value, (_, width) in zip(values, columns, strict=True)
            )
        )

    print(separator)
    print(f"총 도서 수: {len(book_list)}권")


def search_books(library: Library) -> None:
    """검색 하위 메뉴를 반복 실행한다."""

    while True:
        print("\n[도서 검색]")
        print("1. 도서 번호로 검색")
        print("2. 제목으로 검색")
        print("3. 저자로 검색")
        print("0. 이전 메뉴")

        choice = get_integer_input("검색 방법을 선택하세요: ", 0, 3)

        if choice == 0:
            return

        keyword = get_non_empty_input("검색어: ", "검색어")

        if choice == 1:
            book = library.find_book_by_id(keyword)
            results = [book] if book is not None else []
        elif choice == 2:
            results = library.search_by_title(keyword)
        else:
            results = library.search_by_author(keyword)

        if not results:
            print("검색 조건에 해당하는 도서가 없습니다.")
        else:
            display_books(results)


def borrow_book(library: Library, file_path: str | Path) -> None:
    """도서를 대출 처리하고 성공 시 자동 저장한다."""

    print("\n[도서 대출]")
    book_id = get_non_empty_input("대출할 도서 번호: ", "도서 번호")
    book = library.find_book_by_id(book_id)

    if book is None:
        print("오류: 해당 도서 번호의 도서를 찾을 수 없습니다.")
        return

    if book.is_borrowed:
        print("오류: 이미 대출 중인 도서입니다.")
        print(f"현재 대출자: {book.borrower}")
        print(f"대출일: {book.borrowed_date}")
        return

    borrower = get_non_empty_input("대출자 이름: ", "대출자 이름")
    result = library.borrow_book(book_id, borrower, get_current_date())
    print_operation_result(result)

    if result.success:
        save_library(library, file_path)


def return_book(library: Library, file_path: str | Path) -> None:
    """도서를 반납 처리하고 성공 시 자동 저장한다."""

    print("\n[도서 반납]")
    book_id = get_non_empty_input("반납할 도서 번호: ", "도서 번호")
    result = library.return_book(book_id)
    print_operation_result(result)

    if result.success:
        save_library(library, file_path)


def delete_book(library: Library, file_path: str | Path) -> None:
    """삭제 대상을 확인받은 뒤 도서를 삭제하고 자동 저장한다."""

    print("\n[도서 삭제]")
    book_id = get_non_empty_input("삭제할 도서 번호: ", "도서 번호")
    book = library.find_book_by_id(book_id)

    if book is None:
        print("오류: 해당 도서 번호의 도서를 찾을 수 없습니다.")
        return

    if book.is_borrowed:
        print("오류: 대출 중인 도서는 삭제할 수 없습니다.")
        return

    print("\n다음 도서를 삭제하시겠습니까?")
    print_book_details(book)

    if not get_yes_no_input("삭제하시겠습니까? (Y/N): "):
        print("도서 삭제를 취소했습니다.")
        return

    result = library.delete_book(book_id)
    print_operation_result(result)

    if result.success:
        save_library(library, file_path)


def print_operation_result(result: OperationResult) -> None:
    """Library 작업 결과를 사용자 메시지로 출력한다."""

    prefix = "완료" if result.success else "오류"
    print(f"{prefix}: {result.message}")

    if result.success and result.book is not None:
        print_book_details(result.book)


def run_menu(library: Library, file_path: str | Path) -> int:
    """사용자가 종료할 때까지 메인 메뉴를 반복한다."""

    handlers = {
        1: lambda: register_book(library, file_path),
        2: lambda: display_books(library.list_books()),
        3: lambda: search_books(library),
        4: lambda: borrow_book(library, file_path),
        5: lambda: return_book(library, file_path),
        6: lambda: delete_book(library, file_path),
        7: lambda: save_library(library, file_path),
    }

    try:
        while True:
            print_main_menu()
            choice = get_integer_input("메뉴를 선택하세요: ", 0, 7)

            if choice == 0:
                print("프로그램을 종료합니다.")
                break

            handlers[choice]()

    except (KeyboardInterrupt, EOFError):
        print("\n입력이 중단되어 프로그램을 종료합니다.")

    return 0 if save_library(library, file_path) else 1


def main(file_path: str | Path | None = None) -> int:
    """도서 데이터를 불러온 뒤 콘솔 프로그램을 실행한다."""

    target_file = Path(file_path) if file_path is not None else BOOKS_FILE

    try:
        library = load_library(target_file)
    except StorageError as exc:
        print(f"불러오기 오류: {exc}")
        print("기존 파일을 보호하기 위해 프로그램을 종료합니다.")
        return 1

    print(f"도서 데이터 {len(library.list_books())}권을 불러왔습니다.")
    return run_menu(library, target_file)


def _display_width(text: str) -> int:
    """한글·전각 문자를 고려한 터미널 표시 폭을 계산한다."""

    return sum(
        2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1
        for character in text
    )


def _fit_cell(value: object, width: int) -> str:
    """문자열을 열 너비에 맞게 자르거나 공백으로 채운다."""

    text = str(value)

    if _display_width(text) > width:
        available_width = max(width - 1, 0)
        shortened = ""

        for character in text:
            candidate = shortened + character
            if _display_width(candidate) > available_width:
                break
            shortened = candidate

        text = shortened + "…"

    return text + " " * (width - _display_width(text))


if __name__ == "__main__":
    raise SystemExit(main())
