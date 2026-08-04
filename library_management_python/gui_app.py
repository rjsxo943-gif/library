"""공공도서관 스타일의 도서관리 시스템 GUI 애플리케이션."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Iterable

from library import Library, OperationResult
from models import Book
from storage import StorageError, load_books, save_books
from utils import (
    get_current_date,
    normalize_book_id,
    validate_non_empty,
    validate_publication_year,
)

SEARCH_MODES = ("전체", "제목", "저자", "도서번호")
STATUS_FILTERS = ("전체", "대출 가능", "대출 중")

NAVY = "#123B63"
NAVY_DARK = "#0B2947"
BLUE = "#1F5F99"
BLUE_LIGHT = "#EAF3FA"
GREEN = "#1E7A46"
RED = "#B42318"
GRAY_050 = "#F8FAFC"
GRAY_100 = "#F1F5F9"
GRAY_300 = "#CBD5E1"
GRAY_500 = "#64748B"
GRAY_700 = "#334155"
WHITE = "#FFFFFF"


def get_default_books_file() -> Path:
    """실행 방식에 맞는 기본 books.csv 경로를 반환한다."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().with_name("books.csv")

    return Path(__file__).resolve().with_name("books.csv")


def load_library(file_path: str | Path) -> Library:
    """CSV 파일을 읽어 기존 핵심 로직의 Library 객체로 변환한다."""

    library = Library()

    for book in load_books(file_path):
        library.add_book(book)

    return library


def save_library(library: Library, file_path: str | Path) -> int:
    """현재 Library의 전체 도서를 CSV 파일에 저장한다."""

    return save_books(library.list_books(), file_path)


def search_catalog(
    library: Library,
    keyword: str = "",
    search_mode: str = "전체",
    status_filter: str = "전체",
) -> list[Book]:
    """GUI 검색 조건에 맞는 도서를 등록 순서대로 반환한다.

    실제 제목·저자 검색은 Library의 기존 메서드를 호출하므로 CLI와 GUI가
    같은 공백 무시 및 영문 대소문자 무시 규칙을 공유한다.
    """

    if search_mode not in SEARCH_MODES:
        raise ValueError("지원하지 않는 검색 방식입니다.")

    if status_filter not in STATUS_FILTERS:
        raise ValueError("지원하지 않는 대출 상태 필터입니다.")

    normalized_keyword = keyword.strip()
    all_books = library.list_books()

    if not normalized_keyword:
        candidates = all_books
    elif search_mode == "도서번호":
        book = library.find_book_by_id(normalized_keyword)
        candidates = [book] if book is not None else []
    elif search_mode == "제목":
        candidates = library.search_by_title(normalized_keyword)
    elif search_mode == "저자":
        candidates = library.search_by_author(normalized_keyword)
    else:
        title_matches = {id(book) for book in library.search_by_title(normalized_keyword)}
        author_matches = {id(book) for book in library.search_by_author(normalized_keyword)}
        exact_id_book = library.find_book_by_id(normalized_keyword)
        exact_id = id(exact_id_book) if exact_id_book is not None else None

        candidates = [
            book
            for book in all_books
            if id(book) in title_matches
            or id(book) in author_matches
            or id(book) == exact_id
        ]

    if status_filter == "대출 가능":
        return [book for book in candidates if not book.is_borrowed]

    if status_filter == "대출 중":
        return [book for book in candidates if book.is_borrowed]

    return candidates


def book_to_row(book: Book) -> tuple[str, ...]:
    """Book 객체를 Treeview에 표시할 문자열 튜플로 변환한다."""

    return (
        book.book_id,
        book.title,
        book.author,
        book.publisher,
        str(book.year),
        "대출 중" if book.is_borrowed else "대출 가능",
        book.borrower or "-",
        book.borrowed_date or "-",
    )


