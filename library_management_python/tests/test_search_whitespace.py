"""제목과 저자 검색에서 띄어쓰기 차이를 무시하는지 검증한다."""

from library import Library
from models import Book


def make_book(
    book_id: str,
    title: str,
    author: str,
) -> Book:
    """검색 테스트에 사용할 Book 객체를 생성한다."""

    return Book(
        book_id=book_id,
        title=title,
        author=author,
        publisher="전자출판사",
        year=2025,
    )


def test_title_search_ignores_internal_whitespace() -> None:
    """제목과 검색어의 띄어쓰기가 달라도 같은 도서를 찾아야 한다."""

    library = Library()
    book = make_book("B0001", "파이썬 기초 입문", "김철수")
    library.add_book(book)

    assert library.search_by_title("파이썬기초") == [book]
    assert library.search_by_title("파이 썬  기초") == [book]
    assert library.search_by_title("파이썬\t기초") == [book]


def test_author_search_ignores_internal_whitespace() -> None:
    """저자명과 검색어의 띄어쓰기가 달라도 같은 도서를 찾아야 한다."""

    library = Library()
    book = make_book("B0001", "Python 기초", "김 철 수")
    library.add_book(book)

    assert library.search_by_author("김철수") == [book]
    assert library.search_by_author("김  철수") == [book]
