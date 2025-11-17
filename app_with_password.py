#!/usr/bin/env python3
"""
Streamlit eBay Lister - PASSWORD PROTECTED VERSION
For deployment with multi-user access
"""

import streamlit as st
import json
import sqlite3
from pathlib import Path
import base64
from datetime import datetime
import pandas as pd
from PIL import Image
import io
import os
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
import hashlib

# Page config - MOBILE OPTIMIZED
st.set_page_config(
    page_title="eBay Lister Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'About': "# eBay Lister Pro\nMobile-friendly AI-powered listing tool"
    }
)

# SIMPLE PASSWORD PROTECTION
def check_password():
    """Returns True if the user has entered the correct password."""

    # Change this password to whatever you want
    CORRECT_PASSWORD = "ebaylister2024"

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == CORRECT_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # First run - show password input
    if "password_correct" not in st.session_state:
        st.markdown("# 🔐 eBay Lister Pro")
        st.markdown("### Enter password to access")
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter your password"
        )
        st.info("💡 Default password: `ebaylister2024` (change in app_with_password.py)")
        return False

    # Password incorrect
    elif not st.session_state["password_correct"]:
        st.markdown("# 🔐 eBay Lister Pro")
        st.markdown("### Enter password to access")
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter your password"
        )
        st.error("😕 Incorrect password. Please try again.")
        return False

    # Password correct
    else:
        return True

# Add mobile-responsive CSS
st.markdown("""
<style>
    /* Mobile optimization */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
            max-width: 100%;
        }

        .stButton > button {
            min-height: 48px;
            font-size: 16px;
        }

        .stTextInput input {
            font-size: 16px !important;
        }

        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
    }

    img {
        max-width: 100%;
        height: auto;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_photos' not in st.session_state:
    st.session_state.uploaded_photos = []
if 'photo_groups' not in st.session_state:
    st.session_state.photo_groups = {}
if 'unassigned_photos' not in st.session_state:
    st.session_state.unassigned_photos = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'upload'
if 'ai_settings' not in st.session_state:
    st.session_state.ai_settings = {
        'title_formula': '[Brand] [Product_Type] Size [Size] [Color] [Condition]',
        'pricing_rules': []
    }
if 'selected_photos' not in st.session_state:
    st.session_state.selected_photos = set()

# Create necessary directories and files
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
FEEDBACK_DB = DATA_DIR / "feedback.db"
CONFIG_FILE = DATA_DIR / "config.json"

# Import all functions from original app.py
# (Copy all the functions from the original app.py here)

def main():
    """Main application entry point with password protection"""

    # Check password first
    if not check_password():
        st.stop()  # Don't run the rest of the app

    # If password correct, show the app
    # Initialize database
    init_database()

    # Show logged in user info
    with st.sidebar:
        st.success("🔓 Logged in")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["password_correct"] = False
            st.rerun()

    # Render sidebar
    render_sidebar()

    # Render current page
    if st.session_state.current_page == 'upload':
        render_upload_page()
    elif st.session_state.current_page == 'sku_assignment':
        render_sku_assignment_page()
    elif st.session_state.current_page == 'ai_processing':
        render_ai_processing_page()
    elif st.session_state.current_page == 'ai_settings':
        render_ai_settings_page()

if __name__ == "__main__":
    main()

# NOTE: Copy all the functions from app.py below this line
# (init_database, load_config, save_config, render_upload_page, etc.)
