"""
UAI Chat API - Complete Fixed Main File with Profile Setup including Gender
Author: Your Name
Version: 3.3.1
Description: FastAPI backend for UAI Chat with authentication, database, streaming, and profile setup with gender field
"""

import time
import json
import traceback
import os
import logging
from contextlib import contextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Dict, Any, Union, List, Generator
from datetime import datetime, timedelta
import bcrypt
import jwt
import secrets
from .data import *
import uuid
from dotenv import load_dotenv
import asyncio
import aiofiles
from pathlib import Path
import base64

# Load environment variables
load_dotenv()

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ==================== DATABASE MODELS ====================
class ChatRequest(BaseModel):
    session_id: str = Field(default="default", description="Chat session ID")
    query: str = Field(default="", description="User query/message")
    user_id: Optional[int] = Field(default=None, description="User ID for authenticated requests")

class ChatResponse(BaseModel):
    status: str = Field(default="error", description="Response status")
    response: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    response_time_seconds: float = Field(default=0.0, description="Response time in seconds")

class ClearRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to clear")

class StatsRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to get stats for")

class SessionCreate(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Custom session ID")
    session_name: str = Field(default="New Chat", description="Session name")

class SessionInfo(BaseModel):
    id: str
    title: str
    last_activity: Optional[str]
    message_count: int

class Message(BaseModel):
    role: str
    text: str
    timestamp: str
    tokens: int
    imageData: Optional[Dict[str, Any]]

# ==================== PROFILE SETUP MODELS ====================
class ProfileData(BaseModel):
    gender: Optional[str] = Field(None, description="Gender (Male, Female, Non-binary, Prefer not to say)")
    body_type: Optional[str] = Field(None, description="Body type (Rectangle, Hourglass, Pear, Apple, Inverted Triangle)")
    skin_tone: Optional[str] = Field(None, description="Skin tone (Fair, Light, Medium, Olive, Tan, Dark)")
    face_shape: Optional[str] = Field(None, description="Face shape (Oval, Round, Square, Heart, Diamond, Oblong)")
    hair_type: Optional[str] = Field(None, description="Hair type (Straight, Wavy, Curly, Coily, Bald, Short, Long)")
    style_preferences: Optional[List[str]] = Field(default_factory=list, description="Style preferences list")
    measurements: Optional[Dict[str, str]] = Field(default_factory=dict, description="Body measurements")
    height: Optional[str] = Field(None, description="Height in cm")
    weight: Optional[str] = Field(None, description="Weight in kg")
    bust: Optional[str] = Field(None, description="Bust measurement")
    waist: Optional[str] = Field(None, description="Waist measurement")
    hips: Optional[str] = Field(None, description="Hips measurement")

class ProfileRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    profile_data: ProfileData

class ProfileResponse(BaseModel):
    status: str = Field(default="success", description="Response status")
    profile_id: Optional[int] = Field(None, description="Profile ID")
    is_complete: bool = Field(default=False, description="Whether profile is complete")
    completed_sections: int = Field(default=0, description="Number of completed sections")
    message: str = Field(default="", description="Response message")

class ProfileStatusResponse(BaseModel):
    status: str = Field(default="success", description="Response status")
    is_complete: bool = Field(default=False, description="Whether profile is complete")
    completed_sections: int = Field(default=0, description="Number of completed sections")
    profile_data: Optional[ProfileData] = Field(None, description="Profile data")
    message: str = Field(default="", description="Response message")

# ==================== AUTHENTICATION MODELS ====================
class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    session_id: str = Field(..., description="Session ID")

class UserProfile(BaseModel):
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    created_at: datetime = Field(..., description="Account creation date")
    subscription_tier: str = Field(default="free", description="Subscription tier")
    stats: Dict[str, Any] = Field(default_factory=dict, description="User statistics")

class TokenData(BaseModel):
    user_id: int
    username: str

# ==================== JWT CONFIGURATION ====================
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = os.getenv('ALGORITHM', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 1440))

# ==================== FILE PATHS ====================
BASE_DIR = Path(__file__).parent.parent
GENERATED_IMAGES_DIR = BASE_DIR / "generated_images"
STATIC_DIR = BASE_DIR / "static"
LOGS_DIR = BASE_DIR / "logs"

print(f"BASE_DIR: {BASE_DIR}")
print(f"GENERATED_IMAGES_DIR: {GENERATED_IMAGES_DIR}")
print(f"GENERATED_IMAGES_DIR exists: {GENERATED_IMAGES_DIR.exists()}")

