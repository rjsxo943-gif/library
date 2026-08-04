#include "Storage.h"

#include "Utils.h"

#include <fstream>
#include <set>
#include <sstream>

namespace {

std::string escapeCsvField(const std::string& field) {
    const bool mustQuote = field.find_first_of(",\"\r\n") != std::string::npos;
    if (!mustQuote) {
        return field;
    }

    std::string escaped = "\"";
    for (const char ch : field) {
        if (ch == '\"') {
            escaped += "\"\"";
        } else {
            escaped.push_back(ch);
        }
    }
    escaped.push_back('\"');
    return escaped;
}

std::vector<std::vector<std::string>> readRecords(std::istream& input) {
    std::vector<std::vector<std::string>> records;
    std::vector<std::string> row;
    std::string field;
    bool inQuotes = false;
    bool touched = false;

    char ch = '\0';
    while (input.get(ch)) {
        touched = true;
        if (inQuotes) {
            if (ch == '\"') {
                if (input.peek() == '\"') {
                    input.get(ch);
                    field.push_back('\"');
                } else {
                    inQuotes = false;
                }
            } else {
                field.push_back(ch);
            }
            continue;
        }

        if (ch == '\"' && field.empty()) {
            inQuotes = true;
        } else if (ch == ',') {
            row.push_back(field);
            field.clear();
        } else if (ch == '\n') {
            row.push_back(field);
            field.clear();
            records.push_back(row);
            row.clear();
            touched = false;
        } else if (ch != '\r') {
            field.push_back(ch);
        }
    }

    if (inQuotes) {
        throw StorageError("CSV 인용부호가 닫히지 않았습니다.");
    }
    if (touched || !field.empty() || !row.empty()) {
        row.push_back(field);
        records.push_back(row);
    }
    return records;
}

std::string joinHeader(const std::vector<std::string>& values) {
    std::ostringstream output;
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index != 0) {
            output << ',';
        }
        output << values[index];
    }
    return output.str();
}

void appendWarning(std::vector<std::string>* warnings, std::string message) {
    if (warnings != nullptr) {
        warnings->push_back(std::move(message));
    }
}

}  // namespace

namespace storage {

const std::vector<std::string>& csvFieldNames() {
    static const std::vector<std::string> fields = {
        "book_id",
        "title",
        "author",
        "publisher",
        "year",
        "is_borrowed",
        "borrower",
        "borrowed_date",
    };
    return fields;
}

std::size_t saveBooks(const std::vector<Book>& books, const std::filesystem::path& filePath) {
    const auto temporaryPath = std::filesystem::path(filePath.string() + ".tmp");
    const auto backupPath = std::filesystem::path(filePath.string() + ".bak");

    try {
        if (filePath.has_parent_path()) {
            std::filesystem::create_directories(filePath.parent_path());
        }

        std::ofstream output(temporaryPath, std::ios::binary | std::ios::trunc);
        if (!output) {
            throw StorageError("임시 CSV 파일을 열 수 없습니다.");
        }

        output << joinHeader(csvFieldNames()) << '\n';
        for (const Book& book : books) {
            const auto fields = book.toCsvFields();
            for (std::size_t index = 0; index < fields.size(); ++index) {
                if (index != 0) {
                    output << ',';
                }
                output << escapeCsvField(fields[index]);
            }
            output << '\n';
        }
        output.close();
        if (!output) {
            throw StorageError("CSV 파일 기록을 완료하지 못했습니다.");
        }

        std::error_code error;
        std::filesystem::remove(backupPath, error);
        if (std::filesystem::exists(filePath)) {
            std::filesystem::rename(filePath, backupPath);
        }

        try {
            std::filesystem::rename(temporaryPath, filePath);
            std::filesystem::remove(backupPath, error);
        } catch (...) {
            std::filesystem::remove(filePath, error);
            if (std::filesystem::exists(backupPath)) {
                std::filesystem::rename(backupPath, filePath, error);
            }
            throw;
        }
    } catch (const StorageError&) {
        std::error_code ignored;
        std::filesystem::remove(temporaryPath, ignored);
        throw;
    } catch (const std::exception& exception) {
        std::error_code ignored;
        std::filesystem::remove(temporaryPath, ignored);
        throw StorageError(
            "도서 데이터를 '" + filePath.string() + "' 파일에 저장하지 못했습니다: "
            + exception.what()
        );
    }

    return books.size();
}

std::vector<Book> loadBooks(
    const std::filesystem::path& filePath,
    std::vector<std::string>* warnings
) {
    std::error_code error;
    if (!std::filesystem::exists(filePath, error)) {
        return {};
    }
    if (std::filesystem::file_size(filePath, error) == 0U) {
        return {};
    }

    try {
        std::ifstream input(filePath, std::ios::binary);
        if (!input) {
            throw StorageError("CSV 파일을 열 수 없습니다.");
        }

        auto records = readRecords(input);
        if (records.empty()) {
            return {};
        }

        if (!records[0].empty() && records[0][0].rfind("\xEF\xBB\xBF", 0) == 0) {
            records[0][0].erase(0, 3);
        }
        if (records[0] != csvFieldNames()) {
            throw StorageError(
                "CSV 헤더가 올바르지 않습니다. 필요한 헤더: "
                + joinHeader(csvFieldNames())
            );
        }

        std::vector<Book> books;
        std::set<std::string> loadedIds;

        for (std::size_t rowIndex = 1; rowIndex < records.size(); ++rowIndex) {
            const auto& row = records[rowIndex];
            if (row.size() == 1U && row[0].empty()) {
                continue;
            }

            try {
                if (row.size() != csvFieldNames().size()) {
                    throw std::invalid_argument("필드 수가 8개가 아닙니다.");
                }

                const std::string bookId = utils::normalizeBookId(
                    utils::validateNonEmpty(row[0], "book_id")
                );
                const std::string normalizedId = utils::toLowerAscii(bookId);
                if (!loadedIds.insert(normalizedId).second) {
                    throw std::invalid_argument("중복된 도서 번호입니다.");
                }

                const int year = utils::validatePublicationYear(row[4]);
                const std::string borrowedText = utils::toLowerAscii(utils::trim(row[5]));
                bool isBorrowed = false;
                if (borrowedText == "true") {
                    isBorrowed = true;
                } else if (borrowedText != "false") {
                    throw std::invalid_argument("대출 상태는 true 또는 false여야 합니다.");
                }

                books.emplace_back(
                    bookId,
                    utils::validateNonEmpty(row[1], "title"),
                    utils::validateNonEmpty(row[2], "author"),
                    utils::validateNonEmpty(row[3], "publisher"),
                    year,
                    isBorrowed,
                    utils::trim(row[6]),
                    utils::trim(row[7])
                );
            } catch (const std::exception& exception) {
                appendWarning(
                    warnings,
                    std::to_string(rowIndex + 1) + "행을 건너뜁니다: " + exception.what()
                );
            }
        }
        return books;
    } catch (const StorageError&) {
        throw;
    } catch (const std::exception& exception) {
        throw StorageError(
            "도서 데이터 파일 '" + filePath.string() + "'을 읽지 못했습니다: "
            + exception.what()
        );
    }
}

}  // namespace storage
