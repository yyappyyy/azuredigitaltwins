"""
Tests for Azure Digital Twins Service

Unit tests for Azure Digital Twins integration including mock mode testing.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from services.azure_dt_service import AzureDigitalTwinsService
from models.data_models import MachineState, MachineCommand, MachineStatus, MachineType


@pytest.fixture
def dt_service():
    """Create Azure Digital Twins service in mock mode"""
    service = AzureDigitalTwinsService()
    # Force mock mode for testing
    service._is_mock_mode = True
    service._mock_twins = {}
    return service


@pytest.mark.asyncio
async def test_service_initialization(dt_service):
    """Test service initialization in mock mode"""
    await dt_service.initialize()
    
    # In mock mode, sample data should be loaded
    assert len(dt_service._mock_twins) > 0
    assert dt_service.is_connected() is False  # Mock mode is not "connected"
    
    status = dt_service.get_connection_status()
    assert status["mock_mode"] is True
    assert status["connected"] is False


@pytest.mark.asyncio
async def test_update_twin_property_mock(dt_service):
    """Test updating twin property in mock mode"""
    await dt_service.initialize()
    
    # Get a twin ID from mock data
    twin_ids = list(dt_service._mock_twins.keys())
    if twin_ids:
        twin_id = twin_ids[0]
        
        # Update a property
        success = await dt_service.update_twin_property(twin_id, "isRunning", True)
        assert success is True
        
        # Verify the property was updated
        assert dt_service._mock_twins[twin_id]["isRunning"] is True


@pytest.mark.asyncio
async def test_send_telemetry_mock(dt_service):
    """Test sending telemetry in mock mode"""
    await dt_service.initialize()
    
    telemetry_data = {
        "temperature": 25.5,
        "humidity": 60.0,
        "vibration": 0.8
    }
    
    # In mock mode, this should always succeed
    success = await dt_service.send_telemetry("test-twin", telemetry_data)
    assert success is True


@pytest.mark.asyncio
async def test_get_twin_mock(dt_service):
    """Test retrieving twin data in mock mode"""
    await dt_service.initialize()
    
    # Get a twin ID from mock data
    twin_ids = list(dt_service._mock_twins.keys())
    if twin_ids:
        twin_id = twin_ids[0]
        
        twin_data = await dt_service.get_twin(twin_id)
        assert twin_data is not None
        assert twin_data == dt_service._mock_twins[twin_id]
    
    # Test nonexistent twin
    nonexistent = await dt_service.get_twin("nonexistent-twin")
    assert nonexistent is None


@pytest.mark.asyncio
async def test_list_twins_mock(dt_service):
    """Test listing twins in mock mode"""
    await dt_service.initialize()
    
    # List all twins
    all_twins = await dt_service.list_twins()
    assert len(all_twins) > 0
    assert len(all_twins) == len(dt_service._mock_twins)
    
    # List twins by model
    machine_model = "dtmi:digitaltwins:factory:Machine;1"
    machine_twins = await dt_service.list_twins(model_id=machine_model)
    
    # Should have some machine twins
    assert len(machine_twins) > 0
    
    # All returned twins should be of the specified model
    for twin in machine_twins:
        model = twin.get("$metadata", {}).get("$model")
        assert model == machine_model


@pytest.mark.asyncio
async def test_execute_command_mock(dt_service):
    """Test executing commands in mock mode"""
    await dt_service.initialize()
    
    # Get a machine twin ID
    machine_twins = [twin_id for twin_id, data in dt_service._mock_twins.items() 
                    if data.get("$metadata", {}).get("$model") == "dtmi:digitaltwins:factory:Machine;1"]
    
    if machine_twins:
        twin_id = machine_twins[0]
        
        # Test start command
        start_command = MachineCommand(command_type="startMachine")
        success = await dt_service.execute_command(twin_id, start_command)
        assert success is True
        
        # Verify the twin state was updated
        assert dt_service._mock_twins[twin_id]["isRunning"] is True
        
        # Test stop command
        stop_command = MachineCommand(command_type="stopMachine")
        success = await dt_service.execute_command(twin_id, stop_command)
        assert success is True
        
        # Verify the twin state was updated
        assert dt_service._mock_twins[twin_id]["isRunning"] is False


@pytest.mark.asyncio
async def test_update_machine_from_state_mock(dt_service):
    """Test updating twin from machine state in mock mode"""
    await dt_service.initialize()
    
    # Create a test machine state
    machine_state = MachineState(
        machine_id="cnc-01",  # This should map to twin "machine-cnc-01"
        machine_name="Test CNC Machine",
        machine_type=MachineType.CNC,
        status=MachineStatus.RUNNING,
        location="Test Station",
        temperature=28.5,
        humidity=65.0,
        vibration=1.2,
        temperature_threshold=32.0,
        humidity_threshold=75.0,
        vibration_threshold=1.8
    )
    
    # Update twin from machine state
    success = await dt_service.update_machine_from_state(machine_state)
    assert success is True


@pytest.mark.asyncio
async def test_sync_machine_states_mock(dt_service):
    """Test syncing multiple machine states"""
    await dt_service.initialize()
    
    # Create multiple test machine states
    machine_states = [
        MachineState(
            machine_id=f"test-{i:03d}",
            machine_name=f"Test Machine {i}",
            machine_type=MachineType.CNC,
            status=MachineStatus.RUNNING,
            location=f"Station {i}",
            temperature=20.0 + i,
            humidity=50.0 + i,
            vibration=0.5 + i * 0.1
        ) for i in range(3)
    ]
    
    # Sync all machine states
    results = await dt_service.sync_machine_states(machine_states)
    
    # All syncs should succeed in mock mode
    assert len(results) == 3
    for machine_id, success in results.items():
        assert success is True


@pytest.mark.asyncio
async def test_connection_status_mock(dt_service):
    """Test connection status reporting"""
    status = dt_service.get_connection_status()
    
    expected_keys = ["connected", "mock_mode", "azure_url", "client_available"]
    for key in expected_keys:
        assert key in status
    
    assert status["connected"] is False
    assert status["mock_mode"] is True


@pytest.mark.asyncio  
async def test_error_handling(dt_service):
    """Test error handling for invalid operations"""
    # Test updating property on nonexistent twin
    success = await dt_service.update_twin_property("nonexistent", "property", "value")
    assert success is False
    
    # Test sending telemetry to nonexistent twin (should still succeed in mock mode)
    success = await dt_service.send_telemetry("nonexistent", {"temp": 25})
    assert success is True  # Mock mode always succeeds


# Integration tests that would run against real Azure DT (if configured)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_azure_connection():
    """Integration test for real Azure Digital Twins connection"""
    # This test would only run if Azure credentials are configured
    from config.settings import is_azure_configured
    
    if not is_azure_configured():
        pytest.skip("Azure Digital Twins not configured")
    
    service = AzureDigitalTwinsService()
    await service.initialize()
    
    if service.is_connected():
        # Test basic operations against real Azure DT
        models = await service.list_twins()
        # Add more real integration tests here
        pass
    else:
        pytest.skip("Could not connect to Azure Digital Twins")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])