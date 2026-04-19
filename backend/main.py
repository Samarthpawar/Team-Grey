from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import bcrypt as _bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os, random, sqlite3, json
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
    # Seed demo user if table is empty
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        pwd = hash_password("demo1234")
        prefs = json.dumps({"defaultCountry":"USA","alertFrequency":"real-time","notificationChannels":["email","dashboard"]})
        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
            ("user-1","Demo User","demo@crisisx.ai", pwd, "admin",
             datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), prefs))
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
        uid: str = payload.get("user_id")
        if not uid:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = get_user_by_id(uid)
    if not user:
        raise cred_exc
    return user

# ── Pydantic models ───────────────────────────────────────────
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

app = FastAPI(title="CRISIS-X AI", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)



# ── Serve frontend ────────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend")

# ── Mock data (inline for portability) ───────────────────────
GLOBAL_RISK = {"score":61,"status":"HIGH","trend":"+12%","breakdown":{"banking":78,"market":62,"liquidity":85,"sentiment":54}}
COUNTRIES = [
    {"code":"USA","name":"United States","flag":"🇺🇸","risk":72,"type":"Banking Crisis"},
    {"code":"ARG","name":"Argentina","flag":"🇦🇷","risk":68,"type":"Currency Crisis"},
    {"code":"NGA","name":"Nigeria","flag":"🇳🇬","risk":65,"type":"Liquidity Stress"},
    {"code":"CHN","name":"China","flag":"🇨🇳","risk":61,"type":"Property Market"},
    {"code":"RUS","name":"Russia","flag":"🇷🇺","risk":58,"type":"Sanctions Impact"},
    {"code":"ZAF","name":"South Africa","flag":"🇿🇦","risk":56,"type":"Inflation"},
    {"code":"ITA","name":"Italy","flag":"🇮🇹","risk":55,"type":"Debt Risk"},
    {"code":"BRA","name":"Brazil","flag":"🇧🇷","risk":52,"type":"Currency"},
    {"code":"SAU","name":"Saudi Arabia","flag":"🇸🇦","risk":50,"type":"Oil Volatility"},
    {"code":"EGY","name":"Egypt","flag":"🇪🇬","risk":48,"type":"FX Reserves"},
    {"code":"MEX","name":"Mexico","flag":"🇲🇽","risk":48,"type":"Trade"},
    {"code":"UK","name":"United Kingdom","flag":"🇬🇧","risk":45,"type":"Inflation"},
    {"code":"IND","name":"India","flag":"🇮🇳","risk":44,"type":"INR Watch"},
    {"code":"FRA","name":"France","flag":"🇫🇷","risk":42,"type":"Public Debt"},
    {"code":"DEU","name":"Germany","flag":"🇩🇪","risk":38,"type":"Export Risk"},
    {"code":"KOR","name":"South Korea","flag":"🇰🇷","risk":36,"type":"Stable"},
    {"code":"CAN","name":"Canada","flag":"🇨🇦","risk":35,"type":"Stable"},
    {"code":"JPN","name":"Japan","flag":"🇯🇵","risk":32,"type":"Stable"},
    {"code":"AUS","name":"Australia","flag":"🇦🇺","risk":28,"type":"Stable"},
]
MARKET_INDICATORS = [
    {"symbol":"SPX","name":"S&P 500","value":5423.50,"change":-1.2,"sector":"US Equity"},
    {"symbol":"NIFTY","name":"NIFTY 50","value":22865.10,"change":0.4,"sector":"India Equity"},
    {"symbol":"GOLD","name":"Gold","value":2412.80,"change":0.8,"sector":"Commodity"},
    {"symbol":"WTI","name":"Oil (WTI)","value":78.15,"change":-2.1,"sector":"Commodity"},
    {"symbol":"USDINR","name":"USD/INR","value":83.42,"change":-0.3,"sector":"Forex"},
    {"symbol":"VIX","name":"VIX Index","value":28.4,"change":18.0,"sector":"Volatility"},
    {"symbol":"US10Y","name":"US 10Y Yield","value":4.62,"change":0.3,"sector":"Bonds"},
]
VIX_HISTORY = {
    "1D":{"labels":["10AM","11AM","12PM","1PM","2PM","3PM","4PM","Now"],"data":[18.2,19.5,20.1,22.4,23.8,22.1,25.6,28.4]},
    "1W":{"labels":["Mon","Tue","Wed","Thu","Fri","Sat","Sun","Now"],"data":[16.5,17.2,16.8,21.4,24.2,22.8,25.6,28.4]},
    "1M":{"labels":["Wk 1","Wk 2","Wk 3","Wk 4","Now"],"data":[14.2,17.8,22.1,25.5,28.4]},
}
ALERTS = [
    {"id":"ALT-203","severity":"CRITICAL","country":"USA","riskType":"Banking Crisis","probability":72,"confidence":89,"timestamp":"2024-01-15T12:00:00Z","timeAgo":"2 minutes ago","title":"USA Banking Crisis Risk — 72%","summary":"Bond yield spike +3.2%, bank stocks down 8%, VIX surged 18%. Similar pattern to 2008 pre-collapse.","triggers":[{"name":"Bond Yield Spike","value":"+3.2%","icon":"arrow-up","color":"accent","description":"US 10Y Treasury yield spiked 3.2% within 60 minutes."},{"name":"Bank Stocks Decline","value":"-8.4%","icon":"arrow-down","color":"accent","description":"Regional bank index fell 8.4% breaking through 200-day MA."},{"name":"VIX Surge","value":"+18%","icon":"bolt","color":"warning","description":"Fear gauge crossed 28.4, highest since 2023 SVB crisis."}],"historicalMatch":[{"year":2008,"event":"Financial Crisis","match":87},{"year":2023,"event":"SVB Collapse","match":74}],"actions":["Reduce exposure to US banking sector by 15-20%","Increase cash reserves","Monitor Federal Reserve announcements","Hedge portfolio with VIX call options"]},
    {"id":"ALT-202","severity":"WARNING","country":"CHN","riskType":"Property Market","probability":61,"confidence":76,"timestamp":"2024-01-15T11:45:00Z","timeAgo":"15 minutes ago","title":"China Property Stress — 61%","summary":"Evergrande-linked bonds declining, developer defaults rising.","triggers":[{"name":"Property Bonds","value":"-6.5%","icon":"arrow-down","color":"accent","description":"Evergrande-linked bonds declining sharply."}],"historicalMatch":[{"year":2021,"event":"Evergrande Crisis","match":91}],"actions":["Avoid Chinese real estate exposure","Monitor Hang Seng property index"]},
    {"id":"ALT-201","severity":"INFO","country":"IND","riskType":"Currency Watch","probability":44,"confidence":68,"timestamp":"2024-01-15T11:00:00Z","timeAgo":"1 hour ago","title":"India INR Volatility Watch — 44%","summary":"Rupee weakening against dollar, FII outflows detected.","triggers":[{"name":"INR/USD","value":"83.42","icon":"dollar-sign","color":"info","description":"Rupee weakening against dollar."}],"historicalMatch":[],"actions":["Monitor RBI interventions","Watch FII flows daily"]},
]
BANKS = [
    {"ticker":"SB","name":"Silvergate Bank","region":"USA","riskScore":92,"trend":8,"status":"Critical"},
    {"ticker":"FRC","name":"First Republic","region":"USA","riskScore":85,"trend":12,"status":"Critical"},
    {"ticker":"CS","name":"Credit Suisse","region":"Swiss","riskScore":78,"trend":5,"status":"High"},
    {"ticker":"DB","name":"Deutsche Bank","region":"Germany","riskScore":65,"trend":-3,"status":"High"},
    {"ticker":"JPM","name":"JPMorgan Chase","region":"USA","riskScore":28,"trend":-2,"status":"Low"},
]
NEWS = [
    {"source":"Reuters","timeAgo":"5 min","headline":"US regional banks face renewed deposit concerns amid rate uncertainty","sentiment":"Negative","impact":2.3,"category":"Banking"},
    {"source":"Bloomberg","timeAgo":"18 min","headline":"Fed officials signal rates to stay higher for longer than expected","sentiment":"Cautious","impact":1.1,"category":"Market"},
    {"source":"FT","timeAgo":"32 min","headline":"India GDP growth beats estimates, RBI maintains stable outlook","sentiment":"Positive","impact":-0.8,"category":"India"},
    {"source":"WSJ","timeAgo":"1 hr","headline":"European Central Bank hints at rate cuts in upcoming meeting","sentiment":"Positive","impact":-0.5,"category":"Europe"},
]
CRISES = {
    "2008":{"title":"2008 Financial Crisis","subtitle":"June 2008 — November 2008","event":"Lehman Brothers Collapse","date":"September 15, 2008","leadTime":28,"accuracy":87,"capitalSaved":22,"labels":["Jun 1","Jun 15","Jul 1","Jul 15","Aug 1","Aug 15","Aug 18","Sep 1","Sep 7","Sep 12","Sep 15","Sep 25","Oct 5","Oct 15","Oct 27","Nov 1","Nov 15","Nov 30"],"values":[22.4,21.1,23.8,24.5,26.2,25.9,27.3,28.1,32.5,38.2,45.6,52.1,65.4,76.8,89.5,78.2,65.1,58.4],"crashIndex":10,"alertIndex":6,"alertDate":"Aug 18, 2008","crashLabel":"LEHMAN COLLAPSE"},
    "2020":{"title":"COVID-19 Market Crash","subtitle":"February 2020 — April 2020","event":"Pandemic Panic Selloff","date":"March 12, 2020","leadTime":9,"accuracy":84,"capitalSaved":18,"labels":["Feb 3","Feb 10","Feb 17","Feb 24","Feb 28","Mar 3","Mar 6","Mar 9","Mar 12","Mar 16","Mar 20","Mar 27","Apr 3","Apr 10","Apr 17","Apr 24"],"values":[15.2,14.8,16.1,27.8,39.1,36.5,41.9,54.5,75.5,82.7,66.0,65.5,46.8,41.7,38.2,35.9],"crashIndex":8,"alertIndex":3,"alertDate":"Feb 24, 2020","crashLabel":"COVID CRASH"},
    "2023":{"title":"Silicon Valley Bank Collapse","subtitle":"February 2023 — April 2023","event":"SVB Failure","date":"March 10, 2023","leadTime":19,"accuracy":91,"capitalSaved":25,"labels":["Feb 1","Feb 8","Feb 15","Feb 19","Feb 22","Mar 1","Mar 5","Mar 8","Mar 10","Mar 13","Mar 17","Mar 24","Apr 3","Apr 10","Apr 17"],"values":[18.5,19.2,20.1,21.5,23.8,25.1,26.8,31.2,38.7,42.5,35.2,28.4,22.1,19.8,18.5],"crashIndex":8,"alertIndex":3,"alertDate":"Feb 19, 2023","crashLabel":"SVB FAILS"},
}
STATS = {"countriesMonitored":20,"activeAlerts":12,"modelAccuracy":89,"dataFeeds":152}
CHATBOT = [
    {"input":["usa","america","us bank","us banking"],"output":"USA banking risk is currently at <strong class='text-accent'>72%</strong>. Key triggers: Bond yield spike +3.2%, bank stocks down 8%, VIX surged 18%. Pattern matches August 2008 pre-Lehman signature."},
    {"input":["china","chinese","property","real estate"],"output":"China property sector stress is at <strong class='text-warning'>61%</strong>. Evergrande-linked bonds declining, developer defaults rising."},
    {"input":["india","inr","rupee","indian"],"output":"India risk score: <strong class='text-info'>44% (low-moderate)</strong>. INR at 83.42 vs USD, RBI active. GDP growth beating estimates is a positive signal."},
    {"input":["vix","volatility","fear gauge"],"output":"Current VIX index: <strong class='text-accent'>28.4</strong>, up 18% today — highest since 2023 banking stress. Elevated market fear and tail risk pricing."},
    {"input":["crisis","crash","market crash","financial crisis"],"output":"Global risk score: <strong class='text-accent'>61/100</strong>. Multiple convergent signals. Crisis probability: USA 72%, China 61%, India 44%."},
    {"input":["bank","banks","banking","bank risk"],"output":"Top risky banks: Silvergate (92), First Republic (85), Credit Suisse (78). Banking risk index at <strong class='text-accent'>78%</strong>."},
    {"input":["bond","bonds","yield","treasury"],"output":"US 10Y Treasury yield: <strong class='text-warning'>4.62%</strong>, up 0.3% today. Yield spike signals aggressive rate repricing — key pre-crisis signal."},
    {"input":["news","sentiment","headlines"],"output":"Current news sentiment: <strong class='text-accent'>42% Negative</strong>, 28% Neutral, 30% Positive. AI scanning 5,000+ sources daily."},
    {"input":["help","hello","hi","how"],"output":"Hello! I'm CRISIS-X AI monitoring 20 countries and 152 data feeds. Ask me about any country, bank, or market indicator!"},
]

