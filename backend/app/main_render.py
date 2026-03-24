import base64
import json
import logging
import os
import secrets
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import bcrypt
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    import mysql.connector
except Exception:
    mysql = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
GENERATED_IMAGES_DIR = BASE_DIR / "generated_images"
DATA_DIR = BASE_DIR / "data"
JSON_STATE_PATH = Path(os.getenv("JSON_STATE_PATH", str(DATA_DIR / "render_state.json")))
STATIC_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "smart_fashion")
DATABASE_ENABLED = bool(mysql and DB_HOST and DB_USER and DB_NAME)

MOCK_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_state() -> Dict[str, Any]:
    return {
        "users": {
            "demo": {
                "id": 1,
                "username": "demo",
                "email": "demo@example.com",
                "password_hash": hash_password("demo123"),
                "subscription_tier": "free",
                "is_active": True,
                "created_at": now_iso(),
            }
        },
        "profiles": {},
        "sessions": {},
        "messages": {},
        "next_user_id": 2,
    }


in_memory_state: Dict[str, Any] = default_state()


def load_json_state() -> None:
    global in_memory_state

    if not JSON_STATE_PATH.exists():
        in_memory_state = default_state()
        persist_json_state()
        return

    try:
        loaded = json.loads(JSON_STATE_PATH.read_text(encoding="utf-8"))
        state = default_state()
        for key in state:
            state[key] = loaded.get(key, state[key])
        state["users"].setdefault("demo", default_state()["users"]["demo"])
        state["next_user_id"] = max(
            int(state.get("next_user_id", 2)),
            max((user.get("id", 0) for user in state["users"].values()), default=1) + 1,
        )
        in_memory_state = state
    except Exception as exc:
        logger.warning("Failed to load JSON state, using defaults: %s", exc)
        in_memory_state = default_state()
        persist_json_state()


def persist_json_state() -> None:
    if DATABASE_ENABLED:
        return
    JSON_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_STATE_PATH.write_text(json.dumps(in_memory_state, indent=2), encoding="utf-8")

security = HTTPBearer(auto_error=False)
app = FastAPI(title="Smart Fashion API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class AuthRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class ProfileData(BaseModel):
    gender: Optional[str] = None
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    face_shape: Optional[str] = None
    hair_type: List[str] = Field(default_factory=list)
    style_preferences: List[str] = Field(default_factory=list)
    measurements: Dict[str, Any] = Field(default_factory=dict)
    height: Optional[str] = None
    weight: Optional[str] = None
    bust: Optional[str] = None
    waist: Optional[str] = None
    hips: Optional[str] = None


class ProfileSaveRequest(BaseModel):
    session_id: str
    profile_data: ProfileData


class SessionCreateRequest(BaseModel):
    session_id: Optional[str] = None
    session_name: str = "New Chat"


class ChatRequest(BaseModel):
    session_id: str = "default"
    query: str = ""


def normalize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "gender": profile.get("gender"),
        "body_type": profile.get("body_type"),
        "skin_tone": profile.get("skin_tone"),
        "face_shape": profile.get("face_shape"),
        "hair_type": profile.get("hair_type") or [],
        "style_preferences": profile.get("style_preferences") or [],
        "measurements": profile.get("measurements") or {},
        "height": profile.get("height"),
        "weight": profile.get("weight"),
        "bust": profile.get("bust"),
        "waist": profile.get("waist"),
        "hips": profile.get("hips"),
    }
    if not normalized["measurements"]:
        normalized["measurements"] = {
            "height": normalized["height"] or "",
            "weight": normalized["weight"] or "",
            "bust": normalized["bust"] or "",
            "waist": normalized["waist"] or "",
            "hips": normalized["hips"] or "",
        }
    return normalized


def profile_completion(profile: Dict[str, Any]) -> int:
    checks = [
        bool(profile.get("gender")),
        bool(profile.get("body_type")),
        bool(profile.get("skin_tone")),
        bool(profile.get("face_shape")),
        bool(profile.get("hair_type")),
        bool(profile.get("style_preferences")),
        any(bool(value) for value in (profile.get("measurements") or {}).values()),
    ]
    return sum(1 for item in checks if item)


