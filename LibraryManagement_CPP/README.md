# 도서관리 시스템 — C++

Python 버전과 동일한 `Book → Library → Storage → UI` 구조를 C++17로 구현한 버전입니다.
두 프로그램은 동일한 UTF-8 `books.csv`를 사용합니다.

## 제공 프로그램

- `library_cli`: 콘솔 버전
- `library_gui`: Windows Win32 GUI 버전
- `library_tests`: 핵심 로직 및 CSV 호환성 테스트

GUI는 Qt 같은 외부 프레임워크 없이 Windows 기본 API로 작성했습니다.

## 빠른 실행

Visual Studio Installer에서 다음 항목이 필요합니다.

- C++를 사용한 데스크톱 개발
- Windows SDK
- CMake tools for Windows

먼저 다음 파일을 실행합니다.

```text
build_and_test.bat
```

빌드 후 GUI 실행:

```text
run_gui.bat
```

콘솔 실행:

```text
run_cli.bat
```

두 실행 스크립트는 기본적으로 Python 버전의 다음 파일을 함께 사용합니다.

```text
../library_management_python/books.csv
```

## 직접 명령으로 빌드

```powershell
cd LibraryManagement_CPP
cmake -S . -B build -A x64
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

## 주요 기능

- 도서 등록, 전체 조회
- 도서번호·제목·저자 검색
- 제목·저자 검색 시 띄어쓰기와 영문 대소문자 무시
- 대출 및 오늘 날짜 자동 기록
- 반납 및 대출 정보 초기화
- 대출 중인 도서 삭제 차단
- 삭제 전 확인
- 대출 상태 필터
- 검색 결과 열 정렬
- CSV 자동 저장과 불러오기
- 손상된 CSV 행만 건너뛰기
- 임시 파일과 백업을 이용한 안전한 저장

## CSV 규격

```csv
book_id,title,author,publisher,year,is_borrowed,borrower,borrowed_date
```

- UTF-8
- 대출 상태: `true` / `false`
- 날짜: `YYYY-MM-DD`
- 쉼표, 큰따옴표, 줄바꿈이 포함된 필드 인용 처리