# Create directories
for directory in [GENERATED_IMAGES_DIR, STATIC_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== SECURITY ====================
security = HTTPBearer(auto_error=False)

# ==================== DATABASE POOL ====================


# ==================== PASSWORD UTILITIES ====================
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

# ==================== JWT UTILITIES ====================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_jwt_token(token: str) -> Optional[TokenData]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("sub")
        
        if user_id is None or username is None:
            return None
            
        return TokenData(user_id=user_id, username=username)
    except jwt.ExpiredSignatureError:
        logger.info("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        return None

# ==================== AUTHENTICATION DEPENDENCY ====================
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token_data = decode_jwt_token(credentials.credentials)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify user exists and is active
        user = get_user(token_data.user_id)
        if not user or not user.get('is_active'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return {
            "user_id": user['id'],
            "username": user['username'],
            "email": user['email']
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )

# ==================== LLM INITIALIZATION ====================
try:
    logger.info("Attempting to import real LLM from app.services.agent...")
    from app.services.agent import llm as real_llm
    llm = real_llm
    logger.info("✅ Successfully imported real LLM from app.services.agent")
    
    try:
        from app.services.memory import cleanup_old_sessions, get_session_stats
        logger.info("✅ Successfully imported memory functions")
    except ImportError as e:
        logger.info(f"⚠️ Could not import memory functions: {e}")
        def cleanup_old_sessions(days: int = 7) -> int:
            return 0
        
        def get_session_stats(session_id: str) -> Dict[str, Any]:
            return {"message_count": 0, "session_age": 0, "session_id": session_id}
        
except ImportError as e:
    logger.warning(f"❌ Using mock LLM: {e}")
    traceback.print_exc()
    
    class MockLLM:
        def __init__(self):
            self.sessions = {}
            logger.info("Mock LLM initialized")
            self.image_store = {}
        
        async def generate(self, session_id: str, user_input: str, user_id: Optional[int] = None) -> Dict[str, Any]:
            await asyncio.sleep(0.5)
            
            if "image" in user_input.lower() or "picture" in user_input.lower() or "generate" in user_input.lower():
                image_id = f"img_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                filename = f"{image_id}.png"
                filepath = GENERATED_IMAGES_DIR / filename
                
                test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
                
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(test_image_base64))
                
                image_data = {
                    "type": "image",
                    "image_id": image_id,
                    "filename": filename,
                    "prompt": user_input,
                    "model": "mock-image-generator",
                    "size": "1x1",
                    "url": f"/images/{filename}",
                    "image_base64": test_image_base64
                }
                
                self.image_store[session_id] = image_data
                
                return image_data
            else:
                return {
                    "type": "text",
                    "content": f"Mock response to: {user_input}",
                    "tokens": len(user_input.split())
                }
        
        async def stream_generate(self, session_id: str, user_input: str, user_id: Optional[int] = None) -> Generator[str, None, None]:
            if "image" in user_input.lower() or "picture" in user_input.lower() or "generate" in user_input.lower():
                image_id = f"img_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                filename = f"{image_id}.png"
                filepath = GENERATED_IMAGES_DIR / filename
                
                test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
                
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(test_image_base64))
                
                image_data = {
                    "type": "image",
                    "image_id": image_id,
                    "filename": filename,
                    "prompt": user_input,
                    "model": "mock-image-generator",
                    "size": "1x1",
                    "url": f"/images/{filename}",
                    "image_base64": test_image_base64
                }
                
                self.image_store[session_id] = image_data
                
                yield json.dumps(image_data)
            else:
                words = ["Hello!", "This", "is", "a", "mock", "streaming", "response"]
                for i, word in enumerate(words):
                    await asyncio.sleep(0.1)
                    yield json.dumps({
                        "type": "text",
                        "content": word + (" " if i < len(words) - 1 else "")
                    })
        
        async def clear_session_memory(self, session_id: str) -> Dict[str, Any]:
            return {"status": "success", "message": "Session memory cleared"}
    
    llm = MockLLM()
    
    def cleanup_old_sessions(days: int = 7) -> int:
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """DELETE FROM chat_messages 
                       WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
                       AND user_id IS NULL""",
                    (days,)
                )
                deleted = cursor.rowcount
                
                cursor.execute(
                    """DELETE FROM user_sessions 
                       WHERE last_activity < DATE_SUB(NOW(), INTERVAL %s DAY)""",
                    (days,)
                )
                deleted += cursor.rowcount
                
                return deleted
        except Exception:
            return 0
    
    def get_session_stats(session_id: str) -> Dict[str, Any]:
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = %s",
                    (session_id,)
                )
                msg_count = cursor.fetchone()['count'] or 0
                
                cursor.execute(
                    """SELECT TIMESTAMPDIFF(MINUTE, MIN(created_at), NOW()) as age_minutes 
                       FROM chat_messages WHERE session_id = %s""",
                    (session_id,)
                )
                age_result = cursor.fetchone()
                age_minutes = age_result['age_minutes'] if age_result else 0
                
                return {
                    "message_count": msg_count,
                    "session_age_minutes": age_minutes,
                    "session_id": session_id
                }
        except Exception:
            return {"message_count": 0, "session_age_minutes": 0, "session_id": session_id}

