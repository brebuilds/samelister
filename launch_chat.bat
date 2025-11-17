@echo off
title eBay Lister Chat - Conversational Interface
color 0B

echo.
echo ========================================================
echo  eBay Lister Chat - Conversational AI Interface
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
pip install -q streamlit google-generativeai Pillow pandas python-dotenv

echo.
echo Starting chat interface...
echo.
echo 💬 Chat with AI to create listings!
echo 📸 Just send photos and answer questions
echo 📱 Perfect for iPhone and mobile
echo.
echo ========================================================

streamlit run chat_app.py

pause
