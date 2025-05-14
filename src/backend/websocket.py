"""
WebSocket implementation for real-time updates in Incalmo.

This module implements WebSocket support for sending real-time updates
to connected clients about changes in the environment state, attack graph,
and task execution.
"""

import json
import asyncio
from typing import Dict, List, Set, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from models.models import SessionState, TaskResult

class WebSocketManager:
    """
    WebSocket connection manager for handling real-time updates.
    """
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Connect a client to a session's WebSocket updates.
        
        Args:
            websocket: WebSocket connection
            session_id: ID of the session to subscribe to
        """
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
            
        self.active_connections[session_id].add(websocket)
        
    def disconnect(self, websocket: WebSocket, session_id: str):
        """
        Disconnect a client from a session's WebSocket updates.
        
        Args:
            websocket: WebSocket connection
            session_id: ID of the session
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                
    async def broadcast_session_update(self, session_id: str, data: Dict[str, Any]):
        """
        Broadcast a session update to all connected clients for that session.
        
        Args:
            session_id: ID of the session
            data: Update data to broadcast
        """
        if session_id not in self.active_connections:
            return
            
        disconnected = set()
        
        for connection in self.active_connections[session_id]:
            try:
                # Use non-blocking send to avoid delays between chunks
                # This makes streaming more responsive
                await asyncio.shield(connection.send_json(data))
            except Exception:
                disconnected.add(connection)
                
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, session_id)
            
    async def broadcast_task_result(self, session_id: str, task_result: TaskResult):
        """
        Broadcast a task result to all connected clients for a session.
        
        Args:
            session_id: ID of the session
            task_result: Result of the executed task
        """
        data = {
            "type": "task_result",
            "task_type": task_result.task_type,
            "success": task_result.success,
            "result": task_result.result,
            "error": task_result.error,
            "timestamp": task_result.timestamp.isoformat() if task_result.timestamp else None
        }
        
        await self.broadcast_session_update(session_id, data)
        
    async def broadcast_environment_update(self, session_id: str, environment_state: Any):
        """
        Broadcast an environment state update to all connected clients for a session.
        
        Args:
            session_id: ID of the session
            environment_state: Updated environment state
        """
        data = {
            "type": "environment_update",
            "environment_state": environment_state.dict() if hasattr(environment_state, "dict") else environment_state
        }
        
        await self.broadcast_session_update(session_id, data)
        
    async def broadcast_attack_graph_update(self, session_id: str, attack_graph: Any):
        """
        Broadcast an attack graph update to all connected clients for a session.
        
        Args:
            session_id: ID of the session
            attack_graph: Updated attack graph
        """
        data = {
            "type": "attack_graph_update",
            "attack_graph": attack_graph.dict() if hasattr(attack_graph, "dict") else attack_graph
        }
        
        await self.broadcast_session_update(session_id, data)
        
    async def broadcast_llm_response(self, session_id: str, message: Dict[str, Any]):
        """
        Broadcast an LLM response to all connected clients for a session.
        
        Args:
            session_id: ID of the session
            message: LLM response message
        """
        data = {
            "type": "llm_response",
            "message": message
        }
        
        await self.broadcast_session_update(session_id, data)
        
    async def broadcast_llm_streaming_chunk(self, session_id: str, chunk: str, is_done: bool):
        """
        Broadcast a streaming chunk of an LLM response to all connected clients.
        
        Args:
            session_id: ID of the session
            chunk: Text chunk from the streaming response
            is_done: Boolean indicating if this is the final chunk
        """
        print(f"[DEBUG] Broadcasting LLM streaming chunk - session: {session_id}, length: {len(chunk)}, is_done: {is_done}")
        if len(chunk) > 0:
            print(f"[DEBUG] Chunk preview: {chunk[:50]}...")
            
        data = {
            "type": "llm_streaming_chunk",
            "chunk": chunk,
            "is_done": is_done
        }
        
        await self.broadcast_session_update(session_id, data)

# Create a global WebSocket manager instance
websocket_manager = WebSocketManager()

def setup_websocket_routes(app: FastAPI):
    """
    Set up WebSocket routes for the FastAPI application.
    
    Args:
        app: FastAPI application
    """
    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """WebSocket endpoint for real-time session updates."""
        await websocket_manager.connect(websocket, session_id)
        
        try:
            while True:
                # Wait for messages from the client
                # This keeps the connection alive
                data = await websocket.receive_text()
                
                # Process client messages if needed
                try:
                    message = json.loads(data)
                    # Handle client messages here if needed
                except json.JSONDecodeError:
                    pass
                    
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket, session_id)
