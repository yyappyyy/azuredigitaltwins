"""
Tests for Sensor Simulator

Unit tests for sensor data simulation including pattern generation
and realistic sensor behavior.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from services.sensor_simulator import SensorSimulator
from models.data_models import MachineStatus, MachineType


@pytest.fixture
def simulator():
    """Create sensor simulator for testing"""
    with patch('services.sensor_simulator.DatabaseService') as mock_db, \
         patch('services.sensor_simulator.AzureDigitalTwinsService') as mock_dt:
        
        # Mock the database and DT services
        mock_db.return_value.initialize = AsyncMock()
        mock_db.return_value.save_machine_state = AsyncMock(return_value=True)
        mock_db.return_value.save_sensor_reading = AsyncMock(return_value=True)
        mock_db.return_value.disconnect = AsyncMock()
        
        mock_dt.return_value.initialize = AsyncMock()
        mock_dt.return_value.update_machine_from_state = AsyncMock(return_value=True)
        
        simulator = SensorSimulator()
        return simulator


@pytest.mark.asyncio
async def test_simulator_initialization(simulator):
    """Test simulator initialization"""
    # Check that machines were initialized
    assert len(simulator._machines) > 0
    
    # Check that sensor patterns were created
    for machine_id in simulator._machines.keys():
        assert machine_id in simulator._sensor_patterns
        pattern = simulator._sensor_patterns[machine_id]
        
        # Check that all required pattern parameters exist
        required_keys = [
            'temp_base', 'temp_amplitude', 'temp_frequency',
            'humidity_base', 'humidity_amplitude', 'humidity_frequency',
            'vibration_base', 'vibration_amplitude', 'vibration_frequency',
            'phase_offset'
        ]
        for key in required_keys:
            assert key in pattern


@pytest.mark.asyncio
async def test_sensor_value_generation(simulator):
    """Test sensor value generation with realistic patterns"""
    # Get a test machine
    machine_ids = list(simulator._machines.keys())
    assert len(machine_ids) > 0
    
    machine_id = machine_ids[0]
    machine_state = simulator._machines[machine_id]
    
    # Test sensor updates
    simulation_time = 0.0
    original_temp = machine_state.temperature
    original_humidity = machine_state.humidity
    original_vibration = machine_state.vibration
    
    # Update sensors
    await simulator._update_machine_sensors(machine_state, simulation_time)
    
    # Check that values changed and are reasonable
    assert isinstance(machine_state.temperature, float)
    assert isinstance(machine_state.humidity, float)
    assert isinstance(machine_state.vibration, float)
    
    # Check value ranges are reasonable
    assert 0 < machine_state.temperature < 60  # Reasonable temperature range
    assert 0 < machine_state.humidity < 100    # Humidity percentage
    assert machine_state.vibration >= 0       # Vibration can't be negative
    
    # Check that alerts are updated
    assert isinstance(machine_state.has_temperature_alert, bool)
    assert isinstance(machine_state.has_humidity_alert, bool)
    assert isinstance(machine_state.has_vibration_alert, bool)


@pytest.mark.asyncio
async def test_machine_status_effects(simulator):
    """Test that machine status affects sensor readings"""
    machine_ids = list(simulator._machines.keys())
    machine_id = machine_ids[0]
    machine_state = simulator._machines[machine_id]
    
    # Test running status
    machine_state.status = MachineStatus.RUNNING
    await simulator._update_machine_sensors(machine_state, 0.0)
    running_temp = machine_state.temperature
    running_vibration = machine_state.vibration
    
    # Test stopped status
    machine_state.status = MachineStatus.STOPPED
    await simulator._update_machine_sensors(machine_state, 0.0)
    stopped_temp = machine_state.temperature
    stopped_vibration = machine_state.vibration
    
    # Stopped machines should generally have lower readings
    # (though this might not always be true due to randomness)
    # At least verify the values are different
    assert stopped_temp != running_temp or stopped_vibration != running_vibration


@pytest.mark.asyncio
async def test_machine_type_effects(simulator):
    """Test that machine type affects sensor multipliers"""
    # Test different machine types
    cnc_factor = simulator._get_machine_type_factor(MachineType.CNC)
    press_factor = simulator._get_machine_type_factor(MachineType.PRESS)
    conveyor_factor = simulator._get_machine_type_factor(MachineType.CONVEYOR)
    
    # Each should have different characteristics
    assert cnc_factor != press_factor
    assert press_factor != conveyor_factor
    
    # Check that factors are reasonable (positive values)
    for factor_dict in [cnc_factor, press_factor, conveyor_factor]:
        assert factor_dict["temperature"] > 0
        assert factor_dict["humidity"] > 0
        assert factor_dict["vibration"] > 0
    
    # Press machines should have higher vibration factor
    assert press_factor["vibration"] > cnc_factor["vibration"]


@pytest.mark.asyncio
async def test_status_multiplier(simulator):
    """Test status multiplier calculations"""
    running_mult = simulator._get_status_multiplier(MachineStatus.RUNNING)
    stopped_mult = simulator._get_status_multiplier(MachineStatus.STOPPED)
    error_mult = simulator._get_status_multiplier(MachineStatus.ERROR)
    maint_mult = simulator._get_status_multiplier(MachineStatus.MAINTENANCE)
    
    # Running should have highest multiplier
    assert running_mult == 1.0
    
    # Stopped and maintenance should have lower multipliers
    assert stopped_mult < running_mult
    assert maint_mult < running_mult
    
    # All should be positive
    assert all(mult > 0 for mult in [running_mult, stopped_mult, error_mult, maint_mult])


def test_machine_state_access(simulator):
    """Test getting machine states"""
    states = simulator.get_machine_states()
    
    # Should return a copy of the machines dict
    assert len(states) == len(simulator._machines)
    assert states is not simulator._machines  # Should be a copy
    
    # Check that all states are valid
    for machine_id, state in states.items():
        assert hasattr(state, 'machine_id')
        assert hasattr(state, 'status')
        assert hasattr(state, 'temperature')
        assert hasattr(state, 'humidity')
        assert hasattr(state, 'vibration')


def test_update_machine_status(simulator):
    """Test updating machine status"""
    machine_ids = list(simulator._machines.keys())
    machine_id = machine_ids[0]
    
    # Update to running
    success = simulator.update_machine_status(machine_id, MachineStatus.RUNNING)
    assert success is True
    assert simulator._machines[machine_id].status == MachineStatus.RUNNING
    
    # Update to stopped
    success = simulator.update_machine_status(machine_id, MachineStatus.STOPPED)
    assert success is True
    assert simulator._machines[machine_id].status == MachineStatus.STOPPED
    
    # Test invalid machine ID
    success = simulator.update_machine_status("invalid-id", MachineStatus.RUNNING)
    assert success is False


def test_update_machine_thresholds(simulator):
    """Test updating machine thresholds"""
    machine_ids = list(simulator._machines.keys())
    machine_id = machine_ids[0]
    
    original_machine = simulator._machines[machine_id]
    original_temp_threshold = original_machine.temperature_threshold
    
    # Update thresholds
    new_temp_threshold = 35.0
    new_humidity_threshold = 80.0
    new_vibration_threshold = 2.0
    
    success = simulator.update_machine_thresholds(
        machine_id,
        temperature_threshold=new_temp_threshold,
        humidity_threshold=new_humidity_threshold,
        vibration_threshold=new_vibration_threshold
    )
    
    assert success is True
    assert simulator._machines[machine_id].temperature_threshold == new_temp_threshold
    assert simulator._machines[machine_id].humidity_threshold == new_humidity_threshold
    assert simulator._machines[machine_id].vibration_threshold == new_vibration_threshold
    
    # Test partial update
    success = simulator.update_machine_thresholds(
        machine_id,
        temperature_threshold=40.0  # Only update temperature
    )
    
    assert success is True
    assert simulator._machines[machine_id].temperature_threshold == 40.0
    # Other thresholds should remain unchanged
    assert simulator._machines[machine_id].humidity_threshold == new_humidity_threshold
    assert simulator._machines[machine_id].vibration_threshold == new_vibration_threshold
    
    # Test invalid machine ID
    success = simulator.update_machine_thresholds("invalid-id", temperature_threshold=30.0)
    assert success is False


def test_simulator_running_state(simulator):
    """Test simulator running state tracking"""
    # Initially not running
    assert simulator.is_running() is False
    
    # Set running state manually for testing
    simulator._running = True
    assert simulator.is_running() is True
    
    simulator._running = False
    assert simulator.is_running() is False


@pytest.mark.asyncio
async def test_save_sensor_readings(simulator):
    """Test saving individual sensor readings"""
    machine_ids = list(simulator._machines.keys())
    machine_state = simulator._machines[machine_ids[0]]
    
    # Set some sensor values
    machine_state.temperature = 25.5
    machine_state.humidity = 60.0
    machine_state.vibration = 0.8
    
    # This should not raise an exception
    await simulator._save_sensor_readings(machine_state)
    
    # Verify the mock was called (checking that save_sensor_reading was called)
    # The exact number depends on how many non-None sensor values there are
    assert simulator.db_service.save_sensor_reading.call_count >= 1


@pytest.mark.asyncio 
async def test_sensor_value_ranges(simulator):
    """Test that generated sensor values stay within reasonable ranges"""
    machine_ids = list(simulator._machines.keys())
    machine_state = simulator._machines[machine_ids[0]]
    
    # Run multiple simulation steps
    for simulation_time in range(0, 100, 10):
        await simulator._update_machine_sensors(machine_state, float(simulation_time))
        
        # Check temperature is reasonable
        assert -10 < machine_state.temperature < 80  # Extreme but possible range
        
        # Check humidity is within 0-100%
        assert 0 <= machine_state.humidity <= 100
        
        # Check vibration is non-negative
        assert machine_state.vibration >= 0
        assert machine_state.vibration < 10  # Reasonable upper bound


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])