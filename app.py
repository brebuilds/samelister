#!/usr/bin/env python3
"""
Streamlit eBay Lister - Complete Application
Implements manual SKU assignment, customizable AI rules, and feedback learning
MOBILE-RESPONSIVE & MULTI-USER READY
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
    initial_sidebar_state="auto",  # Auto-collapse on mobile
    menu_items={
        'Get Help': 'https://github.com/yourusername/streamlit-ebay-lister',
        'Report a bug': None,
        'About': "# eBay Lister Pro\nMobile-friendly AI-powered listing tool"
    }
)

# Add mobile-responsive CSS
st.markdown("""
<style>
    /* Mobile optimization */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
            max-width: 100%;
        }

        /* Larger touch targets on mobile */
        .stButton > button {
            min-height: 48px;
            font-size: 16px;
        }

        /* Better input fields on mobile */
        .stTextInput input {
            font-size: 16px !important;
        }

        /* Responsive grid */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        /* Better spacing on mobile */
        .element-container {
            margin-bottom: 1rem;
        }
    }

    /* Make images responsive */
    img {
        max-width: 100%;
        height: auto;
    }

    /* Better photo grid on mobile */
    @media (max-width: 768px) {
        .photo-grid {
            grid-template-columns: repeat(2, 1fr) !important;
        }
    }

    @media (min-width: 769px) {
        .photo-grid {
            grid-template-columns: repeat(6, 1fr);
        }
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

def init_database():
    """Initialize SQLite database for feedback"""
    conn = sqlite3.connect(FEEDBACK_DB)
    cursor = conn.cursor()

    # Create feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            field_name TEXT,
            original_value TEXT,
            corrected_value TEXT,
            product_type TEXT,
            context TEXT
        )
    """)

    # Create listings table for saving results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE,
            title TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            material TEXT,
            size TEXT,
            color TEXT,
            condition TEXT,
            brand TEXT,
            photos TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def load_config():
    """Load configuration from file"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'title_formula': '[Brand] [Product_Type] Size [Size] [Color] [Condition]',
        'pricing_rules': [],
        'gemini_api_key': ''
    }

def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_image_hash(image_bytes):
    """Generate hash for image to use as identifier"""
    return hashlib.md5(image_bytes).hexdigest()[:12]

def process_uploaded_files(uploaded_files):
    """Process uploaded files and store in session state"""
    photos = []
    for file in uploaded_files:
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Create thumbnail for display
        thumbnail = image.copy()
        thumbnail.thumbnail((300, 300))
        thumb_io = io.BytesIO()
        thumbnail.save(thumb_io, format='JPEG')
        thumb_bytes = thumb_io.getvalue()

        photo_data = {
            'name': file.name,
            'hash': get_image_hash(image_bytes),
            'image_bytes': image_bytes,
            'thumbnail_bytes': thumb_bytes,
            'assigned': False
        }
        photos.append(photo_data)

    return photos

def render_upload_page():
    """Render the photo upload page"""
    st.title("📸 Upload Product Photos")
    st.markdown("---")

    uploaded_files = st.file_uploader(
        "Drag and drop your product photos here",
        type=['jpg', 'jpeg', 'png', 'webp'],
        accept_multiple_files=True,
        key="photo_uploader"
    )

    if uploaded_files:
        photos = process_uploaded_files(uploaded_files)
        st.session_state.uploaded_photos = photos
        st.session_state.unassigned_photos = [p['hash'] for p in photos]

        st.success(f"✅ Uploaded {len(photos)} photos successfully!")

        # Show preview
        st.subheader("Preview")
        cols = st.columns(6)
        for idx, photo in enumerate(photos[:12]):
            with cols[idx % 6]:
                st.image(photo['thumbnail_bytes'], caption=photo['name'][:20])

        if len(photos) > 12:
            st.info(f"... and {len(photos) - 12} more photos")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Start SKU Assignment", type="primary", use_container_width=True):
                st.session_state.current_page = 'sku_assignment'
                st.rerun()
        with col2:
            if st.button("🔄 Clear and Re-upload", use_container_width=True):
                st.session_state.uploaded_photos = []
                st.session_state.unassigned_photos = []
                st.rerun()

