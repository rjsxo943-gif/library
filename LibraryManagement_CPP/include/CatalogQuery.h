#pragma once

#include "Book.h"
#include "Library.h"

#include <string>
#include <vector>

enum class SearchMode {
    All,
    Title,
    Author,
    BookId,
};

enum class LoanFilter {
    All,
    Available,
    Borrowed,
};

std::vector<const Book*> searchCatalog(
    const Library& library,
    const std::string& keyword = "",
    SearchMode searchMode = SearchMode::All,
    LoanFilter loanFilter = LoanFilter::All
);
