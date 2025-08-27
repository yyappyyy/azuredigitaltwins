"""
Streamlit Digital Twin Dashboard

Interactive dashboard for monitoring and controlling factory machines
"""

import sys
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import statements with error handling for missing packages
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    print("Streamlit not available. Please install with: pip install streamlit")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import websockets
    import requests
    NETWORKING_AVAILABLE = True
except ImportError:
    NETWORKING_AVAILABLE = False

from config.settings import get_settings
from models.data_models import MachineState, MachineStatus, MachineType

# Configure page settings
if STREAMLIT_AVAILABLE:
    st.set_page_config(
        page_title="🏭 Digital Twin Dashboard",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded"
    )


class DigitalTwinDashboard:
    """Main dashboard application class"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_base_url = f"http://{self.settings.API_HOST}:{self.settings.API_PORT}/api"
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize Streamlit session state"""
        if not STREAMLIT_AVAILABLE:
            return
            
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        if 'machines' not in st.session_state:
            st.session_state.machines = []
        if 'selected_machine' not in st.session_state:
            st.session_state.selected_machine = None
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 5
        if 'alert_count' not in st.session_state:
            st.session_state.alert_count = 0
    
    def run(self):
        """Main dashboard application"""
        if not STREAMLIT_AVAILABLE:
            print("❌ Streamlit not available. Please install required packages.")
            return
        
        # Custom CSS for modern design
        self._inject_custom_css()
        
        # Main dashboard layout
        self._render_header()
        self._render_sidebar()
        self._render_main_content()
        self._render_footer()
        
        # Auto-refresh functionality
        if st.session_state.auto_refresh:
            time.sleep(st.session_state.refresh_interval)
            st.rerun()
    
    def _inject_custom_css(self):
        """Inject custom CSS for modern dashboard design"""
        st.markdown("""
        <style>
        /* Main dashboard styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            color: white;
            text-align: center;
            margin: 0.5rem 0;
        }
        
        .metric-card h3 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: bold;
        }
        
        .metric-card p {
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        /* Status badges */
        .status-running {
            background-color: #28a745;
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-stopped {
            background-color: #dc3545;
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-error {
            background-color: #ffc107;
            color: black;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        /* Alert indicators */
        .alert-high {
            background-color: #dc3545;
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 15px;
            font-size: 0.7rem;
            animation: blink 1s infinite;
        }
        
        .alert-normal {
            background-color: #28a745;
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 15px;
            font-size: 0.7rem;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.5; }
        }
        
        /* Machine cards */
        .machine-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .machine-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        /* Charts container */
        .chart-container {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _render_header(self):
        """Render dashboard header"""
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <h1 style="color: #2c3e50; margin: 0;">🏭 Digital Twin Dashboard</h1>
            <p style="color: #7f8c8d; margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                Real-time Factory Machine Monitoring & Control
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_sidebar(self):
        """Render dashboard sidebar with controls"""
        with st.sidebar:
            st.markdown("### ⚙️ Dashboard Controls")
            
            # Auto-refresh settings
            st.session_state.auto_refresh = st.checkbox(
                "🔄 Auto Refresh", 
                value=st.session_state.auto_refresh,
                help="Automatically refresh data every few seconds"
            )
            
            if st.session_state.auto_refresh:
                st.session_state.refresh_interval = st.slider(
                    "Refresh Interval (seconds)",
                    min_value=1,
                    max_value=30,
                    value=st.session_state.refresh_interval,
                    step=1
                )
            
            # Manual refresh button
            if st.button("🔄 Refresh Now", use_container_width=True):
                self._load_data()
                st.rerun()
            
            st.divider()
            
            # Machine selection
            st.markdown("### 🤖 Machine Selection")
            
            if st.session_state.machines:
                machine_names = ["All Machines"] + [m.get("machine_name", m.get("machine_id", "Unknown")) 
                                                   for m in st.session_state.machines]
                selected = st.selectbox(
                    "Select Machine",
                    options=machine_names,
                    index=0
                )
                
                if selected != "All Machines":
                    st.session_state.selected_machine = selected
                else:
                    st.session_state.selected_machine = None
            
            st.divider()
            
            # System status
            st.markdown("### 📊 System Status")
            
            # Load system data
            status_data = self._get_system_status()
            
            if status_data:
                st.metric("🔗 API Status", "Connected" if status_data.get("connected", False) else "Disconnected")
                st.metric("📦 Total Machines", status_data.get("total_machines", 0))
                st.metric("⚡ Running", status_data.get("running_machines", 0))
                st.metric("⚠️ Alerts", status_data.get("alert_count", 0))
            else:
                st.error("❌ Cannot connect to API")
    
    def _render_main_content(self):
        """Render main dashboard content"""
        # Load machine data
        self._load_data()
        
        if not st.session_state.machines:
            st.error("""
            ❌ **No machine data available**
            
            This could be because:
            - The FastAPI backend is not running
            - The database is not initialized
            - Network connectivity issues
            
            **To get started:**
            1. Run `python main.py setup` to initialize the application
            2. Run `python main.py api` to start the backend API
            3. Run `python main.py simulate` to start sensor simulation (optional)
            """)
            return
        
        # Overview metrics
        self._render_overview_metrics()
        
        # Machine grid
        self._render_machine_grid()
        
        # Charts and analytics
        if PLOTLY_AVAILABLE and PANDAS_AVAILABLE:
            self._render_charts()
        else:
            st.warning("📊 Charts not available. Install plotly and pandas for data visualization.")
        
        # Machine controls
        self._render_machine_controls()
    
    def _render_overview_metrics(self):
        """Render overview metrics cards"""
        machines = st.session_state.machines
        
        total_machines = len(machines)
        running_machines = sum(1 for m in machines if m.get("status") == "running")
        stopped_machines = total_machines - running_machines
        alert_count = sum(1 for m in machines 
                         if m.get("has_temperature_alert") or 
                            m.get("has_humidity_alert") or 
                            m.get("has_vibration_alert"))
        
        st.markdown("### 📈 System Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_machines}</h3>
                <p>Total Machines</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                <h3>{running_machines}</h3>
                <p>Running</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #dc3545 0%, #e74c3c 100%);">
                <h3>{stopped_machines}</h3>
                <p>Stopped</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            alert_color = "linear-gradient(135deg, #ffc107 0%, #fd7e14 100%)" if alert_count > 0 else "linear-gradient(135deg, #28a745 0%, #20c997 100%)"
            st.markdown(f"""
            <div class="metric-card" style="background: {alert_color};">
                <h3>{alert_count}</h3>
                <p>Active Alerts</p>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_machine_grid(self):
        """Render machine status grid"""
        st.markdown("### 🏭 Machine Status")
        
        machines = st.session_state.machines
        
        # Filter machines if specific machine selected
        if st.session_state.selected_machine:
            machines = [m for m in machines if m.get("machine_name") == st.session_state.selected_machine]
        
        # Create machine cards in grid layout
        cols_per_row = 2
        for i in range(0, len(machines), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(machines):
                    machine = machines[i + j]
                    with col:
                        self._render_machine_card(machine)
    
    def _render_machine_card(self, machine: Dict):
        """Render individual machine status card"""
        machine_id = machine.get("machine_id", "Unknown")
        machine_name = machine.get("machine_name", machine_id)
        status = machine.get("status", "unknown")
        location = machine.get("location", "Unknown")
        
        # Status styling
        status_class = f"status-{status.lower().replace(' ', '-')}"
        
        # Alert indicators
        temp_alert = machine.get("has_temperature_alert", False)
        humidity_alert = machine.get("has_humidity_alert", False)
        vibration_alert = machine.get("has_vibration_alert", False)
        
        # Sensor readings
        temperature = machine.get("temperature", 0) or 0
        humidity = machine.get("humidity", 0) or 0
        vibration = machine.get("vibration", 0) or 0
        
        temp_threshold = machine.get("temperature_threshold", 30)
        humidity_threshold = machine.get("humidity_threshold", 70)
        vibration_threshold = machine.get("vibration_threshold", 1.5)
        
        st.markdown(f"""
        <div class="machine-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <h4 style="margin: 0; color: #2c3e50;">{machine_name}</h4>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">{location}</p>
                </div>
                <span class="{status_class}">{status.upper()}</span>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: {'#dc3545' if temp_alert else '#28a745'};">
                        {temperature:.1f}°C
                    </div>
                    <div style="font-size: 0.8rem; color: #6c757d;">
                        Temperature
                        <span class="{'alert-high' if temp_alert else 'alert-normal'}">
                            {'⚠️' if temp_alert else '✓'}
                        </span>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: {'#dc3545' if humidity_alert else '#28a745'};">
                        {humidity:.1f}%
                    </div>
                    <div style="font-size: 0.8rem; color: #6c757d;">
                        Humidity
                        <span class="{'alert-high' if humidity_alert else 'alert-normal'}">
                            {'⚠️' if humidity_alert else '✓'}
                        </span>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: {'#dc3545' if vibration_alert else '#28a745'};">
                        {vibration:.2f}
                    </div>
                    <div style="font-size: 0.8rem; color: #6c757d;">
                        Vibration
                        <span class="{'alert-high' if vibration_alert else 'alert-normal'}">
                            {'⚠️' if vibration_alert else '✓'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Machine control buttons (simplified for now)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"▶️ Start", key=f"start_{machine_id}", use_container_width=True):
                self._execute_machine_command(machine_id, "startMachine")
        
        with col2:
            if st.button(f"⏸️ Stop", key=f"stop_{machine_id}", use_container_width=True):
                self._execute_machine_command(machine_id, "stopMachine")
        
        with col3:
            if st.button(f"🔄 Reset", key=f"reset_{machine_id}", use_container_width=True):
                self._execute_machine_command(machine_id, "resetAlarms")
    
    def _render_charts(self):
        """Render data visualization charts"""
        if not (PLOTLY_AVAILABLE and PANDAS_AVAILABLE):
            return
        
        st.markdown("### 📊 Data Visualization")
        
        # Chart type selection
        chart_type = st.radio(
            "Select Chart Type",
            ["Real-time Readings", "Historical Trends", "Alert Analysis"],
            horizontal=True
        )
        
        if chart_type == "Real-time Readings":
            self._render_realtime_charts()
        elif chart_type == "Historical Trends":
            self._render_historical_charts()
        else:
            self._render_alert_charts()
    
    def _render_realtime_charts(self):
        """Render real-time sensor reading charts"""
        st.info("📊 Real-time charts will be implemented with full Plotly integration")
        
        # Placeholder for real-time charts
        machines = st.session_state.machines
        if machines:
            # Simple bar chart of current readings
            data = {
                'Machine': [m.get('machine_name', m.get('machine_id')) for m in machines],
                'Temperature': [m.get('temperature', 0) or 0 for m in machines],
                'Humidity': [m.get('humidity', 0) or 0 for m in machines],
                'Vibration': [m.get('vibration', 0) or 0 for m in machines]
            }
            
            # Display as simple table for now
            st.write("**Current Sensor Readings**")
            st.table(data)
    
    def _render_historical_charts(self):
        """Render historical trend charts"""
        st.info("📈 Historical trend charts will show sensor data over time")
    
    def _render_alert_charts(self):
        """Render alert analysis charts"""
        st.info("⚠️ Alert analysis charts will show alert patterns and statistics")
    
    def _render_machine_controls(self):
        """Render machine control panel"""
        st.markdown("### 🎛️ Machine Controls")
        
        machines = st.session_state.machines
        if not machines:
            return
        
        # Machine selection for control
        machine_options = {m.get("machine_name", m.get("machine_id")): m.get("machine_id") 
                          for m in machines}
        
        selected_machine_name = st.selectbox(
            "Select machine to control:",
            options=list(machine_options.keys()),
            key="control_machine_select"
        )
        
        if selected_machine_name:
            selected_machine_id = machine_options[selected_machine_name]
            selected_machine = next((m for m in machines if m.get("machine_id") == selected_machine_id), None)
            
            if selected_machine:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🎚️ Threshold Controls")
                    
                    temp_threshold = st.slider(
                        "Temperature Threshold (°C)",
                        min_value=15.0,
                        max_value=50.0,
                        value=float(selected_machine.get("temperature_threshold", 30.0)),
                        step=0.5,
                        key=f"temp_threshold_{selected_machine_id}"
                    )
                    
                    humidity_threshold = st.slider(
                        "Humidity Threshold (%)",
                        min_value=30.0,
                        max_value=90.0,
                        value=float(selected_machine.get("humidity_threshold", 70.0)),
                        step=1.0,
                        key=f"humidity_threshold_{selected_machine_id}"
                    )
                    
                    vibration_threshold = st.slider(
                        "Vibration Threshold (m/s²)",
                        min_value=0.1,
                        max_value=3.0,
                        value=float(selected_machine.get("vibration_threshold", 1.5)),
                        step=0.1,
                        key=f"vibration_threshold_{selected_machine_id}"
                    )
                    
                    if st.button("💾 Update Thresholds", key=f"update_thresholds_{selected_machine_id}"):
                        self._update_machine_thresholds(
                            selected_machine_id,
                            temp_threshold,
                            humidity_threshold,
                            vibration_threshold
                        )
                
                with col2:
                    st.markdown("#### 🎮 Machine Commands")
                    
                    # Command buttons in a grid
                    cmd_col1, cmd_col2 = st.columns(2)
                    
                    with cmd_col1:
                        if st.button("▶️ Start Machine", key=f"cmd_start_{selected_machine_id}", use_container_width=True):
                            self._execute_machine_command(selected_machine_id, "startMachine")
                        
                        if st.button("🔄 Reset Alarms", key=f"cmd_reset_{selected_machine_id}", use_container_width=True):
                            self._execute_machine_command(selected_machine_id, "resetAlarms")
                    
                    with cmd_col2:
                        if st.button("⏸️ Stop Machine", key=f"cmd_stop_{selected_machine_id}", use_container_width=True):
                            self._execute_machine_command(selected_machine_id, "stopMachine")
                        
                        if st.button("⚙️ Maintenance Mode", key=f"cmd_maint_{selected_machine_id}", use_container_width=True):
                            # This would update status to maintenance
                            st.info("Maintenance mode feature coming soon!")
    
    def _render_footer(self):
        """Render dashboard footer"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Last Updated:** " + st.session_state.last_update.strftime("%Y-%m-%d %H:%M:%S"))
        
        with col2:
            st.markdown("**API Status:** " + ("🟢 Connected" if self._check_api_connection() else "🔴 Disconnected"))
        
        with col3:
            st.markdown("**Auto Refresh:** " + ("🟢 Enabled" if st.session_state.auto_refresh else "🔴 Disabled"))
    
    def _load_data(self):
        """Load machine data from API"""
        try:
            # Simulate API call for now (will be replaced with actual API call)
            # In a real implementation, this would use requests or httpx
            st.session_state.machines = self._get_mock_machine_data()
            st.session_state.last_update = datetime.now()
            
        except Exception as e:
            st.error(f"Failed to load data: {e}")
    
    def _get_mock_machine_data(self):
        """Generate mock machine data for demonstration"""
        import random
        
        mock_machines = [
            {
                "machine_id": "CNC-001",
                "machine_name": "CNC Machine 1",
                "machine_type": "CNC Milling Machine",
                "status": "running",
                "location": "Station A1",
                "temperature": round(random.uniform(20, 35), 1),
                "humidity": round(random.uniform(40, 75), 1),
                "vibration": round(random.uniform(0.2, 1.8), 2),
                "temperature_threshold": 30.0,
                "humidity_threshold": 70.0,
                "vibration_threshold": 1.5,
                "has_temperature_alert": False,
                "has_humidity_alert": False,
                "has_vibration_alert": False,
                "last_updated": datetime.now().isoformat()
            },
            {
                "machine_id": "PRESS-001",
                "machine_name": "Hydraulic Press 1",
                "machine_type": "Hydraulic Press",
                "status": "stopped",
                "location": "Station B2",
                "temperature": round(random.uniform(18, 28), 1),
                "humidity": round(random.uniform(35, 65), 1),
                "vibration": round(random.uniform(0.1, 0.8), 2),
                "temperature_threshold": 25.0,
                "humidity_threshold": 60.0,
                "vibration_threshold": 1.0,
                "has_temperature_alert": False,
                "has_humidity_alert": False,
                "has_vibration_alert": False,
                "last_updated": datetime.now().isoformat()
            },
            {
                "machine_id": "CONV-001",
                "machine_name": "Conveyor Belt 1",
                "machine_type": "Conveyor System",
                "status": "running",
                "location": "Main Line",
                "temperature": round(random.uniform(19, 25), 1),
                "humidity": round(random.uniform(45, 70), 1),
                "vibration": round(random.uniform(0.2, 0.9), 2),
                "temperature_threshold": 22.0,
                "humidity_threshold": 65.0,
                "vibration_threshold": 0.8,
                "has_temperature_alert": random.random() < 0.2,  # 20% chance of alert
                "has_humidity_alert": False,
                "has_vibration_alert": False,
                "last_updated": datetime.now().isoformat()
            }
        ]
        
        # Randomly generate some alerts
        for machine in mock_machines:
            if machine["status"] == "running":
                # Chance of exceeding thresholds
                if machine["temperature"] > machine["temperature_threshold"]:
                    machine["has_temperature_alert"] = True
                if machine["humidity"] > machine["humidity_threshold"]:
                    machine["has_humidity_alert"] = True
                if machine["vibration"] > machine["vibration_threshold"]:
                    machine["has_vibration_alert"] = True
        
        return mock_machines
    
    def _get_system_status(self):
        """Get system status data"""
        # Mock system status
        machines = st.session_state.machines
        return {
            "connected": True,
            "total_machines": len(machines),
            "running_machines": sum(1 for m in machines if m.get("status") == "running"),
            "alert_count": sum(1 for m in machines 
                              if m.get("has_temperature_alert") or 
                                 m.get("has_humidity_alert") or 
                                 m.get("has_vibration_alert"))
        }
    
    def _check_api_connection(self):
        """Check if API is accessible"""
        # For now, return True (mock)
        return True
    
    def _execute_machine_command(self, machine_id: str, command: str):
        """Execute a command on a machine"""
        try:
            # Mock command execution
            st.success(f"✅ Command '{command}' executed on machine {machine_id}")
            
            # Update local state to reflect command
            for machine in st.session_state.machines:
                if machine.get("machine_id") == machine_id:
                    if command == "startMachine":
                        machine["status"] = "running"
                    elif command == "stopMachine":
                        machine["status"] = "stopped"
                    elif command == "resetAlarms":
                        machine["has_temperature_alert"] = False
                        machine["has_humidity_alert"] = False
                        machine["has_vibration_alert"] = False
                    break
            
            # Auto-refresh to show changes
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to execute command: {e}")
    
    def _update_machine_thresholds(self, machine_id: str, temp_threshold: float, 
                                  humidity_threshold: float, vibration_threshold: float):
        """Update machine alert thresholds"""
        try:
            # Mock threshold update
            for machine in st.session_state.machines:
                if machine.get("machine_id") == machine_id:
                    machine["temperature_threshold"] = temp_threshold
                    machine["humidity_threshold"] = humidity_threshold
                    machine["vibration_threshold"] = vibration_threshold
                    
                    # Recalculate alerts
                    machine["has_temperature_alert"] = (machine.get("temperature", 0) > temp_threshold)
                    machine["has_humidity_alert"] = (machine.get("humidity", 0) > humidity_threshold)
                    machine["has_vibration_alert"] = (machine.get("vibration", 0) > vibration_threshold)
                    break
            
            st.success(f"✅ Thresholds updated for machine {machine_id}")
            
            # Auto-refresh to show changes
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to update thresholds: {e}")


def main():
    """Main entry point for Streamlit app"""
    if not STREAMLIT_AVAILABLE:
        print("""
        ❌ Streamlit Dashboard Not Available
        
        Required packages are missing. Please install them:
        
        pip install streamlit plotly pandas requests websockets
        
        Then run: streamlit run frontend/main.py
        """)
        return
    
    # Initialize and run dashboard
    dashboard = DigitalTwinDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()