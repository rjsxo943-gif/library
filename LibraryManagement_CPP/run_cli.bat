@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

if not exist "build\Release\library_cli.exe" call build_and_test.bat
if errorlevel 1 exit /b 1

"build\Release\library_cli.exe" "..\library_management_python\books.csv"
pause
