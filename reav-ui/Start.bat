@echo off
setlocal enabledelayedexpansion


REM ======================================================
REM Python Virtual Environment Setup and Script Launcher
REM Created by: github.com/Nenotriple
set "SCRIPT_VERSION=1.01"
REM ======================================================


REM Configuration
set "PYTHON_SCRIPT=app.py"
set "REQUIREMENTS_FILE=requirements.txt"

set "FAST_START=FALSE"
set "AUTO_FAST_START=TRUE"
set "AUTO_CLOSE_CONSOLE=TRUE"

set "ENABLE_COLORS=TRUE"
set "QUIET_MODE=FALSE"
set "SETUP_ONLY=FALSE"

REM Runtime Variables
set "SCRIPT_DIR=%~dp0"
set "PIP_TIMEOUT=30"
set "VENV_DIR=venv"


REM ==============================================
REM Main Execution Flow
REM ==============================================


call :initialize_colors

call :PrintHeader

call :ValidatePython || exit /b 1

pushd "%SCRIPT_DIR%" || (call :LogError "Failed to set working directory" & exit /b 1)

call :SetupVirtualEnvironment || exit /b 1

REM Check if only setup is requested
if "%SETUP_ONLY%"=="TRUE" (
    call :LogInfo "SETUP_ONLY is enabled. Skipping script launch."
    call :LogInfo "Dropping into interactive shell inside the virtual environment."
    call "%VENV_DIR%\Scripts\activate.bat"
    cmd /k
    goto :EOF
)

call :LaunchPythonScript || exit /b 1

if "%AUTO_CLOSE_CONSOLE%"=="FALSE" (
    echo.
    call :LogInfo "Script completed."
    echo.
    cmd /k
)

goto :EOF


REM ==============================================
REM Core Functions
REM ==============================================


:SetupVirtualEnvironment
    REM Check for fast start conditions
    if "%AUTO_FAST_START%"=="TRUE" if exist "%VENV_DIR%\Scripts\python.exe" (
        "%VENV_DIR%\Scripts\python.exe" --version >nul 2>&1 && (
            set "FAST_START=TRUE"
            call :LogInfo "Virtual environment verified. Using fast start mode."
        )
    )
    REM Fast start path
    if "%FAST_START%"=="TRUE" (
        call :ActivateVenv && (
            call :CheckRequirementsUpdate
            exit /b 0
        )
        REM If activation fails, fall through to full setup
        set "FAST_START=FALSE"
    )
    REM Full setup path
    call :CreateVirtualEnvironment
    call :ActivateVenv || exit /b 1
    call :InstallOrUpdatePackages
exit /b 0


:CreateVirtualEnvironment
    if exist "%VENV_DIR%\Scripts\python.exe" (
        call :LogInfo "Using existing virtual environment"
        exit /b 0
    )
    if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%" 2>nul
    call :LogInfo "Creating virtual environment: %SCRIPT_DIR%%VENV_DIR%"
    python -m venv "%VENV_DIR%" || (call :LogError "Failed to create virtual environment" & exit /b 1)
    call :LogOK "Virtual environment created"
exit /b 0


:ActivateVenv
    call :LogInfo "Activating virtual environment..."
    call "%VENV_DIR%\Scripts\activate.bat" || (call :LogError "Failed to activate virtual environment" & exit /b 1)
    where python | findstr "%VENV_DIR%" >nul || (call :LogError "Virtual environment activation failed" & exit /b 1)
    call :LogOK "Virtual environment activated"
exit /b 0


:CheckRequirementsUpdate
    if not exist "%REQUIREMENTS_FILE%" exit /b 0
    REM Compare file timestamps
    for /f %%i in ('dir /b /od "%REQUIREMENTS_FILE%" "%VENV_DIR%\Scripts\python.exe" 2^>nul') do set "NEWEST=%%i"
    if /i "!NEWEST!"=="%REQUIREMENTS_FILE%" (
        call :LogInfo "Requirements file is newer - updating packages"
        call :InstallRequirements
    )
