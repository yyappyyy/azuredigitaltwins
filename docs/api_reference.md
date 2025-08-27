# Digital Twin API Reference

## Overview

The Digital Twin API provides RESTful endpoints for managing factory machine digital twins, sensor data, and real-time monitoring capabilities. Built with FastAPI, it includes automatic API documentation and WebSocket support for real-time updates.

## Base URL

When running locally:
```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production environments, implement appropriate authentication mechanisms.

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Core Endpoints

### Health and Status

#### GET /
Root endpoint with basic API information.

**Response**: HTML page with API overview

#### GET /api/health
Comprehensive health check for all services.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "database": {
      "status": "connected",
      "machine_count": 3
    },
    "azure_digital_twins": {
      "connected": false,
      "mock_mode": true,
      "azure_url": null,
      "client_available": true
    },
    "websocket": {
      "active_connections": 0,
      "subscriptions": {}
    },
    "sensor_simulator": {
      "running": false,
      "machine_count": 3
    }
  }
}
```

#### GET /api/status
System status summary.

**Response**:
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "machines": {
    "total": 3,
    "running": 2,
    "stopped": 1,
    "with_alerts": 1
  },
  "services": {
    "database": "connected",
    "azure_dt": "mock_mode",
    "websocket_connections": 0,
    "sensor_simulator": "running"
  },
  "uptime": "00:10:30"
}
```

### Digital Twins Management

#### GET /api/twins/
Get all machine states.

**Response**:
```json
[
  {
    "machine_id": "CNC-001",
    "machine_name": "CNC Machine 1",
    "machine_type": "CNC Milling Machine",
    "status": "running",
    "location": "Station A1",
    "temperature": 28.5,
    "humidity": 65.0,
    "vibration": 1.2,
    "temperature_threshold": 30.0,
    "humidity_threshold": 70.0,
    "vibration_threshold": 1.5,
    "last_updated": "2024-01-01T10:30:00Z",
    "has_temperature_alert": false,
    "has_humidity_alert": false,
    "has_vibration_alert": false
  }
]
```

#### GET /api/twins/dashboard
Get dashboard-ready aggregated data.

**Response**:
```json
{
  "machines": [...],
  "total_machines": 3,
  "running_machines": 2,
  "machines_with_alerts": 1,
  "last_updated": "2024-01-01T10:30:00Z"
}
```

#### GET /api/twins/{machine_id}
Get specific machine state.

**Parameters**:
- `machine_id` (string): Machine identifier

**Response**: Single machine object (same structure as above)

#### PUT /api/twins/{machine_id}
Update machine properties.

**Parameters**:
- `machine_id` (string): Machine identifier

**Request Body**:
```json
{
  "machine_name": "Updated Machine Name",
  "status": "running",
  "location": "New Location",
  "temperature_threshold": 32.0,
  "humidity_threshold": 75.0,
  "vibration_threshold": 1.8
}
```

**Response**:
```json
{
  "success": true,
  "message": "Machine CNC-001 updated successfully",
  "data": {
    "machine_id": "CNC-001",
    ...
  }
}
```

#### POST /api/twins/{machine_id}/commands
Execute a command on a machine.

**Parameters**:
- `machine_id` (string): Machine identifier

**Request Body**:
```json
{
  "command_type": "startMachine",
  "parameters": {}
}
```

**Available Commands**:
- `startMachine`: Start machine operation
- `stopMachine`: Stop machine operation  
- `resetAlarms`: Reset all alarms

**Response**:
```json
{
  "success": true,
  "message": "Command startMachine executed on machine CNC-001",
  "data": {
    "command": "startMachine",
    "machine_state": {...}
  }
}
```

#### GET /api/twins/{machine_id}/twin
Get Azure Digital Twin data directly.

**Parameters**:
- `machine_id` (string): Machine identifier

**Response**:
```json
{
  "twin_id": "machine-cnc-001",
  "data": {
    "$dtId": "machine-cnc-001",
    "machineId": "CNC-001",
    "isRunning": true,
    ...
  },
  "connection_status": {
    "connected": false,
    "mock_mode": true
  }
}
```

### Sensor Data

#### GET /api/sensors/
Get recent sensor readings.

**Query Parameters**:
- `machine_id` (optional): Filter by machine ID
- `sensor_type` (optional): Filter by sensor type (temperature, humidity, vibration)
- `limit` (optional, default=100): Maximum readings to return

**Response**:
```json
[
  {
    "machine_id": "CNC-001",
    "sensor_type": "temperature",
    "value": 28.5,
    "unit": "°C",
    "timestamp": "2024-01-01T10:30:00Z"
  }
]
```

#### GET /api/sensors/{machine_id}/history
Get historical sensor data.

**Parameters**:
- `machine_id` (string): Machine identifier

**Query Parameters**:
- `sensor_type` (required): Sensor type (temperature, humidity, vibration)
- `hours` (optional, default=24): Hours of history
- `limit` (optional, default=1000): Maximum readings

**Response**:
```json
{
  "machine_id": "CNC-001",
  "sensor_type": "temperature",
  "readings": [...],
  "count": 100,
  "start_time": "2024-01-01T09:30:00Z",
  "end_time": "2024-01-01T10:30:00Z"
}
```

#### GET /api/sensors/{machine_id}/latest
Get latest sensor readings for a machine.

**Response**:
```json
{
  "machine_id": "CNC-001",
  "timestamp": "2024-01-01T10:30:00Z",
  "readings": {
    "temperature": {
      "value": 28.5,
      "unit": "°C",
      "threshold": 30.0,
      "alert": false
    },
    "humidity": {
      "value": 65.0,
      "unit": "%",
      "threshold": 70.0,
      "alert": false
    },
    "vibration": {
      "value": 1.2,
      "unit": "m/s²",
      "threshold": 1.5,
      "alert": false
    }
  }
}
```

#### GET /api/sensors/{machine_id}/statistics
Get statistical analysis of sensor data.

**Query Parameters**:
- `sensor_type` (required): Sensor type
- `hours` (optional, default=24): Analysis period

**Response**:
```json
{
  "machine_id": "CNC-001",
  "sensor_type": "temperature",
  "time_period": {
    "start": "2024-01-01T09:30:00Z",
    "end": "2024-01-01T10:30:00Z",
    "hours": 1
  },
  "count": 60,
  "min": 25.2,
  "max": 29.8,
  "average": 27.5,
  "median": 27.4,
  "std_deviation": 1.2,
  "latest": 28.5,
  "unit": "°C"
}
```

#### GET /api/sensors/{machine_id}/alerts
Get sensor alert history.

**Query Parameters**:
- `hours` (optional, default=24): Analysis period

**Response**:
```json
{
  "machine_id": "CNC-001",
  "time_period": {
    "start": "2024-01-01T09:30:00Z",
    "end": "2024-01-01T10:30:00Z",
    "hours": 1
  },
  "alert_count": 5,
  "alerts": [
    {
      "timestamp": "2024-01-01T10:25:00Z",
      "sensor_type": "temperature",
      "value": 31.2,
      "threshold": 30.0,
      "unit": "°C",
      "severity": "warning"
    }
  ]
}
```

## WebSocket Connection

### Connection Endpoint
```
ws://localhost:8000/ws
```

### Message Format
All WebSocket messages use JSON format:

```json
{
  "type": "message_type",
  "data": {...},
  "timestamp": "2024-01-01T10:30:00Z"
}
```

### Client Messages

#### Subscribe to Topics
```json
{
  "type": "subscribe",
  "topics": ["machine_updates", "dashboard", "alerts"]
}
```

#### Unsubscribe from Topics
```json
{
  "type": "unsubscribe",
  "topics": ["machine_updates"]
}
```

#### Health Check
```json
{
  "type": "ping"
}
```

### Server Messages

#### Connection Established
```json
{
  "type": "connection_established",
  "timestamp": "2024-01-01T10:30:00Z",
  "client_id": 12345
}
```

#### Machine Update
```json
{
  "type": "machine_update",
  "machine_id": "CNC-001",
  "data": {...},
  "timestamp": "2024-01-01T10:30:00Z"
}
```

#### Dashboard Update
```json
{
  "type": "dashboard_update",
  "data": {
    "machines": [...],
    "total_machines": 3,
    "running_machines": 2,
    "machines_with_alerts": 1
  },
  "timestamp": "2024-01-01T10:30:00Z"
}
```

#### Alert Notification
```json
{
  "type": "alert",
  "machine_id": "CNC-001",
  "alert_type": "temperature_high",
  "message": "Temperature exceeded threshold",
  "severity": "warning",
  "timestamp": "2024-01-01T10:30:00Z"
}
```

#### Health Check Response
```json
{
  "type": "pong",
  "timestamp": "2024-01-01T10:30:00Z"
}
```

### Available Topics
- `machine_updates`: All machine state changes
- `machine_{machine_id}`: Updates for specific machine
- `dashboard`: Dashboard data updates
- `alerts`: Alert notifications
- `system`: System status updates

## Error Responses

### Standard Error Format
```json
{
  "error": true,
  "message": "Error description",
  "status_code": 400,
  "timestamp": "2024-01-01T10:30:00Z"
}
```

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (machine/resource doesn't exist)
- `500`: Internal Server Error

## Data Models

### MachineState
```json
{
  "machine_id": "string",
  "machine_name": "string", 
  "machine_type": "CNC Milling Machine|Hydraulic Press|Conveyor System|Industrial Robot|Welding Station",
  "status": "running|stopped|error|maintenance",
  "location": "string",
  "temperature": "number|null",
  "humidity": "number|null",
  "vibration": "number|null",
  "temperature_threshold": "number",
  "humidity_threshold": "number",
  "vibration_threshold": "number",
  "has_temperature_alert": "boolean",
  "has_humidity_alert": "boolean", 
  "has_vibration_alert": "boolean",
  "last_updated": "string (ISO 8601)"
}
```

### SensorReading
```json
{
  "machine_id": "string",
  "sensor_type": "temperature|humidity|vibration",
  "value": "number",
  "unit": "string",
  "timestamp": "string (ISO 8601)"
}
```

### MachineCommand
```json
{
  "command_type": "startMachine|stopMachine|resetAlarms",
  "parameters": "object|null"
}
```

## Rate Limits

Currently no rate limiting is implemented. Consider implementing rate limiting for production use:

- General API calls: 100 requests/minute
- WebSocket connections: 10 connections per IP
- Command execution: 10 commands/minute per machine

## Best Practices

### API Usage
- Use appropriate HTTP methods (GET for reading, PUT/POST for updates)
- Include proper error handling for all API calls
- Implement retry logic for transient failures
- Cache responses when appropriate

### WebSocket Usage
- Implement connection retry logic
- Subscribe only to needed topics
- Handle connection loss gracefully
- Send periodic ping messages to maintain connection

### Performance
- Use pagination for large data sets
- Implement client-side filtering when possible
- Consider polling intervals based on use case
- Monitor API response times

### Security
- Implement authentication in production
- Validate all input parameters
- Use HTTPS in production
- Implement CORS properly for cross-origin requests

## Examples

### Python Client Example
```python
import requests
import websockets
import json

# Get all machines
response = requests.get("http://localhost:8000/api/twins/")
machines = response.json()

# Update machine threshold
update_data = {"temperature_threshold": 32.0}
response = requests.put(
    "http://localhost:8000/api/twins/CNC-001", 
    json=update_data
)

# WebSocket connection
async def websocket_client():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Subscribe to machine updates
        await websocket.send(json.dumps({
            "type": "subscribe",
            "topics": ["machine_updates"]
        }))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
```

### JavaScript Client Example
```javascript
// API call
fetch('http://localhost:8000/api/twins/')
  .then(response => response.json())
  .then(machines => console.log(machines));

// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    ws.send(JSON.stringify({
        type: 'subscribe',
        topics: ['machine_updates', 'alerts']
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

## Support

For API support:
- Check the interactive documentation at `/docs`
- Review error messages for specific guidance
- Check the health endpoint for service status
- Monitor WebSocket connection status