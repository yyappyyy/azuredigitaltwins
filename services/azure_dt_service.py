"""
Azure Digital Twins Service

Handles integration with Azure Digital Twins for twin management and real-time updates
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from azure.digitaltwins.core import DigitalTwinsClient
    from azure.identity import ClientSecretCredential
    from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

from models.dtdl_models import DTDL_MODELS, get_sample_twin_data
from models.data_models import MachineState, SensorReading, MachineCommand
from config.settings import get_settings, is_azure_configured

logger = logging.getLogger(__name__)


class AzureDigitalTwinsService:
    """Service for interacting with Azure Digital Twins"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[DigitalTwinsClient] = None
        self._is_mock_mode = not (AZURE_AVAILABLE and is_azure_configured())
        
        if self._is_mock_mode:
            logger.warning("Azure Digital Twins service running in mock mode")
            self._mock_twins = {}
        else:
            logger.info("Azure Digital Twins service initialized with real Azure connection")
    
    async def initialize(self):
        """Initialize the Azure Digital Twins service"""
        try:
            if not self._is_mock_mode:
                await self._setup_azure_client()
                await self._upload_models()
                await self._create_sample_twins()
            else:
                await self._setup_mock_data()
            
            logger.info("Azure Digital Twins service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Digital Twins service: {e}")
            # Fall back to mock mode on initialization failure
            self._is_mock_mode = True
            await self._setup_mock_data()
    
    async def _setup_azure_client(self):
        """Setup Azure Digital Twins client"""
        if not AZURE_AVAILABLE:
            raise ImportError("Azure Digital Twins SDK not available")
        
        credential = ClientSecretCredential(
            tenant_id=self.settings.AZURE_TENANT_ID,
            client_id=self.settings.AZURE_CLIENT_ID,
            client_secret=self.settings.AZURE_CLIENT_SECRET
        )
        
        self._client = DigitalTwinsClient(
            self.settings.AZURE_DT_URL,
            credential
        )
        
        # Test connection
        try:
            # This will raise an exception if connection fails
            models = list(self._client.list_models())
            logger.info(f"Connected to Azure Digital Twins. Found {len(models)} existing models.")
        except Exception as e:
            logger.error(f"Failed to connect to Azure Digital Twins: {e}")
            raise
    
    async def _upload_models(self):
        """Upload DTDL models to Azure Digital Twins"""
        try:
            for model in DTDL_MODELS:
                model_id = model["@id"]
                try:
                    # Check if model already exists
                    existing_model = self._client.get_model(model_id)
                    logger.info(f"Model {model_id} already exists")
                except ResourceNotFoundError:
                    # Model doesn't exist, create it
                    self._client.create_models([model])
                    logger.info(f"Created model {model_id}")
        except Exception as e:
            logger.error(f"Failed to upload models: {e}")
            raise
    
    async def _create_sample_twins(self):
        """Create sample digital twins for demonstration"""
        try:
            sample_data = get_sample_twin_data()
            
            # Create factory floor twin
            floor_data = sample_data["factory_floor"]
            try:
                self._client.upsert_digital_twin(floor_data["dtId"], floor_data)
                logger.info(f"Created/updated factory floor twin: {floor_data['dtId']}")
            except Exception as e:
                logger.warning(f"Failed to create factory floor twin: {e}")
            
            # Create machine twins
            for machine_data in sample_data["machines"]:
                try:
                    self._client.upsert_digital_twin(machine_data["dtId"], machine_data)
                    logger.info(f"Created/updated machine twin: {machine_data['dtId']}")
                except Exception as e:
                    logger.warning(f"Failed to create machine twin {machine_data['dtId']}: {e}")
            
            # Create relationships
            for relationship in sample_data["relationships"]:
                try:
                    self._client.upsert_relationship(
                        relationship["$sourceId"],
                        relationship["$relationshipId"],
                        relationship
                    )
                    logger.info(f"Created/updated relationship: {relationship['$relationshipId']}")
                except Exception as e:
                    logger.warning(f"Failed to create relationship {relationship['$relationshipId']}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to create sample twins: {e}")
    
    async def _setup_mock_data(self):
        """Setup mock data for testing without Azure connection"""
        sample_data = get_sample_twin_data()
        
        # Store mock twins
        self._mock_twins[sample_data["factory_floor"]["dtId"]] = sample_data["factory_floor"]
        for machine_data in sample_data["machines"]:
            self._mock_twins[machine_data["dtId"]] = machine_data
        
        logger.info("Mock Digital Twins data initialized")
    
    async def update_twin_property(self, twin_id: str, property_name: str, value: Any) -> bool:
        """Update a property of a digital twin"""
        try:
            if self._is_mock_mode:
                # Mock implementation
                if twin_id in self._mock_twins:
                    self._mock_twins[twin_id][property_name] = value
                    logger.info(f"Mock: Updated {twin_id}.{property_name} = {value}")
                    return True
                return False
            
            # Real Azure implementation
            patch = [{"op": "replace", "path": f"/{property_name}", "value": value}]
            self._client.update_digital_twin(twin_id, patch)
            logger.info(f"Updated twin {twin_id} property {property_name} to {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update twin property: {e}")
            return False
    
    async def send_telemetry(self, twin_id: str, telemetry_data: Dict[str, Any]) -> bool:
        """Send telemetry data to a digital twin"""
        try:
            if self._is_mock_mode:
                # Mock implementation - just log the telemetry
                logger.info(f"Mock telemetry sent to {twin_id}: {telemetry_data}")
                return True
            
            # Real Azure implementation
            self._client.publish_telemetry(
                twin_id,
                telemetry_data,
                dt_timestamp=datetime.utcnow()
            )
            logger.debug(f"Sent telemetry to twin {twin_id}: {telemetry_data}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send telemetry: {e}")
            return False
    
    async def get_twin(self, twin_id: str) -> Optional[Dict[str, Any]]:
        """Get a digital twin by ID"""
        try:
            if self._is_mock_mode:
                return self._mock_twins.get(twin_id)
            
            twin = self._client.get_digital_twin(twin_id)
            return twin
            
        except ResourceNotFoundError:
            logger.warning(f"Twin {twin_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get twin {twin_id}: {e}")
            return None
    
    async def list_twins(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all twins or twins of a specific model"""
        try:
            if self._is_mock_mode:
                twins = list(self._mock_twins.values())
                if model_id:
                    twins = [t for t in twins if t.get("$metadata", {}).get("$model") == model_id]
                return twins
            
            query = "SELECT * FROM DIGITALTWINS"
            if model_id:
                query += f" WHERE IS_OF_MODEL('{model_id}')"
            
            twins = []
            async for twin in self._client.query_twins(query):
                twins.append(twin)
            return twins
            
        except Exception as e:
            logger.error(f"Failed to list twins: {e}")
            return []
    
    async def execute_command(self, twin_id: str, command: MachineCommand) -> bool:
        """Execute a command on a digital twin"""
        try:
            if self._is_mock_mode:
                # Mock command execution
                logger.info(f"Mock command executed on {twin_id}: {command.command_type}")
                
                # Update mock twin state based on command
                if twin_id in self._mock_twins:
                    if command.command_type == "startMachine":
                        self._mock_twins[twin_id]["isRunning"] = True
                    elif command.command_type == "stopMachine":
                        self._mock_twins[twin_id]["isRunning"] = False
                
                return True
            
            # Real Azure implementation
            command_result = self._client.invoke_command(
                twin_id,
                command.command_type,
                command.parameters or {}
            )
            
            logger.info(f"Command {command.command_type} executed on twin {twin_id}")
            return command_result.get("status") == "Success"
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return False
    
    async def update_machine_from_state(self, machine_state: MachineState) -> bool:
        """Update digital twin from machine state"""
        try:
            twin_id = f"machine-{machine_state.machine_id.lower()}"
            
            # Update properties
            success = True
            success &= await self.update_twin_property(twin_id, "isRunning", 
                                                     machine_state.status.value == "running")
            success &= await self.update_twin_property(twin_id, "temperatureThreshold", 
                                                     machine_state.temperature_threshold)
            success &= await self.update_twin_property(twin_id, "humidityThreshold", 
                                                     machine_state.humidity_threshold)
            success &= await self.update_twin_property(twin_id, "vibrationThreshold", 
                                                     machine_state.vibration_threshold)
            
            # Send telemetry data
            if any([machine_state.temperature, machine_state.humidity, machine_state.vibration]):
                telemetry = {}
                if machine_state.temperature is not None:
                    telemetry["temperature"] = machine_state.temperature
                if machine_state.humidity is not None:
                    telemetry["humidity"] = machine_state.humidity
                if machine_state.vibration is not None:
                    telemetry["vibration"] = machine_state.vibration
                
                success &= await self.send_telemetry(twin_id, telemetry)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update machine twin from state: {e}")
            return False
    
    async def sync_machine_states(self, machine_states: List[MachineState]) -> Dict[str, bool]:
        """Sync multiple machine states to Azure Digital Twins"""
        results = {}
        
        for machine_state in machine_states:
            try:
                result = await self.update_machine_from_state(machine_state)
                results[machine_state.machine_id] = result
            except Exception as e:
                logger.error(f"Failed to sync machine {machine_state.machine_id}: {e}")
                results[machine_state.machine_id] = False
        
        return results
    
    def is_connected(self) -> bool:
        """Check if service is connected to Azure Digital Twins"""
        return not self._is_mock_mode and self._client is not None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "connected": self.is_connected(),
            "mock_mode": self._is_mock_mode,
            "azure_url": self.settings.AZURE_DT_URL if not self._is_mock_mode else None,
            "client_available": AZURE_AVAILABLE
        }