def render_sku_assignment_page():
    """Render the SKU assignment interface"""
    st.title("🏷️ SKU Assignment")

    if not st.session_state.unassigned_photos:
        st.success("✅ All photos have been assigned!")
        if st.button("🤖 Process with AI", type="primary"):
            st.session_state.current_page = 'ai_processing'
            st.rerun()
        return

    # Stats
    total_photos = len(st.session_state.uploaded_photos)
    assigned_photos = total_photos - len(st.session_state.unassigned_photos)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Photos", total_photos)
    with col2:
        st.metric("Assigned", assigned_photos)
    with col3:
        st.metric("Remaining", len(st.session_state.unassigned_photos))

    st.markdown("---")

    # SKU input
    col1, col2 = st.columns([2, 1])
    with col1:
        sku = st.text_input("Enter SKU for selected photos:", key="sku_input")
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        assign_button = st.button("📦 Assign SKU", type="primary", use_container_width=True)

    # Photo grid with checkboxes
    st.subheader("Select photos for this product:")

    # Get unassigned photos
    unassigned_photos = [p for p in st.session_state.uploaded_photos
                        if p['hash'] in st.session_state.unassigned_photos]

    # Display photos in grid
    cols_per_row = 6
    rows = (len(unassigned_photos) + cols_per_row - 1) // cols_per_row

    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            photo_idx = row * cols_per_row + col_idx
            if photo_idx < len(unassigned_photos):
                photo = unassigned_photos[photo_idx]
                with cols[col_idx]:
                    # Display photo
                    st.image(photo['thumbnail_bytes'], use_column_width=True)

                    # Checkbox
                    selected = st.checkbox(
                        photo['name'][:15] + "...",
                        key=f"select_{photo['hash']}",
                        value=photo['hash'] in st.session_state.selected_photos
                    )

                    if selected:
                        st.session_state.selected_photos.add(photo['hash'])
                    elif photo['hash'] in st.session_state.selected_photos:
                        st.session_state.selected_photos.remove(photo['hash'])

    # Process assignment
    if assign_button and sku and st.session_state.selected_photos:
        # Create photo group
        st.session_state.photo_groups[sku] = list(st.session_state.selected_photos)

        # Remove from unassigned
        for photo_hash in st.session_state.selected_photos:
            st.session_state.unassigned_photos.remove(photo_hash)

        # Clear selection
        st.session_state.selected_photos.clear()

        st.success(f"✅ Assigned {len(st.session_state.photo_groups[sku])} photos to SKU: {sku}")
        st.rerun()

    # Quick actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Select All", use_container_width=True):
            st.session_state.selected_photos = set(p['hash'] for p in unassigned_photos)
            st.rerun()
    with col2:
        if st.button("Clear Selection", use_container_width=True):
            st.session_state.selected_photos.clear()
            st.rerun()
    with col3:
        selected_count = len(st.session_state.selected_photos)
        st.info(f"Selected: {selected_count} photos")

