#include "Utils.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <stdexcept>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#endif

namespace {

bool isAsciiSpace(unsigned char ch) {
    return std::isspace(ch) != 0;
}

std::filesystem::path searchFrom(std::filesystem::path current) {
    std::error_code error;
    current = std::filesystem::absolute(current, error);
    if (error) {
        return {};
    }

    for (int depth = 0; depth < 8; ++depth) {
        const auto pythonDirectory = current / "library_management_python";
        if (std::filesystem::is_directory(pythonDirectory, error)) {
            return pythonDirectory / "books.csv";
        }

        const auto localBooks = current / "books.csv";
        if (std::filesystem::exists(localBooks, error)) {
            return localBooks;
        }

        if (!current.has_parent_path() || current.parent_path() == current) {
            break;
        }
        current = current.parent_path();
    }
    return {};
}

}  // namespace

namespace utils {

std::string trim(const std::string& value) {
    const auto begin = std::find_if_not(value.begin(), value.end(), [](unsigned char ch) {
        return isAsciiSpace(ch);
    });
    const auto end = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char ch) {
        return isAsciiSpace(ch);
    }).base();

    if (begin >= end) {
        return {};
    }
    return std::string(begin, end);
}

std::string toLowerAscii(const std::string& value) {
    std::string result = value;
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return result;
}

std::string toUpperAscii(const std::string& value) {
    std::string result = value;
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });
    return result;
}

std::string normalizeBookId(const std::string& bookId) {
    return toUpperAscii(trim(bookId));
}

std::string normalizeSearchText(const std::string& text) {
    std::string result;
    result.reserve(text.size());

    for (const unsigned char ch : text) {
        if (!isAsciiSpace(ch)) {
            result.push_back(static_cast<char>(std::tolower(ch)));
        }
    }
    return result;
}

std::string validateNonEmpty(const std::string& value, const std::string& fieldName) {
    const std::string normalized = trim(value);
    if (normalized.empty()) {
        throw std::invalid_argument(fieldName + "은(는) 비워둘 수 없습니다.");
    }
    return normalized;
}

int parseInteger(const std::string& value, int minValue, int maxValue) {
    const std::string normalized = trim(value);
    std::size_t consumed = 0;
    int number = 0;

    try {
        number = std::stoi(normalized, &consumed);
    } catch (const std::exception&) {
        throw std::invalid_argument("정수로 입력해야 합니다.");
    }

    if (consumed != normalized.size()) {
        throw std::invalid_argument("정수로 입력해야 합니다.");
    }
    if (number < minValue) {
        throw std::invalid_argument(std::to_string(minValue) + " 이상의 값을 입력해야 합니다.");
    }
    if (number > maxValue) {
        throw std::invalid_argument(std::to_string(maxValue) + " 이하의 값을 입력해야 합니다.");
    }
    return number;
}

int currentYear() {
    const std::time_t now = std::time(nullptr);
    std::tm local{};
#ifdef _WIN32
    localtime_s(&local, &now);
#else
    localtime_r(&now, &local);
#endif
    return local.tm_year + 1900;
}

int validatePublicationYear(const std::string& value, int maximumYear) {
    if (maximumYear == 0) {
        maximumYear = currentYear();
    }
    return parseInteger(value, 1000, maximumYear);
}

std::string currentDate() {
    const std::time_t now = std::time(nullptr);
    std::tm local{};
#ifdef _WIN32
    localtime_s(&local, &now);
#else
    localtime_r(&now, &local);
#endif
    std::ostringstream output;
    output << std::put_time(&local, "%Y-%m-%d");
    return output.str();
}

std::filesystem::path resolveBooksFile(const std::filesystem::path& executablePath) {
    if (const char* environmentPath = std::getenv("LIBRARY_BOOKS_FILE")) {
        const std::string value = trim(environmentPath);
        if (!value.empty()) {
            return std::filesystem::path(value);
        }
    }

    if (const auto found = searchFrom(std::filesystem::current_path()); !found.empty()) {
        return found;
    }

    if (!executablePath.empty()) {
        if (const auto found = searchFrom(executablePath.parent_path()); !found.empty()) {
            return found;
        }
        return executablePath.parent_path() / "books.csv";
    }

    return std::filesystem::current_path() / "books.csv";
}

#ifdef _WIN32
std::wstring utf8ToWide(const std::string& value) {
    if (value.empty()) {
        return {};
    }
    const int size = MultiByteToWideChar(
        CP_UTF8,
        MB_ERR_INVALID_CHARS,
        value.data(),
        static_cast<int>(value.size()),
        nullptr,
        0
    );
    if (size <= 0) {
        throw std::runtime_error("UTF-8 문자열을 UTF-16으로 변환하지 못했습니다.");
    }
    std::wstring result(static_cast<std::size_t>(size), L'\0');
    MultiByteToWideChar(
        CP_UTF8,
        MB_ERR_INVALID_CHARS,
        value.data(),
        static_cast<int>(value.size()),
        result.data(),
        size
    );
    return result;
}

std::string wideToUtf8(const std::wstring& value) {
    if (value.empty()) {
        return {};
    }
    const int size = WideCharToMultiByte(
        CP_UTF8,
        WC_ERR_INVALID_CHARS,
        value.data(),
        static_cast<int>(value.size()),
        nullptr,
        0,
        nullptr,
        nullptr
    );
    if (size <= 0) {
        throw std::runtime_error("UTF-16 문자열을 UTF-8로 변환하지 못했습니다.");
    }
    std::string result(static_cast<std::size_t>(size), '\0');
    WideCharToMultiByte(
        CP_UTF8,
        WC_ERR_INVALID_CHARS,
        value.data(),
        static_cast<int>(value.size()),
        result.data(),
        size,
        nullptr,
        nullptr
    );
    return result;
}
#endif

}  // namespace utils
