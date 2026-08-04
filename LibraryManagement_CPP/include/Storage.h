#pragma once

#include "Book.h"

#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>

class StorageError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

namespace storage {

const std::vector<std::string>& csvFieldNames();
std::size_t saveBooks(const std::vector<Book>& books, const std::filesystem::path& filePath);
std::vector<Book> loadBooks(
    const std::filesystem::path& filePath,
    std::vector<std::string>* warnings = nullptr
);

}  // namespace storage
