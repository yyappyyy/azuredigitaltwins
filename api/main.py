"""
FastAPI Main Application

Central FastAPI application with all routes, middleware, and WebSocket support
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.routes.twins import router as twins_router
from api.routes.sensors import router as sensors_router
from services.websocket_service import websocket_manager
from services.sqlite_service import DatabaseService
from services.azure_dt_service import AzureDigitalTwinsService
from services.sensor_simulator import SensorSimulator
from config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
db_service = DatabaseService()
dt_service = AzureDigitalTwinsService()
sensor_simulator = SensorSimulator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown tasks
    """
    # Startup tasks
    logger.info("Starting Digital Twin API...")
    
    try:
        # Initialize database
        await db_service.initialize()
        logger.info("Database initialized")
        
        # Initialize Azure Digital Twins service
        await dt_service.initialize()
        logger.info("Azure Digital Twins service initialized")
        
        # Start background tasks
        logger.info("API startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        # Shutdown tasks
        logger.info("Shutting down Digital Twin API...")
        await db_service.disconnect()
        logger.info("API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Digital Twin API",
    description="""
    Azure Digital Twins Sample Application API
    
    This API provides endpoints for managing factory machine digital twins,
    sensor data, and real-time monitoring capabilities.
    
    Features:
    - Machine state management
    - Sensor data retrieval and history
    - Real-time WebSocket updates
    - Azure Digital Twins integration
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(twins_router, prefix="/api/twins", tags=["Digital Twins"])
app.include_router(sensors_router, prefix="/api/sensors", tags=["Sensors"])


@app.get("/", response_class=HTMLResponse)
async def root():
    """API root endpoint with basic information"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Digital Twin API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #2c3e50; }
            .info { background: #ecf0f1; padding: 20px; border-radius: 5px; }
            .link { color: #3498db; text-decoration: none; }
            .link:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1 class="header">🏭 Digital Twin API</h1>
        <div class="info">
            <p>Welcome to the Azure Digital Twins Sample Application API!</p>
            <p>This API provides endpoints for managing factory machine digital twins and sensor data.</p>
            
            <h3>Available Endpoints:</h3>
            <ul>
                <li><a href="/docs" class="link">📚 Interactive API Documentation</a></li>
                <li><a href="/redoc" class="link">📖 Alternative Documentation</a></li>
                <li><a href="/api/twins/health" class="link">🏥 Health Check</a></li>
                <li><a href="/api/twins/" class="link">🤖 Machine States</a></li>
                <li><a href="/api/sensors/" class="link">📊 Sensor Data</a></li>
            </ul>
            
            <h3>WebSocket Connection:</h3>
            <p>Connect to <code>ws://localhost:8000/ws</code> for real-time updates</p>
            
            <h3>Frontend Application:</h3>
            <p>Access the Streamlit dashboard at <a href="http://localhost:8501" class="link">http://localhost:8501</a></p>
        </div>
    </body>
    </html>
    """)


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    Returns the status of all services
    """
    try:
        # Check database connection
        db_status = "connected"
        try:
            await db_service.connect()
            machine_count = len(await db_service.get_all_machine_states())
        except Exception as e:
            db_status = f"error: {str(e)}"
            machine_count = 0
        
        # Check Azure Digital Twins connection
        dt_status = dt_service.get_connection_status()
        
        # Check WebSocket manager
        ws_connections = websocket_manager.get_connection_count()
        ws_subscriptions = websocket_manager.get_subscription_info()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Will be replaced with actual timestamp
            "services": {
                "database": {
                    "status": db_status,
                    "machine_count": machine_count
                },
                "azure_digital_twins": dt_status,
                "websocket": {
                    "active_connections": ws_connections,
                    "subscriptions": ws_subscriptions
                },
                "sensor_simulator": {
                    "running": sensor_simulator.is_running(),
                    "machine_count": len(sensor_simulator.get_machine_states())
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    
    Clients can subscribe to various topics:
    - 'machine_updates': All machine state updates
    - 'machine_{machine_id}': Updates for specific machine
    - 'dashboard': Dashboard data updates
    - 'alerts': Alert notifications
    - 'system': System status updates
    """
    await websocket.accept()
    await websocket_manager.register_connection(websocket)
    
    try:
        while True:
            # Wait for messages from client
            message = await websocket.receive_text()
            await websocket_manager.handle_message(websocket, message)
            
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket_manager.unregister_connection(websocket)


@app.get("/api/status")
async def get_system_status():
    """Get comprehensive system status"""
    try:
        # Get machine states
        machines = await db_service.get_all_machine_states()
        
        # Calculate statistics
        total_machines = len(machines)
        running_machines = sum(1 for m in machines if m.status.value == "running")
        machines_with_alerts = sum(1 for m in machines 
                                 if m.has_temperature_alert or m.has_humidity_alert or m.has_vibration_alert)
        
        # Service status
        services_status = {
            "database": "connected" if total_machines >= 0 else "disconnected",
            "azure_dt": "connected" if dt_service.is_connected() else "mock_mode",
            "websocket_connections": websocket_manager.get_connection_count(),
            "sensor_simulator": "running" if sensor_simulator.is_running() else "stopped"
        }
        
        return {
            "timestamp": "2024-01-01T00:00:00Z",  # Will be replaced with actual timestamp
            "machines": {
                "total": total_machines,
                "running": running_machines,
                "stopped": total_machines - running_machines,
                "with_alerts": machines_with_alerts
            },
            "services": services_status,
            "uptime": "00:00:00"  # Could be calculated from startup time
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "error": True,
        "message": exc.detail,
        "status_code": exc.status_code,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": True,
        "message": "Internal server error",
        "status_code": 500,
        "timestamp": "2024-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )