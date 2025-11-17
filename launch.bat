@echo off
title eBay Lister Pro - Streamlit App
color 0A

echo.
echo ========================================================
echo  eBay Lister Pro - Streamlit Application
echo ========================================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting Streamlit app...
echo.
echo The app will open in your browser automatically.
echo Press Ctrl+C to stop the server.
echo.
echo ========================================================

streamlit run app.py

pause
