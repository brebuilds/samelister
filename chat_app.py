#!/usr/bin/env python3
"""
eBay Lister - CONVERSATIONAL CHATBOT INTERFACE
Chat with AI, send photos via text, get clarifying questions before listing
Perfect for iPhone and mobile use
"""

import streamlit as st
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
from PIL import Image
import io
import os
import google.generativeai as genai
from typing import Dict, List, Optional
import hashlib
import time

# Page config - MOBILE OPTIMIZED
st.set_page_config(
    page_title="eBay Lister Chat",
    page_icon="💬",
    layout="centered",  # Better for chat on mobile
    initial_sidebar_state="collapsed"  # Hide sidebar for clean chat
)

# Chat-friendly mobile CSS
st.markdown("""
<style>
    /* Chat bubble styling */
    .stChatMessage {
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
    }

    /* Mobile optimization */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem;
        }

        .stButton > button {
            min-height: 48px;
            font-size: 16px;
        }

        .stTextInput input, .stTextArea textarea {
            font-size: 16px !important;
        }
    }

    /* Make images in chat responsive */
    .stChatMessage img {
        max-width: 200px;
        border-radius: 10px;
        margin: 5px 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Hey! I'm your eBay listing assistant. Send me photos of your item and I'll help create a professional listing!\n\nJust upload photos and I'll ask you some questions to get all the details right.",
            "timestamp": datetime.now()
        }
    ]

if 'current_product' not in st.session_state:
    st.session_state.current_product = {
        'photos': [],
        'info': {},
        'conversation_stage': 'awaiting_photos'
    }

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'listings_db' not in st.session_state:
    # Initialize database
    DATA_DIR = Path("data")
    DATA_DIR.mkdir(exist_ok=True)
    st.session_state.listings_db = DATA_DIR / "chat_listings.db"
    init_chat_database()

def init_chat_database():
    """Initialize SQLite database for chat listings"""
    conn = sqlite3.connect(st.session_state.listings_db)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE,
            title TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            brand TEXT,
            size TEXT,
            color TEXT,
            condition TEXT,
            material TEXT,
            photos TEXT,
            conversation_history TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()

def get_config(key: str, default: str = "") -> str:
    """Get configuration value"""
    # Check Streamlit secrets first (for cloud deployment)
    if key == 'gemini_api_key':
        try:
            if hasattr(st, 'secrets') and 'gemini' in st.secrets:
                return st.secrets['gemini']['api_key']
        except:
            pass

    # Fall back to database
    conn = sqlite3.connect(st.session_state.listings_db)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else default

def set_config(key: str, value: str):
    """Set configuration value"""
    conn = sqlite3.connect(st.session_state.listings_db)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def analyze_photos_with_ai(photos: List[bytes], conversation_context: str = "") -> dict:
    """Analyze photos and ask clarifying questions"""
    api_key = get_config('gemini_api_key')

    if not api_key:
        return {
            'needs_clarification': True,
            'questions': [
                "I need a Gemini API key to analyze photos. Would you like to set one up?",
                "Get a free key at: https://makersuite.google.com/app/apikey"
            ],
            'stage': 'need_api_key'
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Prepare images
        image_parts = []
        for photo_bytes in photos[:5]:
            image = Image.open(io.BytesIO(photo_bytes))
            image_parts.append(image)

        # First analysis - what can AI see?
        prompt = f"""You are helping create an eBay listing. Analyze these product photos.

Previous conversation context:
{conversation_context}

Your job is to:
1. Identify what the product is
2. Note what details you CAN see clearly
3. Note what details you CANNOT see and need to ask about
4. Ask SPECIFIC questions to fill in missing information

Return a JSON object like:
{{
    "what_i_can_see": {{
        "product_type": "what is this?",
        "visible_details": ["detail 1", "detail 2"],
        "condition_notes": "visible condition"
    }},
    "questions": [
        "What's the brand name? I can't see a label clearly",
        "What size is this?",
        "Any stains or defects I should mention?"
    ],
    "confidence": "high/medium/low"
}}

Be conversational and friendly in your questions!"""

        response = model.generate_content([prompt] + image_parts)

        try:
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            return {
                'needs_clarification': True,
                'ai_observations': result.get('what_i_can_see', {}),
                'questions': result.get('questions', []),
                'confidence': result.get('confidence', 'medium'),
                'stage': 'gathering_info'
            }
        except json.JSONDecodeError:
            # AI didn't return valid JSON, ask basic questions
            return {
                'needs_clarification': True,
                'questions': [
                    "I can see the photos! Let me ask a few questions:",
                    "1. What's the brand?",
                    "2. What size is it?",
                    "3. What's the condition? (New, Like New, Good, Fair)",
                    "4. Any defects or issues I should mention?",
                    "5. What price would you like?"
                ],
                'stage': 'gathering_info'
            }

    except Exception as e:
        return {
            'needs_clarification': True,
            'questions': [f"Hmm, I had trouble analyzing the photos: {str(e)}"],
            'stage': 'error'
        }

def generate_listing_from_conversation(photos: List[bytes], conversation: List[dict]) -> dict:
    """Generate final listing based on photos and conversation"""
    api_key = get_config('gemini_api_key')

    if not api_key:
        return {
            'title': 'Error - No API Key',
            'description': 'Please configure Gemini API key',
            'price': 0.00,
            'category': 'Unknown'
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Prepare images
        image_parts = []
        for photo_bytes in photos[:5]:
            image = Image.open(io.BytesIO(photo_bytes))
            image_parts.append(image)

        # Build conversation context
        conv_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation
        ])

        prompt = f"""Create a professional eBay listing based on these photos and our conversation.

Conversation history:
{conv_text}

Generate a complete listing in JSON format:
{{
    "title": "eBay-optimized title (80 chars max, include brand, type, size, color, condition)",
    "description": "Professional 3-paragraph description with bullet points for features",
    "category": "Specific eBay category",
    "price": 0.00,
    "brand": "Brand name",
    "size": "Size",
    "color": "Primary color",
    "condition": "New/Like New/Good/Fair",
    "material": "Material type",
    "item_specifics": {{
        "Style": "value",
        "Features": "value"
    }}
}}

Make it professional and keyword-rich for eBay search!"""

        response = model.generate_content([prompt] + image_parts)

        try:
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            return result
        except json.JSONDecodeError:
            return {
                'title': 'Product Listing',
                'description': response.text[:500],
                'price': 0.00,
                'category': 'General',
                'brand': 'Unknown',
                'size': 'N/A',
                'color': 'N/A',
                'condition': 'Good'
            }

    except Exception as e:
        return {
            'title': 'Error generating listing',
            'description': str(e),
            'price': 0.00,
            'category': 'Error'
        }

def save_listing_to_db(listing_data: dict, conversation: List[dict]):
    """Save completed listing to database"""
    conn = sqlite3.connect(st.session_state.listings_db)
    cursor = conn.cursor()

    # Generate SKU
    sku = f"SKU{int(time.time())}"

    cursor.execute("""
        INSERT INTO listings
        (sku, title, description, price, category, brand, size, color, condition, material, conversation_history)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sku,
        listing_data.get('title', ''),
        listing_data.get('description', ''),
        listing_data.get('price', 0.00),
        listing_data.get('category', ''),
        listing_data.get('brand', ''),
        listing_data.get('size', ''),
        listing_data.get('color', ''),
        listing_data.get('condition', ''),
        listing_data.get('material', ''),
        json.dumps(conversation)
    ))

    conn.commit()
    conn.close()

    return sku

