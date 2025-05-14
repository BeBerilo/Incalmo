"""
LLM Router

This module defines the API routes for LLM integration.
"""

from fastapi import APIRouter, HTTPException, Depends
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from models.models import LLMMessage, LLMRequest, LLMResponse, SessionState, TaskType
from services.llm_service import generate_response, create_system_prompt
from services.environment_service import environment_state_service
from services.attack_graph_service import attack_graph_service
from core import create_session, process_llm_message

router = APIRouter()

@router.post("/generate", response_model=LLMResponse)
async def generate_llm_response(request: LLMRequest):
    """
    Generate a response from the LLM based on the conversation history.
    
    Args:
        request: LLM request containing messages and parameters
        
    Returns:
        LLM response with extracted task type and parameters if present
    """
    try:
        response = await generate_response(request.messages)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating LLM response: {str(e)}")

@router.post("/create-system-prompt")
async def create_system_prompt_endpoint(goal: str, environment_state: str, attack_graph: str):
    """
    Create a system prompt for the LLM based on the current goal and environment.
    
    Args:
        goal: The attacker's goal
        environment_state: String representation of the current environment state
        attack_graph: String representation of the current attack graph
        
    Returns:
        Formatted system prompt
    """
    try:
        prompt = create_system_prompt(goal, environment_state, attack_graph)
        return {"prompt": prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating system prompt: {str(e)}")

class SessionRequest(BaseModel):
    goal: str
    environment_config: Optional[Dict[str, Any]] = None

@router.post("/session/create", response_model=SessionState)
async def create_session_endpoint(request: SessionRequest):
    """
    Create a new session with the specified goal and environment configuration.
    
    Args:
        request: Request containing the goal and optional environment configuration
        
    Returns:
        New session state
    """
    try:
        session = await create_session(request.goal, request.environment_config)
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

class MessageRequest(BaseModel):
    message: str
    session_id: str

class MessageRequestWithAutonomy(MessageRequest):
    autonomous_mode: bool = False

@router.post("/message", response_model=Dict[str, Any])
async def send_message(request: MessageRequestWithAutonomy):
    """
    Send a message to the LLM in a specific session.
    
    Args:
        request: Request containing the session_id, message, and autonomous_mode flag
        
    Returns:
        LLM response and any task result
    """
    try:
        # Process the user message and get initial LLM response and task result
        llm_response, task_result = await process_llm_message(request.session_id, request.message, use_streaming=True)
        
        # Get the current session
        from core import active_sessions
        if request.session_id not in active_sessions:
            raise ValueError(f"Session not found: {request.session_id}")
            
        session = active_sessions[request.session_id]
        environment_state = session.environment_state
        
        # For autonomous mode: if a task was executed and succeeded, continue the chain
        if request.autonomous_mode and task_result and task_result.success:
            # Execute up to 3 additional autonomous steps if needed to reach the goal
            max_autonomous_steps = 3
            additional_results = []
            
            for step in range(max_autonomous_steps):
                # Create a prompt describing the previous result to inform the next action
                autonomous_prompt = f"""THE PREVIOUS TASK HAS COMPLETED. DETERMINE THE NEXT ACTION TO TAKE.

### PREVIOUS TASK RESULT ###
Task type: {task_result.task_type.value}
Success: Yes
Result details: {json.dumps(task_result.result, indent=2)}

### YOUR RESPONSE MUST INCLUDE AN ACTION TAG ###
Based on this result, determine the next step toward the goal. If the goal is achieved, respond with <finished>.

CRITICAL: You MUST respond with an <action> tag containing a valid JSON task, or a <finished> tag.
A response without either of these tags will BREAK the system and terminate the session.

Example action response:
<action>
{{
  "task": "scan_network",
  "parameters": {{
    "network": "192.168.1.0/24",
    "scan_type": "aggressive"
  }}
}}
</action>

DO NOT provide text without an action tag. This is NON-NEGOTIABLE."""
                
                # Get the LLM's next action
                next_response, next_task_result = await process_llm_message(request.session_id, autonomous_prompt, use_streaming=True)
                
                # Check if we should stop (finished or no valid task response)
                if not next_task_result or not next_response.task_type:
                    break
                    
                # Handle goal completion
                if next_response.task_type == TaskType.FINISHED:
                    # Create a goal completion message to add to the task result
                    from datetime import datetime
                    
                    # Extract the completion reason
                    reason = next_response.task_parameters.get("reason", "Goal has been achieved successfully.")
                    
                    # Create a goal completion result
                    completion_result = TaskResult(
                        task_type=TaskType.FINISHED,
                        success=True,
                        result={
                            "reason": reason,
                            "goal_achieved": True,
                            "summary": f"""## 🎯 Goal Achieved Successfully!

**Goal:** {session.goal}

**Completion Summary:**
{reason}

**Steps Completed:** {len(session.task_history) + len(additional_results) + 1}
"""
                        },
                        timestamp=datetime.now()
                    )
                    
                    # Add this as the final result
                    additional_results.append(completion_result)
                    task_result = completion_result
                    break
                
                # Record this task result
                additional_results.append(next_task_result)
                task_result = next_task_result
                
                # Update environment state
                environment_state = session.environment_state
                
                # If the task failed, ask the LLM to try with a different approach
                if not task_result.success:
                    # Create a prompt describing the failure to inform the next action
                    error_prompt = f"""############################################################
### COMMAND FAILURE DETECTED - RECOVERY NEEDED ###
############################################################

⚠️ THE PREVIOUS TASK HAS FAILED. YOU MUST TRY A DIFFERENT APPROACH ⚠️

### ERROR DETAILS ###
Task type: {task_result.task_type.value}
Error message: {task_result.error}
{json.dumps(task_result.result, indent=2) if task_result.result else ""}

### RECOVERY STRATEGIES ###
1. If a command was not found, try an alternative:
   - Try installing the tool based on the OS
   - Try alternative tool that does the same job

2. Try using absolute paths to common locations:
   - /usr/bin/[tool]
   - /usr/local/bin/[tool]
   - /opt/homebrew/bin/[tool] (macOS)

3. Break down complex operations into simpler steps:
   - Replace advanced features with basic functionality

### YOUR RESPONSE MUST INCLUDE AN ACTION TAG ###
⚠️ CRITICAL: You MUST respond with an <action> tag containing a valid JSON task.
⚠️ A response without an action tag will BREAK the system and terminate the session.

Example recovery action:
<action>
{{
  "task": "execute_command",
  "parameters": {{
    "command": "brew install nmap"
  }}
}}
</action>

DO NOT provide explanatory text without an action tag. This is NON-NEGOTIABLE."""
                    
                    # Get the LLM's next action after the failure
                    retry_response, retry_task_result = await process_llm_message(request.session_id, error_prompt, use_streaming=True)
                    
                    # Check if we got a valid task response
                    if retry_task_result and retry_response.task_type and retry_task_result.success:
                        # Successfully recovered with a new approach
                        additional_results.append(retry_task_result)
                        task_result = retry_task_result
                        
                        # Update environment state
                        environment_state = session.environment_state
                    else:
                        # Failed to recover, stop the autonomous execution
                        break
            
            # If we did autonomous actions, add them to the response
            if additional_results:
                all_results = [task_result] + additional_results
                all_results_as_dict = [result.dict() for result in all_results]
                
                return {
                    "response": llm_response.content,
                    "task_type": llm_response.task_type.value if llm_response.task_type else None,
                    "task_parameters": llm_response.task_parameters,
                    "task_result": all_results_as_dict[0],  # First result
                    "autonomous_steps": len(additional_results),
                    "all_task_results": all_results_as_dict,
                    "environment_state": environment_state.dict()
                }
        
        # For autonomous mode, we'll always try to execute up to 10 additional steps 
        # after the first command completes, giving plenty of opportunity for recovery and retry
        max_autonomous_steps = 10
        additional_results = []
        
        # Execute autonomous steps as long as we got a task result, regardless of success/failure
        if task_result:
            # Process the autonomous execution steps
            for step in range(max_autonomous_steps):
                # Different prompting depending on whether the previous command succeeded or failed
                if task_result.success:
                    # Command succeeded - continue with next step
                    result_description = json.dumps(task_result.result, indent=2) if task_result.result else "No result"
                    
                    autonomous_prompt = f"""
                    Here is the result of your previous successful command: 
                    
                    Command: {task_result.result.get('command', 'Unknown command')}
                    
                    Output:
                    {result_description}
                    
                    Based on this output, what is the next command you want to execute to continue toward the goal?
                    Remember to use the <action> tag with a command.
                    """
                else:
                    # Command failed - try an alternative approach
                    error_message = task_result.error if task_result.error else "Unknown error"
                    result_description = json.dumps(task_result.result, indent=2) if task_result.result else "No result"
                    
                    autonomous_prompt = f"""
                    THE PREVIOUS COMMAND FAILED. You need to try a different approach.
                    
                    Failed command: {task_result.result.get('command', 'Unknown command')}
                    
                    Error:
                    {error_message}
                    
                    Output:
                    {result_description}
                    
                    Please try a different approach to achieve the same goal. Consider:
                    1. Using different command syntax
                    2. Using alternative tools that provide similar functionality
                    3. Breaking down the task into smaller steps
                    4. Using a different methodology entirely
                    
                    What alternative command would you like to try? 
                    Remember to use the <action> tag with a command.
                    """
                
                # Get the LLM's next action
                next_response, next_task_result = await process_llm_message(request.session_id, autonomous_prompt, use_streaming=True)
                
                # Continue regardless of success/failure - we'll let the LLM handle
                # alternative approaches. Only stop if no task was executed or it returned None.
                if not next_task_result:
                    break
                    
                # Record this task result
                additional_results.append(next_task_result)
                task_result = next_task_result
            
            # Return the initial response plus all additional steps
            all_results = [task_result] + additional_results 
            all_results_as_dict = [result.dict() for result in all_results if result]
            
            return {
                "response": llm_response.content,
                "task_type": llm_response.task_type.value if llm_response.task_type else None,
                "task_parameters": llm_response.task_parameters,
                "task_result": task_result.dict() if task_result else None,
                "autonomous_steps": len(additional_results),
                "all_task_results": all_results_as_dict,
                "environment_state": environment_state.dict()
            }
        else:
            # Standard response if no task was executed or it failed
            return {
                "response": llm_response.content,
                "task_type": llm_response.task_type.value if llm_response.task_type else None,
                "task_parameters": llm_response.task_parameters,
                "task_result": task_result.dict() if task_result else None,
                "autonomous_steps": 0,
                "environment_state": environment_state.dict()
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
