"""
Tasks Router

This module defines the API routes for task translation and execution.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from models.models import TaskType, TaskRequest, TaskResult, EnvironmentState
from services.task_service import task_translation_service

router = APIRouter()

@router.post("/execute", response_model=TaskResult)
async def execute_task(request: TaskRequest, environment_state: EnvironmentState):
    """
    Execute a high-level task by translating it to low-level primitives.
    
    Args:
        request: Task request containing task type and parameters
        environment_state: Current state of the environment
        
    Returns:
        Result of the task execution
    """
    try:
        result = await task_translation_service.execute_task(
            request.task_type, 
            request.parameters, 
            environment_state
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing task: {str(e)}")

@router.get("/types")
async def get_task_types():
    """
    Get all available task types.
    
    Returns:
        List of available task types
    """
    return {"task_types": [t.value for t in TaskType]}
