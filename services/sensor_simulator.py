"""
Sensor Data Simulator

Simulates IoT sensor data (temperature, humidity, vibration) for factory machines
"""

import asyncio
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime
import math

from models.data_models import SensorReading, MachineState, MachineStatus, MachineType
from models.dtdl_models import get_sample_twin_data
from services.sqlite_service import DatabaseService
from services.azure_dt_service import AzureDigitalTwinsService
from config.settings import get_settings

logger = logging.getLogger(__name__)


class SensorSimulator:
    """
    Simulates realistic sensor data for factory machines
    
    Features:
    - Realistic sensor value generation with patterns and noise
    - Machine state-dependent sensor behavior
    - Configurable sensor parameters and thresholds
    - Automatic data persistence and Azure DT sync
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.db_service = DatabaseService()
        self.dt_service = AzureDigitalTwinsService()
        
        self._running = False
        self._machines: Dict[str, MachineState] = {}
        self._sensor_patterns: Dict[str, Dict[str, float]] = {}
        
        # Initialize machines from sample data
        self._initialize_machines()
    
    def _initialize_machines(self):
        """Initialize machine states from sample data"""
        sample_data = get_sample_twin_data()
        
        for machine_data in sample_data["machines"]:
            machine_state = MachineState(
                machine_id=machine_data["machineId"],
                machine_name=machine_data["machineName"],
                machine_type=MachineType(machine_data["machineType"]),
                status=MachineStatus.RUNNING if machine_data["isRunning"] else MachineStatus.STOPPED,
                location=machine_data["location"],
                temperature_threshold=machine_data["temperatureThreshold"],
                humidity_threshold=machine_data["humidityThreshold"],
                vibration_threshold=machine_data["vibrationThreshold"],
                temperature=20.0,  # Initial values
                humidity=50.0,
                vibration=0.3
            )
            
            self._machines[machine_state.machine_id] = machine_state
            
            # Initialize sensor patterns for realistic simulation
            self._sensor_patterns[machine_state.machine_id] = {
                "temp_base": 22.0,
                "temp_amplitude": 3.0,
                "temp_frequency": 0.1,
                "humidity_base": 55.0,
                "humidity_amplitude": 8.0,
                "humidity_frequency": 0.05,
                "vibration_base": 0.4,
                "vibration_amplitude": 0.2,
                "vibration_frequency": 0.3,
                "phase_offset": random.uniform(0, 2 * math.pi)
            }
        
        logger.info(f"Initialized {len(self._machines)} machines for simulation")
    
    async def start(self):
        """Start the sensor simulation"""
        if self._running:
            logger.warning("Sensor simulation is already running")
            return
        
        self._running = True
        logger.info("Starting sensor data simulation...")
        
        # Initialize services
        await self.db_service.initialize()
        await self.dt_service.initialize()
        
        # Start simulation loop
        try:
            await self._simulation_loop()
        except KeyboardInterrupt:
            logger.info("Sensor simulation stopped by user")
        except Exception as e:
            logger.error(f"Sensor simulation error: {e}")
        finally:
            self._running = False
            await self.db_service.disconnect()
    
    def stop(self):
        """Stop the sensor simulation"""
        self._running = False
        logger.info("Stopping sensor simulation...")
    
    async def _simulation_loop(self):
        """Main simulation loop"""
        simulation_time = 0.0
        
        while self._running:
            try:
                # Update sensor readings for all machines
                for machine_id, machine_state in self._machines.items():
                    await self._update_machine_sensors(machine_state, simulation_time)
                    
                    # Save to database
                    await self.db_service.save_machine_state(machine_state)
                    
                    # Sync to Azure Digital Twins
                    await self.dt_service.update_machine_from_state(machine_state)
                    
                    # Save individual sensor readings for history
                    await self._save_sensor_readings(machine_state)
                
                simulation_time += self.settings.SENSOR_UPDATE_INTERVAL
                
                # Log simulation status periodically
                if int(simulation_time) % 60 == 0:  # Every minute
                    running_count = sum(1 for m in self._machines.values() if m.status == MachineStatus.RUNNING)
                    alert_count = sum(1 for m in self._machines.values() 
                                    if m.has_temperature_alert or m.has_humidity_alert or m.has_vibration_alert)
                    logger.info(f"Simulation status: {len(self._machines)} machines, "
                              f"{running_count} running, {alert_count} with alerts")
                
                # Wait for next update
                await asyncio.sleep(self.settings.SENSOR_UPDATE_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _update_machine_sensors(self, machine_state: MachineState, simulation_time: float):
        """Update sensor readings for a specific machine"""
        machine_id = machine_state.machine_id
        patterns = self._sensor_patterns[machine_id]
        
        # Base behavior depends on machine status
        status_multiplier = self._get_status_multiplier(machine_state.status)
        machine_type_factor = self._get_machine_type_factor(machine_state.machine_type)
        
        # Generate realistic temperature reading
        temp_pattern = math.sin(simulation_time * patterns["temp_frequency"] + patterns["phase_offset"])
        temp_noise = random.gauss(0, 0.5)
        machine_state.temperature = round(
            patterns["temp_base"] + 
            patterns["temp_amplitude"] * temp_pattern * status_multiplier * machine_type_factor["temperature"] +
            temp_noise, 2
        )
        
        # Generate realistic humidity reading
        humidity_pattern = math.sin(simulation_time * patterns["humidity_frequency"] + patterns["phase_offset"] + 1)
        humidity_noise = random.gauss(0, 2.0)
        machine_state.humidity = round(
            max(20.0, min(90.0,  # Clamp humidity between realistic values
                patterns["humidity_base"] + 
                patterns["humidity_amplitude"] * humidity_pattern * status_multiplier * machine_type_factor["humidity"] +
                humidity_noise)), 2
        )
        
        # Generate realistic vibration reading
        vibration_pattern = math.sin(simulation_time * patterns["vibration_frequency"] + patterns["phase_offset"] + 2)
        vibration_noise = random.gauss(0, 0.05)
        machine_state.vibration = round(
            max(0.0,  # Vibration can't be negative
                patterns["vibration_base"] * status_multiplier * machine_type_factor["vibration"] + 
                patterns["vibration_amplitude"] * vibration_pattern * status_multiplier +
                vibration_noise), 2
        )
        
        # Add occasional spikes for more realistic behavior
        if random.random() < 0.02:  # 2% chance per update
            spike_type = random.choice(["temperature", "humidity", "vibration"])
            if spike_type == "temperature":
                machine_state.temperature += random.uniform(2.0, 5.0)
            elif spike_type == "humidity":
                machine_state.humidity += random.uniform(5.0, 10.0)
            else:  # vibration
                machine_state.vibration += random.uniform(0.3, 0.8)
        
        # Update alerts and timestamp
        machine_state.update_alerts()
        machine_state.last_updated = datetime.utcnow()
        
        # Simulate machine shutdowns on critical alerts (occasionally)
        if (machine_state.status == MachineStatus.RUNNING and 
            (machine_state.has_temperature_alert or machine_state.has_vibration_alert) and
            random.random() < 0.05):  # 5% chance when there's a critical alert
            
            machine_state.status = MachineStatus.ERROR
            logger.warning(f"Machine {machine_id} shutdown due to critical alert!")
    
    def _get_status_multiplier(self, status: MachineStatus) -> float:
        """Get sensor value multiplier based on machine status"""
        multipliers = {
            MachineStatus.RUNNING: 1.0,
            MachineStatus.STOPPED: 0.3,
            MachineStatus.ERROR: 0.8,  # May still have some heat/activity
            MachineStatus.MAINTENANCE: 0.2
        }
        return multipliers.get(status, 1.0)
    
    def _get_machine_type_factor(self, machine_type: MachineType) -> Dict[str, float]:
        """Get sensor multipliers based on machine type"""
        factors = {
            MachineType.CNC: {
                "temperature": 1.2,  # CNC machines run hotter
                "humidity": 0.9,
                "vibration": 1.1
            },
            MachineType.PRESS: {
                "temperature": 1.0,
                "humidity": 1.0,
                "vibration": 1.5  # Presses have more vibration
            },
            MachineType.CONVEYOR: {
                "temperature": 0.8,  # Conveyors run cooler
                "humidity": 1.0,
                "vibration": 0.7
            },
            MachineType.ROBOT: {
                "temperature": 1.1,
                "humidity": 0.9,
                "vibration": 0.9
            },
            MachineType.WELDER: {
                "temperature": 1.4,  # Welders run very hot
                "humidity": 0.8,
                "vibration": 1.0
            }
        }
        return factors.get(machine_type, {"temperature": 1.0, "humidity": 1.0, "vibration": 1.0})
    
    async def _save_sensor_readings(self, machine_state: MachineState):
        """Save individual sensor readings for historical analysis"""
        timestamp = datetime.utcnow()
        
        if machine_state.temperature is not None:
            temp_reading = SensorReading(
                machine_id=machine_state.machine_id,
                sensor_type="temperature",
                value=machine_state.temperature,
                unit="°C",
                timestamp=timestamp
            )
            await self.db_service.save_sensor_reading(temp_reading)
        
        if machine_state.humidity is not None:
            humidity_reading = SensorReading(
                machine_id=machine_state.machine_id,
                sensor_type="humidity",
                value=machine_state.humidity,
                unit="%",
                timestamp=timestamp
            )
            await self.db_service.save_sensor_reading(humidity_reading)
        
        if machine_state.vibration is not None:
            vibration_reading = SensorReading(
                machine_id=machine_state.machine_id,
                sensor_type="vibration",
                value=machine_state.vibration,
                unit="m/s²",
                timestamp=timestamp
            )
            await self.db_service.save_sensor_reading(vibration_reading)
    
    def get_machine_states(self) -> Dict[str, MachineState]:
        """Get current machine states"""
        return self._machines.copy()
    
    def update_machine_status(self, machine_id: str, status: MachineStatus) -> bool:
        """Update machine status (e.g., from UI control)"""
        if machine_id in self._machines:
            self._machines[machine_id].status = status
            logger.info(f"Updated machine {machine_id} status to {status.value}")
            return True
        return False
    
    def update_machine_thresholds(
        self, 
        machine_id: str, 
        temperature_threshold: Optional[float] = None,
        humidity_threshold: Optional[float] = None,
        vibration_threshold: Optional[float] = None
    ) -> bool:
        """Update machine alert thresholds"""
        if machine_id not in self._machines:
            return False
        
        machine = self._machines[machine_id]
        
        if temperature_threshold is not None:
            machine.temperature_threshold = temperature_threshold
        if humidity_threshold is not None:
            machine.humidity_threshold = humidity_threshold
        if vibration_threshold is not None:
            machine.vibration_threshold = vibration_threshold
        
        machine.update_alerts()  # Recalculate alerts with new thresholds
        logger.info(f"Updated thresholds for machine {machine_id}")
        return True
    
    def is_running(self) -> bool:
        """Check if simulator is running"""
        return self._running