def process_user_message(message: str, uploaded_files=None):
    """Process user message and generate AI response"""

    # Check for API key setup
    if 'set api key' in message.lower() or 'api key' in message.lower():
        # Extract key if provided
        if 'AIza' in message or 'sk-' in message:
            # Looks like an API key
            key = message.strip()
            set_config('gemini_api_key', key)
            return "✅ Great! I've saved your API key. Now send me some product photos to get started!"
        else:
            return "To set your API key, just paste it in the chat.\n\nGet a free key here: https://makersuite.google.com/app/apikey"

    # Handle photo uploads
    if uploaded_files:
        # Process photos
        photos = []
        for file in uploaded_files:
            photo_bytes = file.read()
            photos.append(photo_bytes)
            st.session_state.current_product['photos'].append(photo_bytes)

        # AI analyzes photos and asks questions
        analysis = analyze_photos_with_ai(
            st.session_state.current_product['photos'],
            "\n".join([m['content'] for m in st.session_state.messages[-5:]])
        )

        if analysis.get('stage') == 'need_api_key':
            return "\n".join(analysis['questions'])

        # AI asks clarifying questions
        response = f"📸 Got {len(photos)} photo(s)!\n\n"

        if analysis.get('ai_observations'):
            obs = analysis['ai_observations']
            response += f"I can see this is a **{obs.get('product_type', 'product')}**.\n\n"

        response += "Let me ask you a few questions to get the listing perfect:\n\n"
        response += "\n".join([f"• {q}" for q in analysis.get('questions', [])])

        st.session_state.current_product['conversation_stage'] = 'answering_questions'

        return response

    # Process answers to questions
    if st.session_state.current_product['conversation_stage'] == 'answering_questions':
        # Store the user's answers
        st.session_state.current_product['info']['user_answers'] = message

        # Check if we have enough information
        if len(st.session_state.current_product['photos']) > 0:
            # Generate listing
            listing = generate_listing_from_conversation(
                st.session_state.current_product['photos'],
                st.session_state.messages + [{'role': 'user', 'content': message}]
            )

            # Format response
            response = f"""Perfect! Here's your eBay listing:

📝 **Title:**
{listing.get('title', 'N/A')}

💰 **Price:** ${listing.get('price', 0.00)}

📦 **Category:** {listing.get('category', 'N/A')}

📋 **Description:**
{listing.get('description', 'N/A')}

---

What would you like to do?
• Type "looks good" to save this listing
• Type "change title" or "change price" to modify
• Type "start over" for a new product"""

            st.session_state.current_product['listing_data'] = listing
            st.session_state.current_product['conversation_stage'] = 'reviewing_listing'

            return response

    # Handle listing review
    if st.session_state.current_product['conversation_stage'] == 'reviewing_listing':
        message_lower = message.lower()

        if 'looks good' in message_lower or 'save' in message_lower or 'perfect' in message_lower:
            # Save to database
            sku = save_listing_to_db(
                st.session_state.current_product['listing_data'],
                st.session_state.messages
            )

            # Reset for new product
            st.session_state.current_product = {
                'photos': [],
                'info': {},
                'conversation_stage': 'awaiting_photos'
            }

            return f"""✅ Awesome! Listing saved with SKU: {sku}

Ready for another product? Just upload more photos!

Or type "view my listings" to see all saved items."""

        elif 'change' in message_lower or 'edit' in message_lower or 'modify' in message_lower:
            return f"Sure! What would you like to change? Just tell me:\n• 'Change title to: [new title]'\n• 'Set price to: $29.99'\n• 'Update description: [new description]'"

        elif 'start over' in message_lower or 'new product' in message_lower:
            st.session_state.current_product = {
                'photos': [],
                'info': {},
                'conversation_stage': 'awaiting_photos'
            }
            return "No problem! Send me photos of the next product."

    # View listings
    if 'view' in message.lower() and 'listing' in message.lower():
        conn = sqlite3.connect(st.session_state.listings_db)
        cursor = conn.cursor()
        cursor.execute("SELECT sku, title, price FROM listings ORDER BY created_at DESC LIMIT 10")
        listings = cursor.fetchall()
        conn.close()

        if not listings:
            return "You don't have any saved listings yet. Upload some photos to get started!"

        response = "📋 Your Recent Listings:\n\n"
        for sku, title, price in listings:
            response += f"• **{sku}**: {title} - ${price:.2f}\n"

        response += "\n\nType 'export csv' to download all listings!"
        return response

    # Default helpful response
    return """I'm here to help create eBay listings! Here's what you can do:

📸 **Upload photos** - I'll analyze them and ask clarifying questions
🔑 **Set API key** - Paste your Gemini API key to get started
📋 **View my listings** - See all saved listings
💾 **Export CSV** - Download your listings

What would you like to do?"""

