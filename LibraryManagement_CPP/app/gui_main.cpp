#ifdef _WIN32

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <CommCtrl.h>
#include <Shellapi.h>

#include "Book.h"
#include "CatalogQuery.h"
#include "Library.h"
#include "Storage.h"
#include "Utils.h"

#include <algorithm>
#include <filesystem>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "shell32.lib")

namespace {

constexpr wchar_t kMainClass[] = L"LibraryManagementCppMain";
constexpr wchar_t kRegisterClass[] = L"LibraryManagementCppRegister";
constexpr wchar_t kBorrowClass[] = L"LibraryManagementCppBorrow";

constexpr COLORREF kNavy = RGB(18, 59, 99);
constexpr COLORREF kNavyDark = RGB(11, 41, 71);
constexpr COLORREF kWhite = RGB(255, 255, 255);
constexpr COLORREF kBackground = RGB(248, 250, 252);
constexpr COLORREF kGray = RGB(100, 116, 139);
constexpr COLORREF kGreen = RGB(30, 122, 70);
constexpr COLORREF kRed = RGB(180, 35, 24);

constexpr int IDC_SEARCH_MODE = 1001;
constexpr int IDC_SEARCH_EDIT = 1002;
constexpr int IDC_SEARCH = 1003;
constexpr int IDC_RESET = 1004;
constexpr int IDC_STATUS_FILTER = 1005;
constexpr int IDC_REGISTER = 1006;
constexpr int IDC_REFRESH = 1007;
constexpr int IDC_LIST = 1008;
constexpr int IDC_BORROW = 1009;
constexpr int IDC_RETURN = 1010;
constexpr int IDC_DELETE = 1011;

constexpr int IDC_REG_OK = 2006;
constexpr int IDC_REG_CANCEL = 2007;
constexpr int IDC_BORROW_OK = 3002;
constexpr int IDC_BORROW_CANCEL = 3003;

HFONT createFont(int height, int weight = FW_NORMAL) {
    return CreateFontW(-height, 0, 0, 0, weight, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, L"Malgun Gothic");
}

void setFont(HWND window, HFONT font) {
    SendMessageW(window, WM_SETFONT, reinterpret_cast<WPARAM>(font), TRUE);
}

std::wstring getText(HWND window) {
    const int length = GetWindowTextLengthW(window);
    std::wstring value(static_cast<std::size_t>(length + 1), L'\0');
    if (length > 0) {
        GetWindowTextW(window, value.data(), length + 1);
    }
    value.resize(static_cast<std::size_t>(length));
    return value;
}

void setText(HWND window, const std::string& value) {
    const std::wstring wide = utils::utf8ToWide(value);
    SetWindowTextW(window, wide.c_str());
}

void centerWindow(HWND window, HWND parent) {
    RECT windowRect{};
    RECT parentRect{};
    GetWindowRect(window, &windowRect);
    GetWindowRect(parent, &parentRect);
    const int width = windowRect.right - windowRect.left;
    const int height = windowRect.bottom - windowRect.top;
    const int x = parentRect.left + ((parentRect.right - parentRect.left) - width) / 2;
    const int y = parentRect.top + ((parentRect.bottom - parentRect.top) - height) / 2;
    SetWindowPos(window, nullptr, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER);
}

struct RegisterState {
    Library* library{};
    std::optional<Book> result;
    HWND parent{};
    HWND edits[5]{};
    HFONT font{};
    HFONT boldFont{};
};

LRESULT CALLBACK registerWndProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    auto* state = reinterpret_cast<RegisterState*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    if (message == WM_NCCREATE) {
        auto* create = reinterpret_cast<CREATESTRUCTW*>(lParam);
        state = static_cast<RegisterState*>(create->lpCreateParams);
        SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(state));
    }

    switch (message) {
    case WM_CREATE: {
        state->font = createFont(16);
        state->boldFont = createFont(17, FW_BOLD);
        HWND title = CreateWindowExW(0, L"STATIC", L"신규 도서 등록", WS_CHILD | WS_VISIBLE,
            24, 18, 380, 28, window, nullptr, nullptr, nullptr);
        setFont(title, state->boldFont);

        const wchar_t* labels[] = {L"도서번호", L"도서명", L"저자", L"출판사", L"출판연도"};
        for (int index = 0; index < 5; ++index) {
            HWND label = CreateWindowExW(0, L"STATIC", labels[index], WS_CHILD | WS_VISIBLE,
                24, 65 + index * 48, 90, 26, window, nullptr, nullptr, nullptr);
            setFont(label, state->font);
            state->edits[index] = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
                WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_AUTOHSCROLL,
                120, 61 + index * 48, 300, 30, window, nullptr, nullptr, nullptr);
            setFont(state->edits[index], state->font);
        }

        HWND ok = CreateWindowExW(0, L"BUTTON", L"등록",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_DEFPUSHBUTTON,
            250, 315, 82, 34, window, reinterpret_cast<HMENU>(IDC_REG_OK), nullptr, nullptr);
        HWND cancel = CreateWindowExW(0, L"BUTTON", L"취소",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP,
            340, 315, 82, 34, window, reinterpret_cast<HMENU>(IDC_REG_CANCEL), nullptr, nullptr);
        setFont(ok, state->font);
        setFont(cancel, state->font);
        SetFocus(state->edits[0]);
        return 0;
    }
    case WM_COMMAND:
        if (LOWORD(wParam) == IDC_REG_OK) {
            try {
                const std::string bookId = utils::normalizeBookId(utils::validateNonEmpty(
                    utils::wideToUtf8(getText(state->edits[0])), "도서번호"));
                if (state->library->isDuplicateId(bookId)) {
                    throw std::invalid_argument("이미 등록된 도서번호입니다.");
                }
                state->result.emplace(
                    bookId,
                    utils::validateNonEmpty(utils::wideToUtf8(getText(state->edits[1])), "도서명"),
                    utils::validateNonEmpty(utils::wideToUtf8(getText(state->edits[2])), "저자"),
                    utils::validateNonEmpty(utils::wideToUtf8(getText(state->edits[3])), "출판사"),
                    utils::validatePublicationYear(utils::wideToUtf8(getText(state->edits[4])))
                );
                DestroyWindow(window);
            } catch (const std::exception& exception) {
                MessageBoxW(window, utils::utf8ToWide(exception.what()).c_str(),
                    L"입력 확인", MB_OK | MB_ICONWARNING);
            }
            return 0;
        }
        if (LOWORD(wParam) == IDC_REG_CANCEL) {
            DestroyWindow(window);
            return 0;
        }
        break;
    case WM_CLOSE:
        DestroyWindow(window);
        return 0;
    case WM_DESTROY:
        DeleteObject(state->font);
        DeleteObject(state->boldFont);
        EnableWindow(state->parent, TRUE);
        SetForegroundWindow(state->parent);
        return 0;
    default:
        break;
    }
    return DefWindowProcW(window, message, wParam, lParam);
}

