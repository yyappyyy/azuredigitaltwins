"""
Digital Twins API Routes

Endpoints for managing digital twin states, commands, and properties
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional, Dict, Any
import logging

from models.data_models import (
    MachineState, MachineUpdate, MachineCommand, TwinResponse, 
    DashboardData, MachineStatus
)
from services.sqlite_service import DatabaseService
from services.azure_dt_service import AzureDigitalTwinsService
from services.websocket_service import websocket_manager
from services.sensor_simulator import SensorSimulator

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances (these would be injected in a production app)
db_service = DatabaseService()
dt_service = AzureDigitalTwinsService()
simulator = SensorSimulator()


async def get_db_service():
    """Dependency to get database service"""
    await db_service.connect()
    return db_service


@router.get("/health")
async def health_check():
    """Health check for twins API"""
    return {
        "status": "healthy",
        "service": "digital_twins_api",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/", response_model=List[MachineState])
async def get_all_machines(db: DatabaseService = Depends(get_db_service)):
    """
    Get all machine states
    
    Returns a list of all factory machines with their current states,
    sensor readings, and alert status.
    """
    try:
        machines = await db.get_all_machine_states()
        logger.info(f"Retrieved {len(machines)} machine states")
        return machines
    except Exception as e:
        logger.error(f"Failed to get machine states: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve machine states")


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(db: DatabaseService = Depends(get_db_service)):
    """
    Get aggregated dashboard data
    
    Returns dashboard-ready data including machine counts, statistics,
    and alert summaries for the frontend.
    """
    try:
        machines = await db.get_all_machine_states()
        
        running_machines = sum(1 for m in machines if m.status == MachineStatus.RUNNING)
        machines_with_alerts = sum(
            1 for m in machines 
            if m.has_temperature_alert or m.has_humidity_alert or m.has_vibration_alert
        )
        
        dashboard_data = DashboardData(
            machines=machines,
            total_machines=len(machines),
            running_machines=running_machines,
            machines_with_alerts=machines_with_alerts
        )
        
        logger.info(f"Generated dashboard data for {len(machines)} machines")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/{machine_id}", response_model=MachineState)
async def get_machine(machine_id: str, db: DatabaseService = Depends(get_db_service)):
    """
    Get specific machine state
    
    Returns detailed information for a specific machine including
    current sensor readings and alert status.
    """
    try:
        machine = await db.get_machine_state(machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        logger.info(f"Retrieved machine state for {machine_id}")
        return machine
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get machine {machine_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve machine state")


@router.put("/{machine_id}", response_model=TwinResponse)
async def update_machine(
    machine_id: str, 
    update: MachineUpdate,
    background_tasks: BackgroundTasks,
    db: DatabaseService = Depends(get_db_service)
):
    """
    Update machine properties
    
    Update machine configuration, thresholds, and other properties.
    Changes are synchronized with Azure Digital Twins and broadcast
    via WebSocket to connected clients.
    """
    try:
        # Get current machine state
        machine = await db.get_machine_state(machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Apply updates
        updated = False
        if update.machine_name is not None:
            machine.machine_name = update.machine_name
            updated = True
        if update.status is not None:
            machine.status = update.status
            updated = True
        if update.location is not None:
            machine.location = update.location
            updated = True
        if update.temperature_threshold is not None:
            machine.temperature_threshold = update.temperature_threshold
            updated = True
        if update.humidity_threshold is not None:
            machine.humidity_threshold = update.humidity_threshold
            updated = True
        if update.vibration_threshold is not None:
            machine.vibration_threshold = update.vibration_threshold
            updated = True
        
        if not updated:
            return TwinResponse(
                success=False,
                message="No valid updates provided"
            )
        
        # Recalculate alerts
        machine.update_alerts()
        
        # Save to database
        await db.save_machine_state(machine)
        
        # Update simulator if thresholds changed
        if any([update.temperature_threshold, update.humidity_threshold, update.vibration_threshold]):
            simulator.update_machine_thresholds(
                machine_id,
                update.temperature_threshold,
                update.humidity_threshold,
                update.vibration_threshold
            )
        
        # Update simulator status if changed
        if update.status is not None:
            simulator.update_machine_status(machine_id, update.status)
        
        # Sync to Azure Digital Twins
        background_tasks.add_task(sync_to_azure_dt, machine)
        
        # Broadcast update via WebSocket
        background_tasks.add_task(websocket_manager.broadcast_machine_update, machine)
        
        logger.info(f"Updated machine {machine_id}")
        return TwinResponse(
            success=True,
            message=f"Machine {machine_id} updated successfully",
            data=machine.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update machine {machine_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update machine")


@router.post("/{machine_id}/commands", response_model=TwinResponse)
async def execute_command(
    machine_id: str,
    command: MachineCommand,
    background_tasks: BackgroundTasks,
    db: DatabaseService = Depends(get_db_service)
):
    """
    Execute a command on a machine
    
    Execute commands like start, stop, or reset_alarms on a factory machine.
    Commands are executed on both the simulator and Azure Digital Twins.
    """
    try:
        # Verify machine exists
        machine = await db.get_machine_state(machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Execute command based on type
        if command.command_type == "startMachine":
            machine.status = MachineStatus.RUNNING
            simulator.update_machine_status(machine_id, MachineStatus.RUNNING)
            await db.save_machine_state(machine)
            
        elif command.command_type == "stopMachine":
            machine.status = MachineStatus.STOPPED
            simulator.update_machine_status(machine_id, MachineStatus.STOPPED)
            await db.save_machine_state(machine)
            
        elif command.command_type == "resetAlarms":
            # Reset alert flags
            machine.has_temperature_alert = False
            machine.has_humidity_alert = False
            machine.has_vibration_alert = False
            await db.save_machine_state(machine)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command.command_type}")
        
        # Log the command execution
        await db.log_machine_event(
            machine_id, 
            "command_executed", 
            {"command_type": command.command_type, "parameters": command.parameters}
        )
        
        # Execute command on Azure Digital Twins
        background_tasks.add_task(execute_azure_dt_command, machine_id, command)
        
        # Broadcast update via WebSocket
        background_tasks.add_task(websocket_manager.broadcast_machine_update, machine)
        
        logger.info(f"Executed command {command.command_type} on machine {machine_id}")
        return TwinResponse(
            success=True,
            message=f"Command {command.command_type} executed on machine {machine_id}",
            data={"command": command.command_type, "machine_state": machine.dict()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute command on machine {machine_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute command")


@router.get("/{machine_id}/twin")
async def get_azure_twin(machine_id: str):
    """
    Get Azure Digital Twin data
    
    Retrieve the digital twin data directly from Azure Digital Twins
    for comparison with local state.
    """
    try:
        twin_id = f"machine-{machine_id.lower()}"
        twin_data = await dt_service.get_twin(twin_id)
        
        if not twin_data:
            raise HTTPException(status_code=404, detail=f"Azure twin {twin_id} not found")
        
        return {
            "twin_id": twin_id,
            "data": twin_data,
            "connection_status": dt_service.get_connection_status()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Azure twin for machine {machine_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Azure twin data")


async def sync_to_azure_dt(machine_state: MachineState):
    """Background task to sync machine state to Azure Digital Twins"""
    try:
        success = await dt_service.update_machine_from_state(machine_state)
        if success:
            logger.debug(f"Synced machine {machine_state.machine_id} to Azure DT")
        else:
            logger.warning(f"Failed to sync machine {machine_state.machine_id} to Azure DT")
    except Exception as e:
        logger.error(f"Error syncing machine {machine_state.machine_id} to Azure DT: {e}")


async def execute_azure_dt_command(machine_id: str, command: MachineCommand):
    """Background task to execute command on Azure Digital Twins"""
    try:
        twin_id = f"machine-{machine_id.lower()}"
        success = await dt_service.execute_command(twin_id, command)
        if success:
            logger.debug(f"Executed command {command.command_type} on Azure DT twin {twin_id}")
        else:
            logger.warning(f"Failed to execute command {command.command_type} on Azure DT twin {twin_id}")
    except Exception as e:
        logger.error(f"Error executing command on Azure DT twin {twin_id}: {e}")