# 🚀 Quick Start Guide - eBay Lister Pro

## 📦 Start in 3 Steps

### 1️⃣ Launch the App
**Windows:** Double-click `launch.bat`
**Mac/Linux:** Double-click `launch.sh`

### 2️⃣ Get Your Free AI Key
1. Click "AI Settings" in sidebar
2. Visit: https://makersuite.google.com/app/apikey
3. Create free account & get API key
4. Paste key in app & save

### 3️⃣ Process Your First Batch
1. Click "Upload Photos"
2. Drag & drop your product images
3. Click "Start SKU Assignment"
4. Select photos → Enter SKU → Assign
5. Click "Process with AI"
6. Review results & download CSV

---

## 💡 Pro Tips

### For Best Results:
- **Group Similar Items**: Assign all t-shirts together, all jeans together
- **Use Clear SKUs**: Like "TSHIRT001", "JEANS001"
- **Take Good Photos**: Well-lit, multiple angles
- **Correct the AI**: Your edits make it smarter!

### Title Formula Example:
```
[Brand] [Product_Type] Size [Size] [Color] [Condition]
```
Results in: "Nike T-Shirt Size Large Blue New"

### Quick Pricing Rules:
- If Category is 'T-Shirt' → $19.99
- If Category is 'Jeans' → $29.99
- If Condition is 'New' → Add $10

---

## ❓ Need Help?

### The App Won't Start?
Run these commands:
```bash
pip install streamlit
pip install google-generativeai
pip install Pillow pandas
```

### Where's My Data?
- **Settings**: `data/config.json`
- **Database**: `data/feedback.db`
- **CSV Export**: Downloads folder

### Reset Everything?
Delete the `data` folder and restart

---

**Ready to list! Just drag, assign, and export!** 🎉