std::optional<Book> showRegisterDialog(HWND parent, Library& library, HINSTANCE instance) {
    static bool registered = false;
    if (!registered) {
        WNDCLASSW windowClass{};
        windowClass.lpfnWndProc = registerWndProc;
        windowClass.hInstance = instance;
        windowClass.lpszClassName = kRegisterClass;
        windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
        windowClass.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_WINDOW + 1);
        RegisterClassW(&windowClass);
        registered = true;
    }

    RegisterState state;
    state.library = &library;
    state.parent = parent;
    EnableWindow(parent, FALSE);
    HWND dialog = CreateWindowExW(WS_EX_DLGMODALFRAME, kRegisterClass, L"신규 도서 등록",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU, CW_USEDEFAULT, CW_USEDEFAULT,
        470, 405, parent, nullptr, instance, &state);
    centerWindow(dialog, parent);
    ShowWindow(dialog, SW_SHOW);
    UpdateWindow(dialog);

    MSG message{};
    while (IsWindow(dialog) && GetMessageW(&message, nullptr, 0, 0) > 0) {
        if (!IsDialogMessageW(dialog, &message)) {
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
    }
    return state.result;
}

struct BorrowState {
    const Book* book{};
    std::optional<std::string> result;
    HWND parent{};
    HWND edit{};
    HFONT font{};
    HFONT boldFont{};
};

LRESULT CALLBACK borrowWndProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    auto* state = reinterpret_cast<BorrowState*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    if (message == WM_NCCREATE) {
        auto* create = reinterpret_cast<CREATESTRUCTW*>(lParam);
        state = static_cast<BorrowState*>(create->lpCreateParams);
        SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(state));
    }

    switch (message) {
    case WM_CREATE: {
        state->font = createFont(16);
        state->boldFont = createFont(17, FW_BOLD);
        HWND title = CreateWindowExW(0, L"STATIC", L"도서 대출", WS_CHILD | WS_VISIBLE,
            24, 20, 340, 28, window, nullptr, nullptr, nullptr);
        setFont(title, state->boldFont);
        const std::wstring bookText = utils::utf8ToWide(state->book->title() + " · " + state->book->author());
        HWND book = CreateWindowExW(0, L"STATIC", bookText.c_str(), WS_CHILD | WS_VISIBLE,
            24, 58, 360, 28, window, nullptr, nullptr, nullptr);
        setFont(book, state->font);
        HWND label = CreateWindowExW(0, L"STATIC", L"대출자 이름", WS_CHILD | WS_VISIBLE,
            24, 102, 120, 24, window, nullptr, nullptr, nullptr);
        setFont(label, state->font);
        state->edit = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_AUTOHSCROLL,
            24, 130, 360, 32, window, nullptr, nullptr, nullptr);
        setFont(state->edit, state->font);
        const std::wstring dateText = L"대출일: " + utils::utf8ToWide(utils::currentDate());
        HWND date = CreateWindowExW(0, L"STATIC", dateText.c_str(), WS_CHILD | WS_VISIBLE,
            24, 174, 250, 24, window, nullptr, nullptr, nullptr);
        setFont(date, state->font);
        HWND ok = CreateWindowExW(0, L"BUTTON", L"대출 처리",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_DEFPUSHBUTTON,
            208, 215, 92, 34, window, reinterpret_cast<HMENU>(IDC_BORROW_OK), nullptr, nullptr);
        HWND cancel = CreateWindowExW(0, L"BUTTON", L"취소",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP,
            308, 215, 76, 34, window, reinterpret_cast<HMENU>(IDC_BORROW_CANCEL), nullptr, nullptr);
        setFont(ok, state->font);
        setFont(cancel, state->font);
        SetFocus(state->edit);
        return 0;
    }
    case WM_COMMAND:
        if (LOWORD(wParam) == IDC_BORROW_OK) {
            try {
                state->result = utils::validateNonEmpty(
                    utils::wideToUtf8(getText(state->edit)), "대출자 이름");
                DestroyWindow(window);
            } catch (const std::exception& exception) {
                MessageBoxW(window, utils::utf8ToWide(exception.what()).c_str(),
                    L"입력 확인", MB_OK | MB_ICONWARNING);
            }
            return 0;
        }
        if (LOWORD(wParam) == IDC_BORROW_CANCEL) {
            DestroyWindow(window);
            return 0;
        }
        break;
    case WM_CLOSE:
        DestroyWindow(window);
        return 0;
    case WM_DESTROY:
        DeleteObject(state->font);
        DeleteObject(state->boldFont);
        EnableWindow(state->parent, TRUE);
        SetForegroundWindow(state->parent);
        return 0;
    default:
        break;
    }
    return DefWindowProcW(window, message, wParam, lParam);
}

