"""
Integration tests for the core functionality of Incalmo.

This module contains integration tests that verify the interaction between
different components of the system.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from core import create_session, process_llm_message, execute_task
from models.models import TaskType, LLMMessage, LLMResponse

# Mock the LLM service
@pytest.fixture
def mock_llm_service():
    with patch('core.generate_response') as mock_generate:
        # Configure the mock to return a predefined response
        mock_generate.return_value = LLMResponse(
            content="<action>\n{\n  \"task\": \"scan_network\",\n  \"parameters\": {\n    \"network\": \"192.168.1.0/24\",\n    \"scan_type\": \"basic\"\n  }\n}\n</action>\n\nI'll scan the network to discover hosts and services.",
            task_type="scan_network",
            task_parameters={"network": "192.168.1.0/24", "scan_type": "basic"}
        )
        yield mock_generate

# Mock the task service
@pytest.fixture
def mock_task_service():
    with patch('core.task_translation_service.execute_task') as mock_execute:
        # Configure the mock to return a successful task result
        mock_execute.return_value = MagicMock(
            success=True,
            task_type=TaskType.SCAN_NETWORK,
            result={"network": "192.168.1.0/24", "hosts_found": 3},
            environment_state=MagicMock(
                networks=[MagicMock()],
                discovered_hosts=["host1", "host2", "host3"],
                compromised_hosts=[],
                exfiltrated_data=[]
            )
        )
        yield mock_execute

@pytest.mark.asyncio
async def test_create_session():
    """Test that sessions are correctly created."""
    # Create a session
    session = await create_session("Gain access to the database server and exfiltrate customer data")
    
    # Check that the session has the correct structure
    assert session is not None
    assert session.id is not None
    assert session.environment_state is not None
    assert session.attack_graph is not None
    assert len(session.conversation_history) == 1
    assert session.conversation_history[0].role == "system"
    assert len(session.task_history) == 0

@pytest.mark.asyncio
async def test_process_llm_message(mock_llm_service, mock_task_service):
    """Test that user messages are correctly processed by the LLM and tasks are executed."""
    # Create a session
    session = await create_session("Gain access to the database server and exfiltrate customer data")
    session_id = session.id
    
    # Process a user message
    llm_response, task_result = await process_llm_message(session_id, "Scan the network for vulnerable hosts.")
    
    # Check that the LLM response is correct
    assert llm_response is not None
    assert llm_response.content is not None
    assert llm_response.task_type == "scan_network"
    assert llm_response.task_parameters == {"network": "192.168.1.0/24", "scan_type": "basic"}
    
    # Check that the task was executed
    assert task_result is not None
    assert task_result.success is True
    assert task_result.task_type == TaskType.SCAN_NETWORK
    
    # Check that the session was updated
    session = await get_session(session_id)
    assert len(session.conversation_history) == 3  # system + user + assistant
    assert session.conversation_history[1].role == "user"
    assert session.conversation_history[2].role == "assistant"
    assert len(session.task_history) == 1

@pytest.mark.asyncio
async def test_execute_task(mock_task_service):
    """Test that tasks are correctly executed in the context of a session."""
    # Create a session
    session = await create_session("Gain access to the database server and exfiltrate customer data")
    session_id = session.id
    
    # Execute a task
    task_result = await execute_task(
        session_id,
        "scan_network",
        {"network": "192.168.1.0/24", "scan_type": "basic"}
    )
    
    # Check that the task result is correct
    assert task_result is not None
    assert task_result.success is True
    assert task_result.task_type == TaskType.SCAN_NETWORK
    
    # Check that the session was updated
    session = await get_session(session_id)
    assert len(session.task_history) == 1
    assert session.environment_state.discovered_hosts == ["host1", "host2", "host3"]

@pytest.mark.asyncio
async def test_end_to_end_attack_sequence(mock_llm_service, mock_task_service):
    """Test a complete attack sequence from start to finish."""
    # Create a session
    session = await create_session("Gain access to the database server and exfiltrate customer data")
    session_id = session.id
    
    # Configure the LLM mock to return different responses for different messages
    responses = [
        # Scan network
        LLMResponse(
            content="<action>\n{\n  \"task\": \"scan_network\",\n  \"parameters\": {\n    \"network\": \"192.168.1.0/24\",\n    \"scan_type\": \"basic\"\n  }\n}\n</action>\n\nI'll scan the network to discover hosts and services.",
            task_type="scan_network",
            task_parameters={"network": "192.168.1.0/24", "scan_type": "basic"}
        ),
        # Infect host
        LLMResponse(
            content="<action>\n{\n  \"task\": \"infect_host\",\n  \"parameters\": {\n    \"host_id\": \"host2\",\n    \"vulnerability\": \"CVE-2021-12345\"\n  }\n}\n</action>\n\nI'll attempt to exploit the vulnerability on the webserver.",
            task_type="infect_host",
            task_parameters={"host_id": "host2", "vulnerability": "CVE-2021-12345"}
        ),
        # Lateral movement
        LLMResponse(
            content="<action>\n{\n  \"task\": \"lateral_move\",\n  \"parameters\": {\n    \"source_host_id\": \"host2\",\n    \"target_host_id\": \"host3\",\n    \"method\": \"credential_reuse\"\n  }\n}\n</action>\n\nI'll attempt to move laterally from the webserver to the database server.",
            task_type="lateral_move",
            task_parameters={"source_host_id": "host2", "target_host_id": "host3", "method": "credential_reuse"}
        ),
        # Escalate privileges
        LLMResponse(
            content="<action>\n{\n  \"task\": \"escalate_privilege\",\n  \"parameters\": {\n    \"host_id\": \"host3\",\n    \"method\": \"kernel_exploit\"\n  }\n}\n</action>\n\nI'll attempt to escalate privileges on the database server.",
            task_type="escalate_privilege",
            task_parameters={"host_id": "host3", "method": "kernel_exploit"}
        ),
        # Exfiltrate data
        LLMResponse(
            content="<action>\n{\n  \"task\": \"exfiltrate_data\",\n  \"parameters\": {\n    \"host_id\": \"host3\",\n    \"data_type\": \"customer_data\"\n  }\n}\n</action>\n\nI'll exfiltrate customer data from the database server.",
            task_type="exfiltrate_data",
            task_parameters={"host_id": "host3", "data_type": "customer_data"}
        ),
        # Finish
        LLMResponse(
            content="<finished>\n{\n  \"message\": \"Attack completed successfully. Exfiltrated customer data from the database server.\"\n}\n</finished>\n\nI've successfully completed the attack. I gained access to the database server and exfiltrated customer data.",
            task_type=None,
            task_parameters=None
        )
    ]
    
    mock_llm_service.side_effect = responses
    
    # Configure the task service mock to update the environment state appropriately
    def mock_execute_side_effect(task_type, parameters, environment_state):
        result = MagicMock(success=True, task_type=task_type)
        
        if task_type == TaskType.SCAN_NETWORK:
            environment_state.discovered_hosts = ["host1", "host2", "host3"]
            result.result = {"network": parameters["network"], "hosts_found": 3}
        elif task_type == TaskType.INFECT_HOST:
            environment_state.compromised_hosts.append(parameters["host_id"])
            result.result = {"host_id": parameters["host_id"], "vulnerability": parameters["vulnerability"]}
        elif task_type == TaskType.LATERAL_MOVE:
            environment_state.compromised_hosts.append(parameters["target_host_id"])
            result.result = {"source_host_id": parameters["source_host_id"], "target_host_id": parameters["target_host_id"]}
        elif task_type == TaskType.ESCALATE_PRIVILEGE:
            result.result = {"host_id": parameters["host_id"], "method": parameters["method"]}
        elif task_type == TaskType.EXFILTRATE_DATA:
            environment_state.exfiltrated_data.append({"type": parameters["data_type"], "host_id": parameters["host_id"]})
            result.result = {"host_id": parameters["host_id"], "data_type": parameters["data_type"]}
        
        result.environment_state = environment_state
        return result
    
    mock_task_service.side_effect = mock_execute_side_effect
    
    # Execute the attack sequence
    messages = [
        "Scan the network for vulnerable hosts.",
        "Exploit the vulnerability on the webserver.",
        "Move laterally to the database server.",
        "Escalate privileges on the database server.",
        "Exfiltrate customer data from the database server.",
        "Finish the attack."
    ]
    
    for message in messages:
        llm_response, task_result = await process_llm_message(session_id, message)
    
    # Check the final state
    session = await get_session(session_id)
    assert len(session.conversation_history) == 13  # system + 6 user + 6 assistant
    assert len(session.task_history) == 5  # 5 tasks (no task for the finish message)
    assert len(session.environment_state.discovered_hosts) == 3
    assert len(session.environment_state.compromised_hosts) == 2  # host2 and host3
    assert len(session.environment_state.exfiltrated_data) == 1
    assert session.environment_state.exfiltrated_data[0]["type"] == "customer_data"
    assert session.environment_state.exfiltrated_data[0]["host_id"] == "host3"

# Helper function to get a session
async def get_session(session_id):
    """Get a session by ID."""
    from core import active_sessions
    return active_sessions.get(session_id)
