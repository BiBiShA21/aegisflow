# 🛡️ AegisFlow — AI-Powered DevSecOps Platform

> Autonomous Multi-Agent Security Vulnerability Detection & Remediation  
> B.Tech Final Year Project — SNDT Women's University, Mumbai

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.11+
- MongoDB running on localhost:27017
- Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

---

## 📁 Project Structure

```
aegisflow/
├── backend/
│   ├── app.py                  ← FastAPI main app
│   ├── database.py             ← MongoDB connection
│   ├── agents/
│   │   ├── detection_agent.py  ← 15-type vulnerability detector
│   │   └── fix_agent.py        ← Gemini AI fix generator
│   ├── models/
│   │   └── schemas.py          ← Pydantic models
│   └── services/
│       ├── auth_service.py     ← JWT authentication
│       └── download_service.py ← PDF/MD/ZIP downloads
├── frontend/
│   ├── login.html              ← Login page
│   ├── register.html           ← Registration page
│   └── index.html              ← Main dashboard
├── .env                        ← Environment variables
├── requirements.txt            ← Python dependencies
└── README.md
```

---

## ⚙️ Setup Instructions

### Step 1: Create & Activate Virtual Environment

```powershell
cd C:\aegisflow

# Create new venv
python -m venv venv

# Activate
venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment

Edit `.env` file:
```env
MONGO_URI=mongodb://localhost:27017/aegisflow
DB_NAME=aegisflow
GEMINI_API_KEY=your_actual_gemini_api_key_here
SECRET_KEY=aegisflow-secret-2024-change-this
```

Get Gemini API key FREE at: https://aistudio.google.com/app/apikey

### Step 4: Start MongoDB

Make sure MongoDB Compass is running on `localhost:27017`

### Step 5: Start Backend

```powershell
# From C:\aegisflow folder (venv active)
python -m uvicorn backend.app:app --reload --port 8000
```

✅ You should see:
```
🛡️  AegisFlow Backend v2.0 — STARTED
📡 API:    http://127.0.0.1:8000
📚 Docs:   http://127.0.0.1:8000/docs
```

### Step 6: Start Frontend

```powershell
# New PowerShell window
cd C:\aegisflow\frontend
python -m http.server 3000 --bind 127.0.0.1
```

### Step 7: Open Browser

```
http://127.0.0.1:3000/login.html
```

---

## 🎯 Demo Flow (Presentation)

### 1. Register Account
- Go to `http://127.0.0.1:3000/register.html`
- Fill in: Name, Email, Username, Password
- Click "Create Account"

### 2. Login
- Username + Password → "Sign In"
- Redirects to Dashboard ✅

### 3. Scan Code
- Click "New Scan" in sidebar
- Paste this vulnerable Python code:

```python
import pickle

api_key = "sk_live_12345678"
password = "admin123"

def load_data(data):
    return pickle.loads(data)

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

- Click **"🔍 Analyze Code"**
- Shows: 4 CRITICAL vulnerabilities with confidence scores

### 4. Generate Fix
- Click **"✨ Generate Fix"**
- See side-by-side diff viewer
- Download as PDF/Markdown/ZIP

### 5. Dashboard
- Click "Dashboard" → See analytics, charts, recent scans
- Click "Scan History" → Full paginated history
- Click "Profile" → User details

---

## 📦 Phase Coverage

| Phase | Feature | Status |
|-------|---------|--------|
| Phase 1 | MongoDB Database Integration | ✅ Complete |
| Phase 2 | Gemini AI Integration | ✅ Complete |
| Phase 3 | 15-Type Vulnerability Detection | ✅ Complete |
| Phase 4 | Confidence Scoring System | ✅ Complete |
| Phase 5 | User Authentication (JWT) | ✅ Complete |
| Phase 7 | Analytics Dashboard (Chart.js) | ✅ Complete |
| Phase 9 | Multi-Language Support (10 langs) | ✅ Complete |
| Phase 10 | Security Hardening | ✅ Complete |

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, get JWT token |
| GET | `/api/auth/me` | Get current user profile |
| PUT | `/api/auth/profile` | Update profile |
| POST | `/api/analyze` | Analyze code (paste) |
| POST | `/api/analyze/upload` | Analyze uploaded file |
| POST | `/api/analyze/folder` | Analyze folder |
| POST | `/api/fix` | Generate AI fix |
| GET | `/api/scans` | Get scan history |
| GET | `/api/scans/{id}` | Get scan details |
| DELETE | `/api/scans/{id}` | Delete scan |
| GET | `/api/dashboard` | Dashboard stats |
| GET | `/api/download/{id}/pdf` | Download PDF report |
| GET | `/api/download/{id}/markdown` | Download Markdown |
| GET | `/api/download/{id}/code` | Download fixed code |
| GET | `/api/download/{id}/zip` | Download ZIP |

Full interactive docs: `http://127.0.0.1:8000/docs`

---

## 🐛 Troubleshooting

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'backend'` | Run from `C:\aegisflow`, not from `backend/` |
| `ModuleNotFoundError: passlib` | Run `pip install -r requirements.txt` |
| `MongoDB connection failed` | Start MongoDB Compass, connect localhost:27017 |
| `401 Unauthorized` | Register first, then login |
| Frontend not loading | Start `python -m http.server 3000` from `frontend/` folder |
| CORS error | Already handled — restart backend |
| PDF generation fails | Run `pip install reportlab` |

---

## 👥 Team

- **Bhavishya** (Roll: 54)
- **Gauri** (Roll: 67)  
- **Khushi** (Roll: 77)

**Institution:** SNDT Women's University, Mumbai  
**Program:** B.Tech Computer Science — Final Year  
**Project:** AegisFlow — Autonomous Multi-Agent DevSecOps Pipeline

---

*Built with ❤️ using Python, FastAPI, MongoDB, Gemini AI, Chart.js*