# ── Auth Routes ───────────────────────────────────────────────
@app.post("/api/auth/signup")
async def signup(user: UserCreate):
    if get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    uid = f"user-{int(datetime.utcnow().timestamp())}"
    prefs = json.dumps({"defaultCountry":"USA","alertFrequency":"real-time","notificationChannels":["email","dashboard"]})
    conn = get_db()
    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
        (uid, user.name, user.email, hash_password(user.password),
         "user", datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), prefs))
    conn.commit(); conn.close()
    token = create_token({"user_id": uid, "role": "user"}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer", "user": {"id": uid, "name": user.name, "email": user.email, "role": "user"}}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    db_user = get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Update last login
    conn = get_db()
    conn.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.utcnow().isoformat(), db_user["id"]))
    conn.commit(); conn.close()
    token = create_token({"user_id": db_user["id"], "role": db_user["role"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer", "user": {"id": db_user["id"], "name": db_user["name"], "email": db_user["email"], "role": db_user["role"]}}

@app.get("/api/auth/me")
async def me(current_user=Depends(get_current_user)):
    return {k: v for k, v in current_user.items() if k != "password"}

# ── Data Routes ───────────────────────────────────────────────
@app.get("/api/health")
async def health(): return {"status":"ok","service":"CRISIS-X AI","time":datetime.utcnow().isoformat()}

@app.get("/api/risk/global")
async def global_risk(_=Depends(get_current_user)):
    return {**GLOBAL_RISK,"score":int(GLOBAL_RISK["score"]+random.uniform(-2,2)),"updated":datetime.utcnow().isoformat()}

@app.get("/api/risk/countries")
async def countries(_=Depends(get_current_user)): return COUNTRIES

@app.get("/api/risk/countries/top/{n}")
async def top_countries(n:int, _=Depends(get_current_user)):
    return sorted(COUNTRIES, key=lambda x:x["risk"], reverse=True)[:n]

@app.get("/api/markets/indicators")
async def market_indicators(_=Depends(get_current_user)):
    return [{**m,"value":round(m["value"]*(1+random.uniform(-0.002,0.002)),2)} for m in MARKET_INDICATORS]

@app.get("/api/markets/vix/{range}")
async def vix(range:str, _=Depends(get_current_user)):
    if range not in VIX_HISTORY: raise HTTPException(404,"Use 1D, 1W, or 1M")
    return VIX_HISTORY[range]

@app.get("/api/alerts")
async def alerts(_=Depends(get_current_user)): return ALERTS

@app.get("/api/alerts/{alert_id}")
async def alert(alert_id:str, _=Depends(get_current_user)):
    a = next((x for x in ALERTS if x["id"]==alert_id),None)
    if not a: raise HTTPException(404,"Alert not found")
    return a

@app.get("/api/banks")
async def banks(_=Depends(get_current_user)): return BANKS

@app.get("/api/news")
async def news(_=Depends(get_current_user)): return NEWS

@app.get("/api/news/sentiment")
async def sentiment(_=Depends(get_current_user)):
    total = len(NEWS); neg=sum(1 for n in NEWS if n["sentiment"]=="Negative")
    cau=sum(1 for n in NEWS if n["sentiment"]=="Cautious"); pos=sum(1 for n in NEWS if n["sentiment"]=="Positive")
    return {"distribution":{"negative":int(neg/total*100),"neutral":int(cau/total*100),"positive":int(pos/total*100)},"sourcesScanned":5247,"headlinesAnalyzed":total}

@app.get("/api/crisis")
async def crises_list(_=Depends(get_current_user)):
    return [{"year":y,"title":c["title"],"event":c["event"],"date":c["date"],"leadTime":c["leadTime"]} for y,c in CRISES.items()]

@app.get("/api/crisis/{year}")
async def crisis(year:str, _=Depends(get_current_user)):
    if year not in CRISES: raise HTTPException(404,"Crisis not found")
    return CRISES[year]

@app.get("/api/stats")
async def stats(_=Depends(get_current_user)): return STATS

@app.post("/api/chat")
async def chat(msg: ChatMessage, current_user=Depends(get_current_user)):
    lower = msg.message.lower()
    reply = None
    for item in CHATBOT:
        if any(k in lower for k in item["input"]):
            reply = item["output"]; break
    if not reply:
        reply = f'Analyzing "<em>{msg.message}</em>"… Model detects <strong class="text-warning">moderate</strong> stress signals. VIX: 28.4, US 10Y: 4.62%. Similar to pre-SVB patterns. Monitor closely.'
    ts = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute("INSERT INTO chat_history (user_id,message,reply,timestamp) VALUES (?,?,?,?)",
                 (current_user["id"], msg.message, reply, ts))
    conn.commit(); conn.close()
    return {"reply": reply, "timestamp": ts}

@app.get("/api/chat/history")
async def chat_history(current_user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT 50",(current_user["id"],)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
