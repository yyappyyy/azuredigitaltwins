"""
Pydantic data models for API requests/responses and data validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MachineStatus(str, Enum):
    """Machine operation status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MachineType(str, Enum):
    """Machine type enumeration"""
    CNC = "CNC Milling Machine"
    PRESS = "Hydraulic Press"
    CONVEYOR = "Conveyor System"
    ROBOT = "Industrial Robot"
    WELDER = "Welding Station"


class SensorReading(BaseModel):
    """Individual sensor reading model"""
    machine_id: str = Field(..., description="Machine identifier")
    sensor_type: str = Field(..., description="Type of sensor (temperature, humidity, vibration)")
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Reading timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MachineState(BaseModel):
    """Current state of a factory machine"""
    machine_id: str = Field(..., description="Machine identifier")
    machine_name: str = Field(..., description="Human-readable machine name")
    machine_type: MachineType = Field(..., description="Type of machine")
    status: MachineStatus = Field(..., description="Current machine status")
    location: str = Field(..., description="Physical location of machine")
    
    # Current sensor readings
    temperature: Optional[float] = Field(None, description="Current temperature (°C)")
    humidity: Optional[float] = Field(None, description="Current humidity (%)")
    vibration: Optional[float] = Field(None, description="Current vibration (m/s²)")
    
    # Thresholds
    temperature_threshold: float = Field(30.0, description="Temperature alert threshold")
    humidity_threshold: float = Field(70.0, description="Humidity alert threshold")
    vibration_threshold: float = Field(1.5, description="Vibration alert threshold")
    
    # Timestamps
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Alert status
    has_temperature_alert: bool = Field(False, description="Temperature exceeds threshold")
    has_humidity_alert: bool = Field(False, description="Humidity exceeds threshold")
    has_vibration_alert: bool = Field(False, description="Vibration exceeds threshold")
    
    @validator("temperature", "humidity", "vibration", pre=True)
    def round_sensor_values(cls, v):
        """Round sensor values to 2 decimal places"""
        return round(v, 2) if v is not None else v
    
    def update_alerts(self):
        """Update alert status based on current readings and thresholds"""
        self.has_temperature_alert = (
            self.temperature is not None and 
            self.temperature > self.temperature_threshold
        )
        self.has_humidity_alert = (
            self.humidity is not None and 
            self.humidity > self.humidity_threshold
        )
        self.has_vibration_alert = (
            self.vibration is not None and 
            self.vibration > self.vibration_threshold
        )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MachineCommand(BaseModel):
    """Command to be executed on a machine"""
    command_type: str = Field(..., description="Type of command (start, stop, reset_alarms)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Command parameters")


class MachineUpdate(BaseModel):
    """Update request for machine properties"""
    machine_name: Optional[str] = Field(None, description="New machine name")
    status: Optional[MachineStatus] = Field(None, description="New machine status")
    location: Optional[str] = Field(None, description="New machine location")
    temperature_threshold: Optional[float] = Field(None, description="New temperature threshold")
    humidity_threshold: Optional[float] = Field(None, description="New humidity threshold")
    vibration_threshold: Optional[float] = Field(None, description="New vibration threshold")
    
    @validator("temperature_threshold", "humidity_threshold", "vibration_threshold")
    def validate_positive_thresholds(cls, v):
        """Validate that thresholds are positive values"""
        if v is not None and v <= 0:
            raise ValueError("Threshold values must be positive")
        return v


class TwinResponse(BaseModel):
    """Response model for digital twin operations"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class SensorHistory(BaseModel):
    """Historical sensor data response"""
    machine_id: str = Field(..., description="Machine identifier")
    sensor_type: str = Field(..., description="Type of sensor")
    readings: List[SensorReading] = Field(..., description="Historical readings")
    count: int = Field(..., description="Number of readings")
    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardData(BaseModel):
    """Dashboard data aggregation model"""
    machines: List[MachineState] = Field(..., description="List of all machines")
    total_machines: int = Field(..., description="Total number of machines")
    running_machines: int = Field(..., description="Number of running machines")
    machines_with_alerts: int = Field(..., description="Number of machines with alerts")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }