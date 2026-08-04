"""도서 한 권의 데이터와 상태를 관리하는 모델 모듈."""

from dataclasses import dataclass


@dataclass
class Book:
    """도서 한 권의 정보와 대출 상태를 나타내는 클래스."""

    # 도서를 구분하는 기본 정보
    book_id: str
    title: str
    author: str
    publisher: str
    year: int

    # 신규 도서는 기본적으로 대출 가능한 상태이다.
    is_borrowed: bool = False
    borrower: str = ""
    borrowed_date: str = ""

    def __post_init__(self) -> None:
        """
        Book 객체가 생성된 직후 대출 상태가 올바른지 검사한다.

        대출 중인 도서는 대출자와 대출일이 있어야 하고,
        대출 가능한 도서는 대출자와 대출일이 없어야 한다.
        """

        self._validate_borrow_state()

    def _validate_borrow_state(self) -> None:
        """현재 대출 상태와 대출 정보가 서로 일치하는지 검사한다."""

        if self.is_borrowed:
            # 대출 중인데 대출자나 대출일이 없으면 잘못된 데이터이다.
            if not self.borrower.strip() or not self.borrowed_date.strip():
                raise ValueError(
                    "대출 중인 도서에는 대출자와 대출일이 필요합니다."
                )

        else:
            # 대출 가능 상태인데 대출 정보가 남아 있으면 잘못된 데이터이다.
            if self.borrower.strip() or self.borrowed_date.strip():
                raise ValueError(
                    "대출 가능한 도서에는 대출자와 대출일이 없어야 합니다."
                )

    def is_available(self) -> bool:
        """도서가 현재 대출 가능한 상태인지 반환한다."""

        return not self.is_borrowed

    def borrow(self, borrower: str, borrowed_date: str) -> None:
        """
        도서를 대출 상태로 변경한다.

        Args:
            borrower: 대출자 이름
            borrowed_date: 대출 날짜(YYYY-MM-DD)

        Raises:
            ValueError: 이미 대출 중이거나 입력값이 비어 있는 경우
        """

        if self.is_borrowed:
            raise ValueError("이미 대출 중인 도서입니다.")

        # 사용자 입력 앞뒤의 불필요한 공백을 제거한다.
        borrower = borrower.strip()
        borrowed_date = borrowed_date.strip()

        if not borrower:
            raise ValueError("대출자 이름은 비워둘 수 없습니다.")

        if not borrowed_date:
            raise ValueError("대출일은 비워둘 수 없습니다.")

        self.is_borrowed = True
        self.borrower = borrower
        self.borrowed_date = borrowed_date

    def return_book(self) -> None:
        """
        도서를 반납 상태로 변경한다.

        반납 후에는 대출자와 대출일을 빈 문자열로 초기화한다.

        Raises:
            ValueError: 현재 대출 중이 아닌 경우
        """

        if not self.is_borrowed:
            raise ValueError("현재 대출 중인 도서가 아닙니다.")

        self.is_borrowed = False
        self.borrower = ""
        self.borrowed_date = ""

    def to_dict(self) -> dict[str, str | int]:
        """
        CSV 저장에 사용할 딕셔너리 형태로 도서 정보를 반환한다.

        bool 값은 Python과 C++에서 공통으로 읽을 수 있도록
        소문자 문자열 true 또는 false로 변환한다.
        """

        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "year": self.year,
            "is_borrowed": "true" if self.is_borrowed else "false",
            "borrower": self.borrower,
            "borrowed_date": self.borrowed_date,
        }
