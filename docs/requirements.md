# Incalmo Requirements and Specifications

## Overview
Based on the paper "On the Feasibility of Using LLMs to Execute Multistage Network Attacks", we need to build Incalmo - an LLM-agnostic high-level attack abstraction layer that sits between an LLM and the environment. This tool will use Claude Sonnet 3.7 as the LLM and will have a web browser GUI.

## Core Components

### 1. LLM Integration Layer
- Integrate with Claude Sonnet 3.7 as the primary LLM
- Create a preprompt containing:
  - Attacker goal
  - Instructions for formatting queries and actions
  - Documentation about the high-level API
  - Initial known information about the environment
- Extract LLM responses between `<action></action>` or `<query></query>` tags
- Process LLM responses until a `<finished>` tag is received or a time limit is reached

### 2. High-Level Task Abstraction
- Implement high-level task abstractions that LLMs can use:
  - Network scanning
  - Host infection
  - Lateral movement
  - Privilege escalation
  - Data exfiltration
- Create translations that convert high-level tasks into low-level primitives

### 3. Environment State Service
- Implement a knowledge base using Python objects
- Create parsers to interpret command output and update the knowledge base
- Track the state of the environment including:
  - Discovered hosts
  - Network topology
  - Vulnerabilities
  - Access privileges

### 4. Attack Graph Service
- Provide a structured representation of attack paths
- Help LLMs select actions relevant to a multistage attack
- Enable reasoning about available attack paths
- Support fine-grained access control between hosts

### 5. Web-Based GUI
- Create a user-friendly interface that runs in a web browser
- Provide visualization of:
  - Network topology
  - Attack graph
  - Current environment state
  - LLM interaction history
- Allow users to:
  - Set attack goals
  - Monitor attack progress
  - View detailed logs
  - Interact with the LLM

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
