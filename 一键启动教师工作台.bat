@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0"
set "SERVER=%ROOT%smart-question-tagger\scripts\review_server.py"
set "CHECKER=%ROOT%smart-question-tagger\scripts\check_environment.py"
set "BUILDER=%ROOT%smart-question-tagger\scripts\build_review_workbench.py"
set "FRONTEND_DIR=%ROOT%smart-question-tagger\frontend"
set "FRONTEND_BUNDLE=%ROOT%smart-question-tagger\assets\react-shell\workbench-shell.js"
set "FRONTEND_STYLE=%ROOT%smart-question-tagger\assets\react-shell\workbench-shell.css"
set "BANK=%ROOT%output\示例题库_structured"

rem Drag another prepared structured bank folder onto this script to use it.
if not "%~1"=="" set "BANK=%~1"

if not exist "%SERVER%" (
    echo [ERROR] Teacher workbench server not found: %SERVER%
    pause
    exit /b 1
)

if not exist "%CHECKER%" (
    echo [ERROR] Environment checker not found: %CHECKER%
    pause
    exit /b 1
)

if not exist "%BUILDER%" (
    echo [ERROR] Workbench builder not found: %BUILDER%
    pause
    exit /b 1
)

if not exist "%BANK%\review\index.html" (
    echo [ERROR] Workbench is not built: %BANK%\review\index.html
    echo Run the structure, tagging, and workbench build steps first.
    pause
    exit /b 1
)

if not exist "%BANK%\tags\all_question_tags.json" (
    echo [ERROR] Selected folder is not a prepared structured question bank: %BANK%
    echo Missing: %BANK%\tags\all_question_tags.json
    pause
    exit /b 1
)

set "PYTHON_LAUNCHER="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_LAUNCHER=py"
if not defined PYTHON_LAUNCHER (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_LAUNCHER=python"
)

if not defined PYTHON_LAUNCHER (
    echo [ERROR] Python 3.11 or newer was not found.
    pause
    exit /b 1
)

rem Explorer/cmd may not have refreshed user-level variables; load MinerU token without displaying it.
if not defined MINERU_TOKEN (
    for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('MINERU_TOKEN','User')"`) do if not defined MINERU_TOKEN set "MINERU_TOKEN=%%T"
)

if not exist "%FRONTEND_BUNDLE%" (
    where npm >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] React workbench bundle is missing and npm was not found.
        echo Install Node.js 20 or newer, then run this script again.
        pause
        exit /b 1
    )
    echo Building React workbench shell...
    pushd "%FRONTEND_DIR%"
    if exist "package-lock.json" (
        call npm ci --no-audit --no-fund
    ) else (
        call npm install --no-audit --no-fund
    )
    if errorlevel 1 (
        popd
        echo [ERROR] React dependencies could not be installed.
        pause
        exit /b 1
    )
    call npm run build
    if errorlevel 1 (
        popd
        echo [ERROR] React workbench shell could not be built.
        pause
        exit /b 1
    )
    popd
)

if not exist "%FRONTEND_STYLE%" (
    echo [ERROR] React workbench stylesheet is missing: %FRONTEND_STYLE%
    pause
    exit /b 1
)

echo Updating the selected bank workbench...
if /i "%PYTHON_LAUNCHER%"=="py" (
    py -3 -X utf8 "%BUILDER%" "%BANK%"
) else (
    python -X utf8 "%BUILDER%" "%BANK%"
)
if errorlevel 1 (
    echo [ERROR] Selected bank workbench could not be rebuilt.
    pause
    exit /b 1
)

if not exist "%BANK%\review\workbench-shell.css" (
    echo [ERROR] Selected bank stylesheet is missing: %BANK%\review\workbench-shell.css
    pause
    exit /b 1
)

echo Checking project environment...
if /i "%PYTHON_LAUNCHER%"=="py" (
    py -3 -X utf8 "%CHECKER%" "%BANK%"
) else (
    python -X utf8 "%CHECKER%" "%BANK%"
)
if errorlevel 1 (
    echo [ERROR] Environment check failed. Please fix the items above.
    pause
    exit /b 1
)

echo Starting teacher workbench...
echo Bank: %BANK%
if /i "%PYTHON_LAUNCHER%"=="py" (
    py -3 "%SERVER%" "%BANK%" --open
) else (
    python "%SERVER%" "%BANK%" --open
)

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] Teacher workbench stopped with exit code %EXIT_CODE%.
    pause
)
endlocal & exit /b %EXIT_CODE%
