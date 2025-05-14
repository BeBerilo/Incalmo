"""
Attack Graph Router

This module defines the API routes for attack graph generation and management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from models.models import AttackGraph, EnvironmentState
from services.attack_graph_service import attack_graph_service

router = APIRouter()

@router.post("/generate", response_model=AttackGraph)
async def generate_attack_graph(environment_state: EnvironmentState):
    """
    Generate an attack graph based on the current environment state.
    
    Args:
        environment_state: Current state of the environment
        
    Returns:
        Generated attack graph
    """
    try:
        attack_graph = attack_graph_service.generate_attack_graph(environment_state)
        return attack_graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating attack graph: {str(e)}")

@router.post("/paths")
async def find_attack_paths(attack_graph: AttackGraph, source_id: str, target_id: str):
    """
    Find all possible attack paths between two nodes in the attack graph.
    
    Args:
        attack_graph: Attack graph
        source_id: ID of the source node
        target_id: ID of the target node
        
    Returns:
        List of attack paths, where each path is a list of node IDs
    """
    try:
        paths = attack_graph_service.find_attack_paths(attack_graph, source_id, target_id)
        return {"paths": paths}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding attack paths: {str(e)}")

@router.post("/text")
async def get_attack_graph_text(attack_graph: AttackGraph, environment_state: EnvironmentState):
    """
    Get a text representation of the attack graph for LLM prompts.
    
    Args:
        attack_graph: Attack graph
        environment_state: Current state of the environment
        
    Returns:
        Text representation of the attack graph
    """
    try:
        text = attack_graph_service.get_attack_graph_text(attack_graph, environment_state)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating attack graph text: {str(e)}")
