@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%smart-question-tagger\scripts\select_workbench_bank.ps1" -Root "%ROOT%"
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="2" exit /b 0
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] Could not start the selected workbench.
    pause
)
endlocal & exit /b %EXIT_CODE%