exit /b 0


:InstallOrUpdatePackages
    call :LogInfo "Upgrading pip..."
    set "PIP_FLAGS=--timeout %PIP_TIMEOUT%"
    if "%QUIET_MODE%"=="TRUE" set "PIP_FLAGS=!PIP_FLAGS! --quiet"
    python -m pip install --upgrade pip !PIP_FLAGS! 2>nul
    call :InstallRequirements
exit /b 0


:InstallRequirements
    if not exist "%REQUIREMENTS_FILE%" (
        call :LogWarn "No requirements file found: %REQUIREMENTS_FILE%"
        exit /b 0
    )
    call :LogInfo "Installing requirements from %REQUIREMENTS_FILE%..."
    set "INSTALL_FLAGS=-r "%REQUIREMENTS_FILE%" --timeout %PIP_TIMEOUT%"
    if "%QUIET_MODE%"=="TRUE" set "INSTALL_FLAGS=!INSTALL_FLAGS! --quiet"
    pip install !INSTALL_FLAGS!
    if !ERRORLEVEL! neq 0 (call :LogError "Failed to install requirements" & exit /b 1)
    call :LogOK "Requirements installed successfully"
exit /b 0


:ValidatePython
    call :LogInfo "Checking Python installation..."
    where python >nul 2>&1 || (
        call :LogError "Python is not installed or not found in PATH"
        call :LogError "Please install Python from https://python.org"
        exit /b 1
    )
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do call :LogOK "Found Python %%i"
exit /b 0


:LaunchPythonScript
    if "%PYTHON_SCRIPT%"=="" (call :LogInfo "No Python script specified" & exit /b 0)
    if not exist "%PYTHON_SCRIPT%" (call :LogError "Python script not found: %PYTHON_SCRIPT%" & exit /b 1)
    call :LogInfo "Launching: %PYTHON_SCRIPT%"
    echo.
    python "%PYTHON_SCRIPT%"
    if !ERRORLEVEL! neq 0 (
        call :LogError "Script execution failed with exit code !ERRORLEVEL!"
        exit /b !ERRORLEVEL!
    )
exit /b 0


REM ==============================================
REM Utility Functions
REM ==============================================


:initialize_colors
    if "%ENABLE_COLORS%"=="TRUE" (
        for /f %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"
        set "COLOR_RESET=!ESC![0m"
        set "COLOR_INFO=!ESC![36m"
        set "COLOR_OK=!ESC![32m"
        set "COLOR_WARN=!ESC![33m"
        set "COLOR_ERROR=!ESC![91m"
    ) else (
        set "COLOR_RESET=" & set "COLOR_INFO=" & set "COLOR_OK=" & set "COLOR_WARN=" & set "COLOR_ERROR="
    )
exit /b 0


:PrintHeader
    echo %COLOR_INFO%============================================================%COLOR_RESET%
    echo %COLOR_INFO%  %SCRIPT_VERSION% Python Virtual Environment Setup and Script Launcher%COLOR_RESET%
    echo %COLOR_INFO%  Created by: github.com/Nenotriple%COLOR_RESET%
    echo %COLOR_INFO%============================================================%COLOR_RESET%
    echo.
exit /b 0


:LogInfo
    echo %COLOR_INFO%[INFO] %~1%COLOR_RESET%
exit /b 0


:LogOK
    echo %COLOR_OK%[OK] %~1%COLOR_RESET%
exit /b 0


:LogWarn
    echo %COLOR_WARN%[WARN] %~1%COLOR_RESET%
exit /b 0


:LogError
    echo %COLOR_ERROR%[ERROR] %~1%COLOR_RESET%
    if "%AUTO_CLOSE_CONSOLE%"=="TRUE" (
        echo Press any key to exit...
        pause >nul
    )
exit /b 0
