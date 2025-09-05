@echo off
echo ====================================
echo    Starting Flask App - Deniz
echo ====================================

REM Set the full path to your project folder
set PROJECT_PATH=D:\Sites\deniz

REM Change to project directory
cd /d "%PROJECT_PATH%"

REM Check if project folder exists
if not exist "%PROJECT_PATH%" (
    echo ERROR: Project folder not found!
    echo Check path: %PROJECT_PATH%
    echo Edit PROJECT_PATH variable in this batch file
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%PROJECT_PATH%\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Path: %PROJECT_PATH%\venv\Scripts\activate.bat
    pause
    exit /b 1
)

echo Changing to project folder: %PROJECT_PATH%
echo Activating virtual environment...
call "%PROJECT_PATH%\venv\Scripts\activate.bat"

REM Check if venv is activated
if "%VIRTUAL_ENV%"=="" (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

echo Virtual environment activated: %VIRTUAL_ENV%

REM Set Flask environment variables
set FLASK_APP=run.py
set FLASK_ENV=development
set FLASK_DEBUG=1

echo Starting Flask application...
echo Application will be available at: http://localhost:8000
echo Press Ctrl+C to stop
echo.

REM Start Flask
flask run --host=0.0.0.0 --port=8000

REM If Flask exits, show message
echo.
echo Flask application stopped.
pause
