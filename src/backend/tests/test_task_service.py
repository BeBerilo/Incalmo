"""
Tests for the task translation service.

This module contains unit tests for the task translation service functionality.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from services.task_service import task_translation_service
from models.models import TaskType, TaskResult, EnvironmentState, Host, Network

# Test data
test_environment = EnvironmentState(
    networks=[
        Network(
            id="network1",
            name="Internal Network",
            cidr="192.168.1.0/24",
            hosts=[
                Host(
                    id="host1",
                    ip_address="192.168.1.1",
                    hostname="gateway",
                    os_type="Linux",
                    services=[{"name": "ssh", "port": 22}],
                    vulnerabilities=[],
                    compromised=False
                ),
                Host(
                    id="host2",
                    ip_address="192.168.1.2",
                    hostname="webserver",
                    os_type="Linux",
                    services=[{"name": "http", "port": 80}, {"name": "https", "port": 443}],
                    vulnerabilities=[{"id": "CVE-2021-12345", "name": "Apache Vulnerability"}],
                    compromised=False
                )
            ]
        )
    ],
    discovered_hosts=[],
    compromised_hosts=[],
    exfiltrated_data=[]
)

@pytest.mark.asyncio
async def test_scan_network():
    """Test the scan_network task."""
    # Parameters for the scan_network task
    parameters = {
        "network": "192.168.1.0/24",
        "scan_type": "basic"
    }
    
    # Execute the task
    result = await task_translation_service.execute_task(
        TaskType.SCAN_NETWORK,
        parameters,
        test_environment
    )
    
    # Check that the task was successful
    assert result.success
    assert result.task_type == TaskType.SCAN_NETWORK
    
    # Check that the environment was updated correctly
    assert len(result.environment_state.discovered_hosts) > 0
    assert "host1" in result.environment_state.discovered_hosts
    assert "host2" in result.environment_state.discovered_hosts

@pytest.mark.asyncio
async def test_infect_host():
    """Test the infect_host task."""
    # First, discover the hosts
    scan_parameters = {
        "network": "192.168.1.0/24",
        "scan_type": "basic"
    }
    scan_result = await task_translation_service.execute_task(
        TaskType.SCAN_NETWORK,
        scan_parameters,
        test_environment
    )
    
    # Parameters for the infect_host task
    parameters = {
        "host_id": "host2",
        "vulnerability": "CVE-2021-12345"
    }
    
    # Execute the task
    result = await task_translation_service.execute_task(
        TaskType.INFECT_HOST,
        parameters,
        scan_result.environment_state
    )
    
    # Check that the task was successful
    assert result.success
    assert result.task_type == TaskType.INFECT_HOST
    
    # Check that the environment was updated correctly
    assert "host2" in result.environment_state.compromised_hosts
    
    # Get the host from the environment
    host2 = None
    for network in result.environment_state.networks:
        for host in network.hosts:
            if host.id == "host2":
                host2 = host
                break
    
    assert host2 is not None
    assert host2.compromised

@pytest.mark.asyncio
async def test_lateral_move():
    """Test the lateral_move task."""
    # First, discover and infect a host
    scan_parameters = {
        "network": "192.168.1.0/24",
        "scan_type": "basic"
    }
    scan_result = await task_translation_service.execute_task(
        TaskType.SCAN_NETWORK,
        scan_parameters,
        test_environment
    )
    
    infect_parameters = {
        "host_id": "host2",
        "vulnerability": "CVE-2021-12345"
    }
    infect_result = await task_translation_service.execute_task(
        TaskType.INFECT_HOST,
        infect_parameters,
        scan_result.environment_state
    )
    
    # Parameters for the lateral_move task
    parameters = {
        "source_host_id": "host2",
        "target_host_id": "host1",
        "method": "credential_reuse"
    }
    
    # Execute the task
    result = await task_translation_service.execute_task(
        TaskType.LATERAL_MOVE,
        parameters,
        infect_result.environment_state
    )
    
    # Check that the task was successful
    assert result.success
    assert result.task_type == TaskType.LATERAL_MOVE
    
    # Check that the environment was updated correctly
    assert "host1" in result.environment_state.compromised_hosts
    assert "host2" in result.environment_state.compromised_hosts
    
    # Get the host from the environment
    host1 = None
    for network in result.environment_state.networks:
        for host in network.hosts:
            if host.id == "host1":
                host1 = host
                break
    
    assert host1 is not None
    assert host1.compromised

@pytest.mark.asyncio
async def test_escalate_privilege():
    """Test the escalate_privilege task."""
    # First, discover, infect, and move laterally
    scan_parameters = {
        "network": "192.168.1.0/24",
        "scan_type": "basic"
    }
    scan_result = await task_translation_service.execute_task(
        TaskType.SCAN_NETWORK,
        scan_parameters,
        test_environment
    )
    
    infect_parameters = {
        "host_id": "host2",
        "vulnerability": "CVE-2021-12345"
    }
    infect_result = await task_translation_service.execute_task(
        TaskType.INFECT_HOST,
        infect_parameters,
        scan_result.environment_state
    )
    
    # Parameters for the escalate_privilege task
    parameters = {
        "host_id": "host2",
        "method": "kernel_exploit"
    }
    
    # Execute the task
    result = await task_translation_service.execute_task(
        TaskType.ESCALATE_PRIVILEGE,
        parameters,
        infect_result.environment_state
    )
    
    # Check that the task was successful
    assert result.success
    assert result.task_type == TaskType.ESCALATE_PRIVILEGE
    
    # Check that the environment was updated correctly
    host2 = None
    for network in result.environment_state.networks:
        for host in network.hosts:
            if host.id == "host2":
                host2 = host
                break
    
    assert host2 is not None
    assert host2.access_level == "admin"

@pytest.mark.asyncio
async def test_exfiltrate_data():
    """Test the exfiltrate_data task."""
    # First, discover, infect, and escalate privileges
    scan_parameters = {
        "network": "192.168.1.0/24",
        "scan_type": "basic"
    }
    scan_result = await task_translation_service.execute_task(
        TaskType.SCAN_NETWORK,
        scan_parameters,
        test_environment
    )
    
    infect_parameters = {
        "host_id": "host2",
        "vulnerability": "CVE-2021-12345"
    }
    infect_result = await task_translation_service.execute_task(
        TaskType.INFECT_HOST,
        infect_parameters,
        scan_result.environment_state
    )
    
    escalate_parameters = {
        "host_id": "host2",
        "method": "kernel_exploit"
    }
    escalate_result = await task_translation_service.execute_task(
        TaskType.ESCALATE_PRIVILEGE,
        escalate_parameters,
        infect_result.environment_state
    )
    
    # Parameters for the exfiltrate_data task
    parameters = {
        "host_id": "host2",
        "data_type": "credentials"
    }
    
    # Execute the task
    result = await task_translation_service.execute_task(
        TaskType.EXFILTRATE_DATA,
        parameters,
        escalate_result.environment_state
    )
    
    # Check that the task was successful
    assert result.success
    assert result.task_type == TaskType.EXFILTRATE_DATA
    
    # Check that the environment was updated correctly
    assert len(result.environment_state.exfiltrated_data) > 0
    assert result.environment_state.exfiltrated_data[0]["type"] == "credentials"
    assert result.environment_state.exfiltrated_data[0]["host_id"] == "host2"

@pytest.mark.asyncio
async def test_task_failure_handling():
    """Test that task failures are handled correctly."""
    # Parameters for a task that should fail (trying to infect a host that doesn't exist)
    parameters = {
        "host_id": "nonexistent_host",
        "vulnerability": "CVE-2021-12345"
    }
    
    # Execute the task
    result = await task_translation_service.execute_task(
        TaskType.INFECT_HOST,
        parameters,
        test_environment
    )
    
    # Check that the task failed
    assert not result.success
    assert result.task_type == TaskType.INFECT_HOST
    assert result.error is not None
    assert "Host not found" in result.error
