"""
Environment Router

This module defines the API routes for environment state management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from models.models import EnvironmentState, Host, Network
from services.environment_service import environment_state_service

router = APIRouter()

@router.post("/create", response_model=EnvironmentState)
async def create_environment(config: Optional[Dict[str, Any]] = None):
    """
    Create an initial environment state based on the provided configuration.
    
    Args:
        config: Optional configuration for the environment
        
    Returns:
        Initial environment state
    """
    try:
        environment = environment_state_service.create_initial_environment(config)
        return environment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating environment: {str(e)}")

@router.get("/host/{host_id}", response_model=Host)
async def get_host(host_id: str, environment_state: EnvironmentState):
    """
    Get a host by its ID.
    
    Args:
        host_id: ID of the host to find
        environment_state: Current environment state
        
    Returns:
        Host if found
    """
    host = environment_state_service.get_host_by_id(environment_state, host_id)
    if not host:
        raise HTTPException(status_code=404, detail=f"Host not found: {host_id}")
    return host

@router.get("/network/{network_id}", response_model=Network)
async def get_network(network_id: str, environment_state: EnvironmentState):
    """
    Get a network by its ID.
    
    Args:
        network_id: ID of the network to find
        environment_state: Current environment state
        
    Returns:
        Network if found
    """
    network = environment_state_service.get_network_by_id(environment_state, network_id)
    if not network:
        raise HTTPException(status_code=404, detail=f"Network not found: {network_id}")
    return network

@router.put("/host", response_model=bool)
async def update_host(host: Host, environment_state: EnvironmentState):
    """
    Update a host in the environment state.
    
    Args:
        host: Updated host
        environment_state: Current environment state
        
    Returns:
        True if the host was updated, False otherwise
    """
    result = environment_state_service.update_host(environment_state, host)
    if not result:
        raise HTTPException(status_code=404, detail=f"Host not found: {host.id}")
    return result

@router.post("/host/{network_id}", response_model=bool)
async def add_host(network_id: str, host: Host, environment_state: EnvironmentState):
    """
    Add a host to a network in the environment state.
    
    Args:
        network_id: ID of the network to add the host to
        host: Host to add
        environment_state: Current environment state
        
    Returns:
        True if the host was added, False otherwise
    """
    result = environment_state_service.add_host(environment_state, network_id, host)
    if not result:
        raise HTTPException(status_code=404, detail=f"Network not found: {network_id}")
    return result

@router.delete("/host/{host_id}", response_model=bool)
async def remove_host(host_id: str, environment_state: EnvironmentState):
    """
    Remove a host from the environment state.
    
    Args:
        host_id: ID of the host to remove
        environment_state: Current environment state
        
    Returns:
        True if the host was removed, False otherwise
    """
    result = environment_state_service.remove_host(environment_state, host_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Host not found: {host_id}")
    return result

@router.get("/summary")
async def get_environment_summary(environment_state: EnvironmentState):
    """
    Get a summary of the environment state.
    
    Args:
        environment_state: Current environment state
        
    Returns:
        Summary of the environment state
    """
    return environment_state_service.get_environment_summary(environment_state)

@router.get("/text")
async def get_environment_text(environment_state: EnvironmentState):
    """
    Get a text representation of the environment state for LLM prompts.
    
    Args:
        environment_state: Current environment state
        
    Returns:
        Text representation of the environment state
    """
    return {"text": environment_state_service.get_environment_state_text(environment_state)}
