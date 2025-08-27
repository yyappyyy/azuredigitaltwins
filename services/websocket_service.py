"""
WebSocket Service for Real-time Updates

Manages WebSocket connections for real-time data streaming between backend and frontend
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional, List
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

from models.data_models import MachineState, DashboardData

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and real-time data broadcasting
    
    Features:
    - Multiple client connection management
    - Selective data broadcasting
    - Connection health monitoring
    - Message filtering and routing
    """
    
    def __init__(self):
        self._connections: Set[WebSocketServerProtocol] = set()
        self._subscriptions: Dict[WebSocketServerProtocol, Set[str]] = {}
        self._running = False
    
    async def register_connection(self, websocket: WebSocketServerProtocol):
        """Register a new WebSocket connection"""
        self._connections.add(websocket)
        self._subscriptions[websocket] = set()
        
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"WebSocket client connected: {client_info}")
        
        # Send welcome message
        await self._send_to_connection(websocket, {
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": id(websocket)
        })
    
    async def unregister_connection(self, websocket: WebSocketServerProtocol):
        """Unregister a WebSocket connection"""
        self._connections.discard(websocket)
        self._subscriptions.pop(websocket, None)
        
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"WebSocket client disconnected: {client_info}")
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming WebSocket message from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                # Subscribe to specific data topics
                topics = data.get("topics", [])
                self._subscriptions[websocket].update(topics)
                await self._send_to_connection(websocket, {
                    "type": "subscription_confirmed",
                    "topics": list(self._subscriptions[websocket])
                })
                logger.debug(f"Client subscribed to topics: {topics}")
            
            elif message_type == "unsubscribe":
                # Unsubscribe from topics
                topics = data.get("topics", [])
                self._subscriptions[websocket] -= set(topics)
                await self._send_to_connection(websocket, {
                    "type": "unsubscription_confirmed",
                    "topics": topics
                })
                logger.debug(f"Client unsubscribed from topics: {topics}")
            
            elif message_type == "ping":
                # Health check ping
                await self._send_to_connection(websocket, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "request_data":
                # Client requesting specific data
                data_type = data.get("data_type")
                if data_type == "machine_states":
                    # This would be handled by the API layer
                    await self._send_to_connection(websocket, {
                        "type": "data_request_received",
                        "data_type": data_type
                    })
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from client: {message}")
            await self._send_to_connection(websocket, {
                "type": "error",
                "message": "Invalid JSON format"
            })
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self._send_to_connection(websocket, {
                "type": "error",
                "message": "Internal server error"
            })
    
    async def broadcast_machine_update(self, machine_state: MachineState):
        """Broadcast machine state update to subscribed clients"""
        message = {
            "type": "machine_update",
            "machine_id": machine_state.machine_id,
            "data": machine_state.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._broadcast_to_subscribers("machine_updates", message)
        await self._broadcast_to_subscribers(f"machine_{machine_state.machine_id}", message)
    
    async def broadcast_dashboard_update(self, dashboard_data: DashboardData):
        """Broadcast dashboard data update to subscribed clients"""
        message = {
            "type": "dashboard_update",
            "data": dashboard_data.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._broadcast_to_subscribers("dashboard", message)
    
    async def broadcast_alert(self, machine_id: str, alert_type: str, message: str, severity: str = "warning"):
        """Broadcast alert message to subscribed clients"""
        alert_message = {
            "type": "alert",
            "machine_id": machine_id,
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._broadcast_to_subscribers("alerts", alert_message)
        await self._broadcast_to_subscribers(f"machine_{machine_id}", alert_message)
    
    async def broadcast_system_status(self, status: Dict[str, Any]):
        """Broadcast system status update"""
        message = {
            "type": "system_status",
            "data": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._broadcast_to_subscribers("system", message)
    
    async def _broadcast_to_subscribers(self, topic: str, message: Dict[str, Any]):
        """Broadcast message to clients subscribed to a specific topic"""
        if not self._connections:
            return
        
        # Find connections subscribed to this topic
        subscribed_connections = [
            conn for conn, topics in self._subscriptions.items()
            if topic in topics and conn in self._connections
        ]
        
        if subscribed_connections:
            await self._send_to_connections(subscribed_connections, message)
    
    async def _send_to_connection(self, websocket: WebSocketServerProtocol, message: Dict[str, Any]):
        """Send message to a specific connection"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            logger.debug("Attempted to send to closed connection")
            await self.unregister_connection(websocket)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            await self.unregister_connection(websocket)
    
    async def _send_to_connections(self, connections: List[WebSocketServerProtocol], message: Dict[str, Any]):
        """Send message to multiple connections"""
        if not connections:
            return
        
        message_json = json.dumps(message)
        
        # Send to all connections concurrently
        tasks = []
        for websocket in connections:
            if websocket in self._connections:  # Check if still connected
                tasks.append(self._send_message_safe(websocket, message_json))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_message_safe(self, websocket: WebSocketServerProtocol, message_json: str):
        """Safely send message to a connection with error handling"""
        try:
            await websocket.send(message_json)
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_connection(websocket)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            await self.unregister_connection(websocket)
    
    async def cleanup_dead_connections(self):
        """Clean up dead connections periodically"""
        dead_connections = set()
        
        for websocket in self._connections.copy():
            try:
                # Try to ping the connection
                await websocket.ping()
            except (websockets.exceptions.ConnectionClosed, Exception):
                dead_connections.add(websocket)
        
        for websocket in dead_connections:
            await self.unregister_connection(websocket)
        
        if dead_connections:
            logger.info(f"Cleaned up {len(dead_connections)} dead connections")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self._connections)
    
    def get_subscription_info(self) -> Dict[str, int]:
        """Get subscription statistics"""
        topic_counts = {}
        for topics in self._subscriptions.values():
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        return topic_counts


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def websocket_endpoint(websocket: WebSocketServerProtocol, path: str):
    """
    WebSocket endpoint handler
    
    This function handles the WebSocket connection lifecycle
    """
    await websocket_manager.register_connection(websocket)
    
    try:
        async for message in websocket:
            await websocket_manager.handle_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        logger.debug("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await websocket_manager.unregister_connection(websocket)


async def start_websocket_server(host: str = "localhost", port: int = 8765):
    """Start the WebSocket server"""
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    server = await websockets.serve(websocket_endpoint, host, port)
    
    # Start periodic cleanup task
    async def cleanup_task():
        while True:
            await asyncio.sleep(30)  # Cleanup every 30 seconds
            await websocket_manager.cleanup_dead_connections()
    
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    logger.info(f"WebSocket server started successfully")
    
    try:
        await server.wait_closed()
    finally:
        cleanup_task_handle.cancel()
        logger.info("WebSocket server stopped")