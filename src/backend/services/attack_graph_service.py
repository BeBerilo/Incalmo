"""
Attack Graph Service

This module handles the generation and management of attack graphs,
providing a structured representation of attack paths to help LLMs
select actions relevant to multistage attacks.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx
from models.models import AttackNode, AttackEdge, AttackGraph, Host, Network, EnvironmentState
from services.environment_service import environment_state_service

class AttackGraphService:
    """
    Service for generating and managing attack graphs.
    """
    
    def __init__(self):
        """Initialize the attack graph service."""
        pass
    
    def generate_attack_graph(self, environment_state: EnvironmentState) -> AttackGraph:
        """
        Generate an attack graph based on the current environment state.
        
        Args:
            environment_state: Current state of the environment
            
        Returns:
            Generated attack graph
        """
        # Create a directed graph using NetworkX
        G = nx.DiGraph()
        
        # Track nodes and edges to build the response
        nodes = []
        edges = []
        
        # Add nodes for each host
        for network in environment_state.networks:
            for host in network.hosts:
                # Only include hosts that have been discovered
                if host.id in environment_state.discovered_hosts:
                    # Add host node
                    host_node_id = f"host_{host.id}"
                    host_label = f"{host.hostname or host.ip_address}"
                    host_node = AttackNode(
                        id=host_node_id,
                        type="host",
                        label=host_label,
                        properties={
                            "ip_address": host.ip_address,
                            "hostname": host.hostname,
                            "os_type": host.os_type,
                            "compromised": host.compromised,
                            "access_level": host.access_level
                        }
                    )
                    nodes.append(host_node)
                    G.add_node(host_node_id, **host_node.properties)
                    
                    # Add service nodes for each service
                    if host.services:
                        for i, service in enumerate(host.services):
                            service_node_id = f"service_{host.id}_{i}"
                            service_label = f"{service['name']}:{service['port']}"
                            service_node = AttackNode(
                                id=service_node_id,
                                type="service",
                                label=service_label,
                                properties={
                                    "name": service["name"],
                                    "port": service["port"],
                                    "version": service.get("version", "unknown")
                                }
                            )
                            nodes.append(service_node)
                            G.add_node(service_node_id, **service_node.properties)
                            
                            # Add edge from host to service
                            host_service_edge = AttackEdge(
                                source=host_node_id,
                                target=service_node_id,
                                type="has_service",
                                properties={}
                            )
                            edges.append(host_service_edge)
                            G.add_edge(host_node_id, service_node_id, type="has_service")
                    
                    # Add vulnerability nodes for each vulnerability
                    if host.vulnerabilities:
                        for i, vuln in enumerate(host.vulnerabilities):
                            vuln_node_id = f"vuln_{host.id}_{i}"
                            vuln_label = vuln["name"]
                            vuln_node = AttackNode(
                                id=vuln_node_id,
                                type="vulnerability",
                                label=vuln_label,
                                properties={
                                    "name": vuln["name"],
                                    "description": vuln.get("description", ""),
                                    "service": vuln.get("service", "")
                                }
                            )
                            nodes.append(vuln_node)
                            G.add_node(vuln_node_id, **vuln_node.properties)
                            
                            # Add edge from host to vulnerability
                            host_vuln_edge = AttackEdge(
                                source=host_node_id,
                                target=vuln_node_id,
                                type="has_vulnerability",
                                properties={}
                            )
                            edges.append(host_vuln_edge)
                            G.add_edge(host_node_id, vuln_node_id, type="has_vulnerability")
                            
                            # If vulnerability is associated with a service, add edge from service to vulnerability
                            if "service" in vuln:
                                for i, service in enumerate(host.services or []):
                                    if service["name"] == vuln["service"]:
                                        service_node_id = f"service_{host.id}_{i}"
                                        service_vuln_edge = AttackEdge(
                                            source=service_node_id,
                                            target=vuln_node_id,
                                            type="has_vulnerability",
                                            properties={}
                                        )
                                        edges.append(service_vuln_edge)
                                        G.add_edge(service_node_id, vuln_node_id, type="has_vulnerability")
        
        # Add attack path edges based on network connectivity and compromised status
        self._add_attack_path_edges(G, environment_state, edges)
        
        return AttackGraph(nodes=nodes, edges=edges)
    
    def _add_attack_path_edges(self, G: nx.DiGraph, environment_state: EnvironmentState, edges: List[AttackEdge]):
        """
        Add edges representing possible attack paths to the graph.
        
        Args:
            G: NetworkX graph
            environment_state: Current state of the environment
            edges: List of edges to update
        """
        # Get all host nodes
        host_nodes = [n for n in G.nodes if n.startswith("host_")]
        
        # Get all vulnerability nodes
        vuln_nodes = [n for n in G.nodes if n.startswith("vuln_")]
        
        # For each compromised host, add attack paths to other hosts
        for host_id in environment_state.compromised_hosts:
            source_host_node = f"host_{host_id}"
            if source_host_node not in G:
                continue
            
            source_host = environment_state_service.get_host_by_id(environment_state, host_id)
            if not source_host:
                continue
            
            # For each discovered but not compromised host, add potential attack paths
            for target_host_id in environment_state.discovered_hosts:
                if target_host_id in environment_state.compromised_hosts:
                    continue  # Skip already compromised hosts
                
                target_host_node = f"host_{target_host_id}"
                if target_host_node not in G:
                    continue
                
                target_host = environment_state_service.get_host_by_id(environment_state, target_host_id)
                if not target_host:
                    continue
                
                # Add lateral movement edge
                lateral_edge = AttackEdge(
                    source=source_host_node,
                    target=target_host_node,
                    type="lateral_movement",
                    properties={
                        "method": "network_access"
                    }
                )
                edges.append(lateral_edge)
                G.add_edge(source_host_node, target_host_node, type="lateral_movement", method="network_access")
                
                # Add exploit edges from compromised host to vulnerabilities on target host
                for vuln_node in vuln_nodes:
                    if vuln_node.startswith(f"vuln_{target_host_id}_"):
                        exploit_edge = AttackEdge(
                            source=source_host_node,
                            target=vuln_node,
                            type="can_exploit",
                            properties={}
                        )
                        edges.append(exploit_edge)
                        G.add_edge(source_host_node, vuln_node, type="can_exploit")
        
        # For each vulnerability, add edges to represent successful exploitation
        for vuln_node in vuln_nodes:
            # Extract host_id from vuln_node (format: vuln_host_id_index)
            parts = vuln_node.split("_")
            if len(parts) >= 3:
                host_id = parts[1]
                host_node = f"host_{host_id}"
                
                # Add edge from vulnerability to host representing compromise
                compromise_edge = AttackEdge(
                    source=vuln_node,
                    target=host_node,
                    type="compromises",
                    properties={
                        "access_level": "user"  # Default to user-level access
                    }
                )
                edges.append(compromise_edge)
                G.add_edge(vuln_node, host_node, type="compromises", access_level="user")
    
    def find_attack_paths(self, attack_graph: AttackGraph, source_id: str, target_id: str) -> List[List[str]]:
        """
        Find all possible attack paths between two nodes in the attack graph.
        
        Args:
            attack_graph: Attack graph
            source_id: ID of the source node
            target_id: ID of the target node
            
        Returns:
            List of attack paths, where each path is a list of node IDs
        """
        # Create a NetworkX graph from the attack graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in attack_graph.nodes:
            G.add_node(node.id, **node.properties)
        
        # Add edges
        for edge in attack_graph.edges:
            G.add_edge(edge.source, edge.target, **edge.properties)
        
        # Find all simple paths from source to target
        try:
            paths = list(nx.all_simple_paths(G, source_id, target_id))
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def get_attack_graph_text(self, attack_graph: AttackGraph, environment_state: EnvironmentState) -> str:
        """
        Get a text representation of the attack graph for LLM prompts.
        
        Args:
            attack_graph: Attack graph
            environment_state: Current state of the environment
            
        Returns:
            Text representation of the attack graph
        """
        lines = []
        
        # Add current position
        if environment_state.current_host:
            host = environment_state_service.get_host_by_id(environment_state, environment_state.current_host)
            if host:
                lines.append(f"Current Position: {host.hostname or host.ip_address} ({host.ip_address})")
                lines.append(f"Access Level: {host.access_level or 'none'}")
                lines.append("")
        
        # Add available attack paths
        lines.append("Available Attack Paths:")
        
        # Group nodes by host
        hosts = {}
        for node in attack_graph.nodes:
            if node.type == "host":
                host_id = node.id.replace("host_", "")
                hosts[host_id] = {
                    "node": node,
                    "vulnerabilities": [],
                    "services": []
                }
        
        # Add vulnerabilities and services to hosts
        for node in attack_graph.nodes:
            if node.type == "vulnerability":
                host_id = node.id.split("_")[1]
                if host_id in hosts:
                    hosts[host_id]["vulnerabilities"].append(node)
            elif node.type == "service":
                host_id = node.id.split("_")[1]
                if host_id in hosts:
                    hosts[host_id]["services"].append(node)
        
        # Add attack paths for each compromised host
        for host_id in environment_state.compromised_hosts:
            if host_id in hosts:
                host = hosts[host_id]
                host_node = host["node"]
                lines.append(f"From {host_node.label} ({host_node.properties.get('ip_address', '')}):")
                
                # Find potential targets
                targets = []
                for edge in attack_graph.edges:
                    if edge.source == host_node.id and edge.type == "lateral_movement":
                        target_id = edge.target.replace("host_", "")
                        if target_id in hosts:
                            targets.append(hosts[target_id])
                
                if targets:
                    for target in targets:
                        target_node = target["node"]
                        lines.append(f"  - To {target_node.label} ({target_node.properties.get('ip_address', '')}):")
                        
                        # List vulnerabilities
                        if target["vulnerabilities"]:
                            lines.append("    Vulnerabilities:")
                            for vuln in target["vulnerabilities"]:
                                lines.append(f"      - {vuln.label}: {vuln.properties.get('description', '')}")
                        
                        # List services
                        if target["services"]:
                            lines.append("    Services:")
                            for service in target["services"]:
                                lines.append(f"      - {service.label} ({service.properties.get('version', 'unknown')})")
                else:
                    lines.append("  No available targets")
        
        # If no compromised hosts, suggest initial targets
        if not environment_state.compromised_hosts:
            lines.append("Initial Targets:")
            for host_id, host in hosts.items():
                if host_id in environment_state.discovered_hosts:
                    host_node = host["node"]
                    lines.append(f"  - {host_node.label} ({host_node.properties.get('ip_address', '')}):")
                    
                    # List vulnerabilities
                    if host["vulnerabilities"]:
                        lines.append("    Vulnerabilities:")
                        for vuln in host["vulnerabilities"]:
                            lines.append(f"      - {vuln.label}: {vuln.properties.get('description', '')}")
                    
                    # List services
                    if host["services"]:
                        lines.append("    Services:")
                        for service in host["services"]:
                            lines.append(f"      - {service.label} ({service.properties.get('version', 'unknown')})")
        
        return "\n".join(lines)

# Create a singleton instance
attack_graph_service = AttackGraphService()
