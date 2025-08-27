# Digital Twin Sample Application Setup Guide

## Overview

This application demonstrates a comprehensive Digital Twin solution using Python, Azure Digital Twins SDK, FastAPI, and Streamlit. It provides:

- **Factory machine modeling** using Azure Digital Twins
- **IoT sensor simulation** for temperature, humidity, and vibration data
- **Real-time data storage** in SQLite with historical management
- **REST API endpoints** via FastAPI for twin management
- **Interactive dashboard** with Streamlit for monitoring and control
- **WebSocket support** for real-time updates
- **Bidirectional synchronization** between UI and Azure Digital Twins

## Prerequisites

### Python Environment
- Python 3.8 or higher
- pip package manager

### Azure Requirements (Optional)
- Azure subscription
- Azure Digital Twins instance
- Service principal with appropriate permissions

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd azuredigitaltwins
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

If you encounter installation issues, install packages individually:
```bash
# Core packages
pip install fastapi uvicorn[standard] pydantic pydantic-settings python-dotenv aiosqlite

# UI packages  
pip install streamlit plotly pandas

# Azure packages (optional)
pip install azure-digitaltwins-core azure-identity

# Development packages
pip install pytest pytest-asyncio httpx black flake8
```

### 3. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Azure Digital Twins Configuration (Optional)
AZURE_DT_URL=https://your-dt-instance.api.wcus.digitaltwins.azure.net
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id

# Database Configuration
DATABASE_URL=sqlite:///./digital_twins.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Streamlit Configuration
STREAMLIT_HOST=0.0.0.0
STREAMLIT_PORT=8501

# Sensor Simulation Configuration
SENSOR_UPDATE_INTERVAL=5
TEMPERATURE_MIN=18.0
TEMPERATURE_MAX=35.0
HUMIDITY_MIN=30.0
HUMIDITY_MAX=80.0
VIBRATION_MIN=0.1
VIBRATION_MAX=2.0
```

## Application Setup

### 1. Initialize the Application
```bash
python main.py setup
```

This command will:
- Create and initialize the SQLite database
- Set up Azure Digital Twins models (if configured)
- Create sample digital twin instances

### 2. Verify Installation
Check that all components can start:

```bash
# Test API server (in one terminal)
python main.py api

# Test frontend (in another terminal)
python main.py frontend

# Test sensor simulation (optional, in third terminal)
python main.py simulate
```

## Quick Start

### Option 1: All-in-One Demo (Mock Mode)
If you don't have Azure Digital Twins configured:

```bash
# Terminal 1: Start API server
python main.py api

# Terminal 2: Start Streamlit dashboard
python main.py frontend

# Terminal 3 (optional): Start sensor simulation
python main.py simulate
```

### Option 2: Azure Digital Twins Integration
If you have Azure credentials configured:

1. Update `.env` with your Azure Digital Twins details
2. Run the setup to create models and twins:
   ```bash
   python main.py setup
   ```
3. Start the services as in Option 1

## Accessing the Application

Once running, access these URLs:

- **Streamlit Dashboard**: http://localhost:8501
- **FastAPI Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health
- **WebSocket Endpoint**: ws://localhost:8000/ws

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI       │    │  Azure Digital  │
│   Frontend      │◄──►│    Backend       │◄──►│    Twins        │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   WebSocket     │    │     SQLite       │
│   Real-time     │    │    Database      │
│   Updates       │    │                  │
└─────────────────┘    └──────────────────┘
         │                       │
         │                       │
         └───────┬───────────────┘
                 │
                 ▼
       ┌──────────────────┐
       │  Sensor Data     │
       │  Simulator       │
       │                  │
       └──────────────────┘
```

## Troubleshooting

### Common Issues

#### 1. Package Installation Errors
If pip install fails:
```bash
# Update pip
pip install --upgrade pip

# Install packages one by one
pip install fastapi
pip install streamlit
# etc.
```

#### 2. Database Connection Errors
```bash
# Check database file permissions
ls -la digital_twins.db

# Reinitialize database
rm digital_twins.db
python main.py setup
```

#### 3. Azure Digital Twins Connection Issues
- Verify your service principal has Digital Twins Data Owner role
- Check that the Azure DT URL is correct
- Ensure firewall rules allow access
- The application will fall back to mock mode if Azure connection fails

#### 4. Port Already in Use
```bash
# Find and kill process using port 8000
lsof -i :8000
kill <PID>

# Or use different ports in .env
API_PORT=8001
STREAMLIT_PORT=8502
```

### Logs and Debugging

Enable debug logging:
```bash
export DEBUG=True
python main.py api
```

Check log files in the `logs/` directory (created automatically).

## Next Steps

After setup, see:
- [User Guide](user_guide.md) - How to use the dashboard
- [API Reference](api_reference.md) - API documentation
- Development documentation in source code

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the source code comments and docstrings
3. Check the test files for usage examples