"""
Tests for the LLM service integration with Claude Sonnet 3.7.

This module contains unit tests for the LLM service functionality.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from services.llm_service import generate_response, create_system_prompt
from models.models import LLMMessage, LLMResponse

# Test data
test_messages = [
    LLMMessage(role="system", content="You are an AI assistant for network attacks."),
    LLMMessage(role="user", content="Scan the network for vulnerable hosts.")
]

expected_response = LLMResponse(
    content="<action>\n{\n  \"task\": \"scan_network\",\n  \"parameters\": {\n    \"network\": \"192.168.1.0/24\",\n    \"scan_type\": \"basic\"\n  }\n}\n</action>\n\nI'll scan the network to discover hosts and services.",
    task_type="scan_network",
    task_parameters={"network": "192.168.1.0/24", "scan_type": "basic"}
)

# Mock the Anthropic API client
class MockAnthropicClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or "mock_api_key"
    
    async def messages(self, **kwargs):
        return {
            "content": [
                {
                    "type": "text",
                    "text": expected_response.content
                }
            ]
        }

@pytest.mark.asyncio
@patch('services.llm_service.anthropic.Anthropic', return_value=MockAnthropicClient())
async def test_generate_response(mock_anthropic):
    """Test that the LLM service correctly generates responses and extracts tasks."""
    response = await generate_response(test_messages)
    
    # Check that the response content matches
    assert response.content == expected_response.content
    
    # Check that the task was correctly extracted
    assert response.task_type == expected_response.task_type
    assert response.task_parameters == expected_response.task_parameters
    
    # Verify the Anthropic client was called with the right parameters
    mock_anthropic.assert_called_once()

@pytest.mark.asyncio
async def test_create_system_prompt():
    """Test that the system prompt is correctly created."""
    goal = "Gain access to the database server and exfiltrate customer data"
    environment_state = "Network: 192.168.1.0/24\nHosts: gateway (192.168.1.1), webserver (192.168.1.2), database (192.168.1.3)"
    attack_graph = "Potential paths: gateway -> webserver -> database"
    
    prompt = create_system_prompt(goal, environment_state, attack_graph)
    
    # Check that the prompt contains all the necessary information
    assert goal in prompt
    assert environment_state in prompt
    assert attack_graph in prompt
    assert "You are an AI assistant" in prompt
    assert "task format" in prompt.lower()

@pytest.mark.asyncio
@patch('services.llm_service.anthropic.Anthropic')
async def test_generate_response_error_handling(mock_anthropic):
    """Test that errors from the Anthropic API are properly handled."""
    # Setup the mock to raise an exception
    mock_client = MagicMock()
    mock_client.messages.side_effect = Exception("API Error")
    mock_anthropic.return_value = mock_client
    
    # Test that the exception is properly caught and re-raised
    with pytest.raises(Exception) as excinfo:
        await generate_response(test_messages)
    
    assert "Error generating LLM response" in str(excinfo.value)

@pytest.mark.asyncio
@patch('services.llm_service.anthropic.Anthropic', return_value=MockAnthropicClient())
async def test_task_extraction_with_invalid_format(mock_anthropic):
    """Test that the task extraction handles invalid formats gracefully."""
    # Override the mock response to return an invalid format
    mock_client = MockAnthropicClient()
    mock_client.messages = MagicMock(return_value=asyncio.Future())
    mock_client.messages.return_value.set_result({
        "content": [
            {
                "type": "text",
                "text": "I'll help you scan the network."  # No action block
            }
        ]
    })
    mock_anthropic.return_value = mock_client
    
    response = await generate_response(test_messages)
    
    # Check that the response content is preserved
    assert response.content == "I'll help you scan the network."
    
    # Check that no task was extracted
    assert response.task_type is None
    assert response.task_parameters is None