def create_access_token(user: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["username"],
        "user_id": user["id"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


@contextmanager
def get_db_cursor(commit: bool = False):
    if not DATABASE_ENABLED:
        raise RuntimeError("Database is not configured")

    connection = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False,
    )
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def init_database() -> None:
    if not DATABASE_ENABLED:
        logger.info("Database env vars not set. Running in JSON file mode: %s", JSON_STATE_PATH)
        return

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                subscription_tier VARCHAR(50) DEFAULT 'free',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL UNIQUE,
                gender VARCHAR(50),
                body_type VARCHAR(50),
                skin_tone VARCHAR(50),
                face_shape VARCHAR(50),
                hair_type JSON,
                style_preferences JSON,
                measurements JSON,
                height VARCHAR(20),
                weight VARCHAR(20),
                bust VARCHAR(20),
                waist VARCHAR(20),
                hips VARCHAR(20),
                completed_sections INT DEFAULT 0,
                is_complete BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                session_id VARCHAR(255) NOT NULL UNIQUE,
                user_id INT NOT NULL,
                session_name VARCHAR(100) DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT PRIMARY KEY AUTO_INCREMENT,
                session_id VARCHAR(255) NOT NULL,
                user_id INT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT,
                tokens INT DEFAULT 0,
                image_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session_id (session_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )


def fetch_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    if DATABASE_ENABLED:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cursor.fetchone()
    return in_memory_state["users"].get(username)


def fetch_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    if DATABASE_ENABLED:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()
    for user in in_memory_state["users"].values():
        if user["id"] == user_id:
            return user
    return None


def create_user(username: str, email: str, password: str) -> Dict[str, Any]:
    if fetch_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already exists")

    password_hash = hash_password(password)
    if DATABASE_ENABLED:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash),
            )
            user_id = cursor.lastrowid
        return fetch_user_by_id(user_id)

    user = {
        "id": in_memory_state["next_user_id"],
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "subscription_tier": "free",
        "is_active": True,
        "created_at": now_iso(),
    }
    in_memory_state["users"][username] = user
    in_memory_state["next_user_id"] += 1
    persist_json_state()
    return user


def save_session(user_id: int, session_id: str, session_name: str) -> None:
    if DATABASE_ENABLED:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO user_sessions (session_id, user_id, session_name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE session_name = VALUES(session_name), last_activity = CURRENT_TIMESTAMP
                """,
                (session_id, user_id, session_name),
            )
        return

    in_memory_state["sessions"][session_id] = {
        "session_id": session_id,
        "user_id": user_id,
        "session_name": session_name,
        "created_at": now_iso(),
        "last_activity": now_iso(),
    }
    persist_json_state()


def list_sessions(user_id: int) -> List[Dict[str, Any]]:
    if DATABASE_ENABLED:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT us.session_id, us.session_name, us.last_activity, COUNT(cm.id) AS message_count
                FROM user_sessions us
                LEFT JOIN chat_messages cm ON cm.session_id = us.session_id
                WHERE us.user_id = %s
                GROUP BY us.session_id, us.session_name, us.last_activity
                ORDER BY us.last_activity DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall() or []
            return [
                {
                    "id": row["session_id"],
                    "title": row["session_name"],
                    "last_activity": row["last_activity"].isoformat() if row["last_activity"] else None,
                    "message_count": row["message_count"] or 0,
                }
                for row in rows
            ]

    sessions = []
    for session in in_memory_state["sessions"].values():
        if session["user_id"] == user_id:
            sessions.append(
                {
                    "id": session["session_id"],
                    "title": session["session_name"],
                    "last_activity": session["last_activity"].isoformat(),
                    "message_count": len(in_memory_state["messages"].get(session["session_id"], [])),
                }
            )
    return sorted(sessions, key=lambda item: item["last_activity"] or "", reverse=True)


def save_profile(user_id: int, profile: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_profile(profile)
    completed_sections = profile_completion(normalized)
    is_complete = completed_sections >= 4

    if DATABASE_ENABLED:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO user_profiles (
                    user_id, gender, body_type, skin_tone, face_shape, hair_type,
                    style_preferences, measurements, height, weight, bust, waist, hips,
                    completed_sections, is_complete
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    gender = VALUES(gender),
                    body_type = VALUES(body_type),
                    skin_tone = VALUES(skin_tone),
                    face_shape = VALUES(face_shape),
                    hair_type = VALUES(hair_type),
                    style_preferences = VALUES(style_preferences),
                    measurements = VALUES(measurements),
                    height = VALUES(height),
                    weight = VALUES(weight),
                    bust = VALUES(bust),
                    waist = VALUES(waist),
                    hips = VALUES(hips),
                    completed_sections = VALUES(completed_sections),
                    is_complete = VALUES(is_complete)
                """,
                (
                    user_id,
                    normalized["gender"],
                    normalized["body_type"],
                    normalized["skin_tone"],
                    normalized["face_shape"],
                    json.dumps(normalized["hair_type"]),
                    json.dumps(normalized["style_preferences"]),
                    json.dumps(normalized["measurements"]),
                    normalized["height"],
                    normalized["weight"],
                    normalized["bust"],
                    normalized["waist"],
                    normalized["hips"],
                    completed_sections,
                    is_complete,
                ),
            )
        return {"profile_id": user_id, "completed_sections": completed_sections, "is_complete": is_complete, "profile_data": normalized}

    in_memory_state["profiles"][user_id] = normalized
    persist_json_state()
    return {"profile_id": user_id, "completed_sections": completed_sections, "is_complete": is_complete, "profile_data": normalized}


def get_profile(user_id: int) -> Optional[Dict[str, Any]]:
    if DATABASE_ENABLED:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            row["hair_type"] = json.loads(row["hair_type"] or "[]")
            row["style_preferences"] = json.loads(row["style_preferences"] or "[]")
            row["measurements"] = json.loads(row["measurements"] or "{}")
            return normalize_profile(row)
    return in_memory_state["profiles"].get(user_id)


def save_message(session_id: str, user_id: Optional[int], role: str, content: str, image_data: Optional[Dict[str, Any]] = None) -> None:
    tokens = max(1, len(content.split())) if content else 0
    if DATABASE_ENABLED:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "INSERT INTO chat_messages (session_id, user_id, role, content, tokens, image_data) VALUES (%s, %s, %s, %s, %s, %s)",
                (session_id, user_id, role, content, tokens, json.dumps(image_data) if image_data else None),
            )
            if user_id is not None:
                cursor.execute("UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_id = %s", (session_id,))
        return

    in_memory_state["messages"].setdefault(session_id, []).append(
        {
            "role": role,
            "text": content,
            "timestamp": now_iso(),
            "tokens": tokens,
            "imageData": image_data,
            "user_id": user_id,
        }
    )
    if session_id in in_memory_state["sessions"]:
        in_memory_state["sessions"][session_id]["last_activity"] = now_iso()
    persist_json_state()


def get_messages(session_id: str, user_id: Optional[int]) -> List[Dict[str, Any]]:
    if DATABASE_ENABLED:
        with get_db_cursor() as cursor:
            if user_id is not None:
                cursor.execute(
                    "SELECT role, content, tokens, image_data, created_at FROM chat_messages WHERE session_id = %s AND (user_id = %s OR user_id IS NULL) ORDER BY created_at ASC",
                    (session_id, user_id),
                )
            else:
                cursor.execute(
                    "SELECT role, content, tokens, image_data, created_at FROM chat_messages WHERE session_id = %s ORDER BY created_at ASC",
                    (session_id,),
                )
            rows = cursor.fetchall() or []
            return [
                {
                    "role": row["role"],
                    "text": row["content"] or "",
                    "timestamp": row["created_at"].isoformat() if row["created_at"] else datetime.now(timezone.utc).isoformat(),
                    "tokens": row["tokens"] or 0,
                    "imageData": json.loads(row["image_data"]) if row.get("image_data") else None,
                }
                for row in rows
            ]
    return in_memory_state["messages"].get(session_id, [])


def clear_session_messages(session_id: str, user_id: Optional[int]) -> None:
    if DATABASE_ENABLED:
        with get_db_cursor(commit=True) as cursor:
            if user_id is not None:
                cursor.execute("DELETE FROM chat_messages WHERE session_id = %s AND user_id = %s", (session_id, user_id))
                cursor.execute("DELETE FROM user_sessions WHERE session_id = %s AND user_id = %s", (session_id, user_id))
            else:
                cursor.execute("DELETE FROM chat_messages WHERE session_id = %s", (session_id,))
        return

    in_memory_state["messages"].pop(session_id, None)
    if user_id is not None:
        in_memory_state["sessions"].pop(session_id, None)
    persist_json_state()


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    payload = decode_access_token(credentials.credentials)
    user = fetch_user_by_id(int(payload["user_id"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


class RenderLLM:
    async def generate(self, session_id: str, query: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        lowered = query.lower()
        if any(word in lowered for word in ["image", "picture", "generate", "photo"]):
            image_id = f"render_{uuid.uuid4().hex[:10]}"
            filename = f"{image_id}.png"
            filepath = GENERATED_IMAGES_DIR / filename
            filepath.write_bytes(base64.b64decode(MOCK_IMAGE_BASE64))
            return {
                "type": "image",
                "image_id": image_id,
                "filename": filename,
                "url": f"/images/{filename}",
                "prompt": query,
                "model": "render-mock",
                "size": "512x512",
                "format": "png",
                "image_base64": MOCK_IMAGE_BASE64,
            }
        return {
            "type": "text",
            "content": f"Style recommendation: {query}. Try a clean silhouette, one accent color, and simple accessories.",
            "tokens": max(1, len(query.split())),
        }

    def stream_generate(self, session_id: str, query: str, user_id: Optional[int] = None):
        response = self.generate_sync(session_id, query, user_id=user_id)
        if response["type"] == "image":
            yield f"data: {json.dumps(response)}\n\n"
            return
        for word in response["content"].split():
            yield f"data: {json.dumps({'type': 'text', 'content': word + ' '})}\n\n"
            time.sleep(0.02)

    def generate_sync(self, session_id: str, query: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        lowered = query.lower()
        if any(word in lowered for word in ["image", "picture", "generate", "photo"]):
            image_id = f"render_{uuid.uuid4().hex[:10]}"
            filename = f"{image_id}.png"
            filepath = GENERATED_IMAGES_DIR / filename
            filepath.write_bytes(base64.b64decode(MOCK_IMAGE_BASE64))
            return {
                "type": "image",
                "image_id": image_id,
                "filename": filename,
                "url": f"/images/{filename}",
                "prompt": query,
                "model": "render-mock",
                "size": "512x512",
                "format": "png",
                "image_base64": MOCK_IMAGE_BASE64,
            }
        return {
            "type": "text",
            "content": f"Style recommendation: {query}. Try a clean silhouette, one accent color, and simple accessories.",
            "tokens": max(1, len(query.split())),
        }


llm = RenderLLM()


@app.on_event("startup")
async def on_startup() -> None:
    init_database()
    if DATABASE_ENABLED:
        if not fetch_user_by_username("demo"):
            create_user("demo", "demo@example.com", "demo123")
    else:
        load_json_state()


@app.get("/ready")
async def ready() -> Dict[str, Any]:
    return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "database": "mysql" if DATABASE_ENABLED else "json",
        "json_state_path": None if DATABASE_ENABLED else str(JSON_STATE_PATH),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/auth/register")
async def register(payload: RegisterRequest) -> Dict[str, Any]:
    user = create_user(payload.username.strip(), payload.email.strip(), payload.password)
    return {"status": "success", "user_id": user["id"], "username": user["username"]}


@app.post("/auth/login")
async def login(payload: AuthRequest) -> Dict[str, Any]:
    user = fetch_user_by_username(payload.username.strip())
    if not user or not bcrypt.checkpw(payload.password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_id = str(uuid.uuid4())
    save_session(user["id"], session_id, "New Chat")
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user_id": user["id"],
        "username": user["username"],
        "session_id": session_id,
    }


@app.get("/auth/verify")
async def verify(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {"valid": True, "user_id": user["id"], "username": user["username"]}


@app.get("/auth/profile")
async def auth_profile(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    created_at = user.get("created_at")
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "subscription_tier": user.get("subscription_tier", "free"),
        "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
    }


@app.post("/auth/logout")
async def logout(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {"status": "success", "user_id": user["id"]}


@app.get("/profile/status")
async def profile_status(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    profile = get_profile(user["id"])
    if not profile:
        return {"status": "success", "is_complete": False, "completed_sections": 0, "profile_data": None}
    completed_sections = profile_completion(profile)
    return {"status": "success", "is_complete": completed_sections >= 4, "completed_sections": completed_sections, "profile_data": profile}


@app.get("/profile/get")
async def profile_get(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    profile = get_profile(user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    completed_sections = profile_completion(profile)
    return {"status": "success", "is_complete": completed_sections >= 4, "completed_sections": completed_sections, "profile_data": profile}


@app.post("/profile/save")
async def profile_save(payload: ProfileSaveRequest, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    result = save_profile(user["id"], payload.profile_data.model_dump())
    save_session(user["id"], payload.session_id, "New Chat")
    return {
        "status": "success",
        "profile_id": result["profile_id"],
        "completed_sections": result["completed_sections"],
        "is_complete": result["is_complete"],
        "message": "Profile saved successfully",
        "profile_data": result["profile_data"],
    }


@app.get("/chat/sessions")
async def chat_sessions(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {"sessions": list_sessions(user["id"])}


@app.post("/chat/session/new")
async def chat_session_new(payload: SessionCreateRequest, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    session_id = payload.session_id or str(uuid.uuid4())
    save_session(user["id"], session_id, payload.session_name)
    return {"status": "success", "session_id": session_id, "session_name": payload.session_name}


@app.get("/chat/history/{session_id}")
async def chat_history(session_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {"messages": get_messages(session_id, user["id"])}


@app.post("/chat/clear")
async def chat_clear(request: Request, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    session_id = request.query_params.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    clear_session_messages(session_id, user["id"])
    return {"status": "success", "session_id": session_id}


def stream_chat_response(session_id: str, query: str, user_id: Optional[int]):
    save_message(session_id, user_id, "user", query)
    full_text = ""
    image_data = None
    for chunk in llm.stream_generate(session_id, query, user_id=user_id):
        yield chunk
        try:
            payload = json.loads(chunk[6:].strip())
        except Exception:
            continue
        if payload.get("type") == "text":
            full_text += payload.get("content", "")
        elif payload.get("type") == "image":
            image_data = payload
    save_message(session_id, user_id, "assistant", full_text or "Here's the image you requested:", image_data=image_data)


@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    return StreamingResponse(stream_chat_response(payload.session_id, payload.query, None), media_type="text/event-stream")


@app.post("/chat/authenticated/stream")
async def chat_authenticated_stream(payload: ChatRequest, user: Dict[str, Any] = Depends(get_current_user)) -> StreamingResponse:
    save_session(user["id"], payload.session_id, "New Chat")
    return StreamingResponse(stream_chat_response(payload.session_id, payload.query, user["id"]), media_type="text/event-stream")


@app.post("/chat")
async def chat(payload: ChatRequest) -> Dict[str, Any]:
    response = llm.generate_sync(payload.session_id, payload.query)
    save_message(payload.session_id, None, "user", payload.query)
    save_message(payload.session_id, None, "assistant", response.get("content", "Here's the image you requested:"), image_data=response if response.get("type") == "image" else None)
    return {"status": "success", "response": response, "session_id": payload.session_id}


@app.get("/images/{filename:path}")
async def serve_image(filename: str) -> FileResponse:
    filepath = GENERATED_IMAGES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath, media_type="image/png")


@app.get("/api-status")
async def api_status() -> Dict[str, Any]:
    return {
        "status": "live",
        "database_mode": "mysql" if DATABASE_ENABLED else "json",
        "json_state_path": None if DATABASE_ENABLED else str(JSON_STATE_PATH),
        "endpoints": ["/auth/login", "/profile/save", "/chat/authenticated/stream"],
    }


@app.get("/", response_class=HTMLResponse)
async def index() -> Any:
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<html><body><h1>Smart Fashion API</h1><p>Frontend build not found. Run the frontend build first.</p></body></html>")


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str) -> Any:
    requested = STATIC_DIR / full_path
    if requested.exists() and requested.is_file():
        return FileResponse(requested)
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main_render:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

