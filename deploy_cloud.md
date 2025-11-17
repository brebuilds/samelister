# 📱 Deploy for iPhone & Multi-User Access

## 🎯 Goal: Access from anywhere + Share with your husband

You have **3 deployment options**:

---

## ✨ Option 1: Streamlit Community Cloud (FREE & EASIEST)

### Perfect for: Both accessing from anywhere, including iPhones

**Steps:**

1. **Create GitHub Account** (if you don't have one)
   - Go to: https://github.com
   - Sign up (free)

2. **Upload Your Project**
   - Create a new repository
   - Upload all files from `streamlit-ebay-lister` folder
   - Make it **private** (recommended)

3. **Deploy to Streamlit Cloud**
   - Go to: https://streamlit.io/cloud
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Choose `app.py` as the main file
   - Click "Deploy"

4. **Access Your App**
   - You'll get a URL like: `https://your-app.streamlit.app`
   - Both you and your husband can open this on any device
   - Works perfectly on iPhone Safari/Chrome

**Pros:**
- ✅ 100% FREE
- ✅ Works on iPhone, iPad, any device
- ✅ Both can access simultaneously
- ✅ Shared database (everyone sees same data)
- ✅ Automatic HTTPS security
- ✅ No technical setup needed

**Cons:**
- ⚠️ Anyone with the link can access (use private repo + complex URL)

---

## 🔒 Option 2: Deploy with Password Protection

I can add a simple password system so only you two can access.

**Add this to your app:**

```python
# At the top of app.py, add:
def check_password():
    """Returns True if password is correct."""

    def password_entered():
        if st.session_state["password"] == "YOUR_SECRET_PASSWORD":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# Then in main(), add at the start:
if not check_password():
    st.stop()
```

---

## 🏠 Option 3: Home Network Access (NO CLOUD)

### Perfect for: Access within your home WiFi

**Steps:**

1. **Find Your Computer's IP Address**
   - Windows: Open CMD, type `ipconfig`, look for IPv4
   - Mac: System Preferences → Network
   - Example: `192.168.1.100`

2. **Run the App**
   - On your computer: `launch.bat` or `./launch.sh`
   - App runs on port 8501

3. **Access from iPhone**
   - On iPhone, connect to **same WiFi**
   - Open Safari
   - Go to: `http://192.168.1.100:8501` (use your IP)
   - Bookmark for easy access

4. **Both Access Simultaneously**
   - You: Use computer browser
   - Husband: Use iPhone Safari
   - Same database, real-time sharing

**Pros:**
- ✅ 100% private (only on your network)
- ✅ FREE
- ✅ No cloud needed
- ✅ Shared database

**Cons:**
- ⚠️ Only works at home
- ⚠️ Computer must be running

---

## 🚀 RECOMMENDED SETUP

### For Best Experience:

**Weekdays (at home):**
- Use Option 3 (local network)
- Fast, private, no internet needed

**Weekends/Travel:**
- Use Option 1 (Streamlit Cloud)
- Access from anywhere
- Both can work remotely

---

## 📱 iPhone Optimization Features

Already built into the app:
- ✅ **Touch-friendly buttons** (48px min height)
- ✅ **Responsive grid** (2 columns on phone, 6 on desktop)
- ✅ **Auto-collapsing sidebar** on mobile
- ✅ **Large text inputs** (16px - prevents zoom)
- ✅ **Mobile gestures** work perfectly
- ✅ **Add to Home Screen** for app-like experience

### iPhone Tips:

**Save as App on iPhone:**
1. Open the app in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. Now it opens like a native app!

**Best iPhone Browsers:**
- Safari (recommended)
- Chrome
- Brave

---

## 🗄️ Shared Database Explained

The app uses SQLite database stored in `data/feedback.db`:

**How it works:**
- Both users access **same database**
- All listings stored together
- All AI corrections shared
- One person's edits → AI learns for both

**What each person sees:**
- Same photo groups
- Same SKU assignments
- Same AI corrections
- Same pricing rules
- Same title formulas

**Perfect for couples/teams!**

---

## 🔐 Privacy & Security

### If using Streamlit Cloud:

**Keep it private:**
- Use private GitHub repository
- Don't share the URL publicly
- Use password protection (see Option 2)
- Add `.env` to `.gitignore` (API keys not uploaded)

**Your data:**
- Stored in app's database
- Not shared with Streamlit
- You control everything

---

## ⚡ Quick Deploy Instructions

**5-Minute Setup:**

1. Create free GitHub account
2. Upload project files
3. Deploy on Streamlit Cloud
4. Get your URL
5. Open on iPhone Safari
6. Add to Home Screen
7. Done! 🎉

**Share with husband:**
- Just send him the URL
- He opens on his phone
- Both can work simultaneously

---

## 🆘 Need Help?

I can:
- Add password protection code
- Create step-by-step video instructions
- Set up automatic deployment
- Add user accounts (advanced)
- Configure custom domain

**Want me to implement any of these options?**
