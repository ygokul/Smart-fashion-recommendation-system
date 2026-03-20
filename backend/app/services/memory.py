# from collections import defaultdict
# from typing import List, Dict

# # session_id -> list of messages
# chat_memory: Dict[str, List[dict]] = defaultdict(list)

# def add_message(session_id: str, role: str, content: str):
#     chat_memory[session_id].append({
#         "role": role,
#         "content": content
#     })

# def get_history(session_id: str) -> List[dict]:
#     return chat_memory[session_id]

# def clear_history(session_id: str):
#     chat_memory.pop(session_id, None)
# app/services/memory.py
import json
import time
from typing import List, Dict

# In-memory message store with session management
MESSAGE_STORE = {}
MAX_MESSAGES_PER_SESSION = 30  # Keep last 30 messages total
MAX_SESSION_AGE_HOURS = 24  # Sessions older than this will be cleared

def add_message(session_id: str, role: str, content: str):
    """Add a message to the session history with truncation logic"""
    if session_id not in MESSAGE_STORE:
        MESSAGE_STORE[session_id] = {
            "messages": [],
            "created_at": time.time(),
            "last_accessed": time.time()
        }
    
    session = MESSAGE_STORE[session_id]
    session["last_accessed"] = time.time()
    
    messages = session["messages"]
    messages.append({
        "role": role,
        "content": content,
        "timestamp": time.time()
    })
    
    # Truncate if we have too many messages
    if len(messages) > MAX_MESSAGES_PER_SESSION:
        # Keep system messages and the most recent messages
        system_messages = [m for m in messages if m["role"] == "system"]
        other_messages = [m for m in messages if m["role"] != "system"]
        
        # Calculate how many messages to keep
        keep_count = MAX_MESSAGES_PER_SESSION - len(system_messages)
        if keep_count > 0:
            other_messages = other_messages[-keep_count:]
        else:
            # If system messages exceed limit, keep only the most recent ones
            system_messages = system_messages[-MAX_MESSAGES_PER_SESSION:]
            other_messages = []
        
        session["messages"] = system_messages + other_messages

def get_messages(session_id: str, max_tokens: int = None) -> List[Dict]:
    """Get messages for a session, optionally truncated by token count"""
    if session_id not in MESSAGE_STORE:
        return []
    
    session = MESSAGE_STORE[session_id]
    session["last_accessed"] = time.time()
    messages = session["messages"].copy()
    
    if max_tokens:
        # Simple token estimation (1 token ≈ 4 characters)
        total_tokens = 0
        truncated_messages = []
        
        # Process messages from newest to oldest
        for msg in reversed(messages):
            content = msg.get("content", "")
            estimated_tokens = len(content) // 4
            
            if total_tokens + estimated_tokens > max_tokens:
                # Don't break if this is a system message
                if msg["role"] == "system":
                    # Add it anyway and continue
                    pass
                else:
                    break
                    
            total_tokens += estimated_tokens
            truncated_messages.insert(0, msg)
        
        return truncated_messages
    
    return messages

def get_recent_messages(session_id: str, count: int = 10) -> List[Dict]:
    """Get the most recent N messages"""
    if session_id not in MESSAGE_STORE:
        return []
    
    session = MESSAGE_STORE[session_id]
    session["last_accessed"] = time.time()
    messages = session["messages"]
    
    return messages[-count:] if messages else []

MAX_MESSAGES_PER_SESSION = 20  

def clear_old_messages(session_id: str, keep_last: int = 8):  # Reduced from 15 to 8
    """Clear old messages, keeping only the most recent ones"""
    if session_id in MESSAGE_STORE:
        session = MESSAGE_STORE[session_id]
        messages = session["messages"]
        if len(messages) > keep_last:
            # Keep system messages and recent messages
            system_messages = [m for m in messages if m["role"] == "system"]
            other_messages = [m for m in messages if m["role"] != "system"]
            
            keep_other = keep_last - len(system_messages)
            if keep_other > 0:
                other_messages = other_messages[-keep_other:]
            else:
                other_messages = []
            
            session["messages"] = system_messages + other_messages


def clear_session(session_id: str):
    """Clear all messages for a session"""
    if session_id in MESSAGE_STORE:
        del MESSAGE_STORE[session_id]

def cleanup_old_sessions():
    """Clean up sessions that haven't been accessed in a while"""
    current_time = time.time()
    expired_sessions = []
    
    for session_id, session_data in MESSAGE_STORE.items():
        session_age = current_time - session_data["last_accessed"]
        if session_age > (MAX_SESSION_AGE_HOURS * 3600):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del MESSAGE_STORE[session_id]
    
    return len(expired_sessions)

def get_session_stats(session_id: str) -> Dict:
    """Get statistics for a session"""
    if session_id not in MESSAGE_STORE:
        return {"exists": False}
    
    session = MESSAGE_STORE[session_id]
    messages = session["messages"]
    
    # Count messages by role
    role_counts = {}
    total_tokens = 0
    
    for msg in messages:
        role = msg["role"]
        role_counts[role] = role_counts.get(role, 0) + 1
        
        # Estimate tokens
        content = msg.get("content", "")
        total_tokens += len(content) // 4
    
    return {
        "exists": True,
        "total_messages": len(messages),
        "role_counts": role_counts,
        "estimated_tokens": total_tokens,
        "created_at": session["created_at"],
        "last_accessed": session["last_accessed"],
        "age_hours": (time.time() - session["created_at"]) / 3600
    }