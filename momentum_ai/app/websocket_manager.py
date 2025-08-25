import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.auth import verify_token
from app.database import SessionLocal
from app.models import User


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.user_connections: Dict[int, Set[int]] = {}  # user_id -> set of connection_ids
    
    async def connect(self, websocket: WebSocket, token: str) -> Optional[int]:
        """Connect a WebSocket with authentication."""
        try:
            await websocket.accept()
            
            # Verify token
            payload = verify_token(token, "access")
            user_id = int(payload.get("sub"))
            
            # Get user from database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    await websocket.close(code=4001, reason="User not found")
                    return None
            finally:
                db.close()
            
            # Store connection
            connection_id = id(websocket)
            self.active_connections[connection_id] = websocket
            
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            return user_id
            
        except Exception as e:
            await websocket.close(code=4001, reason="Authentication failed")
            return None
    
    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None):
        """Disconnect a WebSocket."""
        connection_id = id(websocket)
        
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user."""
        if user_id not in self.user_connections:
            return
        
        disconnected = set()
        for connection_id in self.user_connections[user_id]:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception:
                    disconnected.add(connection_id)
            else:
                disconnected.add(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            self.user_connections[user_id].discard(connection_id)
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
        
        if not self.user_connections[user_id]:
            del self.user_connections[user_id]
    
    async def send_alert(self, student_id: int, message: str, severity: str = "medium"):
        """Send a risk alert to mentors assigned to a student."""
        from app.models import Pairing, PairingStatus
        
        db = SessionLocal()
        try:
            # Get mentors assigned to this student
            pairings = db.query(Pairing).filter(
                Pairing.student_id == student_id,
                Pairing.status == PairingStatus.ACTIVE
            ).all()
            
            alert_message = {
                "type": "ALERT",
                "student_id": student_id,
                "message": message,
                "severity": severity,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Send to all assigned mentors
            for pairing in pairings:
                await self.send_personal_message(alert_message, pairing.mentor.user_id)
                
        finally:
            db.close()
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users."""
        disconnected = set()
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.add(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            del self.active_connections[connection_id]
            for user_connections in self.user_connections.values():
                user_connections.discard(connection_id)


# Global connection manager instance
manager = ConnectionManager() 