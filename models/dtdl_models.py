"""
DTDL (Digital Twins Definition Language) Models

Defines the digital twin models for factory machines and sensors
"""

# Factory Machine DTDL Model
FACTORY_MACHINE_MODEL = {
    "@context": "dtmi:dtdl:context;3",
    "@id": "dtmi:digitaltwins:factory:Machine;1",
    "@type": "Interface",
    "displayName": "Factory Machine",
    "description": "A factory machine with temperature, humidity, and vibration sensors",
    "contents": [
        {
            "@type": "Property",
            "name": "machineId",
            "displayName": "Machine ID",
            "description": "Unique identifier for the machine",
            "schema": "string"
        },
        {
            "@type": "Property",
            "name": "machineName",
            "displayName": "Machine Name",
            "description": "Human-readable name for the machine",
            "schema": "string"
        },
        {
            "@type": "Property",
            "name": "machineType",
            "displayName": "Machine Type",
            "description": "Type of factory machine (e.g., CNC, Press, Conveyor)",
            "schema": "string"
        },
        {
            "@type": "Property",
            "name": "isRunning",
            "displayName": "Is Running",
            "description": "Whether the machine is currently running",
            "schema": "boolean"
        },
        {
            "@type": "Property",
            "name": "location",
            "displayName": "Location",
            "description": "Physical location of the machine",
            "schema": "string"
        },
        {
            "@type": "Telemetry",
            "name": "temperature",
            "displayName": "Temperature",
            "description": "Current temperature reading from machine sensor",
            "schema": "double",
            "unit": "degreeCelsius"
        },
        {
            "@type": "Telemetry",
            "name": "humidity",
            "displayName": "Humidity",
            "description": "Current humidity reading from machine sensor",
            "schema": "double",
            "unit": "percent"
        },
        {
            "@type": "Telemetry",
            "name": "vibration",
            "displayName": "Vibration",
            "description": "Current vibration level reading from machine sensor",
            "schema": "double",
            "unit": "metre per second squared"
        },
        {
            "@type": "Property",
            "name": "temperatureThreshold",
            "displayName": "Temperature Threshold",
            "description": "Maximum safe temperature for the machine",
            "schema": "double",
            "writable": True
        },
        {
            "@type": "Property",
            "name": "humidityThreshold",
            "displayName": "Humidity Threshold",
            "description": "Maximum safe humidity for the machine",
            "schema": "double",
            "writable": True
        },
        {
            "@type": "Property",
            "name": "vibrationThreshold",
            "displayName": "Vibration Threshold",
            "description": "Maximum safe vibration level for the machine",
            "schema": "double",
            "writable": True
        },
        {
            "@type": "Command",
            "name": "startMachine",
            "displayName": "Start Machine",
            "description": "Start the machine operation"
        },
        {
            "@type": "Command",
            "name": "stopMachine",
            "displayName": "Stop Machine",
            "description": "Stop the machine operation"
        },
        {
            "@type": "Command",
            "name": "resetAlarms",
            "displayName": "Reset Alarms",
            "description": "Reset all machine alarms"
        }
    ]
}

# Factory Floor DTDL Model
FACTORY_FLOOR_MODEL = {
    "@context": "dtmi:dtdl:context;3",
    "@id": "dtmi:digitaltwins:factory:Floor;1",
    "@type": "Interface",
    "displayName": "Factory Floor",
    "description": "A factory floor containing multiple machines",
    "contents": [
        {
            "@type": "Property",
            "name": "floorId",
            "displayName": "Floor ID",
            "description": "Unique identifier for the factory floor",
            "schema": "string"
        },
        {
            "@type": "Property",
            "name": "floorName",
            "displayName": "Floor Name",
            "description": "Human-readable name for the factory floor",
            "schema": "string"
        },
        {
            "@type": "Property",
            "name": "buildingName",
            "displayName": "Building Name",
            "description": "Name of the building containing this floor",
            "schema": "string"
        },
        {
            "@type": "Relationship",
            "name": "contains",
            "displayName": "Contains",
            "description": "Machines contained on this factory floor",
            "target": "dtmi:digitaltwins:factory:Machine;1"
        }
    ]
}

# List of all models to be uploaded
DTDL_MODELS = [
    FACTORY_MACHINE_MODEL,
    FACTORY_FLOOR_MODEL
]


def get_sample_twin_data():
    """Get sample twin data for testing and demonstration"""
    return {
        "factory_floor": {
            "dtId": "factory-floor-01",
            "floorId": "F01",
            "floorName": "Production Floor 1",
            "buildingName": "Manufacturing Plant A",
            "$metadata": {
                "$model": "dtmi:digitaltwins:factory:Floor;1"
            }
        },
        "machines": [
            {
                "dtId": "machine-cnc-01",
                "machineId": "CNC-001",
                "machineName": "CNC Machine 1",
                "machineType": "CNC Milling Machine",
                "isRunning": True,
                "location": "Station A1",
                "temperatureThreshold": 30.0,
                "humidityThreshold": 70.0,
                "vibrationThreshold": 1.5,
                "$metadata": {
                    "$model": "dtmi:digitaltwins:factory:Machine;1"
                }
            },
            {
                "dtId": "machine-press-01",
                "machineId": "PRESS-001",
                "machineName": "Hydraulic Press 1",
                "machineType": "Hydraulic Press",
                "isRunning": False,
                "location": "Station B2",
                "temperatureThreshold": 25.0,
                "humidityThreshold": 60.0,
                "vibrationThreshold": 1.0,
                "$metadata": {
                    "$model": "dtmi:digitaltwins:factory:Machine;1"
                }
            },
            {
                "dtId": "machine-conveyor-01",
                "machineId": "CONV-001",
                "machineName": "Conveyor Belt 1",
                "machineType": "Conveyor System",
                "isRunning": True,
                "location": "Main Line",
                "temperatureThreshold": 22.0,
                "humidityThreshold": 65.0,
                "vibrationThreshold": 0.8,
                "$metadata": {
                    "$model": "dtmi:digitaltwins:factory:Machine;1"
                }
            }
        ],
        "relationships": [
            {
                "$relationshipId": "floor-contains-cnc01",
                "$sourceId": "factory-floor-01",
                "$relationshipName": "contains",
                "$targetId": "machine-cnc-01"
            },
            {
                "$relationshipId": "floor-contains-press01",
                "$sourceId": "factory-floor-01",
                "$relationshipName": "contains",
                "$targetId": "machine-press-01"
            },
            {
                "$relationshipId": "floor-contains-conveyor01",
                "$sourceId": "factory-floor-01",
                "$relationshipName": "contains",
                "$targetId": "machine-conveyor-01"
            }
        ]
    }