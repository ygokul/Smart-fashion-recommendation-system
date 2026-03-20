from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, validator, Field

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
