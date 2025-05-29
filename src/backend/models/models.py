"""
Incalmo Models - Data Models for the Application

This module defines the Pydantic models used throughout the application
for data validation and serialization.
"""

from pydantic import BaseModel, Field, field_serializer
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime


class PTESPhase(str, Enum):
    """PTES Framework phases for structured penetration testing."""
    PRE_ENGAGEMENT = "pre_engagement"
    INTELLIGENCE_GATHERING = "intelligence_gathering"
    THREAT_MODELING = "threat_modeling"
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"

class OWASPPhase(str, Enum):
    """OWASP Web Security Testing Guide phases for web application security testing."""
    INFORMATION_GATHERING = "information_gathering"
    CONFIGURATION_TESTING = "configuration_testing"
    IDENTITY_MANAGEMENT = "identity_management"
    AUTHENTICATION_TESTING = "authentication_testing"
    AUTHORIZATION_TESTING = "authorization_testing"
    SESSION_MANAGEMENT = "session_management"
    INPUT_VALIDATION = "input_validation"
    ERROR_HANDLING = "error_handling"
    CRYPTOGRAPHY = "cryptography"
    BUSINESS_LOGIC = "business_logic"
    CLIENT_SIDE = "client_side"


class TaskType(str, Enum):
    """Enum for high-level task types supported by Incalmo."""
    # Network and Host Discovery
    SCAN_NETWORK = "scan_network"
    SCAN_PORT = "scan_port"
    DISCOVER_SERVICES = "discover_services"
    ENUMERATE_USERS = "enumerate_users"
    
    # Vulnerability Assessment
    SCAN_VULNERABILITIES = "scan_vulnerabilities"
    ANALYZE_WEB_APP = "analyze_web_app"
    TEST_DEFAULT_CREDS = "test_default_creds"
    CHECK_MISCONFIGURATIONS = "check_misconfigurations"
    
    # Exploitation and Access
    INFECT_HOST = "infect_host"
    LATERAL_MOVE = "lateral_move"
    ESCALATE_PRIVILEGE = "escalate_privilege"
    BRUTE_FORCE_AUTH = "brute_force_auth"
    EXPLOIT_VULNERABILITY = "exploit_vulnerability"
    
    # Data Operations
    EXFILTRATE_DATA = "exfiltrate_data"
    COLLECT_SYSTEM_INFO = "collect_system_info"
    DUMP_CREDENTIALS = "dump_credentials"
    ACCESS_FILES = "access_files"
    
    # Network Operations
    NETWORK_PIVOTING = "network_pivoting"
    TRAFFIC_ANALYSIS = "traffic_analysis"
    MITM_ATTACK = "mitm_attack"
    
    # Tools Management
    INSTALL_TOOL = "install_tool"
    CHECK_TOOL_AVAILABILITY = "check_tool_availability"
    UPDATE_TOOLS = "update_tools"
    
    # System Operations
    EXECUTE_COMMAND = "execute_command"
    MONITOR_SYSTEM = "monitor_system"
    SETUP_PERSISTENCE = "setup_persistence"
    
    # Action Planning
    PLAN_ACTIONS = "plan_actions"
    VALIDATE_GOAL = "validate_goal"
    FINISHED = "finished"
    
    # PTES Framework Management
    ADVANCE_PTES_PHASE = "advance_ptes_phase"
    REVIEW_PHASE_OBJECTIVES = "review_phase_objectives"
    COMPLETE_PHASE = "complete_phase"
    
    # OWASP Framework tasks
    ADVANCE_OWASP_PHASE = "advance_owasp_phase"
    REVIEW_OWASP_OBJECTIVES = "review_owasp_objectives"
    COMPLETE_OWASP_PHASE = "complete_owasp_phase"


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


class ActionPlan(BaseModel):
    """Model representing an action plan to achieve a goal."""
    id: str = Field(..., description="Unique identifier for the action plan")
    goal: str = Field(..., description="The goal this plan aims to achieve")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="List of planned actions")
    current_action_index: int = Field(0, description="Index of the current action being executed")
    status: str = Field("pending", description="Status of the plan (pending, executing, completed, failed)")
    max_retries: int = Field(3, description="Maximum number of retries per action")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp of plan creation")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp of last plan update")
    
    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, dt: datetime):
        return dt.isoformat()


