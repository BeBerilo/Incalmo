"""
Incalmo Core Functionality Implementation

This module implements the core functionality of Incalmo as described in the paper
"On the Feasibility of Using LLMs to Execute Multistage Network Attacks".

It connects the Claude Sonnet 3.7 LLM with the task translation engine,
environment state tracking, and attack graph generation.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models.models import (
    TaskType, TaskRequest, TaskResult, Host, Network, 
    EnvironmentState, AttackNode, AttackEdge, AttackGraph,
    LLMMessage, LLMRequest, LLMResponse, SessionState
)

from services.llm_service import generate_response, generate_streaming_response, create_system_prompt
from services.task_service import task_translation_service
from services.environment_service import environment_state_service
from services.attack_graph_service import attack_graph_service

# Dictionary to store active sessions
active_sessions: Dict[str, SessionState] = {}

async def create_session(goal: str, environment_config: Optional[Dict[str, Any]] = None,
                         provider: str = "anthropic", model: str = "claude-3-7-sonnet-20250219") -> SessionState:
    """
    Create a new Incalmo session with the specified goal and environment configuration.
    
    Args:
        goal: The attacker's goal
        environment_config: Optional configuration for the environment
        
    Returns:
        New session state
    """
    # Create environment
    environment_state = environment_state_service.create_initial_environment(environment_config)
    
    # Generate attack graph
    attack_graph = attack_graph_service.generate_attack_graph(environment_state)
    
    # Create system prompt
    environment_text = environment_state_service.get_environment_state_text(environment_state)
    attack_graph_text = attack_graph_service.get_attack_graph_text(attack_graph, environment_state)
    system_prompt = create_system_prompt(goal, environment_text, attack_graph_text)
    
    # Create session with a more stable ID format
    import uuid
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    session = SessionState(
        id=session_id,
        environment_state=environment_state,
        attack_graph=attack_graph,
        conversation_history=[
            LLMMessage(role="system", content=system_prompt)
        ],
        task_history=[],
        goal=goal if goal else None,
        provider=provider,
        model=model
    )
    
    # Store session
    active_sessions[session_id] = session
    
    return session

async def process_llm_message(session_id: str, message: str, use_streaming: bool = True) -> Tuple[LLMResponse, Optional[TaskResult]]:
    """
    Process a message from the user by sending it to the LLM and executing any resulting task.
    
    Args:
        session_id: ID of the session
        message: User message content
        use_streaming: Whether to use streaming response (default: True)
        
    Returns:
        Tuple of (LLM response, task result if any)
    """
    print(f"[DEBUG] Processing message for session {session_id}: {message[:50]}...")
    
    if session_id not in active_sessions:
        print(f"[ERROR] Session not found: {session_id}")
        raise ValueError(f"Session not found: {session_id}")
    
    session = active_sessions[session_id]
    print(f"[DEBUG] Found session with {len(session.conversation_history)} messages in history")
    
    # Add user message to conversation history directly
    user_message = LLMMessage(role="user", content=message)
    session.conversation_history.append(user_message)
    
    # Generate LLM response - using streaming if enabled
    print(f"[DEBUG] Generating LLM response (streaming={use_streaming})...")
    if use_streaming:
        llm_response = await generate_streaming_response(
            session.conversation_history, session_id, session.provider, session.model
        )
    else:
        llm_response = await generate_response(
            session.conversation_history, session.provider, session.model
        )
    
    print(f"[DEBUG] LLM response received: {llm_response.content[:50]}...")
    
    # Add assistant message to conversation history
    assistant_message = LLMMessage(role="assistant", content=llm_response.content)
    session.conversation_history.append(assistant_message)
    
    # Parse high-level tasks or direct commands from the response
    # This implements Incalmo's feature allowing LLMs to express both high-level intentions
    # and direct terminal commands when needed
    task_result = None
    import re
    import json
    
    # Check for action tags in the content
    print("[DEBUG] Checking for action tags in response...")
    action_match = re.search(r'<action>(.*?)</action>', llm_response.content, re.DOTALL)
    if action_match:
        try:
            action_json = action_match.group(1).strip()
            print(f"[DEBUG] Found action JSON: {action_json[:50]}...")
            
            # Parse the JSON inside the action tags
            action_data = json.loads(action_json)
            print(f"[DEBUG] Parsed action data: {action_data}")
            
            # Check if this is a direct command execution request
            if "command" in action_data:
                print(f"[DEBUG] Executing direct command: {action_data['command']}")
                task_result = await execute_task(session_id, TaskType.EXECUTE_COMMAND, {"command": action_data["command"]})
            # Otherwise, check if it's a task with parameters
            elif "task" in action_data and "parameters" in action_data:
                task_type = action_data["task"]
                print(f"[DEBUG] Executing task type: {task_type} with parameters: {action_data['parameters']}")
                
                # Handle different naming conventions for execute_command
                if task_type == "execute_command" and "command" in action_data["parameters"]:
                    print(f"[DEBUG] Executing command via task: {action_data['parameters']['command']}")
                    task_result = await execute_task(session_id, TaskType.EXECUTE_COMMAND, {"command": action_data["parameters"]["command"]})
                else:
                    # Try to convert string task type to enum and execute the task
                    try:
                        task_enum = TaskType(task_type)
                        print(f"[DEBUG] Executing task enum: {task_enum} with parameters: {action_data['parameters']}")
                        task_result = await execute_task(session_id, task_enum, action_data["parameters"])
                    except ValueError as e:
                        # Unknown task type - inform the user
                        from datetime import datetime
                        error_message = f"Unknown task type: {task_type}. Please use one of: {', '.join([t.value for t in TaskType])}"
                        print(f"[ERROR] {error_message}")
                        task_result = TaskResult(
                            task_type=TaskType.FINISHED,  # Use FINISHED as a placeholder
                            success=False,
                            error=error_message,
                            result={},
                            timestamp=datetime.now()
                        )
        except json.JSONDecodeError as e:
            # Not valid JSON inside action tags
            print(f"[ERROR] JSON decode error in action tag: {str(e)}")
        except Exception as e:
            # Some other error occurred
            print(f"[ERROR] Error processing action: {str(e)}")
    else:
        print("[DEBUG] No action tags found in response")
    
    # Update session
    active_sessions[session_id] = session
    
    if task_result:
        print(f"[DEBUG] Task result: success={task_result.success}, type={task_result.task_type}")
        if not task_result.success:
            print(f"[ERROR] Task failed: {task_result.error}")
    else:
        print("[DEBUG] No task was executed")
    
    return llm_response, task_result

async def execute_task(session_id: str, task_type: str, parameters: Dict[str, Any]) -> TaskResult:
    """
    Execute a task in the context of a session.
    
    Args:
        session_id: ID of the session
        task_type: Type of task to execute
        parameters: Parameters for the task
        
    Returns:
        Result of the task execution
    """
    if session_id not in active_sessions:
        raise ValueError(f"Session not found: {session_id}")
    
    session = active_sessions[session_id]
    
    # Execute task
    task_result = await task_translation_service.execute_task(
        TaskType(task_type), 
        parameters, 
        session.environment_state
    )
    
    # Update session with task result
    session.task_history.append(task_result)
    
    # Update attack graph
    session.attack_graph = attack_graph_service.generate_attack_graph(session.environment_state)
    
    # Update session
    active_sessions[session_id] = session
    
    return task_result

async def update_environment_state(session_id: str, environment_state: EnvironmentState) -> bool:
    """
    Update the environment state of a session.
    
    Args:
        session_id: ID of the session
        environment_state: New environment state
        
    Returns:
        True if successful
    """
    if session_id not in active_sessions:
        raise ValueError(f"Session not found: {session_id}")
    
    session = active_sessions[session_id]
    
    # Update environment state
    session.environment_state = environment_state
    
    # Update attack graph
    session.attack_graph = attack_graph_service.generate_attack_graph(environment_state)
    
    # Update session
    active_sessions[session_id] = session
    
    return True

async def get_session(session_id: str) -> SessionState:
    """
    Get a session by ID.
    
    Args:
        session_id: ID of the session
        
    Returns:
        Session state
    """
    if session_id not in active_sessions:
        raise ValueError(f"Session not found: {session_id}")
    
    return active_sessions[session_id]

async def delete_session(session_id: str) -> bool:
    """
    Delete a session by ID.
    
    Args:
        session_id: ID of the session
        
    Returns:
        True if successful
    """
    if session_id not in active_sessions:
        raise ValueError(f"Session not found: {session_id}")
    
    del active_sessions[session_id]
    
    return True

# Add these functions to the FastAPI app in main.py
def setup_core_routes(app: FastAPI):
    """
    Set up the core routes for the Incalmo API.
    
    Args:
        app: FastAPI application
    """
    @app.post("/api/sessions", response_model=SessionState)
    async def create_new_session(goal: str, environment_config: Optional[Dict[str, Any]] = None,
                                 provider: str = "anthropic", model: str = "claude-3-7-sonnet-20250219"):
        """Create a new Incalmo session."""
        try:
            session = await create_session(goal, environment_config, provider, model)
            return session
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")
    
    @app.get("/api/sessions/{session_id}", response_model=SessionState)
    async def get_session_by_id(session_id: str):
        """Get a session by ID."""
        try:
            return await get_session(session_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")
    
    @app.delete("/api/sessions/{session_id}", response_model=bool)
    async def delete_session_by_id(session_id: str):
        """Delete a session by ID."""
        try:
            return await delete_session(session_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")
    
    @app.post("/api/sessions/{session_id}/message", response_model=Dict[str, Any])
    async def send_message_to_session(session_id: str, message: str):
        """Send a message to a session and get the LLM response and any task result."""
        try:
            llm_response, task_result = await process_llm_message(session_id, message)
            return {
                "llm_response": llm_response,
                "task_result": task_result
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
    
    @app.post("/api/sessions/{session_id}/task", response_model=TaskResult)
    async def execute_task_in_session(session_id: str, task_request: TaskRequest):
        """Execute a task in a session."""
        try:
            return await execute_task(session_id, task_request.task_type, task_request.parameters)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error executing task: {str(e)}")
    
    @app.put("/api/sessions/{session_id}/environment", response_model=bool)
    async def update_session_environment(session_id: str, environment_state: EnvironmentState):
        """Update the environment state of a session."""
        try:
            return await update_environment_state(session_id, environment_state)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating environment: {str(e)}")
