#!/bin/bash

echo ""
echo "========================================================"
echo "  eBay Lister Pro - Streamlit Application"
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
pip install -r requirements.txt

echo ""
echo "Starting Streamlit app..."
echo ""
echo "The app will open in your browser automatically."
echo "Press Ctrl+C to stop the server."
echo ""
echo "========================================================"

streamlit run app.py
