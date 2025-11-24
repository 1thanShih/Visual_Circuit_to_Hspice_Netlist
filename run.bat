@echo off
set ENV_NAME=circuit_cad

echo [1/3] Checking if Conda environment exists...
call conda info --envs | findstr "%ENV_NAME%" >nul

if %errorlevel% neq 0 (
    echo Environment not found. Creating new environment...
    echo Installing Python 3.11 and TK library to fix GUI errors...
    call conda create -n %ENV_NAME% python=3.11 tk -y
) else (
    echo Environment "%ENV_NAME%" already exists. Skipping creation.
)

echo.
echo [2/3] Preparing to launch application...
echo.

echo [3/3] Running Circuit CAD...
call conda run -n %ENV_NAME% python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The program crashed. Please check the error message above.
    pause
)