std::optional<std::string> showBorrowDialog(HWND parent, const Book& book, HINSTANCE instance) {
    static bool registered = false;
    if (!registered) {
        WNDCLASSW windowClass{};
        windowClass.lpfnWndProc = borrowWndProc;
        windowClass.hInstance = instance;
        windowClass.lpszClassName = kBorrowClass;
        windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
        windowClass.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_WINDOW + 1);
        RegisterClassW(&windowClass);
        registered = true;
    }

    BorrowState state;
    state.book = &book;
    state.parent = parent;
    EnableWindow(parent, FALSE);
    HWND dialog = CreateWindowExW(WS_EX_DLGMODALFRAME, kBorrowClass, L"도서 대출",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU, CW_USEDEFAULT, CW_USEDEFAULT,
        435, 305, parent, nullptr, instance, &state);
    centerWindow(dialog, parent);
    ShowWindow(dialog, SW_SHOW);
    UpdateWindow(dialog);

    MSG message{};
    while (IsWindow(dialog) && GetMessageW(&message, nullptr, 0, 0) > 0) {
        if (!IsDialogMessageW(dialog, &message)) {
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
    }
    return state.result;
}

class LibraryGuiApp {
public:
    LibraryGuiApp(HINSTANCE instance, std::filesystem::path filePath, Library library)
        : instance_(instance), filePath_(std::move(filePath)), library_(std::move(library)) {
        normalFont_ = createFont(15);
        smallFont_ = createFont(13);
        boldFont_ = createFont(17, FW_BOLD);
        titleFont_ = createFont(27, FW_BOLD);
        headerBrush_ = CreateSolidBrush(kNavy);
        statusBrush_ = CreateSolidBrush(kNavyDark);
        whiteBrush_ = CreateSolidBrush(kWhite);
        backgroundBrush_ = CreateSolidBrush(kBackground);
    }

    ~LibraryGuiApp() {
        DeleteObject(normalFont_);
        DeleteObject(smallFont_);
        DeleteObject(boldFont_);
        DeleteObject(titleFont_);
        DeleteObject(headerBrush_);
        DeleteObject(statusBrush_);
        DeleteObject(whiteBrush_);
        DeleteObject(backgroundBrush_);
    }

    bool create(int showCommand) {
        WNDCLASSEXW windowClass{};
        windowClass.cbSize = sizeof(windowClass);
        windowClass.lpfnWndProc = &LibraryGuiApp::windowProc;
        windowClass.hInstance = instance_;
        windowClass.lpszClassName = kMainClass;
        windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
        windowClass.hIcon = LoadIconW(nullptr, IDI_APPLICATION);
        windowClass.hbrBackground = backgroundBrush_;
        RegisterClassExW(&windowClass);

        window_ = CreateWindowExW(0, kMainClass, L"공공도서관 도서관리 시스템 - C++",
            WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 1280, 800,
            nullptr, nullptr, instance_, this);
        if (window_ == nullptr) {
            return false;
        }
        ShowWindow(window_, showCommand);
        UpdateWindow(window_);
        return true;
    }