def check_password():
    """Check password for private deployment"""
    # Only require password if deployed (has secrets configured)
    try:
        if hasattr(st, 'secrets') and 'passwords' in st.secrets:
            required_password = st.secrets['passwords']['app_password']

            def password_entered():
                if st.session_state["password"] == required_password:
                    st.session_state["password_correct"] = True
                    del st.session_state["password"]
                else:
                    st.session_state["password_correct"] = False

            if "password_correct" not in st.session_state:
                st.markdown("# 🔐 eBay Lister Chat")
                st.markdown("### Enter password to access")
                st.text_input(
                    "Password",
                    type="password",
                    on_change=password_entered,
                    key="password"
                )
                st.info("💡 Ask your account owner for the password")
                return False
            elif not st.session_state["password_correct"]:
                st.markdown("# 🔐 eBay Lister Chat")
                st.markdown("### Enter password to access")
                st.text_input(
                    "Password",
                    type="password",
                    on_change=password_entered,
                    key="password"
                )
                st.error("😕 Incorrect password")
                return False
            else:
                return True
    except:
        pass

    # No password required for local use
    return True

def main():
    """Main chat application"""

    # Check password first (for deployed version)
    if not check_password():
        st.stop()

    # Header
    st.title("💬 eBay Lister Chat")
    st.caption("Chat with AI • Send photos • Get professional listings")

    # Settings in sidebar (collapsed on mobile)
    with st.sidebar:
        st.header("⚙️ Settings")

        api_key = st.text_input(
            "Gemini API Key",
            value=get_config('gemini_api_key'),
            type="password",
            help="Get free key: https://makersuite.google.com/app/apikey"
        )

        if api_key:
            set_config('gemini_api_key', api_key)
            st.success("✅ API key saved")

        st.divider()

        # Quick stats
        conn = sqlite3.connect(st.session_state.listings_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM listings")
        count = cursor.fetchone()[0]
        conn.close()

        st.metric("Total Listings", count)

        if count > 0:
            if st.button("📥 Export All to CSV", use_container_width=True):
                df = pd.read_sql_query(
                    "SELECT sku, title, description, price, category, brand, size, color, condition FROM listings",
                    sqlite3.connect(st.session_state.listings_db)
                )
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    f"ebay_listings_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [st.session_state.messages[0]]  # Keep welcome message
            st.session_state.current_product = {
                'photos': [],
                'info': {},
                'conversation_stage': 'awaiting_photos'
            }
            st.rerun()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Photo upload (always visible)
    uploaded_files = st.file_uploader(
        "📸 Upload product photos",
        type=['jpg', 'jpeg', 'png', 'webp'],
        accept_multiple_files=True,
        key=f"uploader_{len(st.session_state.messages)}",
        label_visibility="collapsed"
    )

    # Chat input
    if prompt := st.chat_input("Type your message or upload photos above..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process and get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = process_user_message(prompt, uploaded_files)

            st.markdown(response)

        # Add AI response
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        })

        st.rerun()

    # Handle photo uploads without text
    elif uploaded_files:
        # Display photos being uploaded
        with st.chat_message("user"):
            st.markdown(f"*Uploaded {len(uploaded_files)} photo(s)*")
            cols = st.columns(min(len(uploaded_files), 3))
            for idx, file in enumerate(uploaded_files[:3]):
                with cols[idx]:
                    st.image(file, use_column_width=True)

        st.session_state.messages.append({
            "role": "user",
            "content": f"*Uploaded {len(uploaded_files)} photo(s)*",
            "timestamp": datetime.now()
        })

        # Process photos
        with st.chat_message("assistant"):
            with st.spinner("Analyzing photos..."):
                response = process_user_message("", uploaded_files)

            st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        })

        st.rerun()

if __name__ == "__main__":
    main()
