@echo off
setlocal
if defined WT_SESSION goto :run_inline
if defined TERM_PROGRAM goto :run_inline
if "%~1"=="-h" goto :run_inline
if "%~1"=="--help" goto :run_inline
if "%~1"=="-V" goto :run_inline
if "%~1"=="--version" goto :run_inline

where wt.exe >nul 2>&1
if %ERRORLEVEL%==0 (
    start "" wt.exe -d "%CD%." python "%~dp0ffcli.py" %*
    exit /b 0
)

:run_inline
python "%~dp0ffcli.py" %*

