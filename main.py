"""
Digital Twin Sample Application

Main entry point for the Digital Twin application that provides:
- Factory machine modeling and management via Azure Digital Twins
- IoT sensor data simulation and storage
- FastAPI backend with real-time WebSocket updates
- Interactive Streamlit frontend dashboard

Usage:
    python main.py [command]

Commands:
    api         Start FastAPI backend server
    frontend    Start Streamlit frontend
    simulate    Run sensor data simulation
    setup       Initialize database and Azure DT models
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings


def setup_environment():
    """Setup environment and validate configuration"""
    settings = get_settings()
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    return settings


async def run_api():
    """Start the FastAPI backend server"""
    import uvicorn
    from api.main import app
    
    settings = setup_environment()
    
    print(f"🚀 Starting FastAPI server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )


def run_frontend():
    """Start the Streamlit frontend"""
    import subprocess
    
    settings = setup_environment()
    
    print(f"🎨 Starting Streamlit frontend on {settings.STREAMLIT_HOST}:{settings.STREAMLIT_PORT}")
    subprocess.run([
        "streamlit", "run", "frontend/main.py",
        "--server.address", settings.STREAMLIT_HOST,
        "--server.port", str(settings.STREAMLIT_PORT)
    ])


async def run_simulation():
    """Run the sensor data simulation"""
    from services.sensor_simulator import SensorSimulator
    
    settings = setup_environment()
    
    print("📊 Starting sensor data simulation...")
    simulator = SensorSimulator()
    await simulator.start()


async def setup_application():
    """Initialize database and Azure Digital Twins models"""
    from services.sqlite_service import DatabaseService
    from services.azure_dt_service import AzureDigitalTwinsService
    
    print("🔧 Setting up application...")
    
    # Initialize database
    print("📦 Initializing SQLite database...")
    db_service = DatabaseService()
    await db_service.initialize()
    
    # Initialize Azure Digital Twins
    print("☁️  Setting up Azure Digital Twins models...")
    dt_service = AzureDigitalTwinsService()
    await dt_service.initialize()
    
    print("✅ Application setup complete!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Digital Twin Sample Application")
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["api", "frontend", "simulate", "setup", "help"],
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    if args.command == "help":
        parser.print_help()
    elif args.command == "api":
        asyncio.run(run_api())
    elif args.command == "frontend":
        run_frontend()
    elif args.command == "simulate":
        asyncio.run(run_simulation())
    elif args.command == "setup":
        asyncio.run(setup_application())


if __name__ == "__main__":
    main()