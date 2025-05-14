"""
Tests for the environment state service.

This module contains unit tests for the environment state tracking functionality.
"""

import pytest
from services.environment_service import environment_state_service
from models.models import EnvironmentState, Host, Network

def test_create_initial_environment():
    """Test that initial environments are correctly created."""
    # Create default environment
    environment = environment_state_service.create_initial_environment()
    
    # Check that the environment has the correct structure
    assert environment is not None
    assert len(environment.networks) > 0
    assert len(environment.discovered_hosts) == 0
    assert len(environment.compromised_hosts) == 0
    assert len(environment.exfiltrated_data) == 0
    
    # Create environment with custom config
    custom_config = {
        "type": "enterprise",
        "num_networks": 2,
        "hosts_per_network": 5
    }
    
    custom_environment = environment_state_service.create_initial_environment(custom_config)
    
    # Check that the custom environment has the correct structure
    assert custom_environment is not None
    assert len(custom_environment.networks) == 2
    assert sum(len(network.hosts) for network in custom_environment.networks) == 10

def test_get_host_by_id():
    """Test that hosts can be retrieved by ID."""
    # Create environment with a known host
    environment = environment_state_service.create_initial_environment()
    
    # Add a host to the environment
    host = Host(
        id="test_host",
        ip_address="192.168.1.100",
        hostname="testserver",
        os_type="Linux",
        services=[{"name": "ssh", "port": 22}],
        vulnerabilities=[],
        compromised=False
    )
    
    environment.networks[0].hosts.append(host)
    
    # Get the host by ID
    retrieved_host = environment_state_service.get_host_by_id(environment, "test_host")
    
    # Check that the host was correctly retrieved
    assert retrieved_host is not None
    assert retrieved_host.id == "test_host"
    assert retrieved_host.ip_address == "192.168.1.100"
    assert retrieved_host.hostname == "testserver"
    
    # Try to get a non-existent host
    nonexistent_host = environment_state_service.get_host_by_id(environment, "nonexistent_host")
    
    # Check that None is returned for non-existent hosts
    assert nonexistent_host is None

def test_get_network_by_id():
    """Test that networks can be retrieved by ID."""
    # Create environment
    environment = environment_state_service.create_initial_environment()
    
    # Get the first network's ID
    network_id = environment.networks[0].id
    
    # Get the network by ID
    retrieved_network = environment_state_service.get_network_by_id(environment, network_id)
    
    # Check that the network was correctly retrieved
    assert retrieved_network is not None
    assert retrieved_network.id == network_id
    
    # Try to get a non-existent network
    nonexistent_network = environment_state_service.get_network_by_id(environment, "nonexistent_network")
    
    # Check that None is returned for non-existent networks
    assert nonexistent_network is None

def test_update_host():
    """Test that hosts can be updated."""
    # Create environment with a known host
    environment = environment_state_service.create_initial_environment()
    
    # Add a host to the environment
    host = Host(
        id="test_host",
        ip_address="192.168.1.100",
        hostname="testserver",
        os_type="Linux",
        services=[{"name": "ssh", "port": 22}],
        vulnerabilities=[],
        compromised=False
    )
    
    environment.networks[0].hosts.append(host)
    
    # Update the host
    updated_host = Host(
        id="test_host",
        ip_address="192.168.1.100",
        hostname="testserver",
        os_type="Linux",
        services=[{"name": "ssh", "port": 22}],
        vulnerabilities=[],
        compromised=True,
        access_level="user"
    )
    
    result = environment_state_service.update_host(environment, updated_host)
    
    # Check that the update was successful
    assert result is True
    
    # Get the updated host
    retrieved_host = environment_state_service.get_host_by_id(environment, "test_host")
    
    # Check that the host was correctly updated
    assert retrieved_host is not None
    assert retrieved_host.compromised is True
    assert retrieved_host.access_level == "user"
    
    # Try to update a non-existent host
    nonexistent_host = Host(
        id="nonexistent_host",
        ip_address="192.168.1.200",
        hostname="nonexistent",
        os_type="Linux",
        services=[],
        vulnerabilities=[],
        compromised=False
    )
    
    result = environment_state_service.update_host(environment, nonexistent_host)
    
    # Check that the update failed
    assert result is False

def test_add_host():
    """Test that hosts can be added to networks."""
    # Create environment
    environment = environment_state_service.create_initial_environment()
    
    # Get the first network's ID
    network_id = environment.networks[0].id
    
    # Create a new host
    new_host = Host(
        id="new_host",
        ip_address="192.168.1.200",
        hostname="newserver",
        os_type="Linux",
        services=[{"name": "http", "port": 80}],
        vulnerabilities=[],
        compromised=False
    )
    
    # Add the host to the network
    result = environment_state_service.add_host(environment, network_id, new_host)
    
    # Check that the addition was successful
    assert result is True
    
    # Get the added host
    retrieved_host = environment_state_service.get_host_by_id(environment, "new_host")
    
    # Check that the host was correctly added
    assert retrieved_host is not None
    assert retrieved_host.id == "new_host"
    assert retrieved_host.ip_address == "192.168.1.200"
    
    # Try to add a host to a non-existent network
    result = environment_state_service.add_host(environment, "nonexistent_network", new_host)
    
    # Check that the addition failed
    assert result is False

def test_remove_host():
    """Test that hosts can be removed."""
    # Create environment with a known host
    environment = environment_state_service.create_initial_environment()
    
    # Add a host to the environment
    host = Host(
        id="test_host",
        ip_address="192.168.1.100",
        hostname="testserver",
        os_type="Linux",
        services=[{"name": "ssh", "port": 22}],
        vulnerabilities=[],
        compromised=False
    )
    
    environment.networks[0].hosts.append(host)
    
    # Remove the host
    result = environment_state_service.remove_host(environment, "test_host")
    
    # Check that the removal was successful
    assert result is True
    
    # Try to get the removed host
    retrieved_host = environment_state_service.get_host_by_id(environment, "test_host")
    
    # Check that the host was correctly removed
    assert retrieved_host is None
    
    # Try to remove a non-existent host
    result = environment_state_service.remove_host(environment, "nonexistent_host")
    
    # Check that the removal failed
    assert result is False

def test_get_environment_summary():
    """Test that environment summaries are correctly generated."""
    # Create environment
    environment = environment_state_service.create_initial_environment()
    
    # Get summary
    summary = environment_state_service.get_environment_summary(environment)
    
    # Check that the summary has the correct structure
    assert summary is not None
    assert "networks" in summary
    assert "total_hosts" in summary
    assert "discovered_hosts" in summary
    assert "compromised_hosts" in summary
    assert "exfiltrated_data" in summary

def test_get_environment_state_text():
    """Test that environment state text representations are correctly generated."""
    # Create environment
    environment = environment_state_service.create_initial_environment()
    
    # Get text representation
    text = environment_state_service.get_environment_state_text(environment)
    
    # Check that the text contains important information
    assert text is not None
    assert "Network" in text
    assert "Hosts" in text
    assert "Discovered Hosts" in text
    assert "Compromised Hosts" in text
    assert "Exfiltrated Data" in text
