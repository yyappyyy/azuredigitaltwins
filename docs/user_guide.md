# Digital Twin Dashboard User Guide

## Overview

The Digital Twin Dashboard provides an intuitive interface for monitoring and controlling factory machines in real-time. It displays sensor data, alerts, and allows direct control of machine operations.

## Dashboard Layout

### Header Section
- **Title**: Digital Twin Dashboard with factory icon
- **Subtitle**: Real-time Factory Machine Monitoring & Control
- **Status Indicators**: Connection status and last update time

### Sidebar Controls
- **Auto Refresh Toggle**: Enable/disable automatic data refresh
- **Refresh Interval**: Set update frequency (1-30 seconds)
- **Manual Refresh**: Force immediate data update
- **Machine Selection**: Filter view to specific machine
- **System Status**: Overview of connected services

### Main Dashboard

#### System Overview Metrics
Four key performance indicators:
- **Total Machines**: Number of machines in the system
- **Running**: Number of currently active machines
- **Stopped**: Number of inactive machines  
- **Active Alerts**: Number of machines with sensor alerts

#### Machine Status Grid
Each machine is displayed in a card showing:
- **Machine Name** and location
- **Status Badge**: Running (green), Stopped (red), Error (yellow)
- **Sensor Readings**: Temperature, humidity, vibration with current values
- **Alert Indicators**: Visual alerts when thresholds are exceeded
- **Control Buttons**: Start, Stop, Reset alarms

#### Data Visualization
Interactive charts and graphs (when available):
- **Real-time Readings**: Current sensor values across all machines
- **Historical Trends**: Sensor data over time
- **Alert Analysis**: Pattern analysis of alerts and anomalies

#### Machine Controls Panel
Advanced control interface:
- **Machine Selection**: Choose specific machine to control
- **Threshold Controls**: Adjust alert thresholds with sliders
- **Command Buttons**: Execute machine operations
- **Status Feedback**: Confirmation of executed commands

## Using the Dashboard

### Monitoring Machines

1. **Overview Monitoring**
   - Check the system overview metrics for quick status
   - Look for red "Active Alerts" metric indicating problems
   - Observe the running vs stopped machine ratio

2. **Individual Machine Status**
   - Each machine card shows real-time sensor readings
   - Alert indicators flash when thresholds are exceeded
   - Status badges show current operational state

3. **Alert Management**
   - Red values indicate sensors above safe thresholds
   - Blinking alert badges require attention
   - Use "Reset Alarms" to acknowledge alerts after addressing issues

### Controlling Machines

#### Basic Controls (Machine Cards)
- **▶️ Start**: Start a stopped machine
- **⏸️ Stop**: Stop a running machine  
- **🔄 Reset**: Reset all alarms for the machine

#### Advanced Controls (Control Panel)
1. **Select Machine**: Choose from dropdown list
2. **Adjust Thresholds**: Use sliders to set alert limits
   - Temperature: 15°C - 50°C
   - Humidity: 30% - 90%
   - Vibration: 0.1 - 3.0 m/s²
3. **Execute Commands**: Use command buttons for machine operations
4. **Save Changes**: Click "Update Thresholds" to apply changes

### Real-time Features

#### Auto-Refresh
- **Enable**: Check "🔄 Auto Refresh" in sidebar
- **Interval**: Set refresh rate (recommended: 5-10 seconds)
- **Manual**: Use "🔄 Refresh Now" for immediate updates

#### WebSocket Updates
- Real-time data streaming when available
- Instant notification of machine status changes
- Live sensor reading updates without page refresh

### Data Analysis

#### Current Readings
- View live sensor values for all machines
- Compare readings against thresholds
- Identify trends and patterns

#### Historical Data (Future Feature)
- View sensor trends over time
- Analyze patterns and anomalies
- Export data for further analysis

## Alert System

### Alert Types
- **Temperature Alert**: When machine temperature exceeds threshold
- **Humidity Alert**: When humidity levels are too high
- **Vibration Alert**: When vibration exceeds safe limits

### Alert States
- **🟢 Normal**: All sensors within safe ranges
- **⚠️ Warning**: One or more sensors near thresholds
- **🚨 Critical**: Sensors significantly above thresholds

### Alert Actions
1. **Acknowledge**: Use "Reset Alarms" to clear alert state
2. **Investigate**: Check machine physically for issues
3. **Adjust**: Modify thresholds if alert limits are incorrect
4. **Shutdown**: Stop machine if issue is critical

## Machine Status Meanings

### Status Types
- **RUNNING**: Machine is actively operating
- **STOPPED**: Machine is intentionally stopped
- **ERROR**: Machine has encountered an error
- **MAINTENANCE**: Machine is in maintenance mode

### Status Indicators
- **Green Badge**: Normal operation
- **Red Badge**: Stopped or error state
- **Yellow Badge**: Warning or maintenance

## Tips and Best Practices

### Monitoring
- Set appropriate refresh intervals (5-10 seconds for active monitoring)
- Use machine selection to focus on specific equipment
- Monitor the system overview for quick health checks
- Pay attention to alert patterns that might indicate systemic issues

### Control Operations
- Always check machine status before sending commands
- Reset alarms after addressing the underlying issue
- Test threshold changes gradually
- Document any manual interventions

### Performance
- Disable auto-refresh when not actively monitoring to reduce server load
- Use manual refresh when making configuration changes
- Consider browser performance with multiple machines displayed

### Troubleshooting
- Check API connection status in footer
- Verify last update timestamp is recent
- Use manual refresh if auto-refresh seems stuck
- Check browser console for WebSocket connection issues

## Keyboard Shortcuts

- **F5**: Manual refresh (browser default)
- **Ctrl+R**: Reload page (browser default)
- **Esc**: Close any open dialogs

## Mobile Support

The dashboard is designed to be responsive:
- **Tablet**: Full functionality with touch controls
- **Phone**: Optimized layout with collapsible sections
- **Touch**: All controls work with touch gestures

## Accessibility

- **Screen Readers**: All controls have descriptive labels
- **High Contrast**: Alert colors meet accessibility standards  
- **Keyboard Navigation**: Tab through all interactive elements
- **Font Scaling**: Responsive to browser zoom settings

## Advanced Features

### Real-time Synchronization
- Changes made in dashboard immediately sync to Azure Digital Twins
- Multiple users can monitor the same machines simultaneously
- Sensor updates from physical devices appear in real-time

### Data Export (Future)
- Export sensor data to CSV for analysis
- Generate reports on machine performance
- Historical trend analysis

### Custom Dashboards (Future)
- Create custom layouts for specific monitoring needs
- Save preferred machine groupings
- Set custom alert thresholds per user role

## Troubleshooting Common Issues

### Dashboard Not Loading
- Check that FastAPI backend is running
- Verify network connectivity
- Check browser console for errors

### No Data Showing
- Confirm sensor simulator is running
- Check database connection
- Verify API endpoints are responding

### Commands Not Working
- Check machine status before sending commands
- Verify API connection in footer
- Look for error messages in the interface

### Slow Performance
- Reduce auto-refresh frequency
- Limit number of machines displayed
- Check network connection quality

## Getting Help

- **Status Information**: Check footer for connection status
- **Error Messages**: Look for red error notifications
- **Browser Console**: Press F12 for detailed error information
- **API Documentation**: Visit /docs endpoint for API details