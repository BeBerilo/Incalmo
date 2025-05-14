# Software Engineering Plan for Incalmo

## Project Overview
This plan outlines the development approach for building Incalmo, an LLM-agnostic high-level attack abstraction layer with Claude Sonnet 3.7 integration and a web-based GUI. The project will follow an iterative development approach with clear milestones.

## Technology Stack

### Backend
- **Python 3.10+**: Core programming language
- **FastAPI**: Web framework for building APIs
- **Anthropic API**: For Claude Sonnet 3.7 integration
- **SQLite/SQLAlchemy**: For persistent storage
- **Pydantic**: For data validation
- **NetworkX**: For graph representation and algorithms
- **Pytest**: For testing

### Frontend
- **React**: JavaScript library for building user interfaces
- **TypeScript**: For type safety
- **Tailwind CSS**: For styling
- **D3.js**: For network visualization
- **React Flow**: For attack graph visualization
- **Axios**: For API communication
- **Jest**: For testing

## Architecture

### High-Level Architecture
```
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|  Web Browser GUI  | <--> |  Incalmo Backend  | <--> |  Claude Sonnet    |
|  (React)          |      |  (FastAPI)        |      |  3.7 API          |
|                   |      |                   |      |                   |
+-------------------+      +-------------------+      +-------------------+
                                    ^
                                    |
                                    v
                           +-------------------+
                           |                   |
                           |  Environment      |
                           |  Simulation       |
                           |                   |
                           +-------------------+
```

### Component Architecture

#### Backend Components
1. **API Layer**: FastAPI endpoints for frontend communication
2. **LLM Integration Service**: Handles communication with Claude Sonnet 3.7
3. **Task Translation Engine**: Converts high-level tasks to low-level primitives
4. **Environment State Manager**: Tracks and updates environment state
5. **Attack Graph Generator**: Creates and maintains attack graph
6. **Simulation Engine**: Simulates network environments for testing

#### Frontend Components
1. **Dashboard**: Main user interface
2. **Network Visualizer**: Displays network topology
3. **Attack Graph Visualizer**: Shows possible attack paths
4. **Chat Interface**: For LLM interaction
5. **Control Panel**: For setting goals and parameters
6. **Log Viewer**: For detailed execution logs

## Development Phases

### Phase 1: Project Setup and Core Backend (Days 1-3)
- Set up project structure and repositories
- Configure development environment
- Implement basic FastAPI server
- Create Claude Sonnet 3.7 integration service
- Develop core data models

### Phase 2: Task Translation and Environment State (Days 4-6)
- Implement high-level task abstractions
- Create translation mechanisms for converting to low-level primitives
- Develop environment state tracking system
- Build basic knowledge base structure

### Phase 3: Attack Graph and Simulation (Days 7-9)
- Implement attack graph generation
- Create network topology representation
- Develop simple environment simulation
- Build path finding algorithms

### Phase 4: Frontend Foundation (Days 10-12)
- Set up React application
- Implement basic UI components
- Create network visualization
- Develop chat interface for LLM interaction

### Phase 5: Integration and Advanced Features (Days 13-15)
- Connect frontend and backend
- Implement real-time updates
- Add attack graph visualization
- Create detailed logging system

### Phase 6: Testing and Refinement (Days 16-18)
- Write comprehensive tests
- Perform integration testing
- Fix bugs and issues
- Optimize performance

### Phase 7: Documentation and Deployment (Days 19-21)
- Create user documentation
- Write installation guides
- Prepare deployment package
- Deploy web application

## Detailed Task Breakdown

### Backend Development

#### API Layer
- Create FastAPI application structure
- Implement authentication (if required)
- Define API endpoints for:
  - LLM interaction
  - Environment state
  - Attack graph
  - Task execution
  - Simulation control

#### LLM Integration
- Set up Anthropic API client
- Create prompt engineering module
- Implement response parsing
- Build conversation management
- Handle error cases and retries

#### Task Translation
- Define high-level task schema
- Implement translation functions for each task type
- Create validation mechanisms
- Build execution pipeline

#### Environment State
- Design state representation
- Implement state update mechanisms
- Create query interfaces
- Build persistence layer

#### Attack Graph
- Design graph data structure
- Implement node and edge representation
- Create graph update algorithms
- Build path finding functionality

#### Simulation
- Create network simulation framework
- Implement host and service representation
- Build vulnerability simulation
- Create realistic network topologies

### Frontend Development

#### Application Structure
- Set up React with TypeScript
- Configure routing
- Implement state management
- Create component library

#### Visualization
- Implement network topology visualization
- Create attack graph visualization
- Build state transition animations
- Develop interactive elements

#### User Interface
- Design and implement dashboard
- Create chat interface
- Build control panels
- Implement log viewer

#### API Integration
- Create API client
- Implement real-time updates
- Handle error states
- Build authentication flow

## Testing Strategy

### Unit Testing
- Test individual components in isolation
- Verify correct behavior of translation functions
- Validate state management
- Ensure graph algorithms work correctly

### Integration Testing
- Test API endpoints
- Verify frontend-backend communication
- Ensure LLM integration works correctly
- Validate end-to-end workflows

### User Testing
- Verify usability of interface
- Ensure visualizations are clear
- Test different attack scenarios
- Validate error handling

## Deployment Strategy
- Package application for easy deployment
- Create Docker containers for backend and frontend
- Implement environment configuration
- Provide deployment documentation

## Risk Management

### Technical Risks
- LLM API limitations or changes
- Performance issues with complex graphs
- Browser compatibility issues
- Security concerns

### Mitigation Strategies
- Implement fallback mechanisms for API issues
- Use efficient algorithms and pagination
- Test across multiple browsers
- Follow security best practices

## Documentation Plan
- Create API documentation
- Write user guides
- Provide installation instructions
- Document architecture and design decisions

## Timeline and Milestones

### Week 1
- Complete project setup
- Implement core backend functionality
- Create basic LLM integration

### Week 2
- Complete task translation engine
- Implement environment state and attack graph
- Develop frontend foundation

### Week 3
- Integrate all components
- Complete testing and refinement
- Deploy application
- Deliver final documentation
