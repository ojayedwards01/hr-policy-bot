@echo off
echo ================================================
echo   CMU Africa HR Policy Bot Server Startup
echo ================================================
echo.

REM Check if we're in the right directory
if not exist "src\api\app.py" (
    echo ERROR: Please run this script from the andrew-py directory
    echo Current directory: %cd%
    echo Expected files: src\api\app.py
    pause
    exit /b 1
)

echo ✓ Project directory found
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please ensure Python is installed and added to PATH
    pause
    exit /b 1
)

echo ✓ Python found: 
python --version

echo.
echo Starting HR Policy Bot Server...
echo ================================================
echo.
echo Server will be available at:
echo   • API: http://localhost:8080
echo   • Chat Interface: http://localhost:8080/chat
echo   • Or open chat_interface.html in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python run_app.py

echo.
echo ================================================
echo Server stopped
pause
