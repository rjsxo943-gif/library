@echo off
chcp 65001 > nul
cd /d "%~dp0"

where python > nul 2>&1
if errorlevel 1 (
    echo Python을 찾을 수 없습니다. Python 설치 또는 PATH 설정을 확인해 주세요.
    pause
    exit /b 1
)

python gui_app.py
if errorlevel 1 (
    echo.
    echo GUI 실행 중 오류가 발생했습니다.
    pause
)
