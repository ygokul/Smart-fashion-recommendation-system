# Add this import at the top if not already present
from datetime import datetime

# Add this logout endpoint to your authentication section
@app.post("/auth/logout", tags=["authentication"])
async def logout(
    logout_request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Logout user by invalidating session"""
    session_id = logout_request.get('session_id')
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID is required"
        )
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = conn.cursor()
    
    try:
        # Delete the specific session
        cursor.execute(
            "DELETE FROM user_sessions WHERE session_id = %s AND user_id = %s",
            (session_id, current_user['user_id'])
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count == 0:
            return {
                "status": "warning", 
                "message": "Session not found or already logged out"
            }
        
        return {
            "status": "success", 
            "message": "Logged out successfully",
            "session_id": session_id
        }
        
    except mysql.connector.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Optional: Add a logout all sessions endpoint
@app.post("/auth/logout-all", tags=["authentication"])
async def logout_all(
    current_user: dict = Depends(get_current_user)
):
    """Logout user from all sessions"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = conn.cursor()
    
    try:
        # Get count before deletion
        cursor.execute(
            "SELECT COUNT(*) as session_count FROM user_sessions WHERE user_id = %s",
            (current_user['user_id'],)
        )
        result = cursor.fetchone()
        session_count = result[0] if result else 0
        
        # Delete all sessions for this user
        cursor.execute(
            "DELETE FROM user_sessions WHERE user_id = %s",
            (current_user['user_id'],)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        return {
            "status": "success", 
            "message": f"Logged out from all sessions",
            "sessions_ended": deleted_count,
            "total_sessions": session_count
        }
        
    except mysql.connector.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()