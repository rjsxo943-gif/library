#include "Book.h"
#include "CatalogQuery.h"
#include "Library.h"
#include "Storage.h"
#include "Utils.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int failures = 0;
int tests = 0;

void check(bool condition, const std::string& message) {
    ++tests;
    if (!condition) {
        ++failures;
        std::cerr << "[FAIL] " << message << '\n';
    }
}

template <typename Callable>
void checkThrows(Callable callable, const std::string& message) {
    ++tests;
    try {
        callable();
        ++failures;
        std::cerr << "[FAIL] " << message << " (예외 없음)\n";
    } catch (const std::exception&) {
    }
}

Book makeBook(
    std::string id = "B0001",
    std::string title = "파이썬 기초",
    std::string author = "김철수"
) {
    return Book(std::move(id), std::move(title), std::move(author), "전자출판사", 2025);
}

void testBookState() {
    Book book = makeBook();
    check(book.isAvailable(), "신규 도서는 대출 가능해야 한다");
    book.borrow(" 김건태 ", " 2026-08-04 ");
    check(book.isBorrowed(), "대출 후 대출 중이어야 한다");
    check(book.borrower() == "김건태", "대출자 공백이 제거되어야 한다");
    checkThrows([&] { book.borrow("홍길동", "2026-08-05"); }, "중복 대출을 막아야 한다");
    book.returnBook();
    check(book.isAvailable() && book.borrower().empty() && book.borrowedDate().empty(),
        "반납 후 대출 정보가 초기화되어야 한다");
}

void testLibraryOperations() {
    Library library;
    check(library.addBook(makeBook("  b0001  ")), "첫 도서를 등록해야 한다");
    check(library.findBookById("B0001") != nullptr, "ID 대소문자와 공백을 무시해야 한다");
    check(!library.addBook(makeBook("b0001")), "중복 ID를 거부해야 한다");

    Book titleBook("B0002", "파이 썬  기초 입문", "김 철 수", "한빛", 2024);
    library.addBook(titleBook);
    check(library.searchByTitle("파이썬기초").size() == 2U,
        "제목 검색은 내부 띄어쓰기를 무시해야 한다");
    check(library.searchByAuthor("김철수").size() == 2U,
        "저자 검색은 내부 띄어쓰기를 무시해야 한다");

    auto borrowed = library.borrowBook("B0001", "김건태", "2026-08-04");
    check(borrowed.success && borrowed.code == "borrowed", "정상 대출이 성공해야 한다");
    check(library.deleteBook("B0001").code == "book_is_borrowed", "대출 중 삭제를 차단해야 한다");
    check(library.returnBook("B0001").success, "정상 반납이 성공해야 한다");
    check(library.deleteBook("B0001").success, "반납 후 삭제되어야 한다");
    check(library.findBookById("B0001") == nullptr, "삭제 후 검색되지 않아야 한다");
}

void testCatalogQuery() {
    Library library;
    library.addBook(makeBook("B0001", "파이썬 기초", "김철수"));
    library.addBook(Book("B0002", "C++ 프로그래밍", "홍길동", "한빛", 2024,
        true, "김건태", "2026-08-04"));
    library.addBook(makeBook("B0003", "자료 구조", "박영희"));

    check(searchCatalog(library).size() == 3U, "빈 통합검색은 전체를 반환해야 한다");
    check(searchCatalog(library, "파이 썬", SearchMode::All).size() == 1U,
        "통합검색은 띄어쓰기 차이를 무시해야 한다");
    check(searchCatalog(library, "홍길동", SearchMode::Author).front()->bookId() == "B0002",
        "저자 검색이 일치해야 한다");
    check(searchCatalog(library, "", SearchMode::All, LoanFilter::Borrowed).size() == 1U,
        "대출 중 필터가 동작해야 한다");
    check(searchCatalog(library, "", SearchMode::All, LoanFilter::Available).size() == 2U,
        "대출 가능 필터가 동작해야 한다");
}

void testStorage() {
    const auto directory = std::filesystem::temp_directory_path() / "library_cpp_tests";
    const auto filePath = directory / "books.csv";
    std::error_code ignored;
    std::filesystem::remove_all(directory, ignored);

    std::vector<Book> books = {
        Book("B0001", "파이썬, 제대로 배우기", "김철수", "전자출판사", 2025),
        Book("B0002", "C++ Programming", "홍길동", "한빛", 2024,
            true, "김건태", "2026-08-04"),
    };
    check(storage::saveBooks(books, filePath) == 2U, "CSV에 두 권을 저장해야 한다");
    const auto loaded = storage::loadBooks(filePath);
    check(loaded == books, "CSV 왕복 후 모든 필드가 같아야 한다");

    std::ifstream raw(filePath, std::ios::binary);
    const std::string contents((std::istreambuf_iterator<char>(raw)), {});
    check(contents.find("\"파이썬, 제대로 배우기\"") != std::string::npos,
        "쉼표가 포함된 제목은 인용되어야 한다");
    check(contents.find("true,김건태,2026-08-04") != std::string::npos,
        "대출 상태는 Python과 같은 true 형식이어야 한다");

    const auto damagedPath = directory / "damaged.csv";
    std::ofstream damaged(damagedPath, std::ios::binary);
    damaged << "book_id,title,author,publisher,year,is_borrowed,borrower,borrowed_date\n"
            << "B0001,정상 도서,김철수,출판사,2025,false,,\n"
            << "B0002,잘못된 연도,홍길동,출판사,no,false,,\n"
            << "B0003,정상 대출,박영희,출판사,2024,true,김건태,2026-08-04\n";
    damaged.close();
    std::vector<std::string> warnings;
    const auto partiallyLoaded = storage::loadBooks(damagedPath, &warnings);
    check(partiallyLoaded.size() == 2U && warnings.size() == 1U,
        "손상 행만 건너뛰고 정상 행을 복원해야 한다");

    std::filesystem::remove_all(directory, ignored);
}

void testUtilities() {
    check(utils::normalizeBookId("  b001  ") == "B001", "도서 ID를 정규화해야 한다");
    check(utils::normalizeSearchText("파이 썬\t기초") == "파이썬기초",
        "검색 정규화는 모든 ASCII 공백을 제거해야 한다");
    check(utils::validatePublicationYear("2025", 2026) == 2025, "정상 연도를 허용해야 한다");
    checkThrows([] { utils::validatePublicationYear("2027", 2026); }, "미래 연도를 차단해야 한다");
}

}  // namespace

int main() {
    testBookState();
    testLibraryOperations();
    testCatalogQuery();
    testStorage();
    testUtilities();

    if (failures == 0) {
        std::cout << "[PASS] " << tests << " checks passed\n";
        return 0;
    }
    std::cerr << "[FAIL] " << failures << " of " << tests << " checks failed\n";
    return 1;
}
