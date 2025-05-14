# Incalmo - Installation and Usage Guide

## Overview

Incalmo is an LLM-agnostic high-level attack abstraction layer that helps LLMs execute multistage network attacks. This implementation uses Claude Sonnet 3.7 as the LLM and provides a web-based GUI for interaction.

## System Requirements

- Docker and Docker Compose
- Anthropic API key for Claude Sonnet 3.7
- Modern web browser (Chrome, Firefox, Safari, Edge)
- 4GB RAM minimum, 8GB recommended
- 10GB free disk space

## Installation

### Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/your-username/incalmo.git
   cd incalmo
   ```

2. Navigate to the deployment directory:
   ```
   cd deployment
   ```

3. Create an environment file:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

5. Make the deployment script executable:
   ```
   chmod +x deploy.sh
   ```

6. Run the deployment script:
   ```
   ./deploy.sh
   ```

7. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Installation

If you prefer to set up the components manually:

1. Generate backend requirements:
   ```
   chmod +x generate_requirements.sh
   ./generate_requirements.sh
   ```

2. Build and start the containers:
   ```
   docker-compose up -d --build
   ```

## Usage Guide

### Getting Started

1. **Initialize a Session**: Start by creating a new attack session from the Control Panel. Enter your attack goal (e.g., "Gain access to the database server and exfiltrate customer data").

2. **Explore the Environment**: Use the Network Visualization tab to explore the network topology and discover hosts.

3. **Plan Your Attack**: The Attack Graph Visualization tab shows potential attack paths based on the current environment state.

4. **Execute Tasks**: Use the Chat Interface to communicate with Claude Sonnet 3.7. You can:
   - Ask for information about the environment
   - Request specific attack tasks (e.g., "Scan the network for vulnerable hosts")
   - Get recommendations for next steps

5. **Monitor Progress**: The Dashboard shows your current progress, including discovered hosts, compromised hosts, and exfiltrated data.

6. **View Logs**: The Log Viewer tab provides detailed logs of all actions and events.

### Key Features

- **Real-time Updates**: All visualizations and data are updated in real-time via WebSocket connections.
- **Interactive Visualizations**: Both the Network and Attack Graph visualizations are interactive, allowing you to zoom, pan, and click on elements for more information.
- **Task Automation**: Claude Sonnet 3.7 can automatically translate high-level tasks to low-level primitives and execute them.
- **Attack Graph Generation**: The system automatically generates and updates attack graphs based on the current environment state.
- **Session Management**: You can save and load attack sessions to continue your work later.

### Advanced Usage

- **Custom Environments**: Create custom network environments by modifying the environment configuration in the Control Panel.
- **Task Chaining**: Chain multiple tasks together for more complex attack sequences.
- **Path Finding**: Use the path finding feature in the Attack Graph Visualization to discover optimal attack paths.
- **Data Exfiltration**: Simulate data exfiltration from compromised hosts.
- **Report Generation**: Generate detailed reports of your attack sessions for analysis and documentation.

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**: Check that the backend is running and the WebSocket URL is correctly configured in the `.env` file.

2. **API Key Invalid**: Ensure your Anthropic API key is valid and correctly set in the `.env` file.

3. **Docker Containers Not Starting**: Check Docker logs for errors:
   ```
   docker-compose logs
   ```

4. **Frontend Not Loading**: Ensure the nginx configuration is correct and the frontend container is running.

5. **Task Execution Fails**: Check the Log Viewer for detailed error messages.

### Getting Help

If you encounter issues not covered in this guide, please:

1. Check the GitHub repository issues section
2. Consult the API documentation at http://localhost:8000/docs
3. Contact the maintainers at support@example.com

## Security Considerations

Incalmo is designed for educational and research purposes only. Please use responsibly and only in environments where you have explicit permission to conduct security testing.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
