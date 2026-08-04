#pragma once

#include <string>
#include <vector>

class Library;

class Book {
public:
    Book(
        std::string bookId,
        std::string title,
        std::string author,
        std::string publisher,
        int year,
        bool isBorrowed = false,
        std::string borrower = "",
        std::string borrowedDate = ""
    );

    const std::string& bookId() const noexcept;
    const std::string& title() const noexcept;
    const std::string& author() const noexcept;
    const std::string& publisher() const noexcept;
    int year() const noexcept;
    bool isBorrowed() const noexcept;
    bool isAvailable() const noexcept;
    const std::string& borrower() const noexcept;
    const std::string& borrowedDate() const noexcept;

    void borrow(const std::string& borrower, const std::string& borrowedDate);
    void returnBook();

    std::vector<std::string> toCsvFields() const;

    bool operator==(const Book& other) const noexcept;

private:
    friend class Library;

    void setBookIdForRegistration(std::string bookId);
    void validateBorrowState() const;

    std::string bookId_;
    std::string title_;
    std::string author_;
    std::string publisher_;
    int year_;
    bool isBorrowed_;
    std::string borrower_;
    std::string borrowedDate_;
};
