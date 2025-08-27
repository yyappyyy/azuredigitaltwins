"""
SQLite Database Service

Handles sensor data storage, retrieval, and history management
"""

import aiosqlite
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from models.data_models import SensorReading, MachineState, SensorHistory
from config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """SQLite database service for sensor data and machine state management"""
    
    def __init__(self):
        settings = get_settings()
        self.db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            await self.connect()
            await self._create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def connect(self):
        """Establish database connection"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
    
    async def disconnect(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        create_sensor_readings_table = """
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            INDEX(machine_id),
            INDEX(sensor_type),
            INDEX(timestamp)
        )
        """
        
        create_machine_states_table = """
        CREATE TABLE IF NOT EXISTS machine_states (
            machine_id TEXT PRIMARY KEY,
            machine_name TEXT NOT NULL,
            machine_type TEXT NOT NULL,
            status TEXT NOT NULL,
            location TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            vibration REAL,
            temperature_threshold REAL DEFAULT 30.0,
            humidity_threshold REAL DEFAULT 70.0,
            vibration_threshold REAL DEFAULT 1.5,
            has_temperature_alert INTEGER DEFAULT 0,
            has_humidity_alert INTEGER DEFAULT 0,
            has_vibration_alert INTEGER DEFAULT 0,
            last_updated TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        create_machine_events_table = """
        CREATE TABLE IF NOT EXISTS machine_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            INDEX(machine_id),
            INDEX(event_type),
            INDEX(timestamp)
        )
        """
        
        await self._connection.execute(create_sensor_readings_table)
        await self._connection.execute(create_machine_states_table)
        await self._connection.execute(create_machine_events_table)
        await self._connection.commit()
    
    async def save_sensor_reading(self, reading: SensorReading) -> bool:
        """Save a sensor reading to the database"""
        try:
            query = """
            INSERT INTO sensor_readings (machine_id, sensor_type, value, unit, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """
            await self._connection.execute(
                query,
                (
                    reading.machine_id,
                    reading.sensor_type,
                    reading.value,
                    reading.unit,
                    reading.timestamp.isoformat()
                )
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save sensor reading: {e}")
            return False
    
    async def save_machine_state(self, machine_state: MachineState) -> bool:
        """Save or update machine state in the database"""
        try:
            # Update alerts before saving
            machine_state.update_alerts()
            
            query = """
            INSERT OR REPLACE INTO machine_states (
                machine_id, machine_name, machine_type, status, location,
                temperature, humidity, vibration,
                temperature_threshold, humidity_threshold, vibration_threshold,
                has_temperature_alert, has_humidity_alert, has_vibration_alert,
                last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            await self._connection.execute(
                query,
                (
                    machine_state.machine_id,
                    machine_state.machine_name,
                    machine_state.machine_type.value,
                    machine_state.status.value,
                    machine_state.location,
                    machine_state.temperature,
                    machine_state.humidity,
                    machine_state.vibration,
                    machine_state.temperature_threshold,
                    machine_state.humidity_threshold,
                    machine_state.vibration_threshold,
                    int(machine_state.has_temperature_alert),
                    int(machine_state.has_humidity_alert),
                    int(machine_state.has_vibration_alert),
                    machine_state.last_updated.isoformat()
                )
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save machine state: {e}")
            return False
    
    async def get_machine_state(self, machine_id: str) -> Optional[MachineState]:
        """Get current machine state from database"""
        try:
            query = "SELECT * FROM machine_states WHERE machine_id = ?"
            cursor = await self._connection.execute(query, (machine_id,))
            row = await cursor.fetchone()
            
            if row:
                return MachineState(
                    machine_id=row["machine_id"],
                    machine_name=row["machine_name"],
                    machine_type=row["machine_type"],
                    status=row["status"],
                    location=row["location"],
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                    vibration=row["vibration"],
                    temperature_threshold=row["temperature_threshold"],
                    humidity_threshold=row["humidity_threshold"],
                    vibration_threshold=row["vibration_threshold"],
                    has_temperature_alert=bool(row["has_temperature_alert"]),
                    has_humidity_alert=bool(row["has_humidity_alert"]),
                    has_vibration_alert=bool(row["has_vibration_alert"]),
                    last_updated=datetime.fromisoformat(row["last_updated"])
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get machine state: {e}")
            return None
    
    async def get_all_machine_states(self) -> List[MachineState]:
        """Get all machine states from database"""
        try:
            query = "SELECT * FROM machine_states ORDER BY machine_id"
            cursor = await self._connection.execute(query)
            rows = await cursor.fetchall()
            
            machines = []
            for row in rows:
                machine = MachineState(
                    machine_id=row["machine_id"],
                    machine_name=row["machine_name"],
                    machine_type=row["machine_type"],
                    status=row["status"],
                    location=row["location"],
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                    vibration=row["vibration"],
                    temperature_threshold=row["temperature_threshold"],
                    humidity_threshold=row["humidity_threshold"],
                    vibration_threshold=row["vibration_threshold"],
                    has_temperature_alert=bool(row["has_temperature_alert"]),
                    has_humidity_alert=bool(row["has_humidity_alert"]),
                    has_vibration_alert=bool(row["has_vibration_alert"]),
                    last_updated=datetime.fromisoformat(row["last_updated"])
                )
                machines.append(machine)
            
            return machines
        except Exception as e:
            logger.error(f"Failed to get all machine states: {e}")
            return []
    
    async def get_sensor_history(
        self,
        machine_id: str,
        sensor_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> SensorHistory:
        """Get historical sensor data for a specific machine and sensor type"""
        try:
            # Default time range: last 24 hours
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            query = """
            SELECT * FROM sensor_readings 
            WHERE machine_id = ? AND sensor_type = ? 
            AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
            LIMIT ?
            """
            cursor = await self._connection.execute(
                query,
                (
                    machine_id,
                    sensor_type,
                    start_time.isoformat(),
                    end_time.isoformat(),
                    limit
                )
            )
            rows = await cursor.fetchall()
            
            readings = []
            for row in rows:
                reading = SensorReading(
                    machine_id=row["machine_id"],
                    sensor_type=row["sensor_type"],
                    value=row["value"],
                    unit=row["unit"],
                    timestamp=datetime.fromisoformat(row["timestamp"])
                )
                readings.append(reading)
            
            return SensorHistory(
                machine_id=machine_id,
                sensor_type=sensor_type,
                readings=readings,
                count=len(readings),
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            logger.error(f"Failed to get sensor history: {e}")
            return SensorHistory(
                machine_id=machine_id,
                sensor_type=sensor_type,
                readings=[],
                count=0,
                start_time=start_time or datetime.utcnow(),
                end_time=end_time or datetime.utcnow()
            )
    
    async def log_machine_event(
        self,
        machine_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log a machine event to the database"""
        try:
            query = """
            INSERT INTO machine_events (machine_id, event_type, event_data, timestamp)
            VALUES (?, ?, ?, ?)
            """
            await self._connection.execute(
                query,
                (
                    machine_id,
                    event_type,
                    json.dumps(event_data) if event_data else None,
                    datetime.utcnow().isoformat()
                )
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log machine event: {e}")
            return False
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old sensor readings and events"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Clean up old sensor readings
            await self._connection.execute(
                "DELETE FROM sensor_readings WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            
            # Clean up old machine events
            await self._connection.execute(
                "DELETE FROM machine_events WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            
            await self._connection.commit()
            logger.info(f"Cleaned up data older than {days_to_keep} days")
        except Exception as e:
            logger.error(f"Failed to clean up old data: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()