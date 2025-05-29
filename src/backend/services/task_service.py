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
            # Network and Host Discovery
            TaskType.SCAN_NETWORK: self._handle_scan_network,
            TaskType.SCAN_PORT: self._handle_scan_port,
            TaskType.DISCOVER_SERVICES: self._handle_discover_services,
            TaskType.ENUMERATE_USERS: self._handle_enumerate_users,
            
            # Vulnerability Assessment
            TaskType.SCAN_VULNERABILITIES: self._handle_scan_vulnerabilities,
            TaskType.ANALYZE_WEB_APP: self._handle_analyze_web_app,
            TaskType.TEST_DEFAULT_CREDS: self._handle_test_default_creds,
            TaskType.CHECK_MISCONFIGURATIONS: self._handle_check_misconfigurations,
            
            # Exploitation and Access
            TaskType.INFECT_HOST: self._handle_infect_host,
            TaskType.LATERAL_MOVE: self._handle_lateral_move,
            TaskType.ESCALATE_PRIVILEGE: self._handle_escalate_privilege,
            TaskType.BRUTE_FORCE_AUTH: self._handle_brute_force_auth,
            TaskType.EXPLOIT_VULNERABILITY: self._handle_exploit_vulnerability,
            
            # Data Operations
            TaskType.EXFILTRATE_DATA: self._handle_exfiltrate_data,
            TaskType.COLLECT_SYSTEM_INFO: self._handle_collect_system_info,
            TaskType.DUMP_CREDENTIALS: self._handle_dump_credentials,
            TaskType.ACCESS_FILES: self._handle_access_files,
            
            # Network Operations
            TaskType.NETWORK_PIVOTING: self._handle_network_pivoting,
            TaskType.TRAFFIC_ANALYSIS: self._handle_traffic_analysis,
            TaskType.MITM_ATTACK: self._handle_mitm_attack,
            
            # Tools Management
            TaskType.INSTALL_TOOL: self._handle_install_tool,
            TaskType.CHECK_TOOL_AVAILABILITY: self._handle_check_tool_availability,
            TaskType.UPDATE_TOOLS: self._handle_update_tools,
            
            # System Operations
            TaskType.EXECUTE_COMMAND: self._handle_execute_command,
            TaskType.MONITOR_SYSTEM: self._handle_monitor_system,
            TaskType.SETUP_PERSISTENCE: self._handle_setup_persistence,
            
            # Action Planning
            TaskType.PLAN_ACTIONS: self._handle_plan_actions,
            TaskType.VALIDATE_GOAL: self._handle_validate_goal,
            TaskType.FINISHED: self._handle_finished,
            
            # PTES Framework Management
            TaskType.ADVANCE_PTES_PHASE: self._handle_advance_ptes_phase,
            TaskType.REVIEW_PHASE_OBJECTIVES: self._handle_review_phase_objectives,
            TaskType.COMPLETE_PHASE: self._handle_complete_phase,
            
            # OWASP Framework Management
            TaskType.ADVANCE_OWASP_PHASE: self._handle_advance_owasp_phase,
            TaskType.REVIEW_OWASP_OBJECTIVES: self._handle_review_owasp_objectives,
            TaskType.COMPLETE_OWASP_PHASE: self._handle_complete_owasp_phase
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
        Handle the scan_network task by executing the LLM's specified command or providing intelligent defaults.
        
        Args:
            parameters: Parameters for the task (e.g., command, target, method)
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
        
        # Check if the LLM provided a specific command to execute
        if "command" in parameters:
            # Execute the specific command requested by the LLM
            return await self._handle_execute_command(parameters, environment_state)
        
        # Extract parameters
        target_network = parameters.get("network", parameters.get("target", ""))
        scan_type = parameters.get("scan_type", "basic")
        method = parameters.get("method", "auto")  # Allow LLM to specify method
        tool = parameters.get("tool", "auto")      # Allow LLM to specify tool
        
        # If LLM specified a specific tool, try to use it
        cmd = None
        if tool == "nmap" or (tool == "auto"):
            # Check if nmap is available
            nmap_check = await asyncio.create_subprocess_shell(
                "which nmap", stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            nmap_stdout, _ = await nmap_check.communicate()
            
            if nmap_check.returncode == 0:
                # Build nmap command based on parameters
                if scan_type == "aggressive":
                    cmd = f"nmap -A -T4 {target_network}"
                elif scan_type == "comprehensive":
                    cmd = f"nmap -sS -sV -O -A {target_network}"
                else:
                    cmd = f"nmap -sn {target_network}"
        
        # Fallback options if nmap not available or specified
        if not cmd and (tool == "ping" or tool == "auto"):
            if target_network:
                try:
                    network = ipaddress.IPv4Network(target_network, strict=False)
                    base_ip = str(network.network_address).split('.')
                    base_ip.pop()
                    base = '.'.join(base_ip)
                    
                    # Ping sweep for first 10 addresses
                    commands = [f"ping -c 1 -W 1 {base}.{i}" for i in range(1, 11)]
                    cmd = " & ".join(commands)
                except:
                    cmd = "ping -c 1 -W 1 192.168.1.1"
        
        if not cmd:
            return TaskResult(
                task_type=TaskType.SCAN_NETWORK,
                success=False,
                error=f"Unable to determine appropriate scanning method for tool: {tool}",
                result={"available_tools": ["nmap", "ping"], "requested_tool": tool}
            )
        
        try:
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
            # Log the command being executed for visibility
            print(f"[COMMAND EXECUTION] Running: {command}")
            
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
                    "output": combined_output,
                    "command_executed": f"[COMMAND EXECUTION] Running: {command}"
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

    async def _handle_scan_port(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Handle port scanning task."""
        if "command" in parameters:
            return await self._handle_execute_command(parameters, environment_state)
        
        host = parameters.get("host", parameters.get("target", ""))
        port_range = parameters.get("port_range", "1-1000")
        tool = parameters.get("tool", "nmap")
        
        if not host:
            return TaskResult(
                task_type=TaskType.SCAN_PORT,
                success=False,
                error="No host specified for port scan",
                result={"suggestion": "Provide 'host' or 'target' parameter or use 'command' parameter for custom command"}
            )
        
        # Simple command construction - let LLM specify more complex commands if needed
        if tool == "nmap":
            cmd = f"nmap -p {port_range} {host}"
        else:
            cmd = f"nc -zv {host} {port_range.split('-')[0]}-{port_range.split('-')[1]}"
        
        return await self._handle_execute_command({"command": cmd}, environment_state)
    
    async def _handle_discover_services(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Handle service discovery task."""
        if "command" in parameters:
            return await self._handle_execute_command(parameters, environment_state)
        
        host = parameters.get("host", parameters.get("target", ""))
        if not host:
            return TaskResult(
                task_type=TaskType.DISCOVER_SERVICES,
                success=False,
                error="No host specified for service discovery",
                result={"suggestion": "Provide 'host' or 'target' parameter or use 'command' parameter"}
            )
        
        cmd = f"nmap -sV {host}"
        return await self._handle_execute_command({"command": cmd}, environment_state)
    
    # Generic handler for unimplemented tasks
    async def _create_generic_handler(self, task_type: TaskType):
        """Create a generic handler for tasks that delegates to execute_command."""
        async def generic_handler(parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
            if "command" in parameters:
                return await self._handle_execute_command(parameters, environment_state)
            else:
                return TaskResult(
                    task_type=task_type,
                    success=False,
                    error=f"Task {task_type.value} requires a specific 'command' parameter",
                    result={
                        "suggestion": f"Use execute_command task with a specific command, or provide a 'command' parameter to {task_type.value}",
                        "example": f'{{"task": "{task_type.value}", "parameters": {{"command": "your_command_here"}}}}'
                    }
                )
        return generic_handler
    
    # Add generic handlers for all missing task types
    async def _handle_enumerate_users(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.ENUMERATE_USERS))(parameters, environment_state)
    
    async def _handle_scan_vulnerabilities(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.SCAN_VULNERABILITIES))(parameters, environment_state)
    
    async def _handle_analyze_web_app(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.ANALYZE_WEB_APP))(parameters, environment_state)
    
    async def _handle_test_default_creds(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.TEST_DEFAULT_CREDS))(parameters, environment_state)
    
    async def _handle_check_misconfigurations(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.CHECK_MISCONFIGURATIONS))(parameters, environment_state)
    
    async def _handle_brute_force_auth(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.BRUTE_FORCE_AUTH))(parameters, environment_state)
    
    async def _handle_exploit_vulnerability(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.EXPLOIT_VULNERABILITY))(parameters, environment_state)
    
    async def _handle_collect_system_info(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.COLLECT_SYSTEM_INFO))(parameters, environment_state)
    
    async def _handle_dump_credentials(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.DUMP_CREDENTIALS))(parameters, environment_state)
    
    async def _handle_access_files(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.ACCESS_FILES))(parameters, environment_state)
    
    async def _handle_network_pivoting(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.NETWORK_PIVOTING))(parameters, environment_state)
    
    async def _handle_traffic_analysis(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.TRAFFIC_ANALYSIS))(parameters, environment_state)
    
    async def _handle_mitm_attack(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.MITM_ATTACK))(parameters, environment_state)
    
    async def _handle_install_tool(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Handle tool installation - supports macOS package managers."""
        if "command" in parameters:
            return await self._handle_execute_command(parameters, environment_state)
        
        tool_name = parameters.get("tool", parameters.get("name", ""))
        if not tool_name:
            return TaskResult(
                task_type=TaskType.INSTALL_TOOL,
                success=False,
                error="No tool specified for installation",
                result={"suggestion": "Provide 'tool' or 'name' parameter"}
            )
        
        # Try different package managers on macOS
        managers = [
            f"brew install {tool_name}",
            f"port install {tool_name}",
            f"pip3 install {tool_name}",
            f"npm install -g {tool_name}"
        ]
        
        for cmd in managers:
            result = await self._handle_execute_command({"command": f"which {cmd.split()[0]}"}, environment_state)
            if result.success:
                return await self._handle_execute_command({"command": cmd}, environment_state)
        
        return TaskResult(
            task_type=TaskType.INSTALL_TOOL,
            success=False,
            error="No package manager found",
            result={"suggestion": "Install brew, macports, pip, or npm first"}
        )
    
    async def _handle_check_tool_availability(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Check if a tool is available."""
        if "command" in parameters:
            return await self._handle_execute_command(parameters, environment_state)
        
        tool_name = parameters.get("tool", parameters.get("name", ""))
        if not tool_name:
            return TaskResult(
                task_type=TaskType.CHECK_TOOL_AVAILABILITY,
                success=False,
                error="No tool specified",
                result={"suggestion": "Provide 'tool' or 'name' parameter"}
            )
        
        cmd = f"which {tool_name}"
        return await self._handle_execute_command({"command": cmd}, environment_state)
    
    async def _handle_update_tools(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.UPDATE_TOOLS))(parameters, environment_state)
    
    async def _handle_monitor_system(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.MONITOR_SYSTEM))(parameters, environment_state)
    
    async def _handle_setup_persistence(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        return await (await self._create_generic_handler(TaskType.SETUP_PERSISTENCE))(parameters, environment_state)
    
    async def _handle_plan_actions(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Handle action planning."""
        goal = parameters.get("goal", "")
        steps = parameters.get("steps", [])
        
        return TaskResult(
            task_type=TaskType.PLAN_ACTIONS,
            success=True,
            result={
                "goal": goal,
                "planned_steps": steps,
                "message": "Action plan created. Use other tasks to execute the planned steps."
            }
        )
    
    async def _handle_validate_goal(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Validate if goal has been achieved."""
        goal = parameters.get("goal", "")
        criteria = parameters.get("criteria", [])
        
        return TaskResult(
            task_type=TaskType.VALIDATE_GOAL,
            success=True,
            result={
                "goal": goal,
                "criteria": criteria,
                "validation_status": "manual_review_required",
                "message": "Goal validation completed. Review results to determine if goal is achieved."
            }
        )
    
    async def _handle_advance_ptes_phase(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Advance to the next PTES phase."""
        from models.models import PTESPhase
        
        # Mapping from human-readable names to enum values
        phase_name_mapping = {
            "pre-engagement": PTESPhase.PRE_ENGAGEMENT,
            "pre engagement": PTESPhase.PRE_ENGAGEMENT,
            "pre-engagement interactions": PTESPhase.PRE_ENGAGEMENT,
            "pre engagement interactions": PTESPhase.PRE_ENGAGEMENT,
            "preengagement": PTESPhase.PRE_ENGAGEMENT,
            "intelligence gathering": PTESPhase.INTELLIGENCE_GATHERING,
            "intelligence-gathering": PTESPhase.INTELLIGENCE_GATHERING,
            "intelligencegathering": PTESPhase.INTELLIGENCE_GATHERING,
            "threat modeling": PTESPhase.THREAT_MODELING,
            "threat-modeling": PTESPhase.THREAT_MODELING,
            "threatmodeling": PTESPhase.THREAT_MODELING,
            "vulnerability analysis": PTESPhase.VULNERABILITY_ANALYSIS,
            "vulnerability-analysis": PTESPhase.VULNERABILITY_ANALYSIS,
            "vulnerabilityanalysis": PTESPhase.VULNERABILITY_ANALYSIS,
            "exploitation": PTESPhase.EXPLOITATION,
            "post-exploitation": PTESPhase.POST_EXPLOITATION,
            "post exploitation": PTESPhase.POST_EXPLOITATION,
            "postexploitation": PTESPhase.POST_EXPLOITATION,
            "reporting": PTESPhase.REPORTING
        }
        
        def normalize_phase_name(phase_name: str) -> str:
            """Convert human-readable phase name to enum value."""
            if not phase_name:
                return "pre_engagement"
            
            # First try direct enum value
            try:
                PTESPhase(phase_name)
                return phase_name
            except ValueError:
                pass
            
            # Try mapping from human-readable names
            normalized = phase_name.lower().strip()
            if normalized in phase_name_mapping:
                return phase_name_mapping[normalized].value
            
            # Fallback to pre_engagement
            return "pre_engagement"
        
        # Get and normalize phase parameters
        current_phase_param = parameters.get("current_phase", "pre_engagement")
        next_phase_param = parameters.get("next_phase", "")
        
        # Also check for direct phase parameter (sometimes LLM passes just "phase")
        if not next_phase_param and "phase" in parameters:
            next_phase_param = parameters.get("phase", "")
        
        current_phase = normalize_phase_name(current_phase_param)
        next_phase = normalize_phase_name(next_phase_param)
        
        print(f"[PTES DEBUG] Received params: current_phase_param='{current_phase_param}', next_phase_param='{next_phase_param}'")
        print(f"[PTES DEBUG] Normalized: current_phase='{current_phase}', next_phase='{next_phase}'")
        
        # Define phase progression
        phase_order = [
            PTESPhase.PRE_ENGAGEMENT,
            PTESPhase.INTELLIGENCE_GATHERING,
            PTESPhase.THREAT_MODELING,
            PTESPhase.VULNERABILITY_ANALYSIS,
            PTESPhase.EXPLOITATION,
            PTESPhase.POST_EXPLOITATION,
            PTESPhase.REPORTING
        ]
        
        try:
            current_idx = phase_order.index(PTESPhase(current_phase))
            if next_phase:
                next_idx = phase_order.index(PTESPhase(next_phase))
            else:
                next_idx = current_idx + 1
            
            if next_idx >= len(phase_order):
                return TaskResult(
                    task_type=TaskType.ADVANCE_PTES_PHASE,
                    success=False,
                    error="Already at final phase (Reporting)",
                    result={"current_phase": current_phase}
                )
            
            new_phase = phase_order[next_idx]
            
            # Define objectives for each phase
            phase_objectives = {
                PTESPhase.PRE_ENGAGEMENT: [
                    "Define assessment scope and objectives",
                    "Establish rules of engagement",
                    "Confirm authorization and legal boundaries"
                ],
                PTESPhase.INTELLIGENCE_GATHERING: [
                    "Perform passive reconnaissance",
                    "Conduct active information gathering",
                    "Map network topology and services"
                ],
                PTESPhase.THREAT_MODELING: [
                    "Identify potential attack vectors",
                    "Analyze threat landscape",
                    "Prioritize attack paths"
                ],
                PTESPhase.VULNERABILITY_ANALYSIS: [
                    "Discover security vulnerabilities",
                    "Classify and prioritize findings",
                    "Assess exploitability"
                ],
                PTESPhase.EXPLOITATION: [
                    "Validate vulnerabilities through controlled exploitation",
                    "Demonstrate business impact",
                    "Gain initial access where authorized"
                ],
                PTESPhase.POST_EXPLOITATION: [
                    "Assess depth of compromise",
                    "Evaluate privilege escalation potential",
                    "Test lateral movement capabilities"
                ],
                PTESPhase.REPORTING: [
                    "Document all findings with evidence",
                    "Provide remediation recommendations",
                    "Deliver comprehensive assessment report"
                ]
            }
            
            return TaskResult(
                task_type=TaskType.ADVANCE_PTES_PHASE,
                success=True,
                result={
                    "previous_phase": current_phase,
                    "new_phase": new_phase.value,
                    "phase_name": new_phase.value.replace('_', ' ').title(),
                    "objectives": phase_objectives.get(new_phase, []),
                    "message": f"Advanced from {current_phase.replace('_', ' ').title()} to {new_phase.value.replace('_', ' ').title()} phase"
                }
            )
            
        except ValueError as e:
            return TaskResult(
                task_type=TaskType.ADVANCE_PTES_PHASE,
                success=False,
                error=f"Invalid phase: {str(e)}",
                result={"current_phase": current_phase}
            )
    
    async def _handle_review_phase_objectives(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Review current phase objectives and progress."""
        phase = parameters.get("phase", "pre_engagement")
        completed_objectives = parameters.get("completed", [])
        
        return TaskResult(
            task_type=TaskType.REVIEW_PHASE_OBJECTIVES,
            success=True,
            result={
                "phase": phase,
                "phase_name": phase.replace('_', ' ').title(),
                "completed_objectives": completed_objectives,
                "message": "Phase objectives reviewed. Use this information to determine next steps."
            }
        )
    
    async def _handle_complete_phase(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Mark current phase as complete with findings."""
        phase = parameters.get("phase", "")
        findings = parameters.get("findings", {})
        summary = parameters.get("summary", "")
        
        return TaskResult(
            task_type=TaskType.COMPLETE_PHASE,
            success=True,
            result={
                "completed_phase": phase,
                "phase_name": phase.replace('_', ' ').title(),
                "findings": findings,
                "summary": summary,
                "message": f"Phase {phase.replace('_', ' ').title()} completed with findings documented"
            }
        )

    async def _handle_advance_owasp_phase(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Advance to the next OWASP phase."""
        from models.models import OWASPPhase
        
        # Mapping from human-readable names to enum values
        phase_name_mapping = {
            "information gathering": OWASPPhase.INFORMATION_GATHERING,
            "information-gathering": OWASPPhase.INFORMATION_GATHERING,
            "configuration testing": OWASPPhase.CONFIGURATION_TESTING,
            "configuration-testing": OWASPPhase.CONFIGURATION_TESTING,
            "identity management": OWASPPhase.IDENTITY_MANAGEMENT,
            "identity-management": OWASPPhase.IDENTITY_MANAGEMENT,
            "authentication testing": OWASPPhase.AUTHENTICATION_TESTING,
            "authentication-testing": OWASPPhase.AUTHENTICATION_TESTING,
            "authorization testing": OWASPPhase.AUTHORIZATION_TESTING,
            "authorization-testing": OWASPPhase.AUTHORIZATION_TESTING,
            "session management": OWASPPhase.SESSION_MANAGEMENT,
            "session-management": OWASPPhase.SESSION_MANAGEMENT,
            "input validation": OWASPPhase.INPUT_VALIDATION,
            "input-validation": OWASPPhase.INPUT_VALIDATION,
            "error handling": OWASPPhase.ERROR_HANDLING,
            "error-handling": OWASPPhase.ERROR_HANDLING,
            "cryptography": OWASPPhase.CRYPTOGRAPHY,
            "business logic": OWASPPhase.BUSINESS_LOGIC,
            "business-logic": OWASPPhase.BUSINESS_LOGIC,
            "client side": OWASPPhase.CLIENT_SIDE,
            "client-side": OWASPPhase.CLIENT_SIDE,
        }
        
        def normalize_owasp_phase_name(phase_name: str) -> str:
            """Convert human-readable phase name to enum value."""
            if not phase_name:
                return "information_gathering"
            
            # First try direct enum value
            try:
                OWASPPhase(phase_name)
                return phase_name
            except ValueError:
                pass
            
            # Try mapping from human-readable names
            normalized = phase_name.lower().strip()
            if normalized in phase_name_mapping:
                return phase_name_mapping[normalized].value
            
            # Fallback to information_gathering
            return "information_gathering"
        
        current_phase = normalize_owasp_phase_name(parameters.get("current_phase", "information_gathering"))
        next_phase = normalize_owasp_phase_name(parameters.get("next_phase", ""))
        
        print(f"[OWASP DEBUG] Received params: current_phase='{parameters.get('current_phase', '')}', next_phase='{parameters.get('next_phase', '')}'")
        print(f"[OWASP DEBUG] Normalized: current_phase='{current_phase}', next_phase='{next_phase}'")
        
        # Define phase progression
        phase_order = [
            OWASPPhase.INFORMATION_GATHERING,
            OWASPPhase.CONFIGURATION_TESTING,
            OWASPPhase.IDENTITY_MANAGEMENT,
            OWASPPhase.AUTHENTICATION_TESTING,
            OWASPPhase.AUTHORIZATION_TESTING,
            OWASPPhase.SESSION_MANAGEMENT,
            OWASPPhase.INPUT_VALIDATION,
            OWASPPhase.ERROR_HANDLING,
            OWASPPhase.CRYPTOGRAPHY,
            OWASPPhase.BUSINESS_LOGIC,
            OWASPPhase.CLIENT_SIDE
        ]
        
        try:
            current_idx = phase_order.index(OWASPPhase(current_phase))
            if next_phase:
                next_idx = phase_order.index(OWASPPhase(next_phase))
            else:
                next_idx = current_idx + 1
            
            if next_idx >= len(phase_order):
                return TaskResult(
                    task_type=TaskType.ADVANCE_OWASP_PHASE,
                    success=False,
                    error="Already at final phase (Client Side Testing)",
                    result={"current_phase": current_phase}
                )
            
            new_phase = phase_order[next_idx]
            
            print(f"[OWASP DEBUG] Advanced to OWASP phase: {new_phase.value}")
            
            return TaskResult(
                task_type=TaskType.ADVANCE_OWASP_PHASE,
                success=True,
                result={
                    "previous_phase": current_phase,
                    "new_phase": new_phase.value,
                    "phase_name": new_phase.value.replace('_', ' ').title(),
                    "message": f"Advanced from {current_phase.replace('_', ' ').title()} to {new_phase.value.replace('_', ' ').title()} phase"
                }
            )
            
        except ValueError as e:
            return TaskResult(
                task_type=TaskType.ADVANCE_OWASP_PHASE,
                success=False,
                error=f"Invalid phase: '{current_phase}' or '{next_phase}' is not a valid OWASPPhase",
                result={"current_phase": current_phase, "next_phase": next_phase}
            )

    async def _handle_review_owasp_objectives(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Review current OWASP phase objectives."""
        phase = parameters.get("phase", "information_gathering")
        
        # Define objectives for each OWASP phase
        phase_objectives = {
            "information_gathering": [
                "Conduct search engine discovery and reconnaissance",
                "Fingerprint web server and framework",
                "Review webserver metafiles for information leakage",
                "Enumerate applications on webserver",
                "Review webpage comments and metadata for information leakage",
                "Identify application entry points"
            ],
            "configuration_testing": [
                "Test network/infrastructure configuration",
                "Test application platform configuration",
                "Test file extensions handling for sensitive information",
                "Review old, backup and unreferenced files for sensitive information",
                "Test for administrative interfaces",
                "Test HTTP methods and verify HTTPS configuration"
            ],
            "identity_management": [
                "Test role definitions and user registration process",
                "Test account provisioning and de-provisioning process",
                "Test for account enumeration and guessable user accounts",
                "Test for weak or unenforced username policy"
            ],
            "authentication_testing": [
                "Test for credentials transported over encrypted channel",
                "Test for default credentials and weak password policy",
                "Test for weak lock out mechanism and bypassing authentication schema",
                "Test for vulnerable remember password and browser cache weaknesses",
                "Test for weak password change or reset functionalities"
            ],
            "authorization_testing": [
                "Test directory traversal and file include",
                "Test for bypassing authorization schema and privilege escalation",
                "Test for insecure direct object references"
            ],
            "session_management": [
                "Test for session management schema and cookies attributes",
                "Test for session fixation and exposed session variables",
                "Test for Cross Site Request Forgery (CSRF)",
                "Test for logout functionality and session timeout"
            ],
            "input_validation": [
                "Test for reflected, stored, and DOM-based Cross Site Scripting",
                "Test for SQL, LDAP, ORM, XML injection",
                "Test for SSI injection, XPath injection, and IMAP/SMTP injection",
                "Test for code injection and command injection",
                "Test for buffer overflow and incubated vulnerability",
                "Test for HTTP splitting/smuggling"
            ],
            "error_handling": [
                "Test for improper error handling and stack traces"
            ],
            "cryptography": [
                "Test for weak SSL/TLS ciphers and certificates",
                "Test for sensitive information sent via unencrypted channels"
            ],
            "business_logic": [
                "Test business logic data validation and integrity checks",
                "Test for the circumvention of work flows",
                "Test defenses against application misuse"
            ],
            "client_side": [
                "Test for DOM manipulation and HTML injection",
                "Test for client side URL redirect and client side resource manipulation"
            ]
        }
        
        objectives = phase_objectives.get(phase, [])
        
        return TaskResult(
            task_type=TaskType.REVIEW_OWASP_OBJECTIVES,
            success=True,
            result={
                "phase": phase,
                "phase_name": phase.replace('_', ' ').title(),
                "objectives": objectives,
                "message": f"Current phase: {phase.replace('_', ' ').title()}. Review objectives and continue testing."
            }
        )

    async def _handle_complete_owasp_phase(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Mark current OWASP phase as complete with findings."""
        phase = parameters.get("phase", "")
        findings = parameters.get("findings", {})
        summary = parameters.get("summary", "")
        
        return TaskResult(
            task_type=TaskType.COMPLETE_OWASP_PHASE,
            success=True,
            result={
                "completed_phase": phase,
                "phase_name": phase.replace('_', ' ').title(),
                "findings": findings,
                "summary": summary,
                "message": f"OWASP Phase {phase.replace('_', ' ').title()} completed with findings documented"
            }
        )

# Create a singleton instance
task_translation_service = TaskTranslationService()
