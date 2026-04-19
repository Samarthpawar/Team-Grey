from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import bcrypt as _bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os, random, sqlite3, json
import urllib.request
from dotenv import load_dotenv

# ── Load env ──────────────────────────────────────────────────
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "crisis-x-super-secret-key-change-in-production-2024")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # 7 days

# ── DB setup ──────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "crisis_x.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'user',
            created   TEXT NOT NULL,
            last_login TEXT NOT NULL,
            preferences TEXT NOT NULL DEFAULT '{}'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   TEXT NOT NULL,
            message   TEXT NOT NULL,
            reply     TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        pwd = hash_password("demo1234")
        prefs = json.dumps({
            "defaultCountry":"USA",
            "alertFrequency":"real-time",
            "notificationChannels":["email","dashboard"]
        })
        conn.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
            (
                "user-1","Demo User","demo@crisisx.ai", pwd, "admin",
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                prefs
            )
        )
    conn.commit()
    conn.close()

# ── Auth helpers ──────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        h = hashed.encode() if isinstance(hashed, str) else hashed
        return _bcrypt.checkpw(plain.encode(), h)
    except Exception:
        return False

def hash_password(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()

def get_user_by_email(email: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(uid: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid = payload.get("user_id")
        if not uid:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = get_user_by_id(uid)
    if not user:
        raise cred_exc

    return user

# ── Models ────────────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChatMessage(BaseModel):
    message: str

# ── App ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="CRISIS-X AI",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Frontend Path ─────────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

# ✅ ROOT ROUTE FIXED
@app.get("/")
async def home():
    file_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"message": "CRISIS-X AI Backend Running"}

# Optional extra pages
@app.get("/dashboard")
async def dashboard():
    file_path = os.path.join(frontend_dir, "Dashboard.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"detail": "Dashboard file not found"}

@app.get("/login")
async def login_page():
    file_path = os.path.join(frontend_dir, "login.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"detail": "Login file not found"}

# Static files
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend")

# ── Health Route ──────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "CRISIS-X AI",
        "time": datetime.utcnow().isoformat()
    }

# ── Auth Routes ───────────────────────────────────────────────
@app.post("/api/auth/signup")
async def signup(user: UserCreate):
    if get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    uid = f"user-{int(datetime.utcnow().timestamp())}"

    conn = get_db()
    conn.execute(
        "INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
        (
            uid,
            user.name,
            user.email,
            hash_password(user.password),
            "user",
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            "{}"
        )
    )
    conn.commit()
    conn.close()

    token = create_token(
        {"user_id": uid, "role": "user"},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    db_user = get_user_by_email(user.email)

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(
        {"user_id": db_user["id"], "role": db_user["role"]},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)