# ==================== PROFILE HELPER FUNCTIONS ====================
def create_user_profile_table():
    """Create user_profiles table if it doesn't exist"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # First check if table exists
            cursor.execute("SHOW TABLES LIKE 'user_profiles'")
            if cursor.fetchone():
                # Check if trigger exists and drop it
                cursor.execute("SHOW TRIGGERS LIKE 'user_profiles'")
                trigger = cursor.fetchone()
                if trigger:
                    try:
                        cursor.execute("DROP TRIGGER IF EXISTS user_profiles_trigger")
                        logger.info("Dropped problematic trigger from user_profiles table")
                    except Exception as e:
                        logger.error(f"Error dropping trigger: {e}")
            
            # Create table with gender field
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL UNIQUE,
                    gender VARCHAR(50),
                    body_type VARCHAR(50),
                    skin_tone VARCHAR(50),
                    face_shape VARCHAR(50),
                    hair_type VARCHAR(50),
                    style_preferences JSON,
                    measurements JSON,
                    height VARCHAR(20),
                    weight VARCHAR(20),
                    bust VARCHAR(20),
                    waist VARCHAR(20),
                    hips VARCHAR(20),
                    completed_sections INT DEFAULT 0,
                    is_complete BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Try to add indexes
            try:
                cursor.execute("CREATE INDEX idx_user_id ON user_profiles(user_id)")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Could not create idx_user_id: {e}")
            
            try:
                cursor.execute("CREATE INDEX idx_is_complete ON user_profiles(is_complete)")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Could not create idx_is_complete: {e}")
            
            try:
                cursor.execute("CREATE INDEX idx_gender ON user_profiles(gender)")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Could not create idx_gender: {e}")
            
            logger.info("User profiles table created/verified with gender field")
    except Exception as e:
        logger.error(f"Error creating user_profiles table: {e}")

save_user_profile(user_id, profile_data.dict())

def get_user_profile_from_db(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile from database"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, user_id, gender, body_type, skin_tone, face_shape, hair_type,
                    style_preferences, measurements, height, weight, bust,
                    waist, hips, completed_sections, is_complete,
                    created_at, updated_at
                FROM user_profiles 
                WHERE user_id = %s
            """, (user_id,))
            
            profile = cursor.fetchone()
            
            if not profile:
                return None
            
            # Parse JSON fields
            if profile['style_preferences']:
                try:
                    profile['style_preferences'] = json.loads(profile['style_preferences'])
                except:
                    profile['style_preferences'] = []
            else:
                profile['style_preferences'] = []
            
            if profile['measurements']:
                try:
                    profile['measurements'] = json.loads(profile['measurements'])
                except:
                    profile['measurements'] = {}
            else:
                profile['measurements'] = {}
            
            return profile
            
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None

def get_profile_status_from_db(user_id: int) -> Dict[str, Any]:
    """Get profile completion status from database"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT completed_sections, is_complete 
                FROM user_profiles 
                WHERE user_id = %s
            """, (user_id,))
            
            profile = cursor.fetchone()
            
            if not profile:
                return {
                    "is_complete": False,
                    "completed_sections": 0,
                    "has_profile": False
                }
            
            return {
                "is_complete": bool(profile['is_complete']),
                "completed_sections": profile['completed_sections'],
                "has_profile": True
            }
            
    except Exception as e:
        logger.error(f"Error getting profile status: {e}")
        return {
            "is_complete": False,
            "completed_sections": 0,
            "has_profile": False
        }

# ==================== OTHER HELPER FUNCTIONS ====================
def create_missing_tables():
    """Create missing database tables if they don't exist"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Create images table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    image_id VARCHAR(255) NOT NULL UNIQUE,
                    user_id INT NULL,
                    prompt TEXT,
                    filename VARCHAR(255),
                    url VARCHAR(500),
                    model VARCHAR(100),
                    size VARCHAR(50),
                    format VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_image_id (image_id),
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Create user_profiles table with gender
            create_user_profile_table()
            
            # Check and create other tables if needed
            tables = ['users', 'user_sessions', 'chat_messages', 'user_statistics']
            for table in tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    logger.warning(f"Table '{table}' doesn't exist. Run database.sql to create all tables.")
            
            logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

def save_image_metadata(image_data: Dict[str, Any], user_id: Optional[int] = None) -> None:
    """Save image metadata to database"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """INSERT INTO images 
                   (image_id, user_id, prompt, filename, url, model, size, format)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    image_data.get('image_id'),
                    user_id,
                    image_data.get('prompt'),
                    image_data.get('filename'),
                    image_data.get('url'),
                    image_data.get('model'),
                    image_data.get('size'),
                    'png'
                )
            )
    except Exception as e:
        logger.error(f"Failed to save image metadata: {e}")

def update_user_statistics(user_id: int, messages: int = 0, images: int = 0, tokens: int = 0) -> None:
    """Update user statistics"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """UPDATE user_statistics 
                   SET total_messages = total_messages + %s,
                       total_images = total_images + %s,
                       total_tokens = total_tokens + %s,
                       last_updated = NOW()
                   WHERE user_id = %s""",
                (messages, images, tokens, user_id)
            )
            
            if cursor.rowcount == 0:
                cursor.execute(
                    """INSERT INTO user_statistics 
                       (user_id, total_messages, total_images, total_tokens)
                       VALUES (%s, %s, %s, %s)""",
                    (user_id, messages, images, tokens)
                )
    except Exception as e:
        logger.error(f"Failed to update user statistics: {e}")

# ==================== FASTAPI APP ====================
app = FastAPI(
    title="UAI Chat API",
    version="3.3.1",
    description="Ultra AI Chat Assistant with Authentication, Profile Setup (including Gender), and Image Generation",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    servers=[
        {"url": "http://localhost:8000", "description": "Local development server"},
        {"url": "http://127.0.0.1:8000", "description": "Local server"},
    ],
    contact={
        "name": "UAI Support",
        "email": "support@uai.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# ==================== CORS MIDDLEWARE ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Serve frontend static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/", StaticFiles(directory="static", html=True), name="frontend")

# ==================== STATIC FILES ====================
@app.get("/images/{filename}")
async def get_image(filename: str):
    """Serve image files"""
    file_path = GENERATED_IMAGES_DIR / filename
    logger.info(f"Looking for image at: {file_path}")
    
    if file_path.exists() and file_path.is_file():
        if filename.lower().endswith('.png'):
            media_type = 'image/png'
        elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            media_type = 'image/jpeg'
        elif filename.lower().endswith('.gif'):
            media_type = 'image/gif'
        elif filename.lower().endswith('.webp'):
            media_type = 'image/webp'
        else:
            media_type = 'application/octet-stream'
        
        logger.info(f"Serving image: {filename} ({media_type})")
        return FileResponse(file_path, media_type=media_type)
    else:
        logger.warning(f"Image not found: {filename}")
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

@app.get("/static/{filename}")
async def get_static(filename: str):
    """Serve static files"""
    file_path = STATIC_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")

logger.info(f"Serving static files from: {GENERATED_IMAGES_DIR}")

# ==================== HTML LANDING PAGE ====================
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UAI Chat API</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
        }
        h1 {
            color: #764ba2;
            margin-top: 0;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            font-size: 2.5em;
        }
        .status {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #4caf50;
            margin: 20px 0;
            font-weight: bold;
        }
        .endpoints {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .endpoint {
            display: flex;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .method {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            min-width: 70px;
            text-align: center;
            margin-right: 15px;
        }
        .path {
            font-family: monospace;
            color: #333;
            flex: 1;
        }
        .docs-link {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 10px;
            font-weight: bold;
            margin-top: 20px;
            transition: transform 0.2s;
        }
        .docs-link:hover {
            transform: translateY(-2px);
        }
        .badge {
            background: #ff5722;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 UAI Chat API</h1>
        <div class="status">
            ✅ API is running! Version 3.3.1
            <span class="badge">Ready</span>
        </div>
        
        <p>Welcome to the UAI Chat API backend. This is a REST API, not a web application. To interact with the API:</p>
        
        <div class="endpoints">
            <h3>📋 Quick Links:</h3>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/ - API Status</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/health - Health Check</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/test - Test Endpoint</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/docs - API Documentation (Swagger UI)</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/redoc - Alternative Documentation</span>
            </div>
        </div>

        <a href="/docs" class="docs-link">📚 View API Documentation (Swagger UI)</a>
        <a href="/redoc" style="margin-left: 10px;" class="docs-link">📖 View ReDoc</a>
        
        <div style="margin-top: 30px;">
            <h3>🔧 Frontend Integration:</h3>
            <p>Use this URL in your frontend application:</p>
            <code style="background: #f5f5f5; padding: 10px; display: block; border-radius: 5px; font-size: 1.1em;">
                const API_URL = "http://127.0.0.1:8000";
            </code>
            <p style="margin-top: 15px; color: #666;">
                <strong>Note:</strong> This API supports CORS. Make sure your frontend is running on 
                http://localhost:3000, http://localhost:5173, or another allowed origin.
            </p>
        </div>

        <div class="footer">
            <p>Server Time: <span id="timestamp"></span></p>
            <script>
                document.getElementById('timestamp').textContent = new Date().toLocaleString();
            </script>
            <p>UAI Chat API - All endpoints require authentication unless marked public</p>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse, tags=["info"], summary="Root endpoint with HTML landing page")
async def root():
    """Root endpoint with HTML landing page"""
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/api-status", tags=["info"], summary="API status (JSON)")
async def api_status():
    """API status endpoint returning JSON"""
    return {
        "message": "UAI Chat API is running",
        "status": "ok",
        "version": "3.3.1",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "openapi": "/openapi.json"
        }
    }

@app.get("/health", tags=["info"], summary="Health check")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "uai-chat-api",
        "version": "3.3.1"
    }
    
    # Check database
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check images directory
    try:
        images_count = len(list(GENERATED_IMAGES_DIR.glob("*")))
        health_status["images"] = {
            "directory": str(GENERATED_IMAGES_DIR),
            "exists": True,
            "count": images_count
        }
    except Exception as e:
        health_status["images"] = {
            "error": str(e),
            "exists": False
        }
        health_status["status"] = "degraded"
    
    health_status["llm"] = "real" if not hasattr(llm, '__class__') or llm.__class__.__name__ != 'MockLLM' else "mock"
    
    return health_status

@app.get("/test", tags=["info"], summary="Test endpoint")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "Test successful",
        "timestamp": datetime.now().isoformat(),
        "status": "ok"
    }

# ==================== AUTHENTICATION ENDPOINTS ====================
@app.post("/auth/register", tags=["authentication"], summary="Register new user")
async def register(user: UserRegistration):
    """Register a new user"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if user exists
            cursor.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (user.username, user.email)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists"
                )
            
            # Hash password and create user
            hashed_password = hash_password(user.password)
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, subscription_tier, is_active)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user.username, user.email, hashed_password, "free", True)
            )
            
            user_id = cursor.lastrowid
            
            # Initialize statistics
            cursor.execute(
                "INSERT INTO user_statistics (user_id) VALUES (%s)",
                (user_id,)
            )
            
            logger.info(f"New user registered: {user.username} (ID: {user_id})")
            
            return {
                "status": "success",
                "message": "User registered successfully",
                "user_id": user_id,
                "username": user.username
            }
            
    except MySQLError as e:
        logger.error(f"Database error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during registration"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/login", response_model=TokenResponse, tags=["authentication"], summary="Login user")
async def login(user: UserLogin, request: Request):
    """Authenticate user and return JWT token"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Get user
            cursor.execute(
                """SELECT id, username, email, password_hash, is_active 
                   FROM users WHERE username = %s""",
                (user.username,)
            )
            db_user = cursor.fetchone()
            
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            if not db_user['is_active']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated"
                )
            
            # Verify password
            if not verify_password(user.password, db_user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = NOW() WHERE id = %s",
                (db_user['id'],)
            )
            
            # Create session
            session_id = str(uuid.uuid4())
            ip_address = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            cursor.execute(
                """INSERT INTO user_sessions 
                   (session_id, user_id, session_name, ip_address, user_agent)
                   VALUES (%s, %s, %s, %s, %s)""",
                (session_id, db_user['id'], "New Chat", ip_address, user_agent)
            )
            
            # Create token
            access_token = create_access_token(
                data={"sub": db_user['username'], "user_id": db_user['id']}
            )
            
            logger.info(f"User logged in: {user.username} (Session: {session_id})")
            
            return TokenResponse(
                access_token=access_token,
                user_id=db_user['id'],
                username=db_user['username'],
                session_id=session_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@app.post("/auth/logout", tags=["authentication"], summary="Logout user")
async def logout(
    request: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Logout user by invalidating session"""
    try:
        session_id = request.get('session_id')
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required"
            )
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM user_sessions WHERE session_id = %s AND user_id = %s",
                (session_id, current_user['user_id'])
            )
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            logger.info(f"User logged out: {current_user['username']} (Session: {session_id})")
            
            return {
                "status": "success",
                "message": "Logged out successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@app.get("/auth/verify", tags=["authentication"], summary="Verify token")
async def verify_token_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Verify if JWT token is valid"""
    return {
        "status": "valid",
        "user_id": current_user['user_id'],
        "username": current_user['username'],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/auth/profile", response_model=UserProfile, tags=["authentication"], summary="Get user profile")
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user profile with statistics"""
    try:
        with get_db_cursor() as cursor:
            # Get user details
            cursor.execute(
                """SELECT id, username, email, created_at, subscription_tier 
                   FROM users WHERE id = %s""",
                (current_user['user_id'],)
            )
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get statistics
            cursor.execute(
                """SELECT 
                       total_messages,
                       total_images,
                       total_tokens,
                       total_sessions,
                       last_updated
                   FROM user_statistics 
                   WHERE user_id = %s""",
                (current_user['user_id'],)
            )
            stats_row = cursor.fetchone()
            
            stats = {
                "message_count": stats_row['total_messages'] if stats_row else 0,
                "image_count": stats_row['total_images'] if stats_row else 0,
                "total_tokens": stats_row['total_tokens'] if stats_row else 0,
                "total_sessions": stats_row['total_sessions'] if stats_row else 0,
                "last_active": stats_row['last_updated'].isoformat() if stats_row and stats_row['last_updated'] else None
            }
            
            return UserProfile(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                created_at=user['created_at'],
                subscription_tier=user['subscription_tier'],
                stats=stats
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ==================== PROFILE SETUP ENDPOINTS ====================
@app.post("/profile/save", response_model=ProfileResponse, tags=["profile"], summary="Save user profile")
async def save_profile(
    request: ProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Save or update user profile data"""
    try:
        # Save to database
        result = save_user_profile_to_db(
            user_id=current_user['user_id'],
            profile_data=request.profile_data
        )
        
        # Update session activity
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE user_sessions SET last_activity = NOW() WHERE session_id = %s",
                (request.session_id,)
            )
        
        logger.info(f"Profile saved for user {current_user['username']} (Sections: {result['completed_sections']})")
        
        return ProfileResponse(
            status="success",
            profile_id=result["profile_id"],
            is_complete=result["is_complete"],
            completed_sections=result["completed_sections"],
            message=result["message"]
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Save profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {str(e)}"
        )

@app.get("/profile/get", response_model=ProfileStatusResponse, tags=["profile"], summary="Get user profile")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user profile data"""
    try:
        profile = get_user_profile_from_db(current_user['user_id'])
        
        if not profile:
            return ProfileStatusResponse(
                status="success",
                is_complete=False,
                completed_sections=0,
                profile_data=None,
                message="No profile found"
            )
        
        # Convert to ProfileData
        profile_data = ProfileData(
            gender=profile['gender'],
            body_type=profile['body_type'],
            skin_tone=profile['skin_tone'],
            face_shape=profile['face_shape'],
            hair_type=profile['hair_type'],
            style_preferences=profile['style_preferences'],
            measurements=profile['measurements'],
            height=profile['height'],
            weight=profile['weight'],
            bust=profile['bust'],
            waist=profile['waist'],
            hips=profile['hips']
        )
        
        return ProfileStatusResponse(
            status="success",
            is_complete=bool(profile['is_complete']),
            completed_sections=profile['completed_sections'],
            profile_data=profile_data,
            message="Profile retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )

@app.get("/profile/status", tags=["profile"], summary="Get profile completion status")
async def get_profile_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get profile completion status"""
    try:
        status_info = get_profile_status_from_db(current_user['user_id'])
        
        return {
            "status": "success",
            "is_complete": status_info["is_complete"],
            "completed_sections": status_info["completed_sections"],
            "has_profile": status_info["has_profile"],
            "message": f"Profile is {'complete' if status_info['is_complete'] else 'incomplete'} ({status_info['completed_sections']} sections completed)"
        }
        
    except Exception as e:
        logger.error(f"Profile status error: {e}", exc_info=True)
        return {
            "status": "error",
            "is_complete": False,
            "completed_sections": 0,
            "has_profile": False,
            "message": "Error checking profile status"
        }

@app.delete("/profile/reset", tags=["profile"], summary="Reset user profile")
async def reset_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Reset user profile data"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM user_profiles WHERE user_id = %s",
                (current_user['user_id'],)
            )
            
            deleted = cursor.rowcount
            
            if deleted > 0:
                logger.info(f"Profile reset for user {current_user['username']}")
                return {
                    "status": "success",
                    "message": "Profile reset successfully"
                }
            else:
                return {
                    "status": "success",
                    "message": "No profile to reset"
                }
            
    except Exception as e:
        logger.error(f"Reset profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset profile"
        )

# ==================== CHAT ENDPOINTS ====================
@app.post("/chat/authenticated", response_model=ChatResponse, tags=["chat"], summary="Authenticated chat")
async def authenticated_chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Regular chat endpoint for authenticated users"""
    start_time = time.time()
    logger.info(f"Chat request from user {current_user['username']} (Session: {request.session_id})")
    
    try:
        # Store user message
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """INSERT INTO chat_messages (session_id, user_id, role, content)
                   VALUES (%s, %s, %s, %s)""",
                (request.session_id, current_user['user_id'], "user", request.query)
            )
        
        # Get response from LLM
        response = await llm.generate(
            session_id=request.session_id,
            user_input=request.query,
            user_id=current_user['user_id']
        )
        
        response_time = time.time() - start_time
        
        # Store assistant response
        with get_db_cursor(commit=True) as cursor:
            if response.get('type') == 'image':
                # Save image metadata
                save_image_metadata(response, current_user['user_id'])
                
                cursor.execute(
                    """INSERT INTO chat_messages 
                       (session_id, user_id, role, content, image_data)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (request.session_id, current_user['user_id'], "assistant",
                     response.get('prompt', ''), json.dumps(response))
                )
                
                # Update statistics
                update_user_statistics(
                    user_id=current_user['user_id'],
                    images=1
                )
            else:
                tokens = response.get('tokens', len(response.get('content', '').split()))
                cursor.execute(
                    """INSERT INTO chat_messages 
                       (session_id, user_id, role, content, tokens)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (request.session_id, current_user['user_id'], "assistant",
                     response.get('content', ''), tokens)
                )
                
                # Update statistics
                update_user_statistics(
                    user_id=current_user['user_id'],
                    messages=1,
                    tokens=tokens
                )
        
        logger.info(f"Chat response sent to user {current_user['username']} in {response_time:.2f}s")
        
        return ChatResponse(
            status="success",
            response=response,
            response_time_seconds=response_time
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Chat error: {e}", exc_info=True)
        
        return ChatResponse(
            status="error",
            response={
                "type": "error",
                "content": f"An error occurred: {str(e)}",
                "timestamp": datetime.now().isoformat()
            },
            response_time_seconds=response_time
        )

@app.post("/chat/authenticated/stream", tags=["chat"], summary="Authenticated streaming chat")
async def authenticated_chat_stream(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Streaming chat endpoint for authenticated users"""
    start_time = time.time()
    logger.info(f"Stream chat request from user {current_user['username']} (Session: {request.session_id})")
    
    # Store user message
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """INSERT INTO chat_messages (session_id, user_id, role, content)
               VALUES (%s, %s, %s, %s)""",
            (request.session_id, current_user['user_id'], "user", request.query)
        )
    
    async def stream_generator():
        full_response = ""
        image_data = None
        tokens = 0
        
        try:
            async for chunk in llm.stream_generate(
                session_id=request.session_id,
                user_input=request.query,
                user_id=current_user['user_id']
            ):
                yield f"data: {chunk}\n\n"
                
                # Accumulate response
                try:
                    chunk_data = json.loads(chunk)
                    if chunk_data.get('type') == 'text':
                        full_response += chunk_data.get('content', '')
                        tokens = len(full_response.split())
                    elif chunk_data.get('type') == 'image':
                        image_data = chunk_data
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            error_chunk = json.dumps({
                "type": "error",
                "content": f"Streaming error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            yield f"data: {error_chunk}\n\n"
        finally:
            response_time = time.time() - start_time
            logger.info(f"Stream completed in {response_time:.2f}s")
            
            # Store complete response
            with get_db_cursor(commit=True) as cursor:
                if image_data:
                    save_image_metadata(image_data, current_user['user_id'])
                    
                    cursor.execute(
                        """INSERT INTO chat_messages 
                           (session_id, user_id, role, content, image_data)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (request.session_id, current_user['user_id'], "assistant",
                         image_data.get('prompt', ''), json.dumps(image_data))
                    )
                    
                    update_user_statistics(
                        user_id=current_user['user_id'],
                        images=1
                    )
                elif full_response:
                    cursor.execute(
                        """INSERT INTO chat_messages 
                           (session_id, user_id, role, content, tokens)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (request.session_id, current_user['user_id'], "assistant",
                         full_response, tokens)
                    )
                    
                    update_user_statistics(
                        user_id=current_user['user_id'],
                        messages=1,
                        tokens=tokens
                    )
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )

# ==================== OTHER CHAT ENDPOINTS ====================
@app.post("/chat", response_model=ChatResponse, tags=["chat"], summary="Legacy chat (no auth)")
async def chat(request: ChatRequest):
    """Legacy chat endpoint without authentication"""
    start_time = time.time()
    logger.info(f"Legacy chat request (Session: {request.session_id})")
    
    try:
        response = await llm.generate(
            session_id=request.session_id,
            user_input=request.query,
            user_id=request.user_id
        )
        
        response_time = time.time() - start_time
        
        # Store message if user_id is provided
        if request.user_id:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """INSERT INTO chat_messages (session_id, user_id, role, content)
                       VALUES (%s, %s, %s, %s)""",
                    (request.session_id, request.user_id, "user", request.query)
                )
        
        return ChatResponse(
            status="success",
            response=response,
            response_time_seconds=response_time
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Legacy chat error: {e}", exc_info=True)
        
        return ChatResponse(
            status="error",
            response={
                "type": "error",
                "content": f"An error occurred: {str(e)}",
                "timestamp": datetime.now().isoformat()
            },
            response_time_seconds=response_time
        )

# ==================== SESSION MANAGEMENT ENDPOINTS ====================
@app.get("/chat/sessions", tags=["sessions"], summary="Get user sessions")
async def get_user_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all chat sessions for the authenticated user"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    us.session_id as id,
                    us.session_name as title,
                    MAX(cm.created_at) as last_activity,
                    COUNT(cm.id) as message_count
                FROM user_sessions us
                LEFT JOIN chat_messages cm ON us.session_id = cm.session_id
                WHERE us.user_id = %s
                GROUP BY us.session_id, us.session_name
                ORDER BY MAX(cm.created_at) DESC
                LIMIT 50
            """, (current_user['user_id'],))
            
            sessions = cursor.fetchall()
            
            # Format response
            formatted_sessions = []
            for session in sessions:
                formatted_sessions.append({
                    "id": session['id'],
                    "title": session['title'] or "New Chat",
                    "last_activity": session['last_activity'].isoformat() if session['last_activity'] else None,
                    "message_count": session['message_count']
                })
            
            return {"sessions": formatted_sessions}
            
    except Exception as e:
        logger.error(f"Get sessions error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@app.post("/chat/session/new", tags=["sessions"], summary="Create new session")
async def create_new_session(
    request: SessionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new chat session"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        with get_db_cursor(commit=True) as cursor:
            # Check if session already exists
            cursor.execute(
                "SELECT id FROM user_sessions WHERE session_id = %s AND user_id = %s",
                (session_id, current_user['user_id'])
            )
            
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session ID already exists"
                )
            
            # Create new session
            cursor.execute(
                """INSERT INTO user_sessions 
                   (session_id, user_id, session_name, ip_address)
                   VALUES (%s, %s, %s, %s)""",
                (session_id, current_user['user_id'], request.session_name, "127.0.0.1")
            )
            
            logger.info(f"New session created: {session_id} for user {current_user['username']}")
            
            return {
                "status": "success",
                "session_id": session_id,
                "session_name": request.session_name
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create session error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )

@app.get("/chat/history/{session_id}", tags=["sessions"], summary="Get chat history")
async def get_chat_history(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get chat history for a specific session"""
    try:
        with get_db_cursor() as cursor:
            # Verify session belongs to user
            cursor.execute(
                """SELECT 1 FROM user_sessions 
                   WHERE session_id = %s AND user_id = %s""",
                (session_id, current_user['user_id'])
            )
            
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Get messages
            cursor.execute("""
                SELECT 
                    role,
                    content as text,
                    created_at as timestamp,
                    tokens,
                    image_data
                FROM chat_messages 
                WHERE session_id = %s 
                ORDER BY created_at ASC
                LIMIT 100
            """, (session_id,))
            
            messages = cursor.fetchall()
            
            # Format messages
            formatted_messages = []
            for msg in messages:
                image_data = None
                if msg['image_data']:
                    try:
                        image_data = json.loads(msg['image_data'])
                    except:
                        pass
                
                formatted_messages.append({
                    "role": msg['role'],
                    "text": msg['text'] or "",
                    "timestamp": msg['timestamp'].isoformat() if msg['timestamp'] else None,
                    "tokens": msg['tokens'] or 0,
                    "imageData": image_data
                })
            
            return {"messages": formatted_messages}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )

@app.post("/chat/clear", tags=["sessions"], summary="Clear session history")
async def clear_chat_history(
    request: ClearRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear chat history for a specific session"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Verify session belongs to user
            cursor.execute(
                """SELECT 1 FROM user_sessions 
                   WHERE session_id = %s AND user_id = %s""",
                (request.session_id, current_user['user_id'])
            )
            
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Delete messages
            cursor.execute(
                "DELETE FROM chat_messages WHERE session_id = %s",
                (request.session_id,)
            )
            
            deleted_count = cursor.rowcount
            
            # Clear LLM memory
            await llm.clear_session_memory(request.session_id)
            
            logger.info(f"Cleared {deleted_count} messages from session {request.session_id}")
            
            return {
                "status": "success",
                "message": "Chat history cleared",
                "deleted_count": deleted_count
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear history error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear chat history"
        )

# ==================== IMAGE ENDPOINTS ====================
@app.get("/images-check", tags=["images"], summary="Check images directory")
async def images_check():
    """Check if images directory is accessible"""
    try:
        files = list(GENERATED_IMAGES_DIR.glob("*"))
        files_info = []
        
        for file in files[:20]:
            if file.is_file():
                size = file.stat().st_size
                files_info.append({
                    "name": file.name,
                    "size_bytes": size,
                    "size_kb": round(size / 1024, 2),
                    "size_mb": round(size / (1024 * 1024), 2),
                    "modified": file.stat().st_mtime,
                    "url": f"/images/{file.name}"
                })
        
        return {
            "status": "success",
            "directory": str(GENERATED_IMAGES_DIR),
            "exists": True,
            "total_files": len(files),
            "files": files_info
        }
    except Exception as e:
        logger.error(f"Images check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "directory": str(GENERATED_IMAGES_DIR),
            "exists": GENERATED_IMAGES_DIR.exists()
        }

@app.get("/images/list", tags=["images"], summary="List user images")
async def list_user_images(
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List images generated by the user"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    image_id,
                    prompt,
                    filename,
                    url,
                    model,
                    size,
                    format,
                    created_at
                FROM images 
                WHERE user_id = %s 
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (current_user['user_id'], limit, offset))
            
            images = cursor.fetchall()
            
            # Get total count
            cursor.execute(
                "SELECT COUNT(*) as total FROM images WHERE user_id = %s",
                (current_user['user_id'],)
            )
            total = cursor.fetchone()['total']
            
            return {
                "status": "success",
                "images": images,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
    except Exception as e:
        logger.error(f"List images error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve images"
        )

# ==================== DEBUG ENDPOINTS ====================
@app.get("/debug/db-status", tags=["debug"], summary="Database status")
async def debug_db_status():
    """Debug endpoint to check database status"""
    try:
        with get_db_cursor() as cursor:
            # Get table counts
            tables = ['users', 'user_sessions', 'chat_messages', 'user_statistics', 'images', 'user_profiles']
            counts = {}
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    counts[table] = result['count'] if result else 0
                except:
                    counts[table] = "Table does not exist"
            
            # Get database info
            cursor.execute("SELECT VERSION() as version, DATABASE() as database")
            db_info = cursor.fetchone()
            
            return {
                "status": "connected",
                "database": db_info,
                "table_counts": counts,
                "pool_size": DB_CONFIG['pool_size']
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database": DB_CONFIG['database']
        }

# ==================== MIDDLEWARE ====================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests"""
    start_time = time.time()
    
    skip_paths = ["/health", "/favicon.ico", "/images/", "/static/"]
    should_log = not any(request.url.path.startswith(path) for path in skip_paths)
    
    if should_log:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Request: {request.method} {request.url.path} - IP: {client_ip}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        if should_log:
            logger.info(f"Response: {request.method} {request.url.path} - {process_time:.3f}s - Status: {response.status_code}")
        
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-API-Version"] = "3.3.1"
        response.headers["X-Server"] = "UAI-Chat-API"
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Error: {request.method} {request.url.path} - {process_time:.3f}s - Error: {str(e)}")
        raise

# ==================== ERROR HANDLERS ====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal server error occurred",
            "detail": str(exc) if os.getenv("DEBUG", "False").lower() == "true" else "Internal server error",
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )

# ==================== STARTUP AND SHUTDOWN EVENTS ====================
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 60)
    print("UAI Chat API Starting Up - Version 3.3.1")
    print("=" * 60)
    print(f"Backend URL: http://127.0.0.1:{os.getenv('PORT', 8000)}")
    print(f"Serving images from: {GENERATED_IMAGES_DIR}")
    print(f"Authentication: Enabled")
    print(f"Profile Setup: Enabled (with Gender field)")
    print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    # Initialize database pool
    if init_database_pool():
        print("✅ Database connection pool initialized")
    else:
        print("❌ Failed to initialize database pool")
    
    # Create missing tables
    create_missing_tables()
    create_user_profile_table()
    
    # Check images directory
    if GENERATED_IMAGES_DIR.exists():
        files = list(GENERATED_IMAGES_DIR.glob("*.*"))
        image_files = [f for f in files if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']]
        print(f"✅ Found {len(image_files)} image files in directory")
    else:
        print(f"✅ Created images directory: {GENERATED_IMAGES_DIR}")
    
    print("\n📋 Available Endpoints:")
    print("  ===== Profile Setup =====")
    print("    - POST /profile/save      - Save user profile (with gender)")
    print("    - GET  /profile/get       - Get user profile")
    print("    - GET  /profile/status    - Profile completion status")
    print("    - DELETE /profile/reset   - Reset profile")
    print("  ===== Authentication =====")
    print("    - POST /auth/register     - Register user")
    print("    - POST /auth/login        - Login user")
    print("    - GET  /auth/verify       - Verify token")
    print("    - GET  /auth/profile      - User profile")
    print("    - POST /auth/logout       - Logout user")
    print("  ===== Chat Operations =====")
    print("    - POST /chat/authenticated - Authenticated chat")
    print("    - POST /chat/authenticated/stream - Auth streaming")
    print("    - POST /chat              - Legacy chat")
    print("  ===== Session Management =====")
    print("    - GET  /chat/sessions     - Get user sessions")
    print("    - POST /chat/session/new  - Create new session")
    print("    - GET  /chat/history/{id} - Get chat history")
    print("    - POST /chat/clear        - Clear history")
    print("  ===== Image Operations =====")
    print("    - GET  /images/{file}     - Access images")
    print("    - GET  /images-check      - Check images")
    print("    - GET  /images/list       - List user images")
    print("  ===== Health & Info =====")
    print("    - GET  /                  - API Status (HTML page)")
    print("    - GET  /api-status        - API Status (JSON)")
    print("    - GET  /health            - Health check")
    print("    - GET  /test              - Test endpoint")
    print("    - GET  /docs              - Swagger UI Documentation")
    print("    - GET  /redoc             - ReDoc Documentation")
    print("  ===== Debug =====")
    print("    - GET  /debug/db-status   - Database status")
    print("=" * 60)
    print("✅ Server is ready! Press Ctrl+C to stop.")
    print("📚 API Documentation available at: http://127.0.0.1:8000/docs")
    print("🌐 Web Interface: http://127.0.0.1:8000")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("\n🛑 UAI Chat API shutting down...")
    
    global connection_pool
    if connection_pool:
        try:
            connection_pool._remove_connections()
            print("✅ Database connection pool closed")
        except:
            pass
    
    print("✅ Clean shutdown complete")
    print("=" * 60)

# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info" if debug else "warning",
        access_log=True
    )