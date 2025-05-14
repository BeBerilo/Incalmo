"""
Tests for the attack graph service.

This module contains unit tests for the attack graph generation and management functionality.
"""

import pytest
import networkx as nx
from services.attack_graph_service import attack_graph_service
from models.models import EnvironmentState, Host, Network, AttackGraph

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
                    compromised=True,
                    access_level="user"
                ),
                Host(
                    id="host2",
                    ip_address="192.168.1.2",
                    hostname="webserver",
                    os_type="Linux",
                    services=[{"name": "http", "port": 80}, {"name": "https", "port": 443}],
                    vulnerabilities=[{"id": "CVE-2021-12345", "name": "Apache Vulnerability"}],
                    compromised=False
                ),
                Host(
                    id="host3",
                    ip_address="192.168.1.3",
                    hostname="database",
                    os_type="Linux",
                    services=[{"name": "mysql", "port": 3306}],
                    vulnerabilities=[{"id": "CVE-2021-67890", "name": "MySQL Vulnerability"}],
                    compromised=False
                )
            ]
        )
    ],
    discovered_hosts=["host1", "host2", "host3"],
    compromised_hosts=["host1"],
    exfiltrated_data=[]
)

def test_generate_attack_graph():
    """Test that attack graphs are correctly generated from environment state."""
    # Generate attack graph
    attack_graph = attack_graph_service.generate_attack_graph(test_environment)
    
    # Check that the attack graph has the correct structure
    assert attack_graph is not None
    assert len(attack_graph.nodes) > 0
    assert len(attack_graph.edges) > 0
    
    # Check that all hosts are represented in the graph
    host_nodes = [node for node in attack_graph.nodes if node.type == "host"]
    assert len(host_nodes) == 3
    
    # Check that vulnerabilities are represented in the graph
    vuln_nodes = [node for node in attack_graph.nodes if node.type == "vulnerability"]
    assert len(vuln_nodes) > 0
    
    # Check that the compromised host is marked as such
    host1_node = next((node for node in host_nodes if node.id == "host_host1"), None)
    assert host1_node is not None
    assert host1_node.properties.get("compromised") is True

def test_find_attack_paths():
    """Test that attack paths are correctly found between nodes."""
    # Generate attack graph
    attack_graph = attack_graph_service.generate_attack_graph(test_environment)
    
    # Find paths from host1 to host3
    host1_id = next((node.id for node in attack_graph.nodes if node.type == "host" and "host1" in node.id), None)
    host3_id = next((node.id for node in attack_graph.nodes if node.type == "host" and "host3" in node.id), None)
    
    assert host1_id is not None
    assert host3_id is not None
    
    paths = attack_graph_service.find_attack_paths(attack_graph, host1_id, host3_id)
    
    # Check that at least one path exists
    assert len(paths) > 0
    
    # Check that the first path starts with host1 and ends with host3
    assert paths[0][0] == host1_id
    assert paths[0][-1] == host3_id

def test_get_attack_graph_text():
    """Test that attack graphs are correctly converted to text representation."""
    # Generate attack graph
    attack_graph = attack_graph_service.generate_attack_graph(test_environment)
    
    # Get text representation
    text = attack_graph_service.get_attack_graph_text(attack_graph, test_environment)
    
    # Check that the text contains important information
    assert "gateway (192.168.1.1)" in text
    assert "webserver (192.168.1.2)" in text
    assert "database (192.168.1.3)" in text
    assert "CVE-2021-12345" in text
    assert "CVE-2021-67890" in text
    assert "compromised" in text.lower()

def test_attack_graph_with_empty_environment():
    """Test that attack graph generation handles empty environments gracefully."""
    empty_environment = EnvironmentState(
        networks=[],
        discovered_hosts=[],
        compromised_hosts=[],
        exfiltrated_data=[]
    )
    
    # Generate attack graph
    attack_graph = attack_graph_service.generate_attack_graph(empty_environment)
    
    # Check that an empty graph was created
    assert attack_graph is not None
    assert len(attack_graph.nodes) == 0
    assert len(attack_graph.edges) == 0

def test_attack_graph_with_single_host():
    """Test that attack graph generation works with a single host."""
    single_host_environment = EnvironmentState(
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
                    )
                ]
            )
        ],
        discovered_hosts=["host1"],
        compromised_hosts=[],
        exfiltrated_data=[]
    )
    
    # Generate attack graph
    attack_graph = attack_graph_service.generate_attack_graph(single_host_environment)
    
    # Check that the graph has the correct structure
    assert attack_graph is not None
    assert len(attack_graph.nodes) > 0
    
    # Check that the host is represented in the graph
    host_nodes = [node for node in attack_graph.nodes if node.type == "host"]
    assert len(host_nodes) == 1
    assert host_nodes[0].id == "host_host1"
