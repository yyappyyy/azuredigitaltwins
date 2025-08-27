"""
Tests for SQLite Database Service

Unit tests for database operations including machine state management
and sensor data storage/retrieval.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta

from services.sqlite_service import DatabaseService
from models.data_models import MachineState, SensorReading, MachineStatus, MachineType


@pytest.fixture
async def db_service():
    """Create a temporary database service for testing"""
    # Use temporary file for testing database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Modify settings temporarily
    original_db_url = None
    try:
        from config.settings import get_settings
        settings = get_settings()
        original_db_url = settings.DATABASE_URL
        settings.DATABASE_URL = f"sqlite:///{temp_db.name}"
    except ImportError:
        pass
    
    service = DatabaseService()
    service.db_path = temp_db.name
    
    await service.initialize()
    
    yield service
    
    await service.disconnect()
    
    # Clean up temporary file
    if os.path.exists(temp_db.name):
        os.unlink(temp_db.name)
    
    # Restore original settings
    if original_db_url:
        settings.DATABASE_URL = original_db_url


@pytest.mark.asyncio
async def test_database_initialization(db_service):
    """Test database initialization and table creation"""
    # Database should be initialized during fixture setup
    assert db_service._connection is not None
    
    # Test that tables exist by trying to query them
    cursor = await db_service._connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = await cursor.fetchall()
    table_names = [table[0] for table in tables]
    
    expected_tables = ['sensor_readings', 'machine_states', 'machine_events']
    for expected_table in expected_tables:
        assert expected_table in table_names


@pytest.mark.asyncio
async def test_save_and_get_machine_state(db_service):
    """Test saving and retrieving machine state"""
    # Create test machine state
    machine_state = MachineState(
        machine_id="TEST-001",
        machine_name="Test Machine",
        machine_type=MachineType.CNC,
        status=MachineStatus.RUNNING,
        location="Test Station",
        temperature=25.5,
        humidity=55.0,
        vibration=0.8,
        temperature_threshold=30.0,
        humidity_threshold=70.0,
        vibration_threshold=1.5
    )
    
    # Save machine state
    success = await db_service.save_machine_state(machine_state)
    assert success is True
    
    # Retrieve machine state
    retrieved_state = await db_service.get_machine_state("TEST-001")
    assert retrieved_state is not None
    assert retrieved_state.machine_id == "TEST-001"
    assert retrieved_state.machine_name == "Test Machine"
    assert retrieved_state.temperature == 25.5
    assert retrieved_state.status == MachineStatus.RUNNING


@pytest.mark.asyncio
async def test_save_sensor_reading(db_service):
    """Test saving sensor readings"""
    # Create test sensor reading
    reading = SensorReading(
        machine_id="TEST-001",
        sensor_type="temperature",
        value=25.5,
        unit="°C",
        timestamp=datetime.utcnow()
    )
    
    # Save sensor reading
    success = await db_service.save_sensor_reading(reading)
    assert success is True


@pytest.mark.asyncio
async def test_get_sensor_history(db_service):
    """Test retrieving sensor history"""
    machine_id = "TEST-001"
    sensor_type = "temperature"
    
    # Create multiple sensor readings
    readings = []
    for i in range(5):
        reading = SensorReading(
            machine_id=machine_id,
            sensor_type=sensor_type,
            value=20.0 + i,
            unit="°C",
            timestamp=datetime.utcnow() - timedelta(minutes=i)
        )
        readings.append(reading)
        await db_service.save_sensor_reading(reading)
    
    # Retrieve sensor history
    history = await db_service.get_sensor_history(
        machine_id=machine_id,
        sensor_type=sensor_type,
        start_time=datetime.utcnow() - timedelta(hours=1),
        end_time=datetime.utcnow(),
        limit=10
    )
    
    assert history.machine_id == machine_id
    assert history.sensor_type == sensor_type
    assert len(history.readings) == 5
    assert history.count == 5


@pytest.mark.asyncio
async def test_get_all_machine_states(db_service):
    """Test retrieving all machine states"""
    # Create multiple test machines
    machines = []
    for i in range(3):
        machine = MachineState(
            machine_id=f"TEST-00{i+1}",
            machine_name=f"Test Machine {i+1}",
            machine_type=MachineType.CNC,
            status=MachineStatus.RUNNING if i % 2 == 0 else MachineStatus.STOPPED,
            location=f"Test Station {i+1}",
            temperature=20.0 + i,
            humidity=50.0 + i * 5,
            vibration=0.5 + i * 0.1
        )
        machines.append(machine)
        await db_service.save_machine_state(machine)
    
    # Retrieve all machine states
    all_machines = await db_service.get_all_machine_states()
    assert len(all_machines) >= 3
    
    # Check that our test machines are included
    test_machine_ids = {m.machine_id for m in all_machines if m.machine_id.startswith("TEST-")}
    expected_ids = {"TEST-001", "TEST-002", "TEST-003"}
    assert test_machine_ids == expected_ids


@pytest.mark.asyncio
async def test_log_machine_event(db_service):
    """Test logging machine events"""
    machine_id = "TEST-001"
    event_type = "command_executed"
    event_data = {"command": "start", "user": "test_user"}
    
    # Log machine event
    success = await db_service.log_machine_event(machine_id, event_type, event_data)
    assert success is True
    
    # Verify event was logged (check table directly)
    cursor = await db_service._connection.execute(
        "SELECT * FROM machine_events WHERE machine_id = ? AND event_type = ?",
        (machine_id, event_type)
    )
    events = await cursor.fetchall()
    assert len(events) >= 1


@pytest.mark.asyncio
async def test_machine_state_alerts(db_service):
    """Test machine state alert functionality"""
    # Create machine with values that exceed thresholds
    machine_state = MachineState(
        machine_id="ALERT-TEST",
        machine_name="Alert Test Machine",
        machine_type=MachineType.PRESS,
        status=MachineStatus.RUNNING,
        location="Alert Station",
        temperature=35.0,  # Above threshold of 30.0
        humidity=75.0,     # Above threshold of 70.0
        vibration=2.0,     # Above threshold of 1.5
        temperature_threshold=30.0,
        humidity_threshold=70.0,
        vibration_threshold=1.5
    )
    
    # Update alerts should be called when saving
    machine_state.update_alerts()
    
    # Check that alerts are triggered
    assert machine_state.has_temperature_alert is True
    assert machine_state.has_humidity_alert is True
    assert machine_state.has_vibration_alert is True
    
    # Save and retrieve to verify persistence
    await db_service.save_machine_state(machine_state)
    retrieved = await db_service.get_machine_state("ALERT-TEST")
    
    assert retrieved.has_temperature_alert is True
    assert retrieved.has_humidity_alert is True
    assert retrieved.has_vibration_alert is True


@pytest.mark.asyncio
async def test_nonexistent_machine(db_service):
    """Test retrieving nonexistent machine returns None"""
    machine = await db_service.get_machine_state("NONEXISTENT")
    assert machine is None


@pytest.mark.asyncio
async def test_empty_sensor_history(db_service):
    """Test retrieving sensor history for nonexistent machine/sensor"""
    history = await db_service.get_sensor_history(
        machine_id="NONEXISTENT",
        sensor_type="temperature",
        start_time=datetime.utcnow() - timedelta(hours=1),
        end_time=datetime.utcnow()
    )
    
    assert history.machine_id == "NONEXISTENT"
    assert history.sensor_type == "temperature"
    assert len(history.readings) == 0
    assert history.count == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])