class TestExecution(BaseModel):
    """Model representing a test execution instance."""
    id: str = Field(..., description="Unique identifier for the test execution")
    name: str = Field(..., description="Name of the test")
    plan_id: str = Field(..., description="ID of the action plan being executed")
    status: str = Field("pending", description="Status of the test (pending, running, completed, failed)")
    start_time: Optional[datetime] = Field(None, description="Start time of the test")
    end_time: Optional[datetime] = Field(None, description="End time of the test")
    results: List[TaskResult] = Field(default_factory=list, description="Results of executed tasks")
    environment_snapshot: Optional[Dict[str, Any]] = Field(None, description="Snapshot of environment state")
    
    @field_serializer('start_time', 'end_time')
    def serialize_dt(self, dt: Optional[datetime]):
        return dt.isoformat() if dt else None


class SessionCreateRequest(BaseModel):
    """Model for session creation request."""
    goal: str = Field(..., description="The cybersecurity goal for this session")
    environment_config: Optional[Dict[str, Any]] = Field(None, description="Optional environment configuration")
    provider: str = Field("anthropic", description="LLM provider to use")
    model: str = Field("claude-3-7-sonnet-20250219", description="Model to use")
    ptes_enabled: bool = Field(False, description="Whether to enable PTES framework")
    owasp_enabled: bool = Field(False, description="Whether to enable OWASP Web Security Testing Guide framework")

class SessionState(BaseModel):
    """Model representing the state of a session."""
    id: str = Field(..., description="Unique identifier for the session")
    environment_state: EnvironmentState = Field(default_factory=EnvironmentState, description="Current state of the environment")
    attack_graph: AttackGraph = Field(default_factory=AttackGraph, description="Current attack graph")
    conversation_history: List[LLMMessage] = Field(default_factory=list, description="History of the conversation with the LLM")
    task_history: List[TaskResult] = Field(default_factory=list, description="History of executed tasks")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp of session creation")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp of last session update")
    goal: Optional[str] = Field(None, description="The current goal for this session")
    action_plans: List[ActionPlan] = Field(default_factory=list, description="Action plans for achieving goals")
    active_tests: List[TestExecution] = Field(default_factory=list, description="Currently active test executions")
    completed_tests: List[TestExecution] = Field(default_factory=list, description="Completed test executions")
    installed_tools: List[str] = Field(default_factory=list, description="List of installed cybersecurity tools")
    provider: str = Field("anthropic", description="LLM provider for this session")
    model: str = Field("claude-3-7-sonnet-20250219", description="Model used for this session")
    autonomous_mode: bool = Field(False, description="Whether the session is running in autonomous mode")
    max_parallel_tests: int = Field(3, description="Maximum number of parallel test executions")
    
    # PTES Framework tracking
    ptes_enabled: bool = Field(False, description="Whether PTES framework is enabled for this session")
    current_ptes_phase: PTESPhase = Field(PTESPhase.PRE_ENGAGEMENT, description="Current PTES framework phase")
    ptes_phase_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of PTES phase progression")
    phase_objectives: Dict[str, List[str]] = Field(default_factory=dict, description="Objectives for each PTES phase")
    phase_findings: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Findings and results from each phase")
    
    # OWASP Framework tracking
    owasp_enabled: bool = Field(False, description="Whether OWASP Web Security Testing Guide framework is enabled for this session")
    current_owasp_phase: OWASPPhase = Field(OWASPPhase.INFORMATION_GATHERING, description="Current OWASP framework phase")
    owasp_phase_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of OWASP phase progression")
    owasp_objectives: Dict[str, List[str]] = Field(default_factory=dict, description="Objectives for each OWASP phase")
    owasp_findings: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Findings and results from each OWASP phase")

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, dt: datetime):
        return dt.isoformat()
