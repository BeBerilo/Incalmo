"""
Incalmo Models - Data Models for the Application

This module defines the Pydantic models used throughout the application
for data validation and serialization.
"""

from pydantic import BaseModel, Field, field_serializer
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime


class TaskType(str, Enum):
    """Enum for high-level task types supported by Incalmo."""
    SCAN_NETWORK = "scan_network"
    INFECT_HOST = "infect_host"
    LATERAL_MOVE = "lateral_move"
    ESCALATE_PRIVILEGE = "escalate_privilege"
    EXFILTRATE_DATA = "exfiltrate_data"
    EXECUTE_COMMAND = "execute_command"  # Direct terminal command execution
    FINISHED = "finished"


class LLMMessage(BaseModel):
    """Model for messages in the LLM conversation."""
    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: str = Field(..., description="Content of the message")


class LLMRequest(BaseModel):
    """Model for requests to the LLM API."""
    messages: List[LLMMessage] = Field(..., description="List of messages in the conversation")
    max_tokens: Optional[int] = Field(1000, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Temperature for response generation")
    model: str = Field("claude-3-7-sonnet-20250219", description="Model to use for generation")
    provider: str = Field("anthropic", description="LLM provider (anthropic, openai, gemini)")


class LLMResponse(BaseModel):
    """Model for responses from the LLM API."""
    content: str = Field(..., description="Generated content from the LLM")
    task_type: Optional[TaskType] = Field(None, description="Extracted task type if present")
    task_parameters: Optional[Dict[str, Any]] = Field(None, description="Extracted task parameters if present")


class Host(BaseModel):
    """Model representing a host in the environment."""
    id: str = Field(..., description="Unique identifier for the host")
    ip_address: str = Field(..., description="IP address of the host")
    hostname: Optional[str] = Field(None, description="Hostname if known")
    os_type: Optional[str] = Field(None, description="Operating system type if known")
    services: Optional[List[Dict[str, Any]]] = Field(None, description="Services running on the host")
    vulnerabilities: Optional[List[Dict[str, Any]]] = Field(None, description="Known vulnerabilities on the host")
    compromised: bool = Field(False, description="Whether the host is compromised")
    access_level: Optional[str] = Field(None, description="Current access level on the host if compromised")


class Network(BaseModel):
    """Model representing a network in the environment."""
    id: str = Field(..., description="Unique identifier for the network")
    name: str = Field(..., description="Name of the network")
    cidr: str = Field(..., description="CIDR notation for the network")
    hosts: List[Host] = Field(default_factory=list, description="Hosts in the network")


class EnvironmentState(BaseModel):
    """Model representing the current state of the environment."""
    networks: List[Network] = Field(default_factory=list, description="Networks in the environment")
    current_host: Optional[str] = Field(None, description="ID of the current host if any")
    discovered_hosts: List[str] = Field(default_factory=list, description="IDs of discovered hosts")
    compromised_hosts: List[str] = Field(default_factory=list, description="IDs of compromised hosts")
    exfiltrated_data: List[Dict[str, Any]] = Field(default_factory=list, description="Exfiltrated data")


class AttackNode(BaseModel):
    """Model representing a node in the attack graph."""
    id: str = Field(..., description="Unique identifier for the node")
    type: str = Field(..., description="Type of the node (host, service, vulnerability, etc.)")
    label: str = Field(..., description="Label for the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the node")


class AttackEdge(BaseModel):
    """Model representing an edge in the attack graph."""
    source: str = Field(..., description="ID of the source node")
    target: str = Field(..., description="ID of the target node")
    type: str = Field(..., description="Type of the edge (access, exploit, etc.)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the edge")


class AttackGraph(BaseModel):
    """Model representing the attack graph."""
    nodes: List[AttackNode] = Field(default_factory=list, description="Nodes in the attack graph")
    edges: List[AttackEdge] = Field(default_factory=list, description="Edges in the attack graph")


class TaskRequest(BaseModel):
    """Model for task execution requests."""
    task_type: TaskType = Field(..., description="Type of task to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the task")


class TaskResult(BaseModel):
    """Model for task execution results."""
    task_type: TaskType = Field(..., description="Type of task that was executed")
    success: bool = Field(..., description="Whether the task was successful")
    result: Dict[str, Any] = Field(default_factory=dict, description="Result of the task execution")
    error: Optional[str] = Field(None, description="Error message if the task failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the task execution")
    
    @field_serializer('timestamp')
    def serialize_dt(self, dt: datetime):
        return dt.isoformat()


class SessionState(BaseModel):
    """Model representing the state of a session."""
    id: str = Field(..., description="Unique identifier for the session")
    environment_state: EnvironmentState = Field(default_factory=EnvironmentState, description="Current state of the environment")
    attack_graph: AttackGraph = Field(default_factory=AttackGraph, description="Current attack graph")
    conversation_history: List[LLMMessage] = Field(default_factory=list, description="History of the conversation with the LLM")
    task_history: List[TaskResult] = Field(default_factory=list, description="History of executed tasks")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp of session creation")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp of last session update")
    goal: Optional[str] = Field(None, description="The goal for this session if in autonomous mode")
    provider: str = Field("anthropic", description="LLM provider for this session")
    model: str = Field("claude-3-7-sonnet-20250219", description="Model used for this session")

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, dt: datetime):
        return dt.isoformat()
