@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

if not exist "build\Release\library_gui.exe" call build_and_test.bat
if errorlevel 1 exit /b 1

set "BOOKS_FILE=..\library_management_python\books.csv"
start "" "build\Release\library_gui.exe" "%BOOKS_FILE%"
