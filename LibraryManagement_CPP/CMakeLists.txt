cmake_minimum_required(VERSION 3.20)

project(LibraryManagementCpp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(library_core
    src/Book.cpp
    src/Library.cpp
    src/Storage.cpp
    src/Utils.cpp
    src/CatalogQuery.cpp
)

target_include_directories(library_core PUBLIC include)

if(MSVC)
    target_compile_options(library_core PRIVATE /W4 /permissive- /utf-8)
else()
    target_compile_options(library_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(library_cli app/console_main.cpp)
target_link_libraries(library_cli PRIVATE library_core)

if(MSVC)
    target_compile_options(library_cli PRIVATE /W4 /permissive- /utf-8)
endif()

if(WIN32)
    add_executable(library_gui WIN32 app/gui_main.cpp)
    target_link_libraries(library_gui PRIVATE library_core comctl32 shell32)
    if(MSVC)
        target_compile_options(library_gui PRIVATE /W4 /permissive- /utf-8)
        target_compile_definitions(library_gui PRIVATE UNICODE _UNICODE)
    endif()
endif()

enable_testing()
add_executable(library_tests tests/test_main.cpp)
target_link_libraries(library_tests PRIVATE library_core)
if(MSVC)
    target_compile_options(library_tests PRIVATE /W4 /permissive- /utf-8)
endif()
add_test(NAME library_tests COMMAND library_tests)
