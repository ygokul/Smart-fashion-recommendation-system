import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from threading import Lock
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "db"

# Global in-memory data stores (loaded from JSON)
USERS: Dict[int, Dict[str, Any]] = {}
USER_PROFILES: Dict[int, Dict[str, Any]] = {}
USER_SESSIONS: Dict[str, Dict[str, Any]] = {}
CHAT_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}
IMAGES: Dict[str, Dict[str, Any]] = {}
USER_STATS: Dict[int, Dict[str, Any]] = {}

# Thread locks for concurrency safety
users_lock = Lock()
profiles_lock = Lock()
sessions_lock = Lock()
messages_lock = Lock()
images_lock = Lock()
stats_lock = Lock()

def get_db_dir() -> Path:
    """Get db directory path"""
    DB_DIR.mkdir(exist_ok=True)
    return DB_DIR

def load_json_file(filepath: Path) -> List[Dict[str, Any]]:
    """Load JSON file safely"""
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    return []

def save_json_file(filepath: Path, data: List[Dict[str, Any]]) -> None:
    """Save JSON file safely (DEV ONLY)"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        print(f"Error saving {filepath}: {e}")

# ==================== USERS ====================
def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with users_lock:
        return USERS.get(user_id)

def save_user(user_data: Dict[str, Any]) -> int:
    with users_lock:
        user_id = user_data.get('id')
        if user_id:
            USERS[user_id] = user_data
        else:
            max_id = max(USERS.keys()) if USERS else 0
            user_id = max_id + 1
            user_data['id'] = user_id
            USERS[user_id] = user_data
        save_json_file(get_db_dir() / "users.json", list(USERS.values()))
        return user_id

def user_exists(username: str, email: str) -> bool:
    with users_lock:
        return any(u['username'] == username or u['email'] == email for u in USERS.values())

# ==================== PROFILES ====================
def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    with profiles_lock:
        return USER_PROFILES.get(user_id)

def save_user_profile(user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    with profiles_lock:
        # Calculate completion
        sections = sum(1 for k in ['gender', 'body_type', 'skin_tone', 'face_shape', 'hair_type'] if profile_data.get(k))
        if profile_data.get('style_preferences') and len(profile_data.get('style_preferences', [])) > 0:
            sections += 1
        if any(profile_data.get(k) for k in ['height', 'weight', 'bust', 'waist', 'hips']):
            sections += 1
        
        profile = {
            'user_id': user_id,
            **profile_data,
            'completed_sections': sections,
            'is_complete': sections >= 4,
            'created_at': profile_data.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }
        
        USER_PROFILES[user_id] = profile
        save_json_file(get_db_dir() / "user_profiles.json", list(USER_PROFILES.values()))
        
        return {
            'profile_id': user_id,
            'completed_sections': sections,
            'is_complete': sections >= 4,
            'message': 'Profile saved'
        }

def get_profile_status(user_id: int) -> Dict[str, Any]:
    profile = get_user_profile(user_id)
    if not profile:
        return {'is_complete': False, 'completed_sections': 0, 'has_profile': False}
    return {
        'is_complete': profile.get('is_complete', False),
        'completed_sections': profile.get('completed_sections', 0),
        'has_profile': True
    }

# ==================== SESSIONS ====================
def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    with sessions_lock:
        return USER_SESSIONS.get(session_id)

def save_session(session_data: Dict[str, Any]) -> None:
    with sessions_lock:
        session_id = session_data['session_id']
        USER_SESSIONS[session_id] = session_data
        save_json_file(get_db_dir() / "user_sessions.json", list(USER_SESSIONS.values()))

# ==================== CHAT MESSAGES ====================
def save_chat_message(session_id: str, user_id: Optional[int], role: str, content: str, 
                     tokens: int = 0, image_data: Optional[str] = None) -> None:
    msg = {
        'id': len(CHAT_MESSAGES.get(session_id, [])) + 1,
        'session_id': session_id,
        'user_id': user_id,
        'role': role,
        'content': content,
        'tokens': tokens,
        'image_data': image_data,
        'created_at': datetime.now().isoformat()
    }
    
    with messages_lock:
        if session_id not in CHAT_MESSAGES:
            CHAT_MESSAGES[session_id] = []
        CHAT_MESSAGES[session_id].append(msg)
        save_json_file(get_db_dir() / "chat_messages.json", list(CHAT_MESSAGES.values()))

def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    with messages_lock:
        return CHAT_MESSAGES.get(session_id, [])

def clear_chat_history(session_id: str) -> int:
    with messages_lock:
        deleted = len(CHAT_MESSAGES.get(session_id, []))
        CHAT_MESSAGES[session_id] = []
        save_json_file(get_db_dir() / "chat_messages.json", list(CHAT_MESSAGES.values()))
        return deleted

# ==================== IMAGES ====================
def save_image(image_data: Dict[str, Any], user_id: Optional[int] = None) -> None:
    with images_lock:
        image_id = image_data['image_id']
        IMAGES[image_id] = {**image_data, 'user_id': user_id}
        save_json_file(get_db_dir() / "images.json", list(IMAGES.values()))

def get_image(image_id: str) -> Optional[Dict[str, Any]]:
    with images_lock:
        return IMAGES.get(image_id)

# ==================== STATISTICS ====================
def update_user_stats(user_id: int, messages: int = 0, images: int = 0, tokens: int = 0) -> None:
    with stats_lock:
        if user_id not in USER_STATS:
            USER_STATS[user_id] = {'user_id': user_id, 'total_messages': 0, 'total_images': 0, 'total_tokens': 0, 'total_sessions': 1}
        
        stats = USER_STATS[user_id]
        stats['total_messages'] += messages
        stats['total_images'] += images
        stats['total_tokens'] += tokens
        stats['last_updated'] = datetime.now().isoformat()
        
        save_json_file(get_db_dir() / "user_statistics.json", list(USER_STATS.values()))

def get_user_stats(user_id: int) -> Dict[str, Any]:
    with stats_lock:
        return USER_STATS.get(user_id, {'user_id': user_id, 'total_messages': 0, 'total_images': 0, 'total_tokens': 0, 'total_sessions': 1})

# ==================== MAIN LOAD/SAVE ====================
def load_all_data() -> None:
    """Load all JSON data into memory"""
    global USERS, USER_PROFILES, USER_SESSIONS, CHAT_MESSAGES, IMAGES, USER_STATS
    
    print("🔄 Loading data from JSON files...")
    
    # Load users
    users_data = load_json_file(get_db_dir() / "users.json")
    USERS = {u['id']: u for u in users_data}
    print(f"   ✅ Loaded {len(USERS)} users")
    
    # Load profiles
    profiles_data = load_json_file(get_db_dir() / "user_profiles.json")
    USER_PROFILES = {p['user_id']: p for p in profiles_data}
    print(f"   ✅ Loaded {len(USER_PROFILES)} profiles")
    
    # Load sessions
    sessions_data = load_json_file(get_db_dir() / "user_sessions.json")
    USER_SESSIONS = {s['session_id']: s for s in sessions_data}
    print(f"   ✅ Loaded {len(USER_SESSIONS)} sessions")
    
    # Load messages (grouped by session_id)
    msgs_data = load_json_file(get_db_dir() / "chat_messages.json")
    CHAT_MESSAGES = {}
    for msg in msgs_data:
        sid = msg['session_id']
        if sid not in CHAT_MESSAGES:
            CHAT_MESSAGES[sid] = []
        CHAT_MESSAGES[sid].append(msg)
    print(f"   ✅ Loaded {sum(len(msgs) for msgs in CHAT_MESSAGES.values())} messages")
    
    # Load images
    images_data = load_json_file(get_db_dir() / "images.json")
    IMAGES = {i['image_id']: i for i in images_data}
    print(f"   ✅ Loaded {len(IMAGES)} images")
    
    # Load stats
    stats_data = load_json_file(get_db_dir() / "user_statistics.json")
    USER_STATS = {s['user_id']: s for s in stats_data}
    print(f"   ✅ Loaded {len(USER_STATS)} stats")
    
    print("✅ All data loaded successfully!")

def save_all_data() -> None:
    """Save all data to JSON (DEV ONLY)"""
    # This is called on changes - for Render, data is read-only
    pass  # Implement if needed for development

# Auto-init on import
load_all_data()

