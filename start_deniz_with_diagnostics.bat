@echo off
echo ====================================
echo    Flask App Diagnostics - Deniz
echo ====================================

REM Set the full path to your project folder
set PROJECT_PATH=D:\Sites\deniz

echo.
echo === NETWORK DIAGNOSTICS ===
echo Current IP addresses:
ipconfig | findstr "IPv4"

echo.
echo Current listening ports:
netstat -an | findstr :8000

echo.
echo Firewall status:
netsh advfirewall show allprofiles state

echo.
echo === STARTING FLASK APP ===

REM Change to project directory
cd /d "%PROJECT_PATH%"

REM Activate virtual environment
call "%PROJECT_PATH%\venv\Scripts\activate.bat"

REM Set Flask environment variables
set FLASK_APP=run.py
set FLASK_ENV=development
set FLASK_DEBUG=1

echo.
echo Starting Flask application...
echo Application will be available at:
echo - Local: http://localhost:8000
echo - Network: http://0.0.0.0:8000

REM Get local IP for convenience
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4" ^| findstr "192.168"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        echo - Network IP: http://%%b:8000
    )
)

echo.
echo Press Ctrl+C to stop
echo.

REM Start Flask with verbose output
flask run --host=0.0.0.0 --port=8000 --debugger

REM If Flask exits, show message
echo.
echo Flask application stopped.
pause