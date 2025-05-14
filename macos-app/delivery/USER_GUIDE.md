# Incalmo User Guide

## Introduction

Incalmo is an LLM-agnostic high-level attack abstraction layer that helps LLMs execute multistage network attacks. This implementation uses Claude Sonnet 3.7 as the LLM and provides a web-based GUI for interaction.

## Getting Started

### Accessing the Application

The Incalmo tool is currently deployed locally with the following access points:

- **Frontend Interface**: [http://localhost:3456](http://localhost:3456)
- **Backend API**: [http://localhost:8713](http://localhost:8713)
- **API Documentation**: [http://localhost:8713/docs](http://localhost:8713/docs)

### Initial Setup

1. **Open the Application**: Navigate to [http://localhost:3456](http://localhost:3456) in your web browser.

2. **Create a New Session**: From the Control Panel, click "New Session" and enter your attack goal (e.g., "Gain access to the database server and exfiltrate customer data").

3. **Initialize Environment**: Select an environment template or create a custom one to begin your attack simulation.

## Main Features

### Dashboard

The Dashboard provides an overview of your current attack progress, including:

- **Environment Summary**: Networks, hosts, and services discovered
- **Attack Progress**: Compromised hosts and exfiltrated data
- **Session Information**: Current goal and session duration
- **Recent Activities**: Latest tasks executed and their results

### Network Visualization

The Network Visualization tab displays an interactive representation of the network topology:

- **Zoom and Pan**: Use mouse wheel to zoom and drag to pan around the visualization
- **Node Interaction**: Click on nodes to view detailed information
- **Color Coding**: 
  - Blue nodes: Discovered hosts
  - Red nodes: Compromised hosts
  - Green nodes: Services
- **Filtering**: Filter the visualization by network, host type, or compromise status

### Attack Graph Visualization

The Attack Graph Visualization shows potential attack paths based on the current environment state:

- **Path Finding**: Use the panel to find optimal paths between hosts
- **Node Types**:
  - Host nodes: Represent network hosts
  - Vulnerability nodes: Represent exploitable vulnerabilities
  - Action nodes: Represent attack actions
- **Edge Types**:
  - Lateral movement: Paths between compromised hosts
  - Potential target: Possible attack targets
  - Has vulnerability: Connection between host and vulnerability
  - Can exploit: Action that can exploit a vulnerability

### Chat Interface

The Chat Interface allows you to communicate with Claude Sonnet 3.7:

- **Natural Language Input**: Enter high-level commands or questions
- **Task Execution**: The LLM will translate high-level tasks to low-level primitives
- **Contextual Awareness**: The LLM understands the current environment state and attack progress
- **Suggestions**: The LLM can suggest next steps based on the attack graph

### Control Panel

The Control Panel provides configuration options for the attack environment:

- **Session Management**: Create, save, and load attack sessions
- **Environment Configuration**: Customize the network topology and host properties
- **Goal Setting**: Define and modify attack goals
- **Parameter Tuning**: Adjust simulation parameters

### Log Viewer

The Log Viewer provides detailed logs of all actions and events:

- **Filtering**: Filter logs by type (info, success, error, warning)
- **Searching**: Search for specific text within logs
- **Exporting**: Export logs for offline analysis
- **Timestamp Sorting**: Sort logs by timestamp

## Common Tasks

### Scanning a Network

1. In the Chat Interface, type: "Scan the network for vulnerable hosts"
2. The LLM will translate this to a scan_network task
3. The Network Visualization will update with discovered hosts
4. The Log Viewer will show the scan results

### Exploiting a Vulnerability

1. Identify a vulnerable host in the Network Visualization
2. In the Chat Interface, type: "Exploit the vulnerability on [hostname]"
3. The LLM will translate this to an infect_host task with appropriate parameters
4. The Network Visualization will update to show the compromised host
5. The Attack Graph will update with new potential attack paths

### Lateral Movement

1. After compromising a host, identify potential lateral movement targets in the Attack Graph
2. In the Chat Interface, type: "Move laterally from [source_host] to [target_host]"
3. The LLM will translate this to a lateral_move task
4. The Network Visualization will update to show the newly compromised host
5. The Attack Graph will update with new potential attack paths

### Privilege Escalation

1. After compromising a host, in the Chat Interface, type: "Escalate privileges on [hostname]"
2. The LLM will translate this to an escalate_privilege task
3. The host's access level will be updated in the Network Visualization
4. New attack options may become available in the Attack Graph

### Data Exfiltration

1. After compromising a host with valuable data, in the Chat Interface, type: "Exfiltrate data from [hostname]"
2. The LLM will translate this to an exfiltrate_data task
3. The Dashboard will update to show the exfiltrated data
4. The Log Viewer will show details of the exfiltration

## Troubleshooting

### Connection Issues

If you encounter connection issues:

1. Verify that both backend and frontend services are running
2. Check the backend.log and frontend.log files for errors
3. Ensure the ports (3456 for frontend, 8713 for backend) are not blocked by firewall

### LLM Integration Issues

If the LLM is not responding correctly:

1. Verify that the Anthropic API key is correctly set in the configuration
2. Check the backend.log for API-related errors
3. Ensure your internet connection is active for API calls

### Visualization Issues

If visualizations are not rendering correctly:

1. Try refreshing the page
2. Clear your browser cache
3. Ensure your browser is up to date
4. Try a different browser if issues persist

## Stopping the Application

When you're done using Incalmo, you can stop the application by running:

```
./stop_local.sh
```

This will gracefully shut down both the frontend and backend services.

## Security Considerations

Incalmo is designed for educational and research purposes only. Please use responsibly and only in environments where you have explicit permission to conduct security testing.

## Additional Resources

- **API Documentation**: Available at [http://localhost:8713/docs](http://localhost:8713/docs)
- **Source Code**: Located in the `/home/ubuntu/incalmo-project` directory
- **Log Files**: backend.log and frontend.log in the project root directory
