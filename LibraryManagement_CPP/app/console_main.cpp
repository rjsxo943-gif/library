#include "Book.h"
#include "CatalogQuery.h"
#include "Library.h"
#include "Storage.h"
#include "Utils.h"

#include <filesystem>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#endif

namespace {

std::string readLine(const std::string& prompt) {
    std::cout << prompt;
    std::string value;
    if (!std::getline(std::cin, value)) {
        throw std::runtime_error("입력이 중단되었습니다.");
    }
    return value;
}

std::string readNonEmpty(const std::string& prompt, const std::string& fieldName) {
    while (true) {
        try {
            return utils::validateNonEmpty(readLine(prompt), fieldName);
        } catch (const std::invalid_argument& exception) {
            std::cout << "오류: " << exception.what() << '\n';
        }
    }
}

int readInteger(const std::string& prompt, int minValue, int maxValue) {
    while (true) {
        try {
            return utils::parseInteger(readLine(prompt), minValue, maxValue);
        } catch (const std::invalid_argument& exception) {
            std::cout << "오류: " << exception.what() << '\n';
        }
    }
}

bool readYesNo(const std::string& prompt) {
    while (true) {
        const std::string answer = utils::toLowerAscii(utils::trim(readLine(prompt)));
        if (answer == "y") {
            return true;
        }
        if (answer == "n") {
            return false;
        }
        std::cout << "오류: Y 또는 N으로 입력해 주세요.\n";
    }
}

void printBook(const Book& book) {
    std::cout
        << "도서 번호: " << book.bookId() << '\n'
        << "제목: " << book.title() << '\n'
        << "저자: " << book.author() << '\n'
        << "출판사: " << book.publisher() << '\n'
        << "출판 연도: " << book.year() << '\n'
        << "대출 상태: " << (book.isBorrowed() ? "대출 중" : "대출 가능") << '\n'
        << "대출자: " << (book.borrower().empty() ? "-" : book.borrower()) << '\n'
        << "대출일: " << (book.borrowedDate().empty() ? "-" : book.borrowedDate()) << '\n';
}

void printBooks(const std::vector<const Book*>& books) {
    if (books.empty()) {
        std::cout << "등록된 도서가 없습니다.\n";
        return;
    }

    std::cout << "\n" << std::left
        << std::setw(12) << "도서번호"
        << std::setw(30) << "도서명"
        << std::setw(18) << "저자"
        << std::setw(18) << "출판사"
        << std::setw(8) << "연도"
        << std::setw(12) << "대출상태"
        << std::setw(16) << "대출자"
        << "대출일\n";
    std::cout << std::string(126, '-') << '\n';

    for (const Book* book : books) {
        std::cout
            << std::setw(12) << book->bookId()
            << std::setw(30) << book->title()
            << std::setw(18) << book->author()
            << std::setw(18) << book->publisher()
            << std::setw(8) << book->year()
            << std::setw(12) << (book->isBorrowed() ? "대출 중" : "대출 가능")
            << std::setw(16) << (book->borrower().empty() ? "-" : book->borrower())
            << (book->borrowedDate().empty() ? "-" : book->borrowedDate()) << '\n';
    }
    std::cout << "총 도서 수: " << books.size() << "권\n";
}

void printAll(const Library& library) {
    std::vector<const Book*> books;
    for (const Book& book : library.books()) {
        books.push_back(&book);
    }
    printBooks(books);
}

bool saveLibrary(const Library& library, const std::filesystem::path& filePath) {
    try {
        const std::size_t count = storage::saveBooks(library.listBooks(), filePath);
        std::cout << "도서 데이터 " << count << "권을 저장했습니다.\n";
        return true;
    } catch (const StorageError& exception) {
        std::cout << "저장 오류: " << exception.what() << '\n';
        return false;
    }
}

void registerBook(Library& library, const std::filesystem::path& filePath) {
    std::cout << "\n[도서 등록]\n";
    const std::string bookId = utils::normalizeBookId(readNonEmpty("도서 번호: ", "도서 번호"));
    if (library.isDuplicateId(bookId)) {
        std::cout << "오류: 이미 등록된 도서 번호입니다.\n";
        return;
    }

    const std::string title = readNonEmpty("제목: ", "제목");
    const std::string author = readNonEmpty("저자: ", "저자");
    const std::string publisher = readNonEmpty("출판사: ", "출판사");
    int year = 0;
    while (true) {
        try {
            year = utils::validatePublicationYear(readLine("출판 연도: "));
            break;
        } catch (const std::invalid_argument& exception) {
            std::cout << "오류: " << exception.what() << '\n';
        }
    }

    Book book(bookId, title, author, publisher, year);
    if (!library.addBook(book)) {
        std::cout << "오류: 도서를 등록하지 못했습니다.\n";
        return;
    }
    std::cout << "도서가 정상적으로 등록되었습니다.\n";
    printBook(*library.findBookById(bookId));
    saveLibrary(library, filePath);
}

void searchBooks(const Library& library) {
    while (true) {
        std::cout
            << "\n[도서 검색]\n"
            << "1. 도서 번호로 검색\n"
            << "2. 제목으로 검색\n"
            << "3. 저자로 검색\n"
            << "0. 이전 메뉴\n";
        const int choice = readInteger("검색 방법을 선택하세요: ", 0, 3);
        if (choice == 0) {
            return;
        }

        const std::string keyword = readNonEmpty("검색어: ", "검색어");
        SearchMode mode = SearchMode::BookId;
        if (choice == 2) {
            mode = SearchMode::Title;
        } else if (choice == 3) {
            mode = SearchMode::Author;
        }
        const auto results = searchCatalog(library, keyword, mode);
        if (results.empty()) {
            std::cout << "검색 조건에 해당하는 도서가 없습니다.\n";
        } else {
            printBooks(results);
        }
    }
}

void borrowBook(Library& library, const std::filesystem::path& filePath) {
    std::cout << "\n[도서 대출]\n";
    const std::string bookId = readNonEmpty("대출할 도서 번호: ", "도서 번호");
    const Book* book = library.findBookById(bookId);
    if (book == nullptr) {
        std::cout << "오류: 해당 도서 번호의 도서를 찾을 수 없습니다.\n";
        return;
    }
    if (book->isBorrowed()) {
        std::cout << "오류: 이미 대출 중인 도서입니다.\n"
                  << "현재 대출자: " << book->borrower() << '\n'
                  << "대출일: " << book->borrowedDate() << '\n';
        return;
    }

    const std::string borrower = readNonEmpty("대출자 이름: ", "대출자 이름");
    const OperationResult result = library.borrowBook(bookId, borrower, utils::currentDate());
    std::cout << (result.success ? "완료: " : "오류: ") << result.message << '\n';
    if (result.success) {
        saveLibrary(library, filePath);
    }
}

void returnBook(Library& library, const std::filesystem::path& filePath) {
    std::cout << "\n[도서 반납]\n";
    const std::string bookId = readNonEmpty("반납할 도서 번호: ", "도서 번호");
    const OperationResult result = library.returnBook(bookId);
    std::cout << (result.success ? "완료: " : "오류: ") << result.message << '\n';
    if (result.success) {
        saveLibrary(library, filePath);
    }
}

void deleteBook(Library& library, const std::filesystem::path& filePath) {
    std::cout << "\n[도서 삭제]\n";
    const std::string bookId = readNonEmpty("삭제할 도서 번호: ", "도서 번호");
    const Book* book = library.findBookById(bookId);
    if (book == nullptr) {
        std::cout << "오류: 해당 도서 번호의 도서를 찾을 수 없습니다.\n";
        return;
    }
    if (book->isBorrowed()) {
        std::cout << "오류: 대출 중인 도서는 삭제할 수 없습니다.\n";
        return;
    }

    printBook(*book);
    if (!readYesNo("삭제하시겠습니까? (Y/N): ")) {
        std::cout << "도서 삭제를 취소했습니다.\n";
        return;
    }

    const OperationResult result = library.deleteBook(bookId);
    std::cout << (result.success ? "완료: " : "오류: ") << result.message << '\n';
    if (result.success) {
        saveLibrary(library, filePath);
    }
}

void printMenu() {
    std::cout
        << "\n========================================\n"
        << "           도서관리 시스템\n"
        << "========================================\n"
        << "1. 도서 등록\n"
        << "2. 전체 도서 조회\n"
        << "3. 도서 검색\n"
        << "4. 도서 대출\n"
        << "5. 도서 반납\n"
        << "6. 도서 삭제\n"
        << "7. 파일 저장\n"
        << "0. 프로그램 종료\n"
        << "========================================\n";
}

}  // namespace

