#include "Library.h"

#include "Utils.h"

#include <algorithm>

bool Library::addBook(const Book& book) {
    const std::string normalizedId = utils::normalizeBookId(book.bookId());
    if (normalizedId.empty() || isDuplicateId(normalizedId)) {
        return false;
    }

    Book storedBook = book;
    storedBook.setBookIdForRegistration(normalizedId);
    books_.push_back(std::move(storedBook));
    return true;
}

const std::vector<Book>& Library::books() const noexcept { return books_; }
std::vector<Book> Library::listBooks() const { return books_; }

Book* Library::findBookById(const std::string& bookId) {
    const std::string normalizedId = utils::normalizeBookId(bookId);
    if (normalizedId.empty()) {
        return nullptr;
    }

    const auto iterator = std::find_if(books_.begin(), books_.end(), [&](const Book& book) {
        return utils::normalizeBookId(book.bookId()) == normalizedId;
    });
    return iterator == books_.end() ? nullptr : &*iterator;
}

const Book* Library::findBookById(const std::string& bookId) const {
    const std::string normalizedId = utils::normalizeBookId(bookId);
    if (normalizedId.empty()) {
        return nullptr;
    }

    const auto iterator = std::find_if(books_.cbegin(), books_.cend(), [&](const Book& book) {
        return utils::normalizeBookId(book.bookId()) == normalizedId;
    });
    return iterator == books_.cend() ? nullptr : &*iterator;
}

bool Library::isDuplicateId(const std::string& bookId) const {
    return findBookById(bookId) != nullptr;
}

std::vector<Book*> Library::searchByTitle(const std::string& keyword) {
    std::vector<Book*> results;
    const std::string normalizedKeyword = utils::normalizeSearchText(keyword);
    if (normalizedKeyword.empty()) {
        return results;
    }

    for (Book& book : books_) {
        if (utils::normalizeSearchText(book.title()).find(normalizedKeyword) != std::string::npos) {
            results.push_back(&book);
        }
    }
    return results;
}

std::vector<const Book*> Library::searchByTitle(const std::string& keyword) const {
    std::vector<const Book*> results;
    const std::string normalizedKeyword = utils::normalizeSearchText(keyword);
    if (normalizedKeyword.empty()) {
        return results;
    }

    for (const Book& book : books_) {
        if (utils::normalizeSearchText(book.title()).find(normalizedKeyword) != std::string::npos) {
            results.push_back(&book);
        }
    }
    return results;
}

std::vector<Book*> Library::searchByAuthor(const std::string& keyword) {
    std::vector<Book*> results;
    const std::string normalizedKeyword = utils::normalizeSearchText(keyword);
    if (normalizedKeyword.empty()) {
        return results;
    }

    for (Book& book : books_) {
        if (utils::normalizeSearchText(book.author()).find(normalizedKeyword) != std::string::npos) {
            results.push_back(&book);
        }
    }
    return results;
}

std::vector<const Book*> Library::searchByAuthor(const std::string& keyword) const {
    std::vector<const Book*> results;
    const std::string normalizedKeyword = utils::normalizeSearchText(keyword);
    if (normalizedKeyword.empty()) {
        return results;
    }

    for (const Book& book : books_) {
        if (utils::normalizeSearchText(book.author()).find(normalizedKeyword) != std::string::npos) {
            results.push_back(&book);
        }
    }
    return results;
}

OperationResult Library::borrowBook(
    const std::string& bookId,
    const std::string& borrower,
    const std::string& borrowedDate
) {
    Book* book = findBookById(bookId);
    if (book == nullptr) {
        return {false, "book_not_found", "해당 도서 번호의 도서를 찾을 수 없습니다.", std::nullopt};
    }
    if (book->isBorrowed()) {
        return {false, "already_borrowed", "이미 대출 중인 도서입니다.", *book};
    }
    if (utils::trim(borrower).empty()) {
        return {false, "invalid_borrower", "대출자 이름은 비워둘 수 없습니다.", *book};
    }
    if (utils::trim(borrowedDate).empty()) {
        return {false, "invalid_borrowed_date", "대출일은 비워둘 수 없습니다.", *book};
    }

    book->borrow(borrower, borrowedDate);
    return {true, "borrowed", "도서 대출이 완료되었습니다.", *book};
}

OperationResult Library::returnBook(const std::string& bookId) {
    Book* book = findBookById(bookId);
    if (book == nullptr) {
        return {false, "book_not_found", "해당 도서 번호의 도서를 찾을 수 없습니다.", std::nullopt};
    }
    if (!book->isBorrowed()) {
        return {false, "not_borrowed", "현재 대출 중인 도서가 아닙니다.", *book};
    }

    book->returnBook();
    return {true, "returned", "도서 반납이 완료되었습니다.", *book};
}

OperationResult Library::deleteBook(const std::string& bookId) {
    const std::string normalizedId = utils::normalizeBookId(bookId);
    const auto iterator = std::find_if(books_.begin(), books_.end(), [&](const Book& book) {
        return utils::normalizeBookId(book.bookId()) == normalizedId;
    });

    if (iterator == books_.end()) {
        return {false, "book_not_found", "해당 도서 번호의 도서를 찾을 수 없습니다.", std::nullopt};
    }
    if (iterator->isBorrowed()) {
        return {false, "book_is_borrowed", "대출 중인 도서는 삭제할 수 없습니다.", *iterator};
    }

    Book deleted = *iterator;
    books_.erase(iterator);
    return {true, "deleted", "도서 삭제가 완료되었습니다.", deleted};
}