class BookFormDialog(tk.Toplevel):
    """신규 도서 등록 정보를 입력받는 모달 대화상자."""

    def __init__(self, parent: tk.Misc, library: Library) -> None:
        super().__init__(parent)
        self.library = library
        self.result: Book | None = None
        self.entries: dict[str, ttk.Entry] = {}

        self.title("신규 도서 등록")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(background=WHITE)

        self._build_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Return>", lambda _event: self._submit())
        self.bind("<Escape>", lambda _event: self.destroy())

        self.update_idletasks()
        self._center_on_parent(parent)
        self.entries["book_id"].focus_set()

    def _build_widgets(self) -> None:
        header = tk.Frame(self, background=NAVY, padx=24, pady=18)
        header.pack(fill="x")
        tk.Label(
            header,
            text="신규 도서 등록",
            background=NAVY,
            foreground=WHITE,
            font=("맑은 고딕", 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="도서의 기본 정보를 정확하게 입력해 주세요.",
            background=NAVY,
            foreground="#DCEAF5",
            font=("맑은 고딕", 9),
        ).pack(anchor="w", pady=(4, 0))

        form = ttk.Frame(self, padding=(24, 20))
        form.pack(fill="both", expand=True)

        fields = (
            ("book_id", "도서번호", "예: B0001"),
            ("title", "도서명", "예: 파이썬 기초"),
            ("author", "저자", "예: 김철수"),
            ("publisher", "출판사", "예: 한빛출판사"),
            ("year", "출판연도", "예: 2026"),
        )

        for row_index, (key, label_text, hint) in enumerate(fields):
            ttk.Label(form, text=label_text, style="FormLabel.TLabel").grid(
                row=row_index,
                column=0,
                sticky="w",
                padx=(0, 18),
                pady=8,
            )
            entry = ttk.Entry(form, width=38)
            entry.grid(row=row_index, column=1, sticky="ew", pady=8)
            self.entries[key] = entry
            ttk.Label(form, text=hint, style="Hint.TLabel").grid(
                row=row_index,
                column=2,
                sticky="w",
                padx=(10, 0),
            )

        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(self, padding=(24, 0, 24, 22))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="취소", command=self.destroy).pack(side="right")
        ttk.Button(
            buttons,
            text="등록",
            style="Primary.TButton",
            command=self._submit,
        ).pack(side="right", padx=(0, 8))

    def _submit(self) -> None:
        try:
            book_id = normalize_book_id(
                validate_non_empty(self.entries["book_id"].get(), "도서번호")
            )

            if self.library.is_duplicate_id(book_id):
                raise ValueError("이미 등록된 도서번호입니다.")

            self.result = Book(
                book_id=book_id,
                title=validate_non_empty(self.entries["title"].get(), "도서명"),
                author=validate_non_empty(self.entries["author"].get(), "저자"),
                publisher=validate_non_empty(
                    self.entries["publisher"].get(),
                    "출판사",
                ),
                year=validate_publication_year(self.entries["year"].get()),
            )
        except ValueError as exc:
            messagebox.showwarning("입력 확인", str(exc), parent=self)
            return

        self.destroy()

    def _center_on_parent(self, parent: tk.Misc) -> None:
        parent.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.geometry(f"+{x}+{y}")


class BorrowDialog(tk.Toplevel):
    """대출자 이름을 입력받는 모달 대화상자."""

    def __init__(self, parent: tk.Misc, book: Book) -> None:
        super().__init__(parent)
        self.result: str | None = None

        self.title("도서 대출")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(background=WHITE)

        body = ttk.Frame(self, padding=24)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="도서 대출", style="DialogTitle.TLabel").pack(anchor="w")
        ttk.Label(
            body,
            text=f"{book.title}  ·  {book.author}",
            style="DialogBook.TLabel",
        ).pack(anchor="w", pady=(6, 18))
        ttk.Label(body, text="대출자 이름", style="FormLabel.TLabel").pack(anchor="w")

        self.borrower_entry = ttk.Entry(body, width=36)
        self.borrower_entry.pack(fill="x", pady=(6, 6))
        ttk.Label(
            body,
            text=f"대출일은 오늘 날짜({get_current_date()})로 기록됩니다.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 18))

        buttons = ttk.Frame(body)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="취소", command=self.destroy).pack(side="right")
        ttk.Button(
            buttons,
            text="대출 처리",
            style="Primary.TButton",
            command=self._submit,
        ).pack(side="right", padx=(0, 8))

        self.bind("<Return>", lambda _event: self._submit())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.update_idletasks()
        self._center_on_parent(parent)
        self.borrower_entry.focus_set()

    def _submit(self) -> None:
        try:
            self.result = validate_non_empty(
                self.borrower_entry.get(),
                "대출자 이름",
            )
        except ValueError as exc:
            messagebox.showwarning("입력 확인", str(exc), parent=self)
            return

        self.destroy()

    def _center_on_parent(self, parent: tk.Misc) -> None:
        parent.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.geometry(f"+{x}+{y}")


