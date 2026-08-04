"""Book 모델의 동작을 검증하는 테스트."""

import pytest

from models import Book


def test_new_book_has_default_available_state() -> None:
    """새 도서는 기본적으로 대출 가능한 상태여야 한다."""

    book = Book(
        book_id="B0001",
        title="Python 기초",
        author="김철수",
        publisher="전자출판사",
        year=2025,
    )

    assert book.is_borrowed is False
    assert book.is_available() is True
    assert book.borrower == ""
    assert book.borrowed_date == ""


def test_book_can_be_borrowed() -> None:
    """대출 처리 후 대출 상태와 대출 정보가 저장되어야 한다."""

    book = Book(
        book_id="B0001",
        title="Python 기초",
        author="김철수",
        publisher="전자출판사",
        year=2025,
    )

    book.borrow(" 김건태 ", " 2026-08-04 ")

    assert book.is_borrowed is True
    assert book.is_available() is False
    assert book.borrower == "김건태"
    assert book.borrowed_date == "2026-08-04"


def test_borrowed_book_can_be_returned() -> None:
    """반납 처리 후 대출 정보가 초기화되어야 한다."""

    book = Book(
        book_id="B0001",
        title="Python 기초",
        author="김철수",
        publisher="전자출판사",
        year=2025,
    )

    book.borrow("김건태", "2026-08-04")
    book.return_book()

    assert book.is_borrowed is False
    assert book.is_available() is True
    assert book.borrower == ""
    assert book.borrowed_date == ""


def test_book_can_be_converted_to_dict() -> None:
    """도서 정보가 CSV 저장용 딕셔너리로 변환되어야 한다."""

    book = Book(
        book_id="B0001",
        title="Python 기초",
        author="김철수",
        publisher="전자출판사",
        year=2025,
    )

    result = book.to_dict()

    assert result == {
        "book_id": "B0001",
        "title": "Python 기초",
        "author": "김철수",
        "publisher": "전자출판사",
        "year": 2025,
        "is_borrowed": "false",
        "borrower": "",
        "borrowed_date": "",
    }


def test_book_cannot_be_borrowed_twice() -> None:
    """이미 대출 중인 도서를 다시 대출하면 오류가 발생해야 한다."""

    book = Book(
        book_id="B0001",
        title="Python 기초",
        author="김철수",
        publisher="전자출판사",
        year=2025,
    )

    book.borrow("김건태", "2026-08-04")

    with pytest.raises(ValueError, match="이미 대출 중인 도서입니다."):
        book.borrow("홍길동", "2026-08-05")


def test_invalid_borrow_state_is_rejected() -> None:
    """대출 중인데 대출자 정보가 없으면 객체 생성이 거부되어야 한다."""

    with pytest.raises(
        ValueError,
        match="대출 중인 도서에는 대출자와 대출일이 필요합니다.",
    ):
        Book(
            book_id="B0001",
            title="Python 기초",
            author="김철수",
            publisher="전자출판사",
            year=2025,
            is_borrowed=True,
            borrower="",
            borrowed_date="",
        )
