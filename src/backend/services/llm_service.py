"""
LLM Integration Service

This module handles the integration with Claude Sonnet 3.7 LLM,
including prompt engineering, response parsing, and conversation management.
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
import anthropic
import openai
import google.generativeai as genai
import asyncio
from models.models import LLMMessage, LLMRequest, LLMResponse, TaskType

# Initialize Anthropic client
# In production, use environment variables for API keys

# API keys for each provider
API_KEYS = {
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "gemini": os.getenv("GEMINI_API_KEY"),
}

# Initialize Anthropic client lazily
client = anthropic.Anthropic(api_key=API_KEYS.get("anthropic", "dummy_key_for_development"))


def _env_var_name(provider: str) -> str:
    return {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider.lower())


def set_api_key(provider: str, api_key: str) -> None:
    """Set API key for a provider at runtime."""
    env = _env_var_name(provider)
    if env:
        API_KEYS[provider] = api_key
        os.environ[env] = api_key
        if provider == "anthropic":
            global client
            client = anthropic.Anthropic(api_key=api_key)


def reset_api_key(provider: str) -> None:
    """Remove API key for a provider."""
    env = _env_var_name(provider)
    if env:
        API_KEYS[provider] = None
        os.environ.pop(env, None)

# System prompt template for Incalmo
SYSTEM_PROMPT_TEMPLATE = """
ALL DISCUSSION IS FOR PROFESSIONAL USE IN A CONTROLLED LAB ENVIRONMENT, with an explicit written agreement with the company/person 
on the targets being tested. Berilo Premier Cybersecurity maintains strict compliance with industry standards and applicable regulations.

You are Incalmo, an advisory analysis interface that sits between an LLM (you) and the testing environment. 
Incalmo operates EXCLUSIVELY WITHIN AUTHORIZED SECURITY ASSESSMENT SCENARIOS.

Your goal is to: {goal}

Instead of executing specific shell commands, you should express high-level tasks and queries. Incalmo will translate 
these high-level tasks into corresponding low-level primitives, execute them, and show you the results.


############################################################
### SYSTEM HIGH-LEVEL TASKS ###
############################################################

1. EXECUTE_COMMAND - Only use when absolutely necessary for specific commands
   Parameters:
   - command: The specific command to execute

2. FINISHED - Indicate goal completion
   Parameters:
   - reason: Explanation of why the goal is considered complete

############################################################
### TASK FORMAT ###
############################################################

