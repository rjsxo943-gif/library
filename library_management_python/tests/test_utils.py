"""입력 검증과 날짜 보조 기능을 검증하는 테스트."""

from datetime import date

import pytest

from utils import (
    get_current_date,
    get_integer_input,
    get_non_empty_input,
    get_publication_year_input,
    get_yes_no_input,
    normalize_book_id,
    validate_integer,
    validate_non_empty,
    validate_publication_year,
)


def test_normalize_book_id_trims_and_uppercases() -> None:
    """도서 번호는 공백 제거 후 영문 대문자로 통일되어야 한다."""

    assert normalize_book_id("  b0001  ") == "B0001"


def test_validate_non_empty_returns_trimmed_text() -> None:
    """정상 문자열은 앞뒤 공백이 제거되어 반환되어야 한다."""

    assert validate_non_empty("  Python 기초  ", "제목") == "Python 기초"


def test_validate_non_empty_rejects_blank_text() -> None:
    """공백만 있는 문자열은 명확한 오류로 거부되어야 한다."""

    with pytest.raises(ValueError, match=r"제목은\(는\) 비워둘 수 없습니다"):
        validate_non_empty("   ", "제목")


def test_validate_integer_converts_and_checks_range() -> None:
    """정수 문자열을 변환하고 허용 범위를 검사해야 한다."""

    assert validate_integer(" 3 ", min_value=1, max_value=7) == 3

    with pytest.raises(ValueError, match="1 이상의 값"):
        validate_integer("0", min_value=1, max_value=7)

    with pytest.raises(ValueError, match="7 이하의 값"):
        validate_integer("8", min_value=1, max_value=7)


def test_validate_integer_rejects_non_integer() -> None:
    """문자 입력은 정수 변환 오류로 처리되어야 한다."""

    with pytest.raises(ValueError, match="정수로 입력해야 합니다"):
        validate_integer("abc")


def test_validate_publication_year_uses_current_year_limit() -> None:
    """출판 연도는 1000년부터 지정한 현재 연도까지 허용해야 한다."""

    assert validate_publication_year("2025", current_year=2026) == 2025

    with pytest.raises(ValueError, match="2026 이하의 값"):
        validate_publication_year("2027", current_year=2026)


def test_get_current_date_returns_iso_format() -> None:
    """날짜는 YYYY-MM-DD 형식으로 반환되어야 한다."""

    assert get_current_date(date(2026, 8, 4)) == "2026-08-04"


def test_get_non_empty_input_retries_until_valid(monkeypatch, capsys) -> None:
    """빈 문자열 다음에 정상 문자열이 입력되면 재입력 후 반환해야 한다."""

    answers = iter(["   ", " 김건태 "])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = get_non_empty_input("대출자: ", "대출자 이름")

    assert result == "김건태"
    assert "비워둘 수 없습니다" in capsys.readouterr().out


def test_get_integer_input_retries_invalid_and_out_of_range(
    monkeypatch,
    capsys,
) -> None:
    """문자와 범위 밖 숫자 뒤 정상 숫자를 입력하면 정상 반환해야 한다."""

    answers = iter(["abc", "0", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = get_integer_input("메뉴: ", min_value=1, max_value=7)

    assert result == 4
    output = capsys.readouterr().out
    assert "정수로 입력해야 합니다" in output
    assert "1 이상의 값을 입력해야 합니다" in output


def test_get_publication_year_input_retries_future_year(
    monkeypatch,
    capsys,
) -> None:
    """미래 연도 입력 뒤 유효한 연도를 입력하면 정상 반환해야 한다."""

    current_year = date.today().year
    answers = iter([str(current_year + 1), str(current_year)])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = get_publication_year_input()

    assert result == current_year
    assert "이하의 값을 입력해야 합니다" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("answers", "expected"),
    [
        (["maybe", " y "], True),
        (["", "N"], False),
    ],
)
def test_get_yes_no_input_retries_until_y_or_n(
    monkeypatch,
    capsys,
    answers,
    expected,
) -> None:
    """Y/N 이외의 입력은 거부하고 최종 선택을 bool로 반환해야 한다."""

    answer_iterator = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(answer_iterator))

    assert get_yes_no_input("선택(Y/N): ") is expected
    assert "Y 또는 N" in capsys.readouterr().out
