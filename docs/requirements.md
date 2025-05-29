# Incalmo - Intelligent Cybersecurity Automation Platform

## Overview
Incalmo is an LLM-powered cybersecurity automation platform that serves as an intelligent interface between Large Language Models and cybersecurity tools. Originally inspired by research on LLM-driven security assessments, Incalmo has evolved into a comprehensive automation platform for various cybersecurity tasks, including penetration testing, vulnerability assessment, security research, and compliance auditing.

## Core Components

### 1. LLM Integration Layer
- Multi-LLM support (Claude Sonnet, OpenAI GPT, Google Gemini)
- Intelligent prompt engineering for cybersecurity contexts
- Goal-oriented task planning and execution
- Real-time streaming communication via WebSocket
- Dynamic API key management and provider switching

### 2. High-Level Task Abstraction
- Comprehensive cybersecurity task library (25+ task types):
  - Network and host discovery
  - Vulnerability assessment and analysis
  - Security testing and validation
  - Information gathering and analysis
  - Tool management and automation
  - System monitoring and analysis
- Flexible task execution allowing LLM choice of tools and methods
- Autonomous tool installation for macOS environments

### 3. Environment State Service
- Dynamic environment state tracking and management
- Intelligent parsing of command outputs and tool results
- Persistent knowledge base for discovered information:
  - Network topology and discovered hosts
  - Service enumeration and vulnerability data
  - System information and access credentials
  - Tool availability and configuration status

### 4. PTES Framework Integration
- **Structured Methodology**: Full implementation of PTES (Penetration Testing Execution Standard)
- **Sequential Phase Progression**: 7-phase workflow with phase-to-phase output feeding
- **Phase Tracking**: Automatic phase management and objective tracking
- **Guided Execution**: LLM follows structured penetration testing methodology
- **Phase Transitions**: Intelligent progression through assessment phases

**PTES Phases Implemented**:
1. **Pre-engagement Interactions** - Scope definition and authorization
2. **Intelligence Gathering** - Passive and active reconnaissance  
3. **Threat Modeling** - Attack vector identification and prioritization
4. **Vulnerability Analysis** - Security flaw discovery and classification
5. **Exploitation** - Controlled vulnerability validation
6. **Post-exploitation** - Access depth and persistence assessment
7. **Reporting** - Comprehensive findings documentation

### 5. Desktop Application Interface
- Native Electron-based desktop application
- Real-time command execution monitoring
- Interactive chat interface with LLM
- Visual progress tracking and result display
- Comprehensive logging and session management

## Technical Requirements

### Backend
- Build on top of a framework that can support the required functionality
- Implement RESTful API endpoints for frontend communication
- Create a secure communication channel with Claude Sonnet 3.7 API
- Implement the core Incalmo functionality:
  - Task translation
  - Environment state tracking
  - Attack graph generation

### Frontend
- Develop a responsive web application using modern frameworks
- Implement real-time updates of attack progress
- Create intuitive visualizations of network topology and attack paths
- Design a chat-like interface for LLM interaction

### Deployment
- Ensure the application can run in a web browser
- Package the application for easy deployment
- Provide documentation for installation and usage

## Limitations and Considerations
- The tool is for educational and research purposes only
- The implementation will focus on the abstraction layer rather than actual exploitation
- The attack environments will be simulated rather than targeting real systems
- The tool should include appropriate disclaimers about ethical usage
