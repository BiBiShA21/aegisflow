# 🛠️ AegisFlow Troubleshooting Guide

## ❌ "Method Not Allowed" Error (405)

**Problem:** Registration or login fails with "✗ Method Not Allowed"

**Cause:** Backend server not running or CORS misconfigured

**Solutions:**

### 1. Make sure backend is running
```powershell
# Terminal 1 - Backend MUST be running
cd C:\aegisflow
venv\Scripts\activate
python -m uvicorn backend.app:app --reload --port 8000
```

✅ You should see:
```
🛡️  AegisFlow Backend v2.0 — STARTED
📡 API:    http://127.0.0.1:8000
```

### 2. Check frontend port
- Frontend MUST run on port 3000
```powershell
# Terminal 2 - Frontend
cd C:\aegisflow\frontend
python -m http.server 3000 --bind 127.0.0.1
```

### 3. Verify URLs match
- **Login:** `http://127.0.0.1:3000/login.html` ✅
- **API:** `http://127.0.0.1:8000/api/health` ✅
- **NOT:** `http://localhost:3000` ❌
- **NOT:** `http://127.0.0.1:3000/register.html` for API calls ❌

### 4. Clear browser cache
- Press `Ctrl + Shift + Delete`
- Clear Cache & Cookies
- Refresh page

### 5. Check console for errors
- Press `F12` in browser
- Go to "Console" tab
- Look for red errors
- Screenshot and share

---

## ❌ MongoDB Connection Failed

**Problem:** `❌ MongoDB connection failed`

**Solutions:**

1. **Start MongoDB Compass**
   - Launch MongoDB Compass (should be in Start Menu)
   - Should show "Connected" at top

2. **Or start MongoDB server**
   ```powershell
   mongod
   ```

3. **Verify connection**
   ```powershell
   python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017').admin.command('ping'))"
   ```

---

## ❌ ModuleNotFoundError

**Problem:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```powershell
cd C:\aegisflow
venv\Scripts\activate
pip install -r requirements.txt --upgrade
```

---

## ❌ Cannot connect to server

**Problem:** `✗ Cannot connect to server on port 8000`

**Solutions:**

1. **Is backend running?**
   ```
   Check Terminal 1 for "🛡️  AegisFlow Backend v2.0 — STARTED"
   ```

2. **Is port 8000 in use?**
   ```powershell
   netstat -ano | findstr :8000
   # If something is there, close it or use different port
   ```

3. **Try running with different port**
   ```powershell
   python -m uvicorn backend.app:app --reload --port 8001
   ```
   Then update frontend API variable:
   ```javascript
   const API = 'http://127.0.0.1:8001';
   ```

---

## ✅ Quick Health Check

Run this to verify everything is working:

```powershell
# Check backend
curl http://127.0.0.1:8000/api/health

# Should return JSON with status: "healthy"
```

---

## 📋 Full Setup from Scratch (If stuck)

```powershell
# 1. Delete old venv
rmdir venv /s /q

# 2. Create new venv
python -m venv venv

# 3. Activate
venv\Scripts\activate

# 4. Install
pip install --upgrade pip
pip install -r requirements.txt

# 5. Start backend
python -m uvicorn backend.app:app --reload --port 8000

# In new terminal:
# 6. Start frontend
cd frontend
python -m http.server 3000 --bind 127.0.0.1

# 7. Open browser
# http://127.0.0.1:3000/login.html
```

---

## 🐛 Debug Mode

**Enable console logging:**

Backend already logs all requests. Check Terminal 1 for:
- `📝 Registration attempt: username`
- `✅ User registered: username`
- `❌ Error messages`

Frontend logs to browser Console (F12):
- Look for network errors
- Check Request/Response tabs

---

## 📞 Still Stuck?

1. Take a screenshot of the error
2. Open browser F12 → Console tab → copy all red text
3. Check Terminal 1 (backend) for error messages
4. Make sure:
   - ✅ Python 3.11+
   - ✅ MongoDB running
   - ✅ Backend on port 8000
   - ✅ Frontend on port 3000
   - ✅ Gemini API key in .env