    int run() {
        MSG message{};
        while (GetMessageW(&message, nullptr, 0, 0) > 0) {
            if (message.message == WM_KEYDOWN && message.hwnd == searchEdit_ && message.wParam == VK_RETURN) {
                refreshCatalog();
                continue;
            }
            if (message.message == WM_KEYDOWN && message.wParam == VK_F5) {
                refreshCatalog();
                continue;
            }
            if (message.message == WM_KEYDOWN && message.wParam == 'N'
                && (GetKeyState(VK_CONTROL) & 0x8000) != 0) {
                registerBook();
                continue;
            }
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
        return static_cast<int>(message.wParam);
    }

private:
    static LRESULT CALLBACK windowProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
        LibraryGuiApp* app = reinterpret_cast<LibraryGuiApp*>(GetWindowLongPtrW(window, GWLP_USERDATA));
        if (message == WM_NCCREATE) {
            auto* create = reinterpret_cast<CREATESTRUCTW*>(lParam);
            app = static_cast<LibraryGuiApp*>(create->lpCreateParams);
            app->window_ = window;
            SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(app));
        }
        return app != nullptr ? app->handleMessage(message, wParam, lParam)
                              : DefWindowProcW(window, message, wParam, lParam);
    }

    LRESULT handleMessage(UINT message, WPARAM wParam, LPARAM lParam) {
        switch (message) {
        case WM_CREATE:
            createControls();
            refreshCatalog();
            return 0;
        case WM_SIZE:
            layoutControls(LOWORD(lParam), HIWORD(lParam));
            return 0;
        case WM_GETMINMAXINFO: {
            auto* info = reinterpret_cast<MINMAXINFO*>(lParam);
            info->ptMinTrackSize = {1040, 680};
            return 0;
        }
        case WM_COMMAND:
            handleCommand(LOWORD(wParam), HIWORD(wParam));
            return 0;
        case WM_NOTIFY:
            return handleNotify(reinterpret_cast<NMHDR*>(lParam));
        case WM_CTLCOLORSTATIC:
            return handleStaticColor(reinterpret_cast<HDC>(wParam), reinterpret_cast<HWND>(lParam));
        case WM_CLOSE:
            if (save(false)) {
                DestroyWindow(window_);
            }
            return 0;
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProcW(window_, message, wParam, lParam);
        }
    }

    HWND makeStatic(const wchar_t* text, DWORD style = SS_LEFT) {
        HWND control = CreateWindowExW(0, L"STATIC", text, WS_CHILD | WS_VISIBLE | style,
            0, 0, 0, 0, window_, nullptr, instance_, nullptr);
        setFont(control, normalFont_);
        return control;
    }

    HWND makeButton(const wchar_t* text, int id) {
        HWND button = CreateWindowExW(0, L"BUTTON", text,
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
            0, 0, 0, 0, window_, reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)), instance_, nullptr);
        setFont(button, normalFont_);
        return button;
    }

    void createControls() {
        headerTitle_ = makeStatic(L"공공도서관 도서찾기");
        headerSubtitle_ = makeStatic(L"보유 도서 검색 · 대출 · 반납 · 자료 관리");
        headerMark_ = makeStatic(L"LIBRARY CATALOG · C++", SS_RIGHT);
        setFont(headerTitle_, titleFont_);
        setFont(headerMark_, smallFont_);
        searchTitle_ = makeStatic(L"통합검색");
        setFont(searchTitle_, boldFont_);
        searchHint_ = makeStatic(L"띄어쓰기와 영문 대소문자는 구분하지 않습니다.");
        setFont(searchHint_, smallFont_);

        searchMode_ = CreateWindowExW(0, WC_COMBOBOXW, L"",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | CBS_DROPDOWNLIST,
            0, 0, 0, 0, window_, reinterpret_cast<HMENU>(IDC_SEARCH_MODE), instance_, nullptr);
        setFont(searchMode_, normalFont_);
        for (const wchar_t* value : {L"전체", L"제목", L"저자", L"도서번호"}) {
            SendMessageW(searchMode_, CB_ADDSTRING, 0, reinterpret_cast<LPARAM>(value));
        }
        SendMessageW(searchMode_, CB_SETCURSEL, 0, 0);

        searchEdit_ = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_AUTOHSCROLL,
            0, 0, 0, 0, window_, reinterpret_cast<HMENU>(IDC_SEARCH_EDIT), instance_, nullptr);
        setFont(searchEdit_, normalFont_);
        searchButton_ = makeButton(L"검색", IDC_SEARCH);
        resetButton_ = makeButton(L"검색 초기화", IDC_RESET);
        statusFilterLabel_ = makeStatic(L"대출 상태");
        statusFilter_ = CreateWindowExW(0, WC_COMBOBOXW, L"",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | CBS_DROPDOWNLIST,
            0, 0, 0, 0, window_, reinterpret_cast<HMENU>(IDC_STATUS_FILTER), instance_, nullptr);
        setFont(statusFilter_, normalFont_);
        for (const wchar_t* value : {L"전체", L"대출 가능", L"대출 중"}) {
            SendMessageW(statusFilter_, CB_ADDSTRING, 0, reinterpret_cast<LPARAM>(value));
        }
        SendMessageW(statusFilter_, CB_SETCURSEL, 0, 0);

        totalLabel_ = makeStatic(L"전체 보유 도서\r\n0권");
        availableLabel_ = makeStatic(L"대출 가능\r\n0권");
        borrowedLabel_ = makeStatic(L"대출 중\r\n0권");
        setFont(totalLabel_, boldFont_);
        setFont(availableLabel_, boldFont_);
        setFont(borrowedLabel_, boldFont_);

        resultTitle_ = makeStatic(L"검색 결과");
        setFont(resultTitle_, boldFont_);
        resultCount_ = makeStatic(L"0건");
        setFont(resultCount_, smallFont_);
        registerButton_ = makeButton(L"신규 도서 등록", IDC_REGISTER);
        refreshButton_ = makeButton(L"새로고침", IDC_REFRESH);

        list_ = CreateWindowExW(WS_EX_CLIENTEDGE, WC_LISTVIEWW, L"",
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | LVS_REPORT | LVS_SINGLESEL | LVS_SHOWSELALWAYS,
            0, 0, 0, 0, window_, reinterpret_cast<HMENU>(IDC_LIST), instance_, nullptr);
        setFont(list_, normalFont_);
        ListView_SetExtendedListViewStyle(list_,
            LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_DOUBLEBUFFER);
        const wchar_t* headings[] = {L"도서번호", L"도서명", L"저자", L"출판사", L"연도", L"대출상태", L"대출자", L"대출일"};
        const int widths[] = {90, 250, 110, 125, 65, 90, 100, 105};
        for (int index = 0; index < 8; ++index) {
            LVCOLUMNW column{};
            column.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM;
            column.pszText = const_cast<wchar_t*>(headings[index]);
            column.cx = widths[index];
            column.iSubItem = index;
            ListView_InsertColumn(list_, index, &column);
        }

        detailTitle_ = makeStatic(L"도서 상세정보");
        setFont(detailTitle_, boldFont_);
        detailText_ = makeStatic(L"도서를 선택해 주세요.");
        borrowButton_ = makeButton(L"선택 도서 대출", IDC_BORROW);
        returnButton_ = makeButton(L"선택 도서 반납", IDC_RETURN);
        deleteButton_ = makeButton(L"선택 도서 삭제", IDC_DELETE);
        EnableWindow(borrowButton_, FALSE);
        EnableWindow(returnButton_, FALSE);
        EnableWindow(deleteButton_, FALSE);
        statusBar_ = makeStatic(L"도서 데이터를 불러왔습니다.");
        setFont(statusBar_, smallFont_);
    }

    void layoutControls(int width, int height) {
        const int margin = 28;
        const int headerHeight = 112;
        const int statusHeight = 30;
        MoveWindow(headerTitle_, margin, 22, 520, 40, TRUE);
        MoveWindow(headerSubtitle_, margin, 66, 520, 26, TRUE);
        MoveWindow(headerMark_, width - 300, 30, 270, 25, TRUE);

        const int searchY = headerHeight + 18;
        MoveWindow(searchTitle_, margin + 18, searchY + 12, 110, 30, TRUE);
        MoveWindow(searchHint_, margin + 125, searchY + 16, 360, 24, TRUE);
        MoveWindow(searchMode_, margin + 18, searchY + 48, 110, 300, TRUE);
        MoveWindow(searchEdit_, margin + 136, searchY + 48, width - 650, 32, TRUE);
        MoveWindow(searchButton_, width - 480, searchY + 48, 100, 32, TRUE);
        MoveWindow(resetButton_, width - 370, searchY + 48, 110, 32, TRUE);
        MoveWindow(statusFilterLabel_, width - 240, searchY + 54, 75, 25, TRUE);
        MoveWindow(statusFilter_, width - 155, searchY + 48, 120, 300, TRUE);

        const int summaryY = searchY + 102;
        const int cardGap = 10;
        const int cardWidth = (width - margin * 2 - cardGap * 2) / 3;
        MoveWindow(totalLabel_, margin, summaryY, cardWidth, 68, TRUE);
        MoveWindow(availableLabel_, margin + cardWidth + cardGap, summaryY, cardWidth, 68, TRUE);
        MoveWindow(borrowedLabel_, margin + (cardWidth + cardGap) * 2, summaryY, cardWidth, 68, TRUE);

        const int workY = summaryY + 86;
        const int workBottom = height - statusHeight - 12;
        const int detailWidth = 300;
        const int listWidth = width - margin * 2 - detailWidth - 16;
        MoveWindow(resultTitle_, margin + 12, workY, 130, 30, TRUE);
        MoveWindow(resultCount_, margin + 130, workY + 5, 80, 22, TRUE);
        MoveWindow(registerButton_, margin + listWidth - 135, workY - 2, 135, 34, TRUE);
        MoveWindow(refreshButton_, margin + listWidth - 235, workY - 2, 92, 34, TRUE);
        MoveWindow(list_, margin, workY + 40, listWidth, workBottom - workY - 40, TRUE);

        const int detailX = margin + listWidth + 16;
        MoveWindow(detailTitle_, detailX + 10, workY, detailWidth - 20, 30, TRUE);
        MoveWindow(detailText_, detailX + 10, workY + 44, detailWidth - 20,
            workBottom - workY - 190, TRUE);
        MoveWindow(borrowButton_, detailX + 10, workBottom - 132, detailWidth - 20, 36, TRUE);
        MoveWindow(returnButton_, detailX + 10, workBottom - 88, detailWidth - 20, 36, TRUE);
        MoveWindow(deleteButton_, detailX + 10, workBottom - 44, detailWidth - 20, 36, TRUE);
        MoveWindow(statusBar_, 0, height - statusHeight, width, statusHeight, TRUE);
        InvalidateRect(window_, nullptr, TRUE);
    }

    void handleCommand(int id, int notification) {
        switch (id) {
        case IDC_SEARCH: refreshCatalog(); break;
        case IDC_RESET:
            SetWindowTextW(searchEdit_, L"");
            SendMessageW(searchMode_, CB_SETCURSEL, 0, 0);
            SendMessageW(statusFilter_, CB_SETCURSEL, 0, 0);
            refreshCatalog();
            SetFocus(searchEdit_);
            break;
        case IDC_SEARCH_MODE:
            if (notification == CBN_SELCHANGE) refreshCatalog();
            break;
        case IDC_STATUS_FILTER:
            if (notification == CBN_SELCHANGE) refreshCatalog();
            break;
        case IDC_REGISTER: registerBook(); break;
        case IDC_REFRESH: refreshCatalog(); break;
        case IDC_BORROW: borrowSelected(); break;
        case IDC_RETURN: returnSelected(); break;
        case IDC_DELETE: deleteSelected(); break;
        default: break;
        }
    }

    LRESULT handleNotify(NMHDR* header) {
        if (header->idFrom != IDC_LIST) return 0;
        if (header->code == LVN_ITEMCHANGED) {
            showBook(selectedBook());
        } else if (header->code == NM_DBLCLK) {
            if (const Book* book = selectedBook(); book != nullptr && book->isAvailable()) {
                borrowSelected();
            }
        } else if (header->code == LVN_COLUMNCLICK) {
            sortByColumn(reinterpret_cast<NMLISTVIEW*>(header)->iSubItem);
        }
        return 0;
    }

    LRESULT handleStaticColor(HDC dc, HWND control) {
        if (control == headerTitle_ || control == headerSubtitle_ || control == headerMark_) {
            SetBkColor(dc, kNavy);
            SetTextColor(dc, control == headerTitle_ ? kWhite : RGB(220, 234, 245));
            return reinterpret_cast<LRESULT>(headerBrush_);
        }
        if (control == statusBar_) {
            SetBkColor(dc, kNavyDark);
            SetTextColor(dc, RGB(220, 234, 245));
            return reinterpret_cast<LRESULT>(statusBrush_);
        }
        if (control == totalLabel_ || control == availableLabel_ || control == borrowedLabel_) {
            SetBkColor(dc, kWhite);
            SetTextColor(dc, control == totalLabel_ ? kNavy : (control == availableLabel_ ? kGreen : kRed));
            return reinterpret_cast<LRESULT>(whiteBrush_);
        }
        SetBkColor(dc, kBackground);
        SetTextColor(dc, control == searchHint_ || control == resultCount_ ? kGray : kNavyDark);
        return reinterpret_cast<LRESULT>(backgroundBrush_);
    }

    SearchMode selectedSearchMode() const {
        switch (static_cast<int>(SendMessageW(searchMode_, CB_GETCURSEL, 0, 0))) {
        case 1: return SearchMode::Title;
        case 2: return SearchMode::Author;
        case 3: return SearchMode::BookId;
        default: return SearchMode::All;
        }
    }

    LoanFilter selectedLoanFilter() const {
        switch (static_cast<int>(SendMessageW(statusFilter_, CB_GETCURSEL, 0, 0))) {
        case 1: return LoanFilter::Available;
        case 2: return LoanFilter::Borrowed;
        default: return LoanFilter::All;
        }
    }

    void refreshCatalog() {
        const std::string selectedId = selectedBookId();
        current_ = searchCatalog(library_, utils::wideToUtf8(getText(searchEdit_)),
            selectedSearchMode(), selectedLoanFilter());
        populateList();
        updateSummary();
        if (!selectedId.empty()) selectBook(selectedId);
        if (ListView_GetSelectedCount(list_) == 0) showBook(nullptr);
    }

    void populateList() {
        ListView_DeleteAllItems(list_);
        for (int row = 0; row < static_cast<int>(current_.size()); ++row) {
            const Book& book = *current_[static_cast<std::size_t>(row)];
            const std::vector<std::string> values = {
                book.bookId(), book.title(), book.author(), book.publisher(),
                std::to_string(book.year()), book.isBorrowed() ? "대출 중" : "대출 가능",
                book.borrower().empty() ? "-" : book.borrower(),
                book.borrowedDate().empty() ? "-" : book.borrowedDate(),
            };
            std::vector<std::wstring> wideValues;
            for (const auto& value : values) wideValues.push_back(utils::utf8ToWide(value));
            LVITEMW item{};
            item.mask = LVIF_TEXT;
            item.iItem = row;
            item.pszText = wideValues[0].data();
            const int inserted = ListView_InsertItem(list_, &item);
            for (int column = 1; column < 8; ++column) {
                ListView_SetItemText(list_, inserted, column,
                    wideValues[static_cast<std::size_t>(column)].data());
            }
        }
    }

    void updateSummary() {
        std::size_t available = 0;
        for (const Book& book : library_.books()) if (book.isAvailable()) ++available;
        const std::size_t borrowed = library_.books().size() - available;
        setText(totalLabel_, "전체 보유 도서\r\n" + std::to_string(library_.books().size()) + "권");
        setText(availableLabel_, "대출 가능\r\n" + std::to_string(available) + "권");
        setText(borrowedLabel_, "대출 중\r\n" + std::to_string(borrowed) + "권");
        setText(resultCount_, std::to_string(current_.size()) + "건");
        setText(statusBar_, "검색 결과 " + std::to_string(current_.size())
            + "건 · 전체 보유 도서 " + std::to_string(library_.books().size())
            + "권 · " + filePath_.string());
    }

    std::string selectedBookId() const {
        const int selected = ListView_GetNextItem(list_, -1, LVNI_SELECTED);
        if (selected < 0) return {};
        wchar_t buffer[256]{};
        ListView_GetItemText(list_, selected, 0, buffer, 256);
        return utils::wideToUtf8(buffer);
    }

    Book* selectedBook() {
        const std::string id = selectedBookId();
        return id.empty() ? nullptr : library_.findBookById(id);
    }

    void showBook(const Book* book) {
        if (book == nullptr) {
            SetWindowTextW(detailText_, L"도서를 선택해 주세요.");
            EnableWindow(borrowButton_, FALSE);
            EnableWindow(returnButton_, FALSE);
            EnableWindow(deleteButton_, FALSE);
            return;
        }
        std::ostringstream text;
        text << book->title() << "\r\n\r\n"
             << "도서번호     " << book->bookId() << "\r\n"
             << "저자             " << book->author() << "\r\n"
             << "출판사         " << book->publisher() << "\r\n"
             << "출판연도     " << book->year() << "\r\n"
             << "대출상태     " << (book->isBorrowed() ? "대출 중" : "대출 가능") << "\r\n"
             << "대출자         " << (book->borrower().empty() ? "-" : book->borrower()) << "\r\n"
             << "대출일         " << (book->borrowedDate().empty() ? "-" : book->borrowedDate());
        setText(detailText_, text.str());
        EnableWindow(borrowButton_, book->isAvailable());
        EnableWindow(returnButton_, book->isBorrowed());
        EnableWindow(deleteButton_, TRUE);
    }

    void selectBook(const std::string& bookId) {
        for (int row = 0; row < ListView_GetItemCount(list_); ++row) {
            wchar_t buffer[256]{};
            ListView_GetItemText(list_, row, 0, buffer, 256);
            if (utils::normalizeBookId(utils::wideToUtf8(buffer)) == utils::normalizeBookId(bookId)) {
                ListView_SetItemState(list_, row, LVIS_SELECTED | LVIS_FOCUSED,
                    LVIS_SELECTED | LVIS_FOCUSED);
                ListView_EnsureVisible(list_, row, FALSE);
                showBook(library_.findBookById(bookId));
                return;
            }
        }
    }

    void sortByColumn(int column) {
        const bool reverse = sortColumn_ == column ? !sortReverse_ : false;
        sortColumn_ = column;
        sortReverse_ = reverse;
        auto value = [column](const Book* book) -> std::string {
            switch (column) {
            case 0: return book->bookId();
            case 1: return book->title();
            case 2: return book->author();
            case 3: return book->publisher();
            case 4: return std::to_string(book->year());
            case 5: return book->isBorrowed() ? "1" : "0";
            case 6: return book->borrower();
            case 7: return book->borrowedDate();
            default: return {};
            }
        };
        std::sort(current_.begin(), current_.end(), [&](const Book* left, const Book* right) {
            const std::string a = utils::normalizeSearchText(value(left));
            const std::string b = utils::normalizeSearchText(value(right));
            return reverse ? a > b : a < b;
        });
        populateList();
    }

    bool save(bool showSuccess = true) {
        try {
            const std::size_t count = storage::saveBooks(library_.listBooks(), filePath_);
            if (showSuccess) setText(statusBar_, "도서 데이터 " + std::to_string(count) + "권을 저장했습니다.");
            return true;
        } catch (const StorageError& exception) {
            MessageBoxW(window_, utils::utf8ToWide(std::string("도서 데이터를 저장하지 못했습니다.\n\n")
                + exception.what()).c_str(), L"저장 오류", MB_OK | MB_ICONERROR);
            return false;
        }
    }

    void handleResult(const OperationResult& result) {
        if (!result.success) {
            MessageBoxW(window_, utils::utf8ToWide(result.message).c_str(),
                L"처리 실패", MB_OK | MB_ICONWARNING);
            return;
        }
        const std::string id = result.book ? result.book->bookId() : "";
        if (save(false)) {
            refreshCatalog();
            if (!id.empty()) selectBook(id);
            MessageBoxW(window_, utils::utf8ToWide(result.message).c_str(),
                L"처리 완료", MB_OK | MB_ICONINFORMATION);
        }
    }

    void registerBook() {
        const auto result = showRegisterDialog(window_, library_, instance_);
        if (!result) return;
        if (!library_.addBook(*result)) {
            MessageBoxW(window_, L"도서를 등록하지 못했습니다.",
                L"등록 실패", MB_OK | MB_ICONERROR);
            return;
        }
        if (save(false)) {
            SetWindowTextW(searchEdit_, L"");
            SendMessageW(searchMode_, CB_SETCURSEL, 0, 0);
            SendMessageW(statusFilter_, CB_SETCURSEL, 0, 0);
            refreshCatalog();
            selectBook(result->bookId());
            MessageBoxW(window_, L"도서가 정상적으로 등록되었습니다.",
                L"등록 완료", MB_OK | MB_ICONINFORMATION);
        }
    }

    void borrowSelected() {
        Book* book = selectedBook();
        if (book == nullptr) {
            MessageBoxW(window_, L"대출할 도서를 먼저 선택해 주세요.",
                L"도서 선택", MB_OK | MB_ICONINFORMATION);
            return;
        }
        if (book->isBorrowed()) {
            MessageBoxW(window_, L"이미 대출 중인 도서입니다.",
                L"대출 불가", MB_OK | MB_ICONWARNING);
            return;
        }
        const auto borrower = showBorrowDialog(window_, *book, instance_);
        if (borrower) handleResult(library_.borrowBook(book->bookId(), *borrower, utils::currentDate()));
    }

    void returnSelected() {
        Book* book = selectedBook();
        if (book == nullptr) {
            MessageBoxW(window_, L"반납할 도서를 먼저 선택해 주세요.",
                L"도서 선택", MB_OK | MB_ICONINFORMATION);
            return;
        }
        const std::wstring question = L"'" + utils::utf8ToWide(book->title())
            + L"' 도서를 반납 처리하시겠습니까?";
        if (MessageBoxW(window_, question.c_str(), L"반납 확인",
                MB_YESNO | MB_ICONQUESTION) == IDYES) {
            handleResult(library_.returnBook(book->bookId()));
        }
    }

    void deleteSelected() {
        Book* book = selectedBook();
        if (book == nullptr) {
            MessageBoxW(window_, L"삭제할 도서를 먼저 선택해 주세요.",
                L"도서 선택", MB_OK | MB_ICONINFORMATION);
            return;
        }
        if (book->isBorrowed()) {
            MessageBoxW(window_, L"대출 중인 도서는 삭제할 수 없습니다. 먼저 반납 처리해 주세요.",
                L"삭제 불가", MB_OK | MB_ICONWARNING);
            return;
        }
        const std::wstring question = L"다음 도서를 삭제하시겠습니까?\n\n"
            + utils::utf8ToWide(book->title() + "\n" + book->author() + " · " + book->publisher());
        if (MessageBoxW(window_, question.c_str(), L"도서 삭제 확인",
                MB_YESNO | MB_ICONWARNING) == IDYES) {
            handleResult(library_.deleteBook(book->bookId()));
        }
    }

    HINSTANCE instance_{};
    HWND window_{};
    std::filesystem::path filePath_;
    Library library_;
    std::vector<const Book*> current_;
    int sortColumn_ = -1;
    bool sortReverse_ = false;

    HFONT normalFont_{};
    HFONT smallFont_{};
    HFONT boldFont_{};
    HFONT titleFont_{};
    HBRUSH headerBrush_{};
    HBRUSH statusBrush_{};
    HBRUSH whiteBrush_{};
    HBRUSH backgroundBrush_{};

    HWND headerTitle_{};
    HWND headerSubtitle_{};
    HWND headerMark_{};
    HWND searchTitle_{};
    HWND searchHint_{};
    HWND searchMode_{};
    HWND searchEdit_{};
    HWND searchButton_{};
    HWND resetButton_{};
    HWND statusFilterLabel_{};
    HWND statusFilter_{};
    HWND totalLabel_{};
    HWND availableLabel_{};
    HWND borrowedLabel_{};
    HWND resultTitle_{};
    HWND resultCount_{};
    HWND registerButton_{};
    HWND refreshButton_{};
    HWND list_{};
    HWND detailTitle_{};
    HWND detailText_{};
    HWND borrowButton_{};
    HWND returnButton_{};
    HWND deleteButton_{};
    HWND statusBar_{};
};

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand) {
    INITCOMMONCONTROLSEX controls{};
    controls.dwSize = sizeof(controls);
    controls.dwICC = ICC_LISTVIEW_CLASSES | ICC_STANDARD_CLASSES;
    InitCommonControlsEx(&controls);

    int argumentCount = 0;
    LPWSTR* arguments = CommandLineToArgvW(GetCommandLineW(), &argumentCount);
    const std::filesystem::path executable = argumentCount > 0 ? arguments[0] : L"";
    const std::filesystem::path filePath = argumentCount > 1
        ? std::filesystem::path(arguments[1])
        : utils::resolveBooksFile(executable);
    LocalFree(arguments);

    Library library;
    try {
        std::vector<std::string> warnings;
        for (const Book& book : storage::loadBooks(filePath, &warnings)) {
            library.addBook(book);
        }
        if (!warnings.empty()) {
            std::ostringstream text;
            text << "일부 CSV 행을 건너뛰었습니다.\n\n";
            for (const auto& warning : warnings) text << warning << '\n';
            MessageBoxW(nullptr, utils::utf8ToWide(text.str()).c_str(),
                L"CSV 경고", MB_OK | MB_ICONWARNING);
        }
    } catch (const StorageError& exception) {
        MessageBoxW(nullptr, utils::utf8ToWide(
            std::string("기존 데이터 파일을 읽지 못했습니다.\n원본 파일 보호를 위해 프로그램을 종료합니다.\n\n")
            + exception.what()).c_str(), L"불러오기 오류", MB_OK | MB_ICONERROR);
        return 1;
    }

    LibraryGuiApp app(instance, filePath, std::move(library));
    if (!app.create(showCommand)) {
        MessageBoxW(nullptr, L"GUI 창을 생성하지 못했습니다.",
            L"실행 오류", MB_OK | MB_ICONERROR);
        return 1;
    }
    return app.run();
}

#else
int main() { return 0; }
#endif
