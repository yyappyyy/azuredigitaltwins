"""
Sensor Data API Routes

Endpoints for retrieving sensor data, historical records, and analytics
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from models.data_models import SensorReading, SensorHistory
from services.sqlite_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances
db_service = DatabaseService()


async def get_db_service():
    """Dependency to get database service"""
    await db_service.connect()
    return db_service


@router.get("/health")
async def health_check():
    """Health check for sensors API"""
    return {
        "status": "healthy",
        "service": "sensors_api",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/", response_model=List[SensorReading])
async def get_recent_sensor_readings(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type (temperature, humidity, vibration)"),
    limit: int = Query(100, description="Maximum number of readings to return", ge=1, le=1000),
    db: DatabaseService = Depends(get_db_service)
):
    """
    Get recent sensor readings
    
    Retrieve the most recent sensor readings, optionally filtered by
    machine ID and/or sensor type.
    """
    try:
        # For now, we'll implement a simple query to get recent readings
        # In a full implementation, you'd want a dedicated method for this
        
        # Get all machines if no specific machine requested
        if machine_id:
            machine_ids = [machine_id]
        else:
            machines = await db.get_all_machine_states()
            machine_ids = [m.machine_id for m in machines]
        
        # Get sensor types to query
        if sensor_type:
            sensor_types = [sensor_type]
        else:
            sensor_types = ["temperature", "humidity", "vibration"]
        
        all_readings = []
        
        # Get recent readings for each machine and sensor type
        for mid in machine_ids:
            for stype in sensor_types:
                history = await db.get_sensor_history(
                    machine_id=mid,
                    sensor_type=stype,
                    start_time=datetime.utcnow() - timedelta(hours=1),  # Last hour
                    end_time=datetime.utcnow(),
                    limit=min(limit // (len(machine_ids) * len(sensor_types)), 50)
                )
                all_readings.extend(history.readings)
        
        # Sort by timestamp and limit results
        all_readings.sort(key=lambda x: x.timestamp, reverse=True)
        result = all_readings[:limit]
        
        logger.info(f"Retrieved {len(result)} recent sensor readings")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get sensor readings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sensor readings")


@router.get("/{machine_id}/history", response_model=SensorHistory)
async def get_sensor_history(
    machine_id: str,
    sensor_type: str = Query(..., description="Sensor type (temperature, humidity, vibration)"),
    hours: int = Query(24, description="Hours of history to retrieve", ge=1, le=168),  # Max 1 week
    limit: int = Query(1000, description="Maximum number of readings", ge=1, le=10000),
    db: DatabaseService = Depends(get_db_service)
):
    """
    Get historical sensor data for a specific machine
    
    Retrieve historical sensor readings for analysis and visualization.
    Data is returned in chronological order with configurable time range.
    """
    try:
        # Validate sensor type
        if sensor_type not in ["temperature", "humidity", "vibration"]:
            raise HTTPException(
                status_code=400, 
                detail="Sensor type must be one of: temperature, humidity, vibration"
            )
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get sensor history
        history = await db.get_sensor_history(
            machine_id=machine_id,
            sensor_type=sensor_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        logger.info(f"Retrieved {history.count} {sensor_type} readings for machine {machine_id}")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sensor history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sensor history")


@router.get("/{machine_id}/latest")
async def get_latest_sensor_readings(
    machine_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """
    Get the latest sensor readings for a specific machine
    
    Returns the most recent temperature, humidity, and vibration readings
    for quick status checks.
    """
    try:
        # Get machine state which includes latest sensor readings
        machine = await db.get_machine_state(machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        return {
            "machine_id": machine_id,
            "timestamp": machine.last_updated,
            "readings": {
                "temperature": {
                    "value": machine.temperature,
                    "unit": "°C",
                    "threshold": machine.temperature_threshold,
                    "alert": machine.has_temperature_alert
                },
                "humidity": {
                    "value": machine.humidity,
                    "unit": "%",
                    "threshold": machine.humidity_threshold,
                    "alert": machine.has_humidity_alert
                },
                "vibration": {
                    "value": machine.vibration,
                    "unit": "m/s²",
                    "threshold": machine.vibration_threshold,
                    "alert": machine.has_vibration_alert
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest readings for machine {machine_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve latest sensor readings")


@router.get("/{machine_id}/statistics")
async def get_sensor_statistics(
    machine_id: str,
    sensor_type: str = Query(..., description="Sensor type (temperature, humidity, vibration)"),
    hours: int = Query(24, description="Hours of data to analyze", ge=1, le=168),
    db: DatabaseService = Depends(get_db_service)
):
    """
    Get statistical analysis of sensor data
    
    Calculate min, max, average, and other statistics for sensor readings
    over a specified time period.
    """
    try:
        # Validate sensor type
        if sensor_type not in ["temperature", "humidity", "vibration"]:
            raise HTTPException(
                status_code=400,
                detail="Sensor type must be one of: temperature, humidity, vibration"
            )
        
        # Get sensor history
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        history = await db.get_sensor_history(
            machine_id=machine_id,
            sensor_type=sensor_type,
            start_time=start_time,
            end_time=end_time,
            limit=10000  # Large limit for statistical analysis
        )
        
        if not history.readings:
            raise HTTPException(
                status_code=404,
                detail=f"No {sensor_type} readings found for machine {machine_id}"
            )
        
        # Calculate statistics
        values = [reading.value for reading in history.readings]
        
        statistics = {
            "machine_id": machine_id,
            "sensor_type": sensor_type,
            "time_period": {
                "start": start_time,
                "end": end_time,
                "hours": hours
            },
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "average": sum(values) / len(values),
            "latest": values[0] if values else None,  # readings are sorted by timestamp desc
            "unit": history.readings[0].unit if history.readings else ""
        }
        
        # Calculate additional statistics if we have enough data
        if len(values) > 1:
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            # Median
            if n % 2 == 0:
                statistics["median"] = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
            else:
                statistics["median"] = sorted_values[n//2]
            
            # Standard deviation
            mean = statistics["average"]
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            statistics["std_deviation"] = variance ** 0.5
            
            # Percentiles
            statistics["percentile_25"] = sorted_values[int(0.25 * n)]
            statistics["percentile_75"] = sorted_values[int(0.75 * n)]
        
        logger.info(f"Calculated statistics for {sensor_type} on machine {machine_id}")
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate sensor statistics")


@router.get("/{machine_id}/alerts")
async def get_sensor_alerts(
    machine_id: str,
    hours: int = Query(24, description="Hours of history to check for alerts", ge=1, le=168),
    db: DatabaseService = Depends(get_db_service)
):
    """
    Get sensor alert history
    
    Analyze historical data to identify periods when sensors exceeded
    their configured thresholds.
    """
    try:
        # Get machine state for current thresholds
        machine = await db.get_machine_state(machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Time range for analysis
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        alerts = []
        
        # Check each sensor type
        sensor_configs = [
            ("temperature", machine.temperature_threshold, "°C"),
            ("humidity", machine.humidity_threshold, "%"),
            ("vibration", machine.vibration_threshold, "m/s²")
        ]
        
        for sensor_type, threshold, unit in sensor_configs:
            history = await db.get_sensor_history(
                machine_id=machine_id,
                sensor_type=sensor_type,
                start_time=start_time,
                end_time=end_time,
                limit=5000
            )
            
            # Find readings that exceeded threshold
            for reading in history.readings:
                if reading.value > threshold:
                    alerts.append({
                        "timestamp": reading.timestamp,
                        "sensor_type": sensor_type,
                        "value": reading.value,
                        "threshold": threshold,
                        "unit": unit,
                        "severity": "critical" if reading.value > threshold * 1.2 else "warning"
                    })
        
        # Sort alerts by timestamp (most recent first)
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "machine_id": machine_id,
            "time_period": {
                "start": start_time,
                "end": end_time,
                "hours": hours
            },
            "alert_count": len(alerts),
            "alerts": alerts[:100]  # Limit to 100 most recent alerts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sensor alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sensor alerts")