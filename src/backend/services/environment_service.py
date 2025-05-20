"""
Environment State Service

This module handles the tracking and updating of the environment state,
including networks, hosts, services, and vulnerabilities.
"""

from typing import Dict, List, Any, Optional, Union
import uuid
from models.models import Host, Network, EnvironmentState

class EnvironmentStateService:
    """
    Service for managing the environment state.
    """
    
    def __init__(self):
        """Initialize the environment state service."""
        pass
    
    def create_initial_environment(self, config: Dict[str, Any] = None) -> EnvironmentState:
        """
        Create an initial environment state based on the provided configuration.
        
        Args:
            config: Optional configuration for the environment
            
        Returns:
            Initial environment state
        """

        if not config:
            # Create a default environment for testing
            return self._create_default_environment()

        # Support simple config shortcut using num_networks and hosts_per_network
        if "networks" not in config:
            num_networks = int(config.get("num_networks", 1))
            hosts_per_network = int(config.get("hosts_per_network", 3))

            networks = []
            for net_idx in range(num_networks):
                hosts = []
                for host_idx in range(hosts_per_network):
                    host_id = f"net{net_idx+1}_host{host_idx+1}"
                    ip_address = f"192.168.{net_idx}.{host_idx+1}"
                    host = Host(
                        id=host_id,
                        ip_address=ip_address,
                        hostname=f"host{host_idx+1}",
                        os_type="Linux",
                        services=[{"name": "ssh", "port": 22}],
                        vulnerabilities=[],
                        compromised=False,
                    )
                    hosts.append(host)

                network = Network(
                    id=f"network{net_idx+1}",
                    name=f"Network {net_idx+1}",
                    cidr=f"192.168.{net_idx}.0/24",
                    hosts=hosts,
                )
                networks.append(network)

            return EnvironmentState(
                networks=networks,
                current_host=None,
                discovered_hosts=[],
                compromised_hosts=[],
                exfiltrated_data=[],
            )
        
        # Create environment from config
        networks = []
        for network_config in config.get("networks", []):
            hosts = []
            for host_config in network_config.get("hosts", []):
                host = Host(
                    id=host_config.get("id", str(uuid.uuid4())),
                    ip_address=host_config.get("ip_address", ""),
                    hostname=host_config.get("hostname"),
                    os_type=host_config.get("os_type"),
                    services=host_config.get("services", []),
                    vulnerabilities=host_config.get("vulnerabilities", []),
                    compromised=host_config.get("compromised", False),
                    access_level=host_config.get("access_level")
                )
                hosts.append(host)
            
            network = Network(
                id=network_config.get("id", str(uuid.uuid4())),
                name=network_config.get("name", ""),
                cidr=network_config.get("cidr", ""),
                hosts=hosts
            )
            networks.append(network)
        
        return EnvironmentState(
            networks=networks,
            current_host=config.get("current_host"),
            discovered_hosts=config.get("discovered_hosts", []),
            compromised_hosts=config.get("compromised_hosts", []),
            exfiltrated_data=config.get("exfiltrated_data", [])
        )
    
    def _create_default_environment(self) -> EnvironmentState:
        """
        Create a default environment for testing.
        
        Returns:
            Default environment state
        """
        # Create a simple network with a few hosts
        hosts = [
            Host(
                id="host1",
                ip_address="192.168.1.1",
                hostname="gateway",
                os_type="Linux",
                services=[
                    {"name": "ssh", "port": 22, "version": "OpenSSH 8.2"},
                    {"name": "http", "port": 80, "version": "Apache 2.4.41"}
                ],
                vulnerabilities=[
                    {"name": "CVE-2021-12345", "service": "http", "description": "Remote code execution in Apache"}
                ]
            ),
            Host(
                id="host2",
                ip_address="192.168.1.2",
                hostname="webserver",
                os_type="Linux",
                services=[
                    {"name": "ssh", "port": 22, "version": "OpenSSH 8.2"},
                    {"name": "http", "port": 80, "version": "Apache 2.4.41"},
                    {"name": "https", "port": 443, "version": "Apache 2.4.41"}
                ],
                vulnerabilities=[
                    {"name": "CVE-2021-23456", "service": "http", "description": "SQL injection in web application"}
                ]
            ),
            Host(
                id="host3",
                ip_address="192.168.1.3",
                hostname="database",
                os_type="Linux",
                services=[
                    {"name": "ssh", "port": 22, "version": "OpenSSH 8.2"},
                    {"name": "mysql", "port": 3306, "version": "MySQL 8.0.23"}
                ],
                vulnerabilities=[
                    {"name": "CVE-2021-34567", "service": "mysql", "description": "Privilege escalation in MySQL"}
                ]
            )
        ]
        
        network = Network(
            id="network1",
            name="Internal Network",
            cidr="192.168.1.0/24",
            hosts=hosts
        )
        
        return EnvironmentState(
            networks=[network],
            current_host=None,
            discovered_hosts=[],
            compromised_hosts=[],
            exfiltrated_data=[]
        )
    
    def get_host_by_id(self, environment_state: EnvironmentState, host_id: str) -> Optional[Host]:
        """
        Get a host by its ID.
        
        Args:
            environment_state: Current environment state
            host_id: ID of the host to find
            
        Returns:
            Host if found, None otherwise
        """
        for network in environment_state.networks:
            for host in network.hosts:
                if host.id == host_id:
                    return host
        return None
    
    def get_network_by_id(self, environment_state: EnvironmentState, network_id: str) -> Optional[Network]:
        """
        Get a network by its ID.
        
        Args:
            environment_state: Current environment state
            network_id: ID of the network to find
            
        Returns:
            Network if found, None otherwise
        """
        for network in environment_state.networks:
            if network.id == network_id:
                return network
        return None
    
    def update_host(self, environment_state: EnvironmentState, host: Host) -> bool:
        """
        Update a host in the environment state.
        
        Args:
            environment_state: Current environment state
            host: Updated host
            
        Returns:
            True if the host was updated, False otherwise
        """
        for network in environment_state.networks:
            for i, existing_host in enumerate(network.hosts):
                if existing_host.id == host.id:
                    network.hosts[i] = host
                    return True
        return False
    
    def add_host(self, environment_state: EnvironmentState, network_id: str, host: Host) -> bool:
        """
        Add a host to a network in the environment state.
        
        Args:
            environment_state: Current environment state
            network_id: ID of the network to add the host to
            host: Host to add
            
        Returns:
            True if the host was added, False otherwise
        """
        for network in environment_state.networks:
            if network.id == network_id:
                network.hosts.append(host)
                return True
        return False
    
    def remove_host(self, environment_state: EnvironmentState, host_id: str) -> bool:
        """
        Remove a host from the environment state.
        
        Args:
            environment_state: Current environment state
            host_id: ID of the host to remove
            
        Returns:
            True if the host was removed, False otherwise
        """
        for network in environment_state.networks:
            for i, host in enumerate(network.hosts):
                if host.id == host_id:
                    network.hosts.pop(i)
                    
                    # Update related lists
                    if host_id in environment_state.discovered_hosts:
                        environment_state.discovered_hosts.remove(host_id)
                    if host_id in environment_state.compromised_hosts:
                        environment_state.compromised_hosts.remove(host_id)
                    if environment_state.current_host == host_id:
                        environment_state.current_host = None
                    
                    return True
        return False
    
    def get_environment_summary(self, environment_state: EnvironmentState) -> Dict[str, Any]:
        """
        Get a summary of the environment state.
        
        Args:
            environment_state: Current environment state
            
        Returns:
            Summary of the environment state
        """
        total_hosts = sum(len(network.hosts) for network in environment_state.networks)
        
        return {
            "networks": len(environment_state.networks),
            "total_hosts": total_hosts,
            "discovered_hosts": len(environment_state.discovered_hosts),
            "compromised_hosts": len(environment_state.compromised_hosts),
            "current_host": environment_state.current_host,
            # Keep key name consistent with API tests
            "exfiltrated_data": len(environment_state.exfiltrated_data)
        }
    
    def get_environment_state_text(self, environment_state: EnvironmentState) -> str:
        """
        Get a text representation of the environment state for LLM prompts.
        
        Args:
            environment_state: Current environment state
            
        Returns:
            Text representation of the environment state
        """
        lines = []
        
        # Add networks
        lines.append(f"Networks ({len(environment_state.networks)}):")
        for network in environment_state.networks:
            lines.append(f"- Network: {network.name} ({network.cidr})")
        
        # Add discovered hosts
        lines.append(f"\nDiscovered Hosts ({len(environment_state.discovered_hosts)}):")
        for host_id in environment_state.discovered_hosts:
            host = self.get_host_by_id(environment_state, host_id)
            if host:
                services_str = ", ".join([f"{s['name']}:{s['port']}" for s in (host.services or [])])
                lines.append(f"- Host: {host.hostname or 'unknown'} ({host.ip_address}), OS: {host.os_type or 'unknown'}, Services: {services_str}")
        
        # Add compromised hosts
        lines.append(f"\nCompromised Hosts ({len(environment_state.compromised_hosts)}):")
        for host_id in environment_state.compromised_hosts:
            host = self.get_host_by_id(environment_state, host_id)
            if host:
                lines.append(f"- Host: {host.hostname or 'unknown'} ({host.ip_address}), Access Level: {host.access_level}")
        
        # Add current host
        if environment_state.current_host:
            host = self.get_host_by_id(environment_state, environment_state.current_host)
            if host:
                lines.append(f"\nCurrent Host: {host.hostname or 'unknown'} ({host.ip_address}), Access Level: {host.access_level}")
        else:
            lines.append("\nCurrent Host: None")
        
        # Add exfiltrated data
        lines.append(f"\nExfiltrated Data ({len(environment_state.exfiltrated_data)}):")
        for data in environment_state.exfiltrated_data:
            lines.append(f"- {data['data_type']} from {data['ip_address']}")
        
        return "\n".join(lines)

# Create a singleton instance
environment_state_service = EnvironmentStateService()
