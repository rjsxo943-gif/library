"""콘솔 애플리케이션 통합 흐름을 검증하는 테스트."""

import main as app
from library import Library
from models import Book
from storage import load_books, save_books


def _set_inputs(monkeypatch, answers: list[str]) -> None:
    """테스트 입력 순서를 builtins.input에 연결한다."""

    iterator = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(iterator))


def test_main_exits_cleanly_and_creates_csv(tmp_path, monkeypatch, capsys) -> None:
    """빈 데이터로 실행해 종료하면 헤더가 있는 CSV가 생성되어야 한다."""

    file_path = tmp_path / "books.csv"
    _set_inputs(monkeypatch, ["0"])

    result = app.main(file_path)

    assert result == 0
    assert file_path.exists()
    assert load_books(file_path) == []
    output = capsys.readouterr().out
    assert "도서 데이터 0권을 불러왔습니다" in output
    assert "프로그램을 종료합니다" in output


def test_full_register_borrow_return_delete_flow(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    """메뉴를 통해 등록·대출·반납·삭제하고 매 단계 저장해야 한다."""

    file_path = tmp_path / "books.csv"
    monkeypatch.setattr(app, "get_current_date", lambda: "2026-08-04")
    _set_inputs(
        monkeypatch,
        [
            "1",
            "b0001",
            "Python 기초",
            "김철수",
            "전자출판사",
            "2025",
            "4",
            "B0001",
            "김건태",
            "5",
            "B0001",
            "6",
            "B0001",
            "y",
            "0",
        ],
    )

    result = app.main(file_path)

    assert result == 0
    assert load_books(file_path) == []
    output = capsys.readouterr().out
    assert "도서가 정상적으로 등록되었습니다" in output
    assert "도서 대출이 완료되었습니다" in output
    assert "도서 반납이 완료되었습니다" in output
    assert "도서 삭제가 완료되었습니다" in output


def test_search_submenu_displays_partial_title_matches(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    """제목 일부 검색 결과를 표로 출력하고 이전 메뉴로 돌아와야 한다."""

    file_path = tmp_path / "books.csv"
    books = [
        Book("B0001", "Python 기초", "김철수", "전자출판사", 2025),
        Book("B0002", "실전 Python", "박영희", "한빛출판사", 2024),
    ]
    save_books(books, file_path)
    _set_inputs(monkeypatch, ["3", "2", "python", "0", "0"])

    assert app.main(file_path) == 0

    output = capsys.readouterr().out
    assert "Python 기초" in output
    assert "실전 Python" in output
    assert "총 도서 수: 2권" in output


def test_invalid_main_menu_input_retries(monkeypatch, tmp_path, capsys) -> None:
    """문자와 범위 밖 메뉴 입력 뒤에도 정상적으로 종료할 수 있어야 한다."""

    _set_inputs(monkeypatch, ["abc", "9", "0"])

    assert app.main(tmp_path / "books.csv") == 0

    output = capsys.readouterr().out
    assert "정수로 입력해야 합니다" in output
    assert "7 이하의 값을 입력해야 합니다" in output


def test_invalid_csv_header_aborts_without_overwriting(tmp_path, capsys) -> None:
    """불러오기 실패 시 기존 파일을 덮어쓰지 않고 프로그램을 종료해야 한다."""

    file_path = tmp_path / "books.csv"
    original_content = "id,name\nB0001,Python"
    file_path.write_text(original_content, encoding="utf-8")

    assert app.main(file_path) == 1
    assert file_path.read_text(encoding="utf-8") == original_content
    assert "기존 파일을 보호하기 위해 프로그램을 종료합니다" in capsys.readouterr().out


def test_duplicate_registration_stops_before_other_fields(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    """중복 번호면 제목 등의 추가 입력을 받지 않고 등록을 중단해야 한다."""

    library = Library()
    original = Book("B0001", "기존 도서", "김철수", "전자출판사", 2025)
    library.add_book(original)
    _set_inputs(monkeypatch, [" b0001 "])

    app.register_book(library, tmp_path / "books.csv")

    assert library.list_books() == [original]
    assert "이미 등록된 도서 번호" in capsys.readouterr().out


def test_delete_can_be_cancelled(tmp_path, monkeypatch, capsys) -> None:
    """삭제 확인에서 N을 선택하면 목록과 파일을 변경하지 않아야 한다."""

    library = Library()
    book = Book("B0001", "Python 기초", "김철수", "전자출판사", 2025)
    library.add_book(book)
    file_path = tmp_path / "books.csv"
    save_books(library.list_books(), file_path)
    _set_inputs(monkeypatch, ["B0001", "n"])

    app.delete_book(library, file_path)

    assert library.list_books() == [book]
    assert load_books(file_path) == [book]
    assert "도서 삭제를 취소했습니다" in capsys.readouterr().out


def test_display_books_reports_empty_collection(capsys) -> None:
    """빈 목록은 표 대신 안내 문구를 출력해야 한다."""

    app.display_books([])

    assert capsys.readouterr().out.strip() == "등록된 도서가 없습니다."


def test_korean_display_width_is_counted_as_double() -> None:
    """한글 표 정렬을 위해 전각 문자는 두 칸으로 계산해야 한다."""

    assert app._display_width("도서A") == 5
    assert app._display_width(app._fit_cell("도서", 8)) == 8