class LibraryGUI:
    """기존 Library 로직을 사용하는 검색 중심 데스크톱 GUI."""

    def __init__(
        self,
        root: tk.Tk,
        library: Library,
        file_path: str | Path,
    ) -> None:
        self.root = root
        self.library = library
        self.file_path = Path(file_path)
        self.current_books: list[Book] = []

        self.search_mode_var = tk.StringVar(value="전체")
        self.search_text_var = tk.StringVar()
        self.status_filter_var = tk.StringVar(value="전체")
        self.result_summary_var = tk.StringVar()
        self.status_message_var = tk.StringVar(value="도서 데이터를 불러왔습니다.")
        self.detail_vars = {
            "book_id": tk.StringVar(value="-"),
            "title": tk.StringVar(value="도서를 선택해 주세요."),
            "author": tk.StringVar(value="-"),
            "publisher": tk.StringVar(value="-"),
            "year": tk.StringVar(value="-"),
            "status": tk.StringVar(value="-"),
            "borrower": tk.StringVar(value="-"),
            "borrowed_date": tk.StringVar(value="-"),
        }

        self._configure_root()
        self._configure_styles()
        self._build_layout()
        self._bind_events()
        self.refresh_catalog()

    def _configure_root(self) -> None:
        self.root.title("공공도서관 도서관리 시스템")
        self.root.geometry("1280x780")
        self.root.minsize(1040, 680)
        self.root.configure(background=GRAY_050)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=GRAY_050)
        style.configure("Card.TFrame", background=WHITE, relief="flat")
        style.configure(
            "Primary.TButton",
            background=BLUE,
            foreground=WHITE,
            borderwidth=0,
            padding=(16, 9),
            font=("맑은 고딕", 9, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", NAVY), ("pressed", NAVY_DARK)],
            foreground=[("disabled", "#D7E0E8")],
        )
        style.configure(
            "Secondary.TButton",
            background=WHITE,
            foreground=NAVY,
            bordercolor=GRAY_300,
            borderwidth=1,
            padding=(13, 8),
            font=("맑은 고딕", 9, "bold"),
        )
        style.map("Secondary.TButton", background=[("active", BLUE_LIGHT)])
        style.configure(
            "Danger.TButton",
            background=WHITE,
            foreground=RED,
            bordercolor="#F0B5B0",
            borderwidth=1,
            padding=(13, 8),
            font=("맑은 고딕", 9, "bold"),
        )
        style.map("Danger.TButton", background=[("active", "#FFF0EE")])
        style.configure(
            "FormLabel.TLabel",
            background=WHITE,
            foreground=GRAY_700,
            font=("맑은 고딕", 9, "bold"),
        )
        style.configure(
            "Hint.TLabel",
            background=WHITE,
            foreground=GRAY_500,
            font=("맑은 고딕", 8),
        )
        style.configure(
            "DialogTitle.TLabel",
            background=WHITE,
            foreground=NAVY,
            font=("맑은 고딕", 15, "bold"),
        )
        style.configure(
            "DialogBook.TLabel",
            background=WHITE,
            foreground=GRAY_700,
            font=("맑은 고딕", 10),
        )
        style.configure(
            "Treeview",
            background=WHITE,
            fieldbackground=WHITE,
            foreground=GRAY_700,
            rowheight=34,
            borderwidth=0,
            font=("맑은 고딕", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=GRAY_100,
            foreground=NAVY,
            relief="flat",
            font=("맑은 고딕", 9, "bold"),
            padding=(5, 8),
        )
        style.map("Treeview", background=[("selected", "#D8EAF8")])
        style.map("Treeview.Heading", background=[("active", "#E2E8F0")])
        style.configure("TEntry", padding=7)
        style.configure("TCombobox", padding=6)

    def _build_layout(self) -> None:
        self._build_header()

        content = ttk.Frame(self.root, padding=(28, 22, 28, 18))
        content.pack(fill="both", expand=True)

        self._build_search_panel(content)
        self._build_summary_cards(content)

        workspace = ttk.Panedwindow(content, orient="horizontal")
        workspace.pack(fill="both", expand=True, pady=(18, 0))

        catalog_frame = self._build_catalog_panel(workspace)
        detail_frame = self._build_detail_panel(workspace)
        workspace.add(catalog_frame, weight=4)
        workspace.add(detail_frame, weight=1)

        self._build_status_bar()

    def _build_header(self) -> None:
        header = tk.Frame(self.root, background=NAVY, padx=30, pady=20)
        header.pack(fill="x")

        title_group = tk.Frame(header, background=NAVY)
        title_group.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_group,
            text="공공도서관 도서찾기",
            background=NAVY,
            foreground=WHITE,
            font=("맑은 고딕", 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_group,
            text="보유 도서 검색 · 대출 · 반납 · 자료 관리",
            background=NAVY,
            foreground="#DCEAF5",
            font=("맑은 고딕", 10),
        ).pack(anchor="w", pady=(5, 0))

        tk.Label(
            header,
            text="LIBRARY CATALOG",
            background=NAVY,
            foreground="#AFCBE0",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="right", anchor="n", pady=(6, 0))

    def _build_search_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=20)
        panel.pack(fill="x")

        top = ttk.Frame(panel, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(
            top,
            text="통합검색",
            style="DialogTitle.TLabel",
        ).pack(side="left")
        ttk.Label(
            top,
            text="띄어쓰기와 영문 대소문자는 구분하지 않습니다.",
            style="Hint.TLabel",
        ).pack(side="left", padx=(12, 0), pady=(5, 0))

        controls = ttk.Frame(panel, style="Card.TFrame")
        controls.pack(fill="x", pady=(14, 0))

        mode_box = ttk.Combobox(
            controls,
            textvariable=self.search_mode_var,
            values=SEARCH_MODES,
            state="readonly",
            width=11,
        )
        mode_box.pack(side="left")

        self.search_entry = ttk.Entry(
            controls,
            textvariable=self.search_text_var,
            font=("맑은 고딕", 11),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=8)

        ttk.Button(
            controls,
            text="검색",
            style="Primary.TButton",
            command=self.refresh_catalog,
        ).pack(side="left")
        ttk.Button(
            controls,
            text="검색 초기화",
            style="Secondary.TButton",
            command=self.reset_search,
        ).pack(side="left", padx=(8, 0))

        ttk.Label(
            controls,
            text="대출 상태",
            style="FormLabel.TLabel",
        ).pack(side="left", padx=(18, 8))
        status_box = ttk.Combobox(
            controls,
            textvariable=self.status_filter_var,
            values=STATUS_FILTERS,
            state="readonly",
            width=11,
        )
        status_box.pack(side="left")

    def _build_summary_cards(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent)
        container.pack(fill="x", pady=(16, 0))

        self.total_count_var = tk.StringVar(value="0")
        self.available_count_var = tk.StringVar(value="0")
        self.borrowed_count_var = tk.StringVar(value="0")

        cards = (
            ("전체 보유 도서", self.total_count_var, NAVY),
            ("대출 가능", self.available_count_var, GREEN),
            ("대출 중", self.borrowed_count_var, RED),
        )

        for index, (title, variable, accent) in enumerate(cards):
            card = tk.Frame(
                container,
                background=WHITE,
                highlightthickness=1,
                highlightbackground="#E2E8F0",
                padx=18,
                pady=13,
            )
            card.grid(row=0, column=index, sticky="ew", padx=(0, 10 if index < 2 else 0))
            tk.Label(
                card,
                text=title,
                background=WHITE,
                foreground=GRAY_500,
                font=("맑은 고딕", 9, "bold"),
            ).pack(anchor="w")
            tk.Label(
                card,
                textvariable=variable,
                background=WHITE,
                foreground=accent,
                font=("맑은 고딕", 19, "bold"),
            ).pack(anchor="w", pady=(3, 0))
            container.columnconfigure(index, weight=1)

    def _build_catalog_panel(self, parent: ttk.Panedwindow) -> ttk.Frame:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=(18, 16))

        toolbar = ttk.Frame(panel, style="Card.TFrame")
        toolbar.pack(fill="x", pady=(0, 12))
        ttk.Label(
            toolbar,
            text="검색 결과",
            style="DialogTitle.TLabel",
        ).pack(side="left")
        ttk.Label(
            toolbar,
            textvariable=self.result_summary_var,
            style="Hint.TLabel",
        ).pack(side="left", padx=(10, 0), pady=(5, 0))

        ttk.Button(
            toolbar,
            text="신규 도서 등록",
            style="Primary.TButton",
            command=self.open_register_dialog,
        ).pack(side="right")
        ttk.Button(
            toolbar,
            text="새로고침",
            style="Secondary.TButton",
            command=self.refresh_catalog,
        ).pack(side="right", padx=(0, 8))

        tree_container = ttk.Frame(panel, style="Card.TFrame")
        tree_container.pack(fill="both", expand=True)

        columns = (
            "book_id",
            "title",
            "author",
            "publisher",
            "year",
            "status",
            "borrower",
            "borrowed_date",
        )
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        headings = {
            "book_id": "도서번호",
            "title": "도서명",
            "author": "저자",
            "publisher": "출판사",
            "year": "연도",
            "status": "대출상태",
            "borrower": "대출자",
            "borrowed_date": "대출일",
        }
        widths = {
            "book_id": 90,
            "title": 240,
            "author": 105,
            "publisher": 120,
            "year": 60,
            "status": 85,
            "borrower": 95,
            "borrowed_date": 100,
        }

        for column in columns:
            self.tree.heading(
                column,
                text=headings[column],
                command=lambda name=column: self.sort_catalog(name),
            )
            self.tree.column(
                column,
                width=widths[column],
                minwidth=55,
                anchor="center" if column in {"year", "status", "borrowed_date"} else "w",
            )

        vertical_scrollbar = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self.tree.yview,
        )
        horizontal_scrollbar = ttk.Scrollbar(
            tree_container,
            orient="horizontal",
            command=self.tree.xview,
        )
        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree.tag_configure("available", foreground=GREEN)
        self.tree.tag_configure("borrowed", foreground=RED)

        return panel

    def _build_detail_panel(self, parent: ttk.Panedwindow) -> ttk.Frame:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=20)

        ttk.Label(panel, text="도서 상세정보", style="DialogTitle.TLabel").pack(anchor="w")
        ttk.Separator(panel).pack(fill="x", pady=14)

        title = ttk.Label(
            panel,
            textvariable=self.detail_vars["title"],
            wraplength=270,
            justify="left",
            style="DialogBook.TLabel",
        )
        title.pack(anchor="w", fill="x", pady=(0, 14))

        detail_rows = (
            ("도서번호", "book_id"),
            ("저자", "author"),
            ("출판사", "publisher"),
            ("출판연도", "year"),
            ("대출상태", "status"),
            ("대출자", "borrower"),
            ("대출일", "borrowed_date"),
        )

        for label_text, key in detail_rows:
            row = ttk.Frame(panel, style="Card.TFrame")
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label_text, style="FormLabel.TLabel").pack(side="left")
            ttk.Label(
                row,
                textvariable=self.detail_vars[key],
                style="Hint.TLabel",
                wraplength=165,
                justify="right",
            ).pack(side="right")

        ttk.Separator(panel).pack(fill="x", pady=16)

        self.borrow_button = ttk.Button(
            panel,
            text="선택 도서 대출",
            style="Primary.TButton",
            command=self.borrow_selected_book,
        )
        self.borrow_button.pack(fill="x", pady=(0, 8))

        self.return_button = ttk.Button(
            panel,
            text="선택 도서 반납",
            style="Secondary.TButton",
            command=self.return_selected_book,
        )
        self.return_button.pack(fill="x", pady=(0, 8))

        self.delete_button = ttk.Button(
            panel,
            text="선택 도서 삭제",
            style="Danger.TButton",
            command=self.delete_selected_book,
        )
        self.delete_button.pack(fill="x")

        ttk.Label(
            panel,
            text="목록에서 도서를 선택하면 대출·반납·삭제 기능을 사용할 수 있습니다.",
            wraplength=260,
            justify="left",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(18, 0))

        self._set_action_state(None)
        return panel

    def _build_status_bar(self) -> None:
        bar = tk.Frame(self.root, background=NAVY_DARK, padx=16, pady=7)
        bar.pack(fill="x", side="bottom")
        tk.Label(
            bar,
            textvariable=self.status_message_var,
            background=NAVY_DARK,
            foreground="#DCEAF5",
            font=("맑은 고딕", 9),
        ).pack(side="left")
        tk.Label(
            bar,
            text="Enter 검색  ·  Ctrl+N 도서 등록  ·  F5 새로고침",
            background=NAVY_DARK,
            foreground="#9FBBD0",
            font=("맑은 고딕", 8),
        ).pack(side="right")

    def _bind_events(self) -> None:
        self.search_entry.bind("<Return>", lambda _event: self.refresh_catalog())
        self.search_mode_var.trace_add("write", lambda *_args: self.refresh_catalog())
        self.status_filter_var.trace_add("write", lambda *_args: self.refresh_catalog())
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", lambda _event: self.borrow_selected_book())
        self.root.bind("<Control-n>", lambda _event: self.open_register_dialog())
        self.root.bind("<F5>", lambda _event: self.refresh_catalog())

    def refresh_catalog(self) -> None:
        """검색 조건을 적용해 표·통계·상세 패널을 갱신한다."""

        self.current_books = search_catalog(
            self.library,
            self.search_text_var.get(),
            self.search_mode_var.get(),
            self.status_filter_var.get(),
        )

        selected_id = self.get_selected_book_id()
        self.tree.delete(*self.tree.get_children())

        for book in self.current_books:
            tag = "borrowed" if book.is_borrowed else "available"
            self.tree.insert(
                "",
                "end",
                iid=book.book_id,
                values=book_to_row(book),
                tags=(tag,),
            )

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)
            self.tree.focus(selected_id)
        else:
            self._show_book_details(None)

        all_books = self.library.list_books()
        available_count = sum(not book.is_borrowed for book in all_books)
        borrowed_count = len(all_books) - available_count

        self.total_count_var.set(f"{len(all_books)}권")
        self.available_count_var.set(f"{available_count}권")
        self.borrowed_count_var.set(f"{borrowed_count}권")
        self.result_summary_var.set(f"{len(self.current_books)}건")
        self.status_message_var.set(
            f"검색 결과 {len(self.current_books)}건 · 전체 보유 도서 {len(all_books)}권"
        )

    def reset_search(self) -> None:
        self.search_mode_var.set("전체")
        self.status_filter_var.set("전체")
        self.search_text_var.set("")
        self.search_entry.focus_set()
        self.refresh_catalog()

    def sort_catalog(self, column: str) -> None:
        """현재 표시된 목록을 선택한 열 기준으로 정렬한다."""

        children = list(self.tree.get_children())
        reverse = getattr(self, "_sort_state", (None, False))[0] == column and not getattr(
            self,
            "_sort_state",
            (None, False),
        )[1]

        column_index = self.tree["columns"].index(column)

        def sort_key(item_id: str) -> object:
            value = self.tree.item(item_id, "values")[column_index]
            return int(value) if column == "year" and str(value).isdigit() else str(value).casefold()

        children.sort(key=sort_key, reverse=reverse)

        for index, item_id in enumerate(children):
            self.tree.move(item_id, "", index)

        self._sort_state = (column, reverse)

    def on_tree_select(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self._show_book_details(self.get_selected_book())

    def get_selected_book_id(self) -> str | None:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def get_selected_book(self) -> Book | None:
        book_id = self.get_selected_book_id()
        return self.library.find_book_by_id(book_id) if book_id else None

    def _show_book_details(self, book: Book | None) -> None:
        if book is None:
            values = {
                "book_id": "-",
                "title": "도서를 선택해 주세요.",
                "author": "-",
                "publisher": "-",
                "year": "-",
                "status": "-",
                "borrower": "-",
                "borrowed_date": "-",
            }
        else:
            values = {
                "book_id": book.book_id,
                "title": book.title,
                "author": book.author,
                "publisher": book.publisher,
                "year": str(book.year),
                "status": "대출 중" if book.is_borrowed else "대출 가능",
                "borrower": book.borrower or "-",
                "borrowed_date": book.borrowed_date or "-",
            }

        for key, value in values.items():
            self.detail_vars[key].set(value)

        self._set_action_state(book)

    def _set_action_state(self, book: Book | None) -> None:
        if book is None:
            self.borrow_button.state(["disabled"])
            self.return_button.state(["disabled"])
            self.delete_button.state(["disabled"])
            return

        self.delete_button.state(["!disabled"])

        if book.is_borrowed:
            self.borrow_button.state(["disabled"])
            self.return_button.state(["!disabled"])
        else:
            self.borrow_button.state(["!disabled"])
            self.return_button.state(["disabled"])

    def open_register_dialog(self) -> None:
        dialog = BookFormDialog(self.root, self.library)
        self.root.wait_window(dialog)

        if dialog.result is None:
            return

        if not self.library.add_book(dialog.result):
            messagebox.showerror("등록 실패", "도서를 등록하지 못했습니다.", parent=self.root)
            return

        if self._save_changes("도서가 정상적으로 등록되었습니다."):
            self.reset_search()
            self._select_book(dialog.result.book_id)

    def borrow_selected_book(self) -> None:
        book = self.get_selected_book()

        if book is None:
            messagebox.showinfo("도서 선택", "대출할 도서를 먼저 선택해 주세요.", parent=self.root)
            return

        if book.is_borrowed:
            messagebox.showwarning(
                "대출 불가",
                f"이미 대출 중인 도서입니다.\n대출자: {book.borrower}\n대출일: {book.borrowed_date}",
                parent=self.root,
            )
            return

        dialog = BorrowDialog(self.root, book)
        self.root.wait_window(dialog)

        if dialog.result is None:
            return

        result = self.library.borrow_book(
            book.book_id,
            dialog.result,
            get_current_date(),
        )
        self._handle_operation_result(result)

    def return_selected_book(self) -> None:
        book = self.get_selected_book()

        if book is None:
            messagebox.showinfo("도서 선택", "반납할 도서를 먼저 선택해 주세요.", parent=self.root)
            return

        if not messagebox.askyesno(
            "반납 확인",
            f"'{book.title}' 도서를 반납 처리하시겠습니까?",
            parent=self.root,
        ):
            return

        self._handle_operation_result(self.library.return_book(book.book_id))

    def delete_selected_book(self) -> None:
        book = self.get_selected_book()

        if book is None:
            messagebox.showinfo("도서 선택", "삭제할 도서를 먼저 선택해 주세요.", parent=self.root)
            return

        if book.is_borrowed:
            messagebox.showwarning(
                "삭제 불가",
                "대출 중인 도서는 삭제할 수 없습니다. 먼저 반납 처리해 주세요.",
                parent=self.root,
            )
            return

        if not messagebox.askyesno(
            "도서 삭제 확인",
            f"다음 도서를 삭제하시겠습니까?\n\n{book.title}\n{book.author} · {book.publisher}",
            icon="warning",
            parent=self.root,
        ):
            return

        self._handle_operation_result(self.library.delete_book(book.book_id))

    def _handle_operation_result(self, result: OperationResult) -> None:
        if not result.success:
            messagebox.showwarning("처리 실패", result.message, parent=self.root)
            return

        selected_id = result.book.book_id if result.book is not None else None

        if self._save_changes(result.message):
            self.refresh_catalog()
            if selected_id and self.tree.exists(selected_id):
                self._select_book(selected_id)
            messagebox.showinfo("처리 완료", result.message, parent=self.root)

    def _save_changes(self, success_message: str) -> bool:
        try:
            saved_count = save_library(self.library, self.file_path)
        except StorageError as exc:
            messagebox.showerror(
                "저장 오류",
                f"도서 데이터를 저장하지 못했습니다.\n\n{exc}",
                parent=self.root,
            )
            self.status_message_var.set("저장 오류가 발생했습니다.")
            return False

        self.status_message_var.set(f"{success_message} · {saved_count}권 저장 완료")
        return True

    def _select_book(self, book_id: str) -> None:
        if not self.tree.exists(book_id):
            return

        self.tree.selection_set(book_id)
        self.tree.focus(book_id)
        self.tree.see(book_id)
        self._show_book_details(self.library.find_book_by_id(book_id))

    def on_close(self) -> None:
        try:
            save_library(self.library, self.file_path)
        except StorageError as exc:
            close_anyway = messagebox.askyesno(
                "저장 오류",
                f"종료 전 저장에 실패했습니다.\n\n{exc}\n\n그래도 종료하시겠습니까?",
                icon="warning",
                parent=self.root,
            )
            if not close_anyway:
                return

        self.root.destroy()


def main(file_path: str | Path | None = None) -> int:
    """CSV 데이터를 불러와 GUI 애플리케이션을 실행한다."""

    target_file = Path(file_path) if file_path is not None else get_default_books_file()

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"GUI 실행 오류: {exc}")
        return 1

    root.withdraw()

    try:
        library = load_library(target_file)
    except StorageError as exc:
        messagebox.showerror(
            "불러오기 오류",
            f"기존 데이터 파일을 읽지 못했습니다.\n원본 파일 보호를 위해 프로그램을 종료합니다.\n\n{exc}",
            parent=root,
        )
        root.destroy()
        return 1

    root.deiconify()
    LibraryGUI(root, library, target_file)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
