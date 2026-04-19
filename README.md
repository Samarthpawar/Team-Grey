# CRISIS-X AI — v2.0 (Fixed & Full-Stack)

Real-time financial crisis prediction platform with working authentication,
SQLite database, and fully connected frontend.

---

## 🚀 Quick Start (3 steps)

### Step 1 — Install Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2 — Start the backend
```bash
python main.py
# OR
bash start.sh   # from project root
```

Backend runs at: **http://localhost:5000**
API docs at: **http://localhost:5000/docs**

### Step 3 — Open the frontend
```bash
cd frontend
python3 -m http.server 8080
# Open: http://localhost:8080/login.html
```

**Demo account:** `demo@crisisx.ai` / `demo1234`

---

## 🗄️ Database — crisis_x.db

The app uses **SQLite** — a single file stored at `backend/crisis_x.db`.

It is created automatically on first run. No setup needed.

### How to view the database

**Option 1 — DB Browser for SQLite (recommended GUI)**
1. Download from https://sqlitebrowser.org/ (free, Windows/Mac/Linux)
2. Open → select `backend/crisis_x.db`
3. Browse `users` and `chat_history` tables

**Option 2 — VS Code extension**
1. Install "SQLite Viewer" by Florian Klampfer
2. Click `crisis_x.db` in the file explorer — it opens as a table

**Option 3 — Command line**
```bash
sqlite3 backend/crisis_x.db
.tables
SELECT * FROM users;
SELECT * FROM chat_history;
.quit
```

### Tables
| Table | Contents |
|-------|----------|
| `users` | id, name, email, hashed_password, role, created, last_login |
| `chat_history` | user_id, message, reply, timestamp |

---

## 🔑 API Keys

All keys go in `backend/.env`. The app works without any of them
(uses mock data). Add keys to upgrade specific features:

| Key | Feature | Where to get |
|-----|---------|--------------|
| `SECRET_KEY` | JWT signing — **change this!** | Any random 32+ char string |
| `ANTHROPIC_API_KEY` | Real AI chatbot | https://console.anthropic.com |
| `OPENAI_API_KEY` | Real AI chatbot (alternative) | https://platform.openai.com |
| `NEWS_API_KEY` | Live financial news | https://newsapi.org (free tier) |
| `ALPHA_VANTAGE_KEY` | Live market data (VIX, S&P etc.) | https://alphavantage.co (free) |

### How to add a key:
1. Open `backend/.env`
2. Uncomment the line and paste your key:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```
3. Restart the backend

---

## 📁 Project Structure

```
crisis-x-ai/
├── backend/
│   ├── main.py            ← FastAPI app (auth + all API routes)
│   ├── requirements.txt   ← Python dependencies
│   ├── .env               ← Your API keys (never commit this!)
│   └── crisis_x.db        ← SQLite database (auto-created)
│
├── frontend/
│   ├── api.js             ← Shared API client + auth guard
│   ├── login.html         ← Login/signup (connected to real API)
│   ├── Dashboard.html     ← Main dashboard (auth-protected)
│   ├── alert.html         ← Alert detail page (auth-protected)
│   ├── history.html       ← Crisis history (auth-protected)
│   └── index.html         ← Landing page
│
└── start.sh               ← One-click startup script
```

---

## 🐛 What Was Fixed

| Bug | Fix |
|-----|-----|
| Login/signup never called the API | Replaced fake `setTimeout` redirects with real `fetch` calls |
| Passwords stored in plaintext | All passwords now bcrypt-hashed in SQLite |
| No database persistence | SQLite via SQLAlchemy — data survives restarts |
| JWT auth broken (`Depends()` error) | Replaced with `OAuth2PasswordBearer` + proper token decode |
| Dashboard accessible without login | Auth guard on every protected page |
| Mobile sidebar broken | Overlay + hamburger menu added |
| `requirements.txt` had Flask (wrong stack) | Replaced with correct FastAPI packages |
| Chat had no history | Chat history saved per user to DB |
| Navigation links used `/dashboard.html` | Fixed to relative `Dashboard.html` |

---

## 🔌 API Endpoints

All `/api/*` endpoints (except `/api/health`) require:
```
Authorization: Bearer <token>
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/login` | Login, get JWT token |
| GET | `/api/auth/me` | Get current user info |
| GET | `/api/risk/global` | Global risk score |
| GET | `/api/risk/countries` | All country risks |
| GET | `/api/markets/indicators` | Market data |
| GET | `/api/markets/vix/{range}` | VIX history (1D/1W/1M) |
| GET | `/api/alerts` | All alerts |
| GET | `/api/alerts/{id}` | Single alert detail |
| GET | `/api/banks` | Bank risk scores |
| GET | `/api/news` | News + sentiment |
| GET | `/api/crisis` | Crisis history list |
| GET | `/api/crisis/{year}` | Crisis detail (2008/2020/2023) |
| GET | `/api/stats` | Dashboard stats |
| POST | `/api/chat` | AI chatbot |
| GET | `/api/chat/history` | Your chat history |
| GET | `/docs` | Interactive API docs (Swagger UI) |