def get_ai_prompt_with_rules(sku: str, config: dict) -> str:
    """Generate AI prompt with user-defined rules and feedback"""
    # Get recent feedback examples
    conn = sqlite3.connect(FEEDBACK_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT field_name, original_value, corrected_value, product_type
        FROM feedback
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    feedback_examples = cursor.fetchall()
    conn.close()

    # Build feedback section
    feedback_text = ""
    if feedback_examples:
        feedback_text = "\n\nLEARN FROM THESE CORRECTIONS:\n"
        for field, original, corrected, product_type in feedback_examples:
            feedback_text += f"- For {product_type}, when {field} was '{original}', user corrected to '{corrected}'\n"

    # Build pricing rules
    pricing_text = "\n\nPRICING RULES:\n"
    for rule in config.get('pricing_rules', []):
        pricing_text += f"- If {rule['condition']}, set price to ${rule['price']}\n"

    prompt = f"""You are an expert eBay listing creator. Analyze these product images and create a professional listing.

SKU: {sku}

TITLE FORMULA: {config.get('title_formula', '[Brand] [Product_Type] Size [Size] [Color] [Condition]')}
{pricing_text}
{feedback_text}

Analyze the images and provide the following in JSON format:
{{
    "title": "Professional eBay title following the formula",
    "description": "Detailed product description (3-4 paragraphs)",
    "category": "Most specific eBay category",
    "price": 0.00,
    "brand": "Brand name or 'Unbranded'",
    "product_type": "Specific product type",
    "material": "Primary material",
    "size": "Size or 'N/A'",
    "color": "Primary color",
    "condition": "New/Used/Pre-owned",
    "features": ["feature1", "feature2", "feature3"],
    "item_specifics": {{"key": "value"}}
}}

Be specific and accurate. Use the title formula exactly."""

    return prompt

def process_with_ai(sku: str, photo_hashes: List[str], config: dict) -> dict:
    """Process product group with Gemini AI"""
    # Get photos
    photos = [p for p in st.session_state.uploaded_photos if p['hash'] in photo_hashes]

    if not config.get('gemini_api_key'):
        return {
            'title': f'Product {sku}',
            'description': 'AI processing requires Gemini API key. Please configure in AI Settings.',
            'category': 'General',
            'price': 0.00,
            'brand': 'Unknown',
            'material': 'Unknown',
            'size': 'N/A',
            'color': 'Unknown',
            'condition': 'Used'
        }

    try:
        # Configure Gemini
        genai.configure(api_key=config['gemini_api_key'])
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Prepare images
        image_parts = []
        for photo in photos[:5]:  # Limit to 5 images
            image = Image.open(io.BytesIO(photo['image_bytes']))
            image_parts.append(image)

        # Generate prompt
        prompt = get_ai_prompt_with_rules(sku, config)

        # Get AI response
        response = model.generate_content([prompt] + image_parts)

        # Parse JSON response
        try:
            result = json.loads(response.text)
            return result
        except:
            # Fallback if JSON parsing fails
            return {
                'title': f'Product {sku}',
                'description': response.text[:500],
                'category': 'General',
                'price': 0.00,
                'brand': 'Unknown',
                'material': 'Unknown',
                'size': 'N/A',
                'color': 'Unknown',
                'condition': 'Used'
            }

    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return {
            'title': f'Product {sku} - Error',
            'description': f'Error processing with AI: {str(e)}',
            'category': 'General',
            'price': 0.00,
            'brand': 'Unknown',
            'material': 'Unknown',
            'size': 'N/A',
            'color': 'Unknown',
            'condition': 'Used'
        }

def render_ai_processing_page():
    """Process all SKU groups with AI and show editable results"""
    st.title("🤖 AI Processing & Review")

    config = load_config()

    if 'ai_results' not in st.session_state:
        # Process all groups
        with st.spinner("🔄 Processing with AI..."):
            results = {}
            progress_bar = st.progress(0)

            total_groups = len(st.session_state.photo_groups)
            for idx, (sku, photo_hashes) in enumerate(st.session_state.photo_groups.items()):
                results[sku] = process_with_ai(sku, photo_hashes, config)
                progress_bar.progress((idx + 1) / total_groups)

            st.session_state.ai_results = results

    # Display editable results
    st.subheader("📝 Review and Edit Results")
    st.info("Click on any cell to edit. Your corrections will be saved for AI learning.")

    # Convert results to DataFrame for editing
    df_data = []
    for sku, data in st.session_state.ai_results.items():
        row = {
            'SKU': sku,
            'Title': data.get('title', ''),
            'Price': data.get('price', 0.00),
            'Category': data.get('category', ''),
            'Brand': data.get('brand', ''),
            'Material': data.get('material', ''),
            'Size': data.get('size', ''),
            'Color': data.get('color', ''),
            'Condition': data.get('condition', ''),
            'Description': data.get('description', '')
        }
        df_data.append(row)

    df = pd.DataFrame(df_data)

    # Editable dataframe
    edited_df = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        height=400,
        column_config={
            "Price": st.column_config.NumberColumn(
                "Price",
                format="$%.2f",
                min_value=0.00,
                max_value=10000.00,
            ),
            "Description": st.column_config.TextColumn(
                "Description",
                width="large",
            ),
        }
    )

    # Save feedback for changes
    if not df.equals(edited_df):
        conn = sqlite3.connect(FEEDBACK_DB)
        cursor = conn.cursor()

        for idx, row in edited_df.iterrows():
            original_row = df.iloc[idx]
            sku = row['SKU']

            # Check each field for changes
            for field in ['Title', 'Price', 'Category', 'Brand', 'Material', 'Size', 'Color', 'Condition']:
                if row[field] != original_row[field]:
                    cursor.execute("""
                        INSERT INTO feedback (field_name, original_value, corrected_value, product_type)
                        VALUES (?, ?, ?, ?)
                    """, (field, str(original_row[field]), str(row[field]), row.get('Category', 'Unknown')))

        conn.commit()
        conn.close()
        st.success("✅ Feedback saved for AI learning!")

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Save to Database", type="primary", use_container_width=True):
            # Save to database
            conn = sqlite3.connect(FEEDBACK_DB)
            cursor = conn.cursor()

            for idx, row in edited_df.iterrows():
                sku = row['SKU']
                photo_hashes = st.session_state.photo_groups[sku]

                cursor.execute("""
                    INSERT OR REPLACE INTO listings
                    (sku, title, description, price, category, material, size, color, condition, brand, photos)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sku, row['Title'], row['Description'], row['Price'],
                    row['Category'], row['Material'], row['Size'],
                    row['Color'], row['Condition'], row['Brand'],
                    json.dumps(photo_hashes)
                ))

            conn.commit()
            conn.close()
            st.success("✅ Saved to database!")

    with col2:
        # Export to CSV
        csv = edited_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"ebay_listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col3:
        if st.button("🔄 Start New Batch", use_container_width=True):
            # Clear session state
            st.session_state.uploaded_photos = []
            st.session_state.photo_groups = {}
            st.session_state.unassigned_photos = []
            st.session_state.current_page = 'upload'
            st.session_state.selected_photos = set()
            if 'ai_results' in st.session_state:
                del st.session_state.ai_results
            st.rerun()

def render_ai_settings_page():
    """Render AI settings and configuration page"""
    st.title("⚙️ AI Settings & Rules")

    config = load_config()

    # API Key
    st.subheader("🔑 API Configuration")
    api_key = st.text_input(
        "Gemini API Key",
        value=config.get('gemini_api_key', ''),
        type="password",
        help="Get your free API key at https://makersuite.google.com/app/apikey"
    )

    st.markdown("---")

    # Title Formula
    st.subheader("📝 Title Formula")
    st.info("Use placeholders like [Brand], [Product_Type], [Size], [Color], [Material], [Condition]")

    title_formula = st.text_input(
        "Title Template",
        value=config.get('title_formula', '[Brand] [Product_Type] Size [Size] [Color] [Condition]'),
        help="AI will follow this formula when generating titles"
    )

    st.markdown("---")

    # Pricing Rules
    st.subheader("💰 Pricing Rules")

    # Display existing rules
    pricing_rules = config.get('pricing_rules', [])

    if pricing_rules:
        st.write("**Current Rules:**")
        for idx, rule in enumerate(pricing_rules):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.text(f"If {rule['condition']}")
            with col2:
                st.text(f"→ ${rule['price']}")
            with col3:
                if st.button(f"🗑️", key=f"delete_rule_{idx}"):
                    pricing_rules.pop(idx)
                    config['pricing_rules'] = pricing_rules
                    save_config(config)
                    st.rerun()

    # Add new rule
    st.write("**Add New Rule:**")
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        conditions = [
            "Category is 'T-Shirt'",
            "Category is 'Jeans'",
            "Category is 'Jacket'",
            "Brand is 'Nike'",
            "Brand is 'Adidas'",
            "Condition is 'New'",
            "Condition is 'Used'",
            "Material contains 'Cotton'",
            "Material contains 'Polyester'"
        ]
        condition = st.selectbox("Condition", conditions)

    with col2:
        price = st.number_input("Price", min_value=0.00, max_value=1000.00, value=19.99, step=0.01)

    with col3:
        st.write("")  # Spacer
        if st.button("➕ Add Rule", type="primary"):
            pricing_rules.append({'condition': condition, 'price': price})
            config['pricing_rules'] = pricing_rules
            save_config(config)
            st.success("✅ Rule added!")
            st.rerun()

    st.markdown("---")

    # Feedback History
    st.subheader("📊 Learning History")

    conn = sqlite3.connect(FEEDBACK_DB)

    # Get feedback stats
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM feedback")
    feedback_count = cursor.fetchone()[0]

    if feedback_count > 0:
        st.metric("Total Corrections Learned", feedback_count)

        # Show recent feedback
        df_feedback = pd.read_sql_query(
            """
            SELECT timestamp, field_name, original_value, corrected_value, product_type
            FROM feedback
            ORDER BY timestamp DESC
            LIMIT 20
            """,
            conn
        )

        if not df_feedback.empty:
            st.write("**Recent Corrections:**")
            st.dataframe(df_feedback, use_container_width=True, height=300)
    else:
        st.info("No corrections yet. The AI will learn from your edits in the review stage.")

    conn.close()

    # Save button
    st.markdown("---")
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        config['gemini_api_key'] = api_key
        config['title_formula'] = title_formula
        save_config(config)
        st.success("✅ Settings saved successfully!")

def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.title("📦 eBay Lister Pro")
        st.markdown("---")

        # Navigation
        st.subheader("Navigation")

        pages = {
            'upload': '📸 Upload Photos',
            'sku_assignment': '🏷️ SKU Assignment',
            'ai_processing': '🤖 AI Processing',
            'ai_settings': '⚙️ AI Settings'
        }

        for page_key, page_name in pages.items():
            if st.button(page_name, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()

        # Stats
        st.markdown("---")
        st.subheader("📊 Current Session")

        if st.session_state.uploaded_photos:
            st.metric("Total Photos", len(st.session_state.uploaded_photos))
            st.metric("SKU Groups", len(st.session_state.photo_groups))

            # Show groups
            if st.session_state.photo_groups:
                st.write("**Groups:**")
                for sku, photos in st.session_state.photo_groups.items():
                    st.text(f"• {sku}: {len(photos)} photos")
        else:
            st.info("No photos uploaded yet")

        # Database stats
        st.markdown("---")
        st.subheader("📈 Database Stats")

        conn = sqlite3.connect(FEEDBACK_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM listings")
        listing_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM feedback")
        feedback_count = cursor.fetchone()[0]

        conn.close()

        st.metric("Total Listings", listing_count)
        st.metric("AI Corrections", feedback_count)

def main():
    """Main application entry point"""
    # Initialize database
    init_database()

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
