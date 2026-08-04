"""입력값 검증, 문자열 정리, 날짜 생성을 담당하는 보조 모듈."""

from __future__ import annotations

from datetime import date


def normalize_book_id(book_id: str) -> str:
    """
    도서 번호의 앞뒤 공백을 제거하고 영문을 대문자로 통일한다.

    콘솔과 GUI에서 신규 도서를 생성하기 전에 같은 규칙을 적용할 수 있다.
    """

    return book_id.strip().upper()


def validate_non_empty(value: str, field_name: str = "입력값") -> str:
    """문자열의 앞뒤 공백을 제거하고 빈 값이면 ValueError를 발생시킨다."""

    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(f"{field_name}은(는) 비워둘 수 없습니다.")

    return normalized_value


def validate_integer(
    value: str,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """문자열을 정수로 변환하고 선택적인 최솟값·최댓값 범위를 검사한다."""

    try:
        number = int(value.strip())
    except ValueError as exc:
        raise ValueError("정수로 입력해야 합니다.") from exc

    if min_value is not None and number < min_value:
        raise ValueError(f"{min_value} 이상의 값을 입력해야 합니다.")

    if max_value is not None and number > max_value:
        raise ValueError(f"{max_value} 이하의 값을 입력해야 합니다.")

    return number


def validate_publication_year(value: str, current_year: int | None = None) -> int:
    """출판 연도가 1000년부터 현재 연도 사이인지 검사한다."""

    maximum_year = current_year if current_year is not None else date.today().year
    return validate_integer(value, min_value=1000, max_value=maximum_year)


def get_current_date(today: date | None = None) -> str:
    """현재 날짜를 Python과 C++의 공통 형식인 YYYY-MM-DD로 반환한다."""

    target_date = today if today is not None else date.today()
    return target_date.isoformat()


def get_non_empty_input(prompt: str, field_name: str = "입력값") -> str:
    """비어 있지 않은 문자열이 입력될 때까지 반복해서 입력받는다."""

    while True:
        try:
            return validate_non_empty(input(prompt), field_name)
        except ValueError as exc:
            print(f"오류: {exc}")


def get_integer_input(
    prompt: str,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """지정된 범위의 정수가 입력될 때까지 반복해서 입력받는다."""

    while True:
        try:
            return validate_integer(input(prompt), min_value, max_value)
        except ValueError as exc:
            print(f"오류: {exc}")


def get_publication_year_input(prompt: str = "출판 연도: ") -> int:
    """유효한 출판 연도가 입력될 때까지 반복해서 입력받는다."""

    while True:
        try:
            return validate_publication_year(input(prompt))
        except ValueError as exc:
            print(f"오류: {exc}")


def get_yes_no_input(prompt: str) -> bool:
    """Y 또는 N이 입력될 때까지 반복하고, Y이면 True를 반환한다."""

    while True:
        answer = input(prompt).strip().casefold()

        if answer == "y":
            return True

        if answer == "n":
            return False

        print("오류: Y 또는 N으로 입력해 주세요.")
