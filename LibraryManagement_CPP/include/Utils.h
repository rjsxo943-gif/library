#pragma once

#include <filesystem>
#include <string>

namespace utils {

std::string trim(const std::string& value);
std::string toLowerAscii(const std::string& value);
std::string toUpperAscii(const std::string& value);
std::string normalizeBookId(const std::string& bookId);
std::string normalizeSearchText(const std::string& text);
std::string validateNonEmpty(const std::string& value, const std::string& fieldName = "입력값");
int parseInteger(const std::string& value, int minValue, int maxValue);
int validatePublicationYear(const std::string& value, int currentYear = 0);
int currentYear();
std::string currentDate();
std::filesystem::path resolveBooksFile(const std::filesystem::path& executablePath = {});

#ifdef _WIN32
std::wstring utf8ToWide(const std::string& value);
std::string wideToUtf8(const std::wstring& value);
#endif

}  // namespace utils