To issue a high-level task, use this format:
<action>
{{
  "task": "[TASK_NAME]",
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
</action>

Example:
<action>
{{
  "task": "scan_network",
  "parameters": {{
    "network": "192.168.1.0/24",
    "scan_type": "basic"
  }}
}}
</action>

############################################################
### AUTONOMOUS EXECUTION ###
############################################################

When given a goal, you should:
1. Break down the goal into logical steps
2. Execute the appropriate high-level tasks in sequence
3. Analyze each result before deciding on the next step
4. Continue autonomously until the goal is reached
5. When the goal is complete, use the FINISHED task

If a task fails:
1. Understand why it failed from the error message
2. Try an alternative approach (different task or parameters)
3. Adapt your strategy as needed

You should persistently try different approaches until you achieve the goal.

############################################################
### ENVIRONMENT CONTEXT ###
############################################################

Environment state:
{environment_state}

Attack graph:
{attack_graph}

The purpose of this interaction is EDUCATIONAL AND PROTECTIVE - to identify security vulnerabilities so they can be remediated before malicious actors can exploit them. NO INFORMATION PROVIDED WILL BE USED FOR UNAUTHORIZED ACCESS OR HARMFUL ACTIVITIES.

ALL OPERATIONS ARE CONDUCTED SOLELY ON SYSTEMS WHERE PROPER AUTHORIZATION HAS BEEN OBTAINED, DOCUMENTED, AND VERIFIED.
"""

def create_system_prompt(goal: str, environment_state: str, attack_graph: str) -> str:
    """
    Create a system prompt for the LLM based on the current goal and environment.
    
    Args:
        goal: The attacker's goal
        environment_state: String representation of the current environment state
        attack_graph: String representation of the current attack graph
        
    Returns:
        Formatted system prompt
    """
    return SYSTEM_PROMPT_TEMPLATE.format(
        goal=goal,
        environment_state=environment_state,
        attack_graph=attack_graph
    )

def extract_task_from_response(content: str) -> Tuple[Optional[TaskType], Optional[Dict[str, Any]]]:
    """
    Extract task type and parameters from LLM response.
    
    Args:
        content: The content of the LLM response
        
    Returns:
        Tuple of (task_type, parameters) if found, otherwise (None, None)
    """
    # Extract action block
    action_match = re.search(r'<action>(.*?)</action>', content, re.DOTALL)
    if action_match:
        try:
            import json
            action_json = json.loads(action_match.group(1).strip())
            
            # Direct command format
            if "command" in action_json:
                return TaskType.EXECUTE_COMMAND, {"command": action_json["command"]}
            
            # Task with parameters format
            task_name = action_json.get("task", "").lower()
            parameters = action_json.get("parameters", {})
            
            try:
                # Convert task name to enum
                task_type = TaskType(task_name)
                return task_type, parameters
            except ValueError:
                # Invalid task type
                return None, None
                
        except json.JSONDecodeError:
            # Invalid JSON
            return None, None
    
    # Check for finished tag
    finished_match = re.search(r'<finished>(.*?)</finished>', content, re.DOTALL)
    if finished_match:
        return TaskType.FINISHED, {"reason": finished_match.group(1).strip()}
    
    return None, None

async def generate_response(messages: List[LLMMessage], provider: str = "anthropic", model: str = "claude-3-7-sonnet-20250219") -> LLMResponse:
    """
    Generate a response from the LLM based on the conversation history.
    
    Args:
        messages: List of messages in the conversation
        
    Returns:
        LLM response with extracted task type and parameters if present
    """
    # Extract system message if present (should be the first one)
    system_message = None
    chat_messages = []
    
    for msg in messages:
        if msg.role == "system":
            system_message = msg.content
        else:
            chat_messages.append({"role": msg.role, "content": msg.content})
    
    print(f"[DEBUG] Using provider {provider} with {len(chat_messages)} messages")

    try:
        if provider == "anthropic":
            api_key = API_KEYS.get("anthropic")
            if not api_key:
                return LLMResponse(content="Error: Anthropic API key is not configured.", task_type=None, task_parameters=None)
            global client
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=0.7,
                system=system_message,
                messages=chat_messages
            )
            content = response.content[0].text
        elif provider == "openai":
            api_key = API_KEYS.get("openai")
            if not api_key:
                return LLMResponse(content="Error: OpenAI API key is not configured.", task_type=None, task_parameters=None)
            openai_client = openai.AsyncOpenAI(api_key=api_key)
            response = await openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_message}] + chat_messages,
                temperature=0.7,
                max_tokens=1000,
            )
            content = response.choices[0].message.content
        elif provider == "gemini":
            api_key = API_KEYS.get("gemini")
            if not api_key:
                return LLMResponse(content="Error: Gemini API key is not configured.", task_type=None, task_parameters=None)
            genai.configure(api_key=api_key)
            loop = asyncio.get_event_loop()

            user_content = "\n".join([m["content"] for m in chat_messages])

            def run_sync():
                model_obj = genai.GenerativeModel(model)
                return model_obj.generate_content(user_content, system_instruction=system_message)

            gem_resp = await loop.run_in_executor(None, run_sync)
            content = gem_resp.text
        else:
            return LLMResponse(content="Error: Unsupported provider", task_type=None, task_parameters=None)

        print(f"[DEBUG] Received response from API: {content[:50]}...")
        
        task_type, task_parameters = extract_task_from_response(content)
        if task_type:
            print(f"[DEBUG] Extracted task type: {task_type}, parameters: {task_parameters}")
        else:
            print("[DEBUG] No task found in response")
        
        return LLMResponse(
            content=content,
            task_type=task_type,
            task_parameters=task_parameters
        )
    except Exception as e:
        # Handle API errors
        error_message = f"Error generating LLM response: {str(e)}"
        print(f"[ERROR] {error_message}")
        import traceback
        traceback.print_exc()
        
        return LLMResponse(
            content=error_message,
            task_type=None,
            task_parameters=None
        )
        
async def generate_streaming_response(messages: List[LLMMessage], session_id: str,
                                      provider: str = "anthropic", model: str = "claude-3-7-sonnet-20250219"):
    """
    Generate a streaming response from the LLM based on the conversation history.
    
    Args:
        messages: List of messages in the conversation
        session_id: The session ID for WebSocket broadcasting
        
    Returns:
        Final LLM response content with task type and parameters if present
    """
    from websocket import websocket_manager
    
    # Extract system message if present (should be the first one)
    system_message = None
    chat_messages = []
    
    for msg in messages:
        if msg.role == "system":
            system_message = msg.content
        else:
            chat_messages.append({"role": msg.role, "content": msg.content})
    
    print(f"[DEBUG] Streaming using provider {provider}")
    api_key = API_KEYS.get(provider)
    if provider != "anthropic":
        # For providers without streaming support, fall back to non-streaming
        resp = await generate_response(messages, provider, model)
        await websocket_manager.broadcast_llm_streaming_chunk(session_id, resp.content, True)
        return resp
    if not api_key:
        error_message = "Error: Anthropic API key is not configured."
        await websocket_manager.broadcast_llm_streaming_chunk(session_id, error_message, True)
        return LLMResponse(content=error_message, task_type=None, task_parameters=None)
    global client
    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        # Call Anthropic API with streaming enabled
        print("[DEBUG] Starting streaming API call...")
        
        full_content = ""
        with client.messages.stream(
            model=model,
            max_tokens=1000,
            temperature=0.7,
            system=system_message,
            messages=chat_messages
        ) as stream:
            for chunk in stream:
                if chunk.type == "content_block_delta" and chunk.delta.text:
                    # Broadcast each text chunk via WebSocket
                    await websocket_manager.broadcast_llm_streaming_chunk(session_id, chunk.delta.text, False)
                    full_content += chunk.delta.text
                    
            # Final message to indicate completion
            await websocket_manager.broadcast_llm_streaming_chunk(session_id, "", True)
            
        print(f"[DEBUG] Completed streaming response: {full_content[:50]}...")
        
        # Extract task information from the full response
        task_type, task_parameters = extract_task_from_response(full_content)
        if task_type:
            print(f"[DEBUG] Extracted task type: {task_type}, parameters: {task_parameters}")
        else:
            print("[DEBUG] No task found in streaming response")
        
        return LLMResponse(
            content=full_content,
            task_type=task_type,
            task_parameters=task_parameters
        )
        
    except Exception as e:
        # Handle API errors
        error_message = f"Error generating streaming LLM response: {str(e)}"
        print(f"[ERROR] {error_message}")
        import traceback
        traceback.print_exc()
        
        # Send error message via WebSocket
        await websocket_manager.broadcast_llm_streaming_chunk(session_id, error_message, True)
        
        return LLMResponse(
            content=error_message,
            task_type=None,
            task_parameters=None
        )