#!/bin/bash

echo ""
echo "========================================================"
echo "  eBay Lister Chat - Conversational AI Interface"
echo "========================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Installing dependencies..."
pip install -q streamlit google-generativeai Pillow pandas python-dotenv

echo ""
echo "Starting chat interface..."
echo ""
echo "💬 Chat with AI to create listings!"
echo "📸 Just send photos and answer questions"
echo "📱 Perfect for iPhone and mobile"
echo ""
echo "========================================================"

streamlit run chat_app.py
