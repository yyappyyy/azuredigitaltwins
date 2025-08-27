"""
Application settings and configuration

Manages environment variables and application configuration using Pydantic Settings
"""

from pydantic import BaseSettings, Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Azure Digital Twins Configuration
    AZURE_DT_URL: str = Field(
        default="",
        description="Azure Digital Twins instance URL"
    )
    AZURE_CLIENT_ID: str = Field(
        default="",
        description="Azure application client ID"
    )
    AZURE_CLIENT_SECRET: str = Field(
        default="",
        description="Azure application client secret"
    )
    AZURE_TENANT_ID: str = Field(
        default="",
        description="Azure tenant ID"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./digital_twins.db",
        description="SQLite database URL"
    )
    
    # API Configuration
    API_HOST: str = Field(
        default="0.0.0.0",
        description="FastAPI server host"
    )
    API_PORT: int = Field(
        default=8000,
        description="FastAPI server port"
    )
    DEBUG: bool = Field(
        default=True,
        description="Debug mode"
    )
    
    # Streamlit Configuration
    STREAMLIT_HOST: str = Field(
        default="0.0.0.0",
        description="Streamlit server host"
    )
    STREAMLIT_PORT: int = Field(
        default=8501,
        description="Streamlit server port"
    )
    
    # Sensor Simulation Configuration
    SENSOR_UPDATE_INTERVAL: int = Field(
        default=5,
        description="Sensor data update interval in seconds"
    )
    TEMPERATURE_MIN: float = Field(
        default=18.0,
        description="Minimum temperature value for simulation"
    )
    TEMPERATURE_MAX: float = Field(
        default=35.0,
        description="Maximum temperature value for simulation"
    )
    HUMIDITY_MIN: float = Field(
        default=30.0,
        description="Minimum humidity value for simulation"
    )
    HUMIDITY_MAX: float = Field(
        default=80.0,
        description="Maximum humidity value for simulation"
    )
    VIBRATION_MIN: float = Field(
        default=0.1,
        description="Minimum vibration value for simulation"
    )
    VIBRATION_MAX: float = Field(
        default=2.0,
        description="Maximum vibration value for simulation"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def is_azure_configured() -> bool:
    """Check if Azure Digital Twins is properly configured"""
    settings = get_settings()
    return bool(
        settings.AZURE_DT_URL and
        settings.AZURE_CLIENT_ID and
        settings.AZURE_CLIENT_SECRET and
        settings.AZURE_TENANT_ID
    )