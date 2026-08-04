@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

where cmake > nul 2>&1
if errorlevel 1 (
    echo CMake를 찾을 수 없습니다. Visual Studio Installer에서 C++ 데스크톱 개발과 CMake 도구를 설치해 주세요.
    pause
    exit /b 1
)

cmake -S . -B build -A x64
if errorlevel 1 goto :failed

cmake --build build --config Release
if errorlevel 1 goto :failed

ctest --test-dir build -C Release --output-on-failure
if errorlevel 1 goto :failed

echo.
echo C++ 빌드와 테스트가 모두 완료되었습니다.
exit /b 0

:failed
echo.
echo 빌드 또는 테스트에 실패했습니다.
pause
exit /b 1
