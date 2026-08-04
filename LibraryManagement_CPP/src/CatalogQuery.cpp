#include "CatalogQuery.h"

#include "Utils.h"

#include <unordered_set>

std::vector<const Book*> searchCatalog(
    const Library& library,
    const std::string& keyword,
    SearchMode searchMode,
    LoanFilter loanFilter
) {
    const std::string normalizedKeyword = utils::trim(keyword);
    std::vector<const Book*> candidates;

    if (normalizedKeyword.empty()) {
        for (const Book& book : library.books()) {
            candidates.push_back(&book);
        }
    } else if (searchMode == SearchMode::BookId) {
        if (const Book* book = library.findBookById(normalizedKeyword)) {
            candidates.push_back(book);
        }
    } else if (searchMode == SearchMode::Title) {
        candidates = library.searchByTitle(normalizedKeyword);
    } else if (searchMode == SearchMode::Author) {
        candidates = library.searchByAuthor(normalizedKeyword);
    } else {
        std::unordered_set<const Book*> matched;
        for (const Book* book : library.searchByTitle(normalizedKeyword)) {
            matched.insert(book);
        }
        for (const Book* book : library.searchByAuthor(normalizedKeyword)) {
            matched.insert(book);
        }
        if (const Book* book = library.findBookById(normalizedKeyword)) {
            matched.insert(book);
        }

        for (const Book& book : library.books()) {
            if (matched.count(&book) != 0U) {
                candidates.push_back(&book);
            }
        }
    }

    if (loanFilter == LoanFilter::All) {
        return candidates;
    }

    std::vector<const Book*> filtered;
    for (const Book* book : candidates) {
        const bool matches = loanFilter == LoanFilter::Borrowed
            ? book->isBorrowed()
            : book->isAvailable();
        if (matches) {
            filtered.push_back(book);
        }
    }
    return filtered;
}
