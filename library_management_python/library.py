"""여러 도서를 등록하고 검색하는 도서관 관리 모듈."""

from models import Book


class Library:
    """Book 객체 목록과 도서 등록·조회·검색 기능을 관리한다."""

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