int main(int argc, char* argv[]) {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
#endif

    const std::filesystem::path executable = argc > 0 ? argv[0] : "";
    const std::filesystem::path filePath = argc > 1
        ? std::filesystem::path(argv[1])
        : utils::resolveBooksFile(executable);

    Library library;
    try {
        std::vector<std::string> warnings;
        for (const Book& book : storage::loadBooks(filePath, &warnings)) {
            library.addBook(book);
        }
        for (const std::string& warning : warnings) {
            std::cout << "CSV 경고: " << warning << '\n';
        }
    } catch (const StorageError& exception) {
        std::cout << "불러오기 오류: " << exception.what() << '\n'
                  << "기존 파일을 보호하기 위해 프로그램을 종료합니다.\n";
        return 1;
    }

    std::cout << "데이터 파일: " << filePath.string() << '\n'
              << "도서 데이터 " << library.books().size() << "권을 불러왔습니다.\n";

    try {
        while (true) {
            printMenu();
            const int choice = readInteger("메뉴를 선택하세요: ", 0, 7);
            if (choice == 0) {
                std::cout << "프로그램을 종료합니다.\n";
                break;
            }

            switch (choice) {
            case 1: registerBook(library, filePath); break;
            case 2: printAll(library); break;
            case 3: searchBooks(library); break;
            case 4: borrowBook(library, filePath); break;
            case 5: returnBook(library, filePath); break;
            case 6: deleteBook(library, filePath); break;
            case 7: saveLibrary(library, filePath); break;
            default: break;
            }
        }
    } catch (const std::exception& exception) {
        std::cout << "\n입력이 중단되었습니다: " << exception.what() << '\n';
    }

    return saveLibrary(library, filePath) ? 0 : 1;
}
