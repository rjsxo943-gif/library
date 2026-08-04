"""Book 객체 목록을 UTF-8 CSV 파일로 저장하고 불러오는 모듈."""

from __future__ import annotations

import csv
import warnings
from datetime import date
from pathlib import Path
from typing import Iterable

from models import Book


CSV_FIELDNAMES: tuple[str, ...] = (
    "book_id",
    "title",
    "author",
    "publisher",
    "year",
    "is_borrowed",
    "borrower",
    "borrowed_date",
)


class StorageError(Exception):
    """CSV 파일 전체를 정상적으로 처리할 수 없을 때 발생하는 예외."""


def save_books(books: Iterable[Book], file_path: str | Path) -> int:
    """
    도서 목록 전체를 UTF-8 CSV 파일에 저장한다.

    저장 중 오류가 발생하면 기존 파일이 손상되지 않도록 임시 파일에
    먼저 기록한 뒤 정상 완료된 경우에만 실제 파일로 교체한다.

    Returns:
        저장한 도서 수

    Raises:
        StorageError: 디렉터리 생성 또는 파일 저장에 실패한 경우
    """

    path = Path(file_path)
    temporary_path = path.with_name(f"{path.name}.tmp")
    book_list = list(books)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with temporary_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=CSV_FIELDNAMES,
                extrasaction="raise",
            )
            writer.writeheader()

            for book in book_list:
                writer.writerow(book.to_dict())

        temporary_path.replace(path)

    except (OSError, csv.Error, ValueError, TypeError) as exc:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise StorageError(
            f"도서 데이터를 '{path}' 파일에 저장하지 못했습니다."
        ) from exc

    return len(book_list)


def load_books(file_path: str | Path) -> list[Book]:
    """
    UTF-8 CSV 파일에서 정상적인 도서 행만 불러온다.

    파일이 없거나 비어 있으면 빈 목록을 반환한다. 일부 행이 손상된
    경우 해당 행만 건너뛰고 RuntimeWarning을 발생시킨다.

    Raises:
        StorageError: 파일을 읽을 수 없거나 CSV 헤더가 다른 경우
    """

    path = Path(file_path)

    if not path.exists() or path.stat().st_size == 0:
        return []

    try:
        with path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                return []

            _validate_header(reader.fieldnames, path)

            books: list[Book] = []
            loaded_ids: set[str] = set()

            for line_number, row in enumerate(reader, start=2):
                try:
                    book = _book_from_row(row)
                    normalized_id = book.book_id.casefold()

                    if normalized_id in loaded_ids:
                        raise ValueError("중복된 도서 번호입니다.")

                    loaded_ids.add(normalized_id)
                    books.append(book)

                except (KeyError, TypeError, ValueError) as exc:
                    warnings.warn(
                        f"{line_number}행을 불러오지 못해 건너뜁니다: {exc}",
                        RuntimeWarning,
                        stacklevel=2,
                    )

            return books

    except StorageError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise StorageError(
            f"도서 데이터 파일 '{path}'을(를) 읽지 못했습니다."
        ) from exc


def _validate_header(fieldnames: list[str], path: Path) -> None:
    """CSV 헤더가 공통 데이터 규격과 정확히 일치하는지 검사한다."""

    if tuple(fieldnames) != CSV_FIELDNAMES:
        expected = ",".join(CSV_FIELDNAMES)
        raise StorageError(
            f"CSV 헤더가 올바르지 않습니다: '{path}'. "
            f"필요한 헤더: {expected}"
        )


def _book_from_row(row: dict[str, str | None]) -> Book:
    """CSV 한 행을 검증하고 Book 객체로 변환한다."""

    book_id = _required_text(row, "book_id")
    title = _required_text(row, "title")
    author = _required_text(row, "author")
    publisher = _required_text(row, "publisher")

    year_text = _required_text(row, "year")

    try:
        year = int(year_text)
    except ValueError as exc:
        raise ValueError("출판 연도는 정수여야 합니다.") from exc

    if not 1000 <= year <= date.today().year:
        raise ValueError(
            f"출판 연도는 1000년부터 {date.today().year}년 사이여야 합니다."
        )

    borrowed_text = _required_text(row, "is_borrowed").casefold()

    if borrowed_text == "true":
        is_borrowed = True
    elif borrowed_text == "false":
        is_borrowed = False
    else:
        raise ValueError("대출 상태는 true 또는 false여야 합니다.")

    borrower = (row.get("borrower") or "").strip()
    borrowed_date = (row.get("borrowed_date") or "").strip()

    return Book(
        book_id=book_id,
        title=title,
        author=author,
        publisher=publisher,
        year=year,
        is_borrowed=is_borrowed,
        borrower=borrower,
        borrowed_date=borrowed_date,
    )


def _required_text(row: dict[str, str | None], field_name: str) -> str:
    """필수 CSV 필드를 공백 제거 후 반환한다."""

    value = row.get(field_name)

    if value is None or not value.strip():
        raise ValueError(f"{field_name} 필드는 비워둘 수 없습니다.")

    return value.strip()
