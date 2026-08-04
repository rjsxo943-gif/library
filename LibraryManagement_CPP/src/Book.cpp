#include "Book.h"

#include "Utils.h"

#include <stdexcept>
#include <utility>

Book::Book(
    std::string bookId,
    std::string title,
    std::string author,
    std::string publisher,
    int year,
    bool isBorrowed,
    std::string borrower,
    std::string borrowedDate
)
    : bookId_(std::move(bookId)),
      title_(std::move(title)),
      author_(std::move(author)),
      publisher_(std::move(publisher)),
      year_(year),
      isBorrowed_(isBorrowed),
      borrower_(std::move(borrower)),
      borrowedDate_(std::move(borrowedDate)) {
    validateBorrowState();
}

const std::string& Book::bookId() const noexcept { return bookId_; }
const std::string& Book::title() const noexcept { return title_; }
const std::string& Book::author() const noexcept { return author_; }
const std::string& Book::publisher() const noexcept { return publisher_; }
int Book::year() const noexcept { return year_; }
bool Book::isBorrowed() const noexcept { return isBorrowed_; }
bool Book::isAvailable() const noexcept { return !isBorrowed_; }
const std::string& Book::borrower() const noexcept { return borrower_; }
const std::string& Book::borrowedDate() const noexcept { return borrowedDate_; }

void Book::borrow(const std::string& borrower, const std::string& borrowedDate) {
    if (isBorrowed_) {
        throw std::invalid_argument("이미 대출 중인 도서입니다.");
    }

    borrower_ = utils::validateNonEmpty(borrower, "대출자 이름");
    borrowedDate_ = utils::validateNonEmpty(borrowedDate, "대출일");
    isBorrowed_ = true;
}

void Book::returnBook() {
    if (!isBorrowed_) {
        throw std::invalid_argument("현재 대출 중인 도서가 아닙니다.");
    }

    isBorrowed_ = false;
    borrower_.clear();
    borrowedDate_.clear();
}

std::vector<std::string> Book::toCsvFields() const {
    return {
        bookId_,
        title_,
        author_,
        publisher_,
        std::to_string(year_),
        isBorrowed_ ? "true" : "false",
        borrower_,
        borrowedDate_,
    };
}

bool Book::operator==(const Book& other) const noexcept {
    return bookId_ == other.bookId_
        && title_ == other.title_
        && author_ == other.author_
        && publisher_ == other.publisher_
        && year_ == other.year_
        && isBorrowed_ == other.isBorrowed_
        && borrower_ == other.borrower_
        && borrowedDate_ == other.borrowedDate_;
}

void Book::setBookIdForRegistration(std::string bookId) {
    bookId_ = std::move(bookId);
}

void Book::validateBorrowState() const {
    if (isBorrowed_) {
        if (utils::trim(borrower_).empty() || utils::trim(borrowedDate_).empty()) {
            throw std::invalid_argument("대출 중인 도서에는 대출자와 대출일이 필요합니다.");
        }
    } else if (!utils::trim(borrower_).empty() || !utils::trim(borrowedDate_).empty()) {
        throw std::invalid_argument("대출 가능한 도서에는 대출자와 대출일이 없어야 합니다.");
    }
}
