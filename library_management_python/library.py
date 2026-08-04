"""여러 도서를 등록하고 검색하며 대출 상태를 관리하는 모듈."""

from dataclasses import dataclass

from models import Book


@dataclass(frozen=True)
class OperationResult:
    """도서관리 작업의 성공 여부와 상세 결과를 전달한다."""

    success: bool
    code: str
    message: str
    book: Book | None = None


class Library:
    """Book 객체 목록과 등록·조회·검색·대출·반납 기능을 관리한다."""

    def __init__(self) -> None:
        """비어 있는 도서 목록으로 Library 객체를 생성한다."""

        self._books: list[Book] = []

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        """도서 번호 비교를 위해 공백과 영문 대소문자를 정규화한다."""

        return book_id.strip().casefold()

    @staticmethod
    def _normalize_search_text(text: str) -> str:
        """부분 검색을 위해 검색어의 공백과 영문 대소문자를 정규화한다."""

        return text.strip().casefold()

    def add_book(self, book: Book) -> bool:
        """
        새로운 도서를 등록한다.

        도서 번호는 앞뒤 공백을 제거해 저장하고, 이미 같은 번호가
        등록되어 있으면 목록을 변경하지 않고 False를 반환한다.
        """

        normalized_id = self._normalize_book_id(book.book_id)

        if not normalized_id:
            return False

        if self.is_duplicate_id(book.book_id):
            return False

        book.book_id = book.book_id.strip()
        self._books.append(book)
        return True

    def list_books(self) -> list[Book]:
        """등록 순서대로 전체 도서 목록의 복사본을 반환한다."""

        return self._books.copy()

    def find_book_by_id(self, book_id: str) -> Book | None:
        """도서 번호가 정확히 일치하는 Book 객체를 찾아 반환한다."""

        normalized_id = self._normalize_book_id(book_id)

        if not normalized_id:
            return None

        for book in self._books:
            if self._normalize_book_id(book.book_id) == normalized_id:
                return book

        return None

    def is_duplicate_id(self, book_id: str) -> bool:
        """같은 도서 번호가 이미 등록되어 있는지 반환한다."""

        return self.find_book_by_id(book_id) is not None

    def search_by_title(self, keyword: str) -> list[Book]:
        """
        제목에 검색어가 포함된 도서를 등록 순서대로 반환한다.

        검색어의 앞뒤 공백과 영문 대소문자는 무시하며,
        빈 검색어가 입력되면 빈 목록을 반환한다.
        """

        normalized_keyword = self._normalize_search_text(keyword)

        if not normalized_keyword:
            return []

        return [
            book
            for book in self._books
            if normalized_keyword in book.title.casefold()
        ]

    def search_by_author(self, keyword: str) -> list[Book]:
        """
        저자명에 검색어가 포함된 도서를 등록 순서대로 반환한다.

        검색어의 앞뒤 공백과 영문 대소문자는 무시하며,
        빈 검색어가 입력되면 빈 목록을 반환한다.
        """

        normalized_keyword = self._normalize_search_text(keyword)

        if not normalized_keyword:
            return []

        return [
            book
            for book in self._books
            if normalized_keyword in book.author.casefold()
        ]

    def borrow_book(
        self,
        book_id: str,
        borrower: str,
        borrowed_date: str,
    ) -> OperationResult:
        """
        대출 가능한 도서를 대출 처리한다.

        호출자는 결과의 ``code``를 이용해 실패 원인을 구분하고,
        ``message``를 콘솔이나 GUI에 그대로 표시할 수 있다.
        """

        book = self.find_book_by_id(book_id)

        if book is None:
            return OperationResult(
                success=False,
                code="book_not_found",
                message="해당 도서 번호의 도서를 찾을 수 없습니다.",
            )

        if book.is_borrowed:
            return OperationResult(
                success=False,
                code="already_borrowed",
                message="이미 대출 중인 도서입니다.",
                book=book,
            )

        normalized_borrower = borrower.strip()
        normalized_date = borrowed_date.strip()

        if not normalized_borrower:
            return OperationResult(
                success=False,
                code="invalid_borrower",
                message="대출자 이름은 비워둘 수 없습니다.",
                book=book,
            )

        if not normalized_date:
            return OperationResult(
                success=False,
                code="invalid_borrowed_date",
                message="대출일은 비워둘 수 없습니다.",
                book=book,
            )

        book.borrow(normalized_borrower, normalized_date)

        return OperationResult(
            success=True,
            code="borrowed",
            message="도서 대출이 완료되었습니다.",
            book=book,
        )

    def return_book(self, book_id: str) -> OperationResult:
        """대출 중인 도서를 반납 처리한다."""

        book = self.find_book_by_id(book_id)

        if book is None:
            return OperationResult(
                success=False,
                code="book_not_found",
                message="해당 도서 번호의 도서를 찾을 수 없습니다.",
            )

        if not book.is_borrowed:
            return OperationResult(
                success=False,
                code="not_borrowed",
                message="현재 대출 중인 도서가 아닙니다.",
                book=book,
            )

        book.return_book()

        return OperationResult(
            success=True,
            code="returned",
            message="도서 반납이 완료되었습니다.",
            book=book,
        )
