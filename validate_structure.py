"""
Simple validation script to check if the application structure is correct
This can run without external dependencies
"""

import sys
import os
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report status"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - MISSING")
        return False

def check_directory_structure():
    """Validate the project directory structure"""
    print("🔍 Checking project structure...\n")
    
    all_good = True
    
    # Core files
    all_good &= check_file_exists("main.py", "Main entry point")
    all_good &= check_file_exists("requirements.txt", "Dependencies")
    all_good &= check_file_exists(".env.example", "Environment template")
    all_good &= check_file_exists("README.md", "Documentation")
    
    # Configuration
    all_good &= check_file_exists("config/__init__.py", "Config module")
    all_good &= check_file_exists("config/settings.py", "Settings")
    
    # Models
    all_good &= check_file_exists("models/__init__.py", "Models module")
    all_good &= check_file_exists("models/data_models.py", "Data models")
    all_good &= check_file_exists("models/dtdl_models.py", "DTDL models")
    
    # Services
    all_good &= check_file_exists("services/__init__.py", "Services module")
    all_good &= check_file_exists("services/sqlite_service.py", "Database service")
    all_good &= check_file_exists("services/azure_dt_service.py", "Azure DT service")
    all_good &= check_file_exists("services/sensor_simulator.py", "Sensor simulator")
    all_good &= check_file_exists("services/websocket_service.py", "WebSocket service")
    
    # API
    all_good &= check_file_exists("api/__init__.py", "API module")
    all_good &= check_file_exists("api/main.py", "FastAPI app")
    all_good &= check_file_exists("api/routes/__init__.py", "API routes module")
    all_good &= check_file_exists("api/routes/twins.py", "Twins API routes")
    all_good &= check_file_exists("api/routes/sensors.py", "Sensors API routes")
    
    # Frontend
    all_good &= check_file_exists("frontend/__init__.py", "Frontend module")
    all_good &= check_file_exists("frontend/main.py", "Streamlit app")
    all_good &= check_file_exists("frontend/components/__init__.py", "Frontend components")
    all_good &= check_file_exists("frontend/styles/__init__.py", "Frontend styles")
    
    # Tests
    all_good &= check_file_exists("tests/__init__.py", "Tests module")
    all_good &= check_file_exists("tests/test_sqlite_service.py", "Database tests")
    all_good &= check_file_exists("tests/test_azure_dt_service.py", "Azure DT tests")
    all_good &= check_file_exists("tests/test_sensor_simulator.py", "Simulator tests")
    
    # Documentation
    all_good &= check_file_exists("docs/__init__.py", "Docs module")
    all_good &= check_file_exists("docs/setup.md", "Setup guide")
    all_good &= check_file_exists("docs/user_guide.md", "User guide")
    all_good &= check_file_exists("docs/api_reference.md", "API reference")
    
    return all_good

def check_import_structure():
    """Test basic Python import structure"""
    print("\n🐍 Checking Python import structure...\n")
    
    try:
        # Test basic imports without external dependencies
        import json
        import asyncio
        import sqlite3
        import logging
        from datetime import datetime
        print("✅ Standard library imports work")
        
        # Test project structure imports (this will fail if pydantic isn't available)
        try:
            sys.path.insert(0, '.')
            
            # This will fail without pydantic, but that's expected
            from models.dtdl_models import DTDL_MODELS, get_sample_twin_data
            print("✅ DTDL models can be imported")
            
            sample_data = get_sample_twin_data()
            print(f"✅ Sample data includes {len(sample_data['machines'])} machines")
            
        except ImportError as e:
            print(f"⚠️  Model imports require external dependencies: {e}")
            print("   This is expected if packages aren't installed yet")
        
        return True
        
    except Exception as e:
        print(f"❌ Import structure error: {e}")
        return False

def show_next_steps():
    """Show next steps for setup"""
    print("\n📋 Next Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Copy environment file: cp .env.example .env")
    print("3. Initialize application: python main.py setup")
    print("4. Start API server: python main.py api")
    print("5. Start dashboard: python main.py frontend")
    print("6. Run tests: python -m pytest tests/ -v")

def main():
    """Main validation function"""
    print("🏭 Digital Twin Application Structure Validation")
    print("=" * 50)
    
    structure_ok = check_directory_structure()
    imports_ok = check_import_structure()
    
    print("\n" + "=" * 50)
    if structure_ok:
        print("✅ Project structure is complete!")
        if imports_ok:
            print("✅ Basic imports work correctly!")
        else:
            print("⚠️  Some imports need dependencies installed")
    else:
        print("❌ Project structure has missing files!")
    
    show_next_steps()

if __name__ == "__main__":
    main()