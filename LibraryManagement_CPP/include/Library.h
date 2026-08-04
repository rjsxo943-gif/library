#pragma once

#include "Book.h"

#include <optional>
#include <string>
#include <vector>

struct OperationResult {
    bool success;
    std::string code;
    std::string message;
    std::optional<Book> book;
};

class Library {
public:
    bool addBook(const Book& book);

    const std::vector<Book>& books() const noexcept;
    std::vector<Book> listBooks() const;

    Book* findBookById(const std::string& bookId);
    const Book* findBookById(const std::string& bookId) const;
    bool isDuplicateId(const std::string& bookId) const;

    std::vector<Book*> searchByTitle(const std::string& keyword);
    std::vector<const Book*> searchByTitle(const std::string& keyword) const;
    std::vector<Book*> searchByAuthor(const std::string& keyword);
    std::vector<const Book*> searchByAuthor(const std::string& keyword) const;

    OperationResult borrowBook(
        const std::string& bookId,
        const std::string& borrower,
        const std::string& borrowedDate
    );
    OperationResult returnBook(const std::string& bookId);
    OperationResult deleteBook(const std::string& bookId);

private:
    std::vector<Book> books_;
};
