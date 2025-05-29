"""
Action Planner Service

This module implements an intelligent action planner that can:
- Create action plans to achieve cybersecurity goals
- Execute multiple tests in parallel
- Automatically install required tools
- Persist goals and retry failed actions
- Adapt strategies based on environment feedback
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from models.models import (
    ActionPlan, TestExecution, TaskType, TaskResult, 
    EnvironmentState, SessionState, LLMMessage
)


class ActionPlannerService:
    """
    Intelligent action planner for cybersecurity automation.
    """
    
    def __init__(self, llm_service, task_service):
        """Initialize the action planner service."""
        self.llm_service = llm_service
        self.task_service = task_service
        
        # Tool installation mappings for macOS
        self.tool_install_commands = {
            "nmap": "brew install nmap",
            "nikto": "brew install nikto",
            "hydra": "brew install hydra",
            "metasploit": "brew install --cask metasploit",
            "burpsuite": "brew install --cask burp-suite",
            "wireshark": "brew install --cask wireshark",
            "john": "brew install john",
            "hashcat": "brew install hashcat",
            "sqlmap": "brew install sqlmap",
            "gobuster": "brew install gobuster",
            "dirb": "brew install dirb",
            "masscan": "brew install masscan",
            "zap": "brew install --cask owasp-zap",
            "nessus": "brew install --cask tenable-nessus",
            "aircrack-ng": "brew install aircrack-ng",
            "tcpdump": "brew install tcpdump",
            "netcat": "brew install netcat",
            "socat": "brew install socat",
            "openssh": "brew install openssh",
            "curl": "brew install curl",
            "wget": "brew install wget",
            "jq": "brew install jq",
            "yq": "brew install yq"
        }
        
        # Tool categories for intelligent selection
        self.tool_categories = {
            "network_scanning": ["nmap", "masscan", "rustscan"],
            "vulnerability_scanning": ["nikto", "nessus", "zap"],
            "web_testing": ["burpsuite", "zap", "sqlmap", "gobuster", "dirb"],
            "password_attacks": ["hydra", "john", "hashcat"],
            "exploitation": ["metasploit", "sqlmap"],
            "traffic_analysis": ["wireshark", "tcpdump"],
            "wireless": ["aircrack-ng"],
            "general": ["curl", "wget", "netcat", "socat", "jq"]
        }

    async def create_action_plan(self, goal: str, environment_state: EnvironmentState) -> ActionPlan:
        """
        Create an action plan to achieve the specified goal.
        
        Args:
            goal: The cybersecurity goal to achieve
            environment_state: Current state of the environment
            
        Returns:
            ActionPlan object with planned actions
        """
        plan_id = str(uuid.uuid4())
        
        # Use LLM to analyze the goal and create a plan
        planning_prompt = f"""
        You are an expert cybersecurity automation planner. Create a detailed action plan to achieve this goal:
        
        GOAL: {goal}
        
        CURRENT ENVIRONMENT STATE:
        - Networks discovered: {len(environment_state.networks)}
        - Hosts discovered: {len(environment_state.discovered_hosts)}
        - Hosts compromised: {len(environment_state.compromised_hosts)}
        - Current host: {environment_state.current_host or 'None'}
        
        Available task types:
        {', '.join([task_type.value for task_type in TaskType])}
        
        Create a JSON array of actions, where each action has:
        - task_type: The task type to execute
        - parameters: Parameters for the task
        - description: Human-readable description
        - required_tools: List of tools needed (if any)
        - retry_count: Number of retries attempted (start with 0)
        
        Focus on:
        1. Thorough reconnaissance before exploitation
        2. Tool availability checking and installation
        3. Multiple attack vectors
        4. Proper privilege escalation
        5. Goal validation at the end
        
        Return ONLY the JSON array, no other text.
        """
        
        messages = [
            LLMMessage(role="system", content="You are a cybersecurity automation expert."),
            LLMMessage(role="user", content=planning_prompt)
        ]
        
        try:
            response = await self.llm_service.generate_response(messages)
            
            # Parse the LLM response to extract actions
            import json
            actions_json = response.content.strip()
            
            # Clean up the response if it has markdown formatting
            if actions_json.startswith("```json"):
                actions_json = actions_json.split("```json")[1].split("```")[0].strip()
            elif actions_json.startswith("```"):
                actions_json = actions_json.split("```")[1].split("```")[0].strip()
            
            actions = json.loads(actions_json)
            
            # Validate and enhance actions
            validated_actions = []
            for action in actions:
                if isinstance(action, dict) and "task_type" in action:
                    # Set defaults
                    action.setdefault("parameters", {})
                    action.setdefault("description", f"Execute {action['task_type']}")
                    action.setdefault("required_tools", [])
                    action.setdefault("retry_count", 0)
                    validated_actions.append(action)
            
            return ActionPlan(
                id=plan_id,
                goal=goal,
                actions=validated_actions,
                current_action_index=0,
                status="pending"
            )
            
        except Exception as e:
            # Fallback: create a basic plan
            fallback_actions = [
                {
                    "task_type": "check_tool_availability",
                    "parameters": {"tools": ["nmap", "curl", "netcat"]},
                    "description": "Check availability of basic tools",
                    "required_tools": [],
                    "retry_count": 0
                },
                {
                    "task_type": "scan_network",
                    "parameters": {"target": "192.168.1.0/24", "scan_type": "basic"},
                    "description": "Perform basic network scan",
                    "required_tools": ["nmap"],
                    "retry_count": 0
                },
                {
                    "task_type": "validate_goal",
                    "parameters": {"goal": goal},
                    "description": "Validate if goal has been achieved",
                    "required_tools": [],
                    "retry_count": 0
                }
            ]
            
            return ActionPlan(
                id=plan_id,
                goal=goal,
                actions=fallback_actions,
                current_action_index=0,
                status="pending"
            )

    async def start_test_execution(self, session_state: SessionState, plan: ActionPlan, test_name: str) -> TestExecution:
        """
        Start a new test execution based on an action plan.
        
        Args:
            session_state: Current session state
            plan: The action plan to execute
            test_name: Name for this test execution
            
        Returns:
            TestExecution object
        """
        test_id = str(uuid.uuid4())
        
        test_execution = TestExecution(
            id=test_id,
            name=test_name,
            plan_id=plan.id,
            status="running",
            start_time=datetime.now(),
            environment_snapshot=session_state.environment_state.dict()
        )
        
        # Add to active tests
        session_state.active_tests.append(test_execution)
        
        # Start execution in background
        asyncio.create_task(self._execute_test(session_state, test_execution, plan))
        
        return test_execution

    async def _execute_test(self, session_state: SessionState, test_execution: TestExecution, plan: ActionPlan):
        """
        Execute a test in the background.
        
        Args:
            session_state: Current session state
            test_execution: The test execution to run
            plan: The action plan to execute
        """
        try:
            for i, action in enumerate(plan.actions):
                if plan.current_action_index > i:
                    continue  # Skip already executed actions
                
                # Check if we need to install tools first
                required_tools = action.get("required_tools", [])
                for tool in required_tools:
                    if tool not in session_state.installed_tools:
                        await self._install_tool(tool, session_state)
                
                # Execute the action
                task_result = await self._execute_action(action, session_state.environment_state)
                test_execution.results.append(task_result)
                
                # Update plan progress
                plan.current_action_index = i + 1
                
                # If action failed and we have retries left, retry
                if not task_result.success and action["retry_count"] < plan.max_retries:
                    action["retry_count"] += 1
                    plan.current_action_index = i  # Retry this action
                    continue
                
                # If action failed with no retries left, consider alternative approaches
                if not task_result.success:
                    alternative_action = await self._find_alternative_action(
                        action, session_state.environment_state, plan.goal
                    )
                    if alternative_action:
                        plan.actions.insert(i + 1, alternative_action)
                
                # Check if goal is achieved after each action
                if await self._is_goal_achieved(plan.goal, session_state.environment_state):
                    break
            
            # Mark test as completed
            test_execution.status = "completed"
            test_execution.end_time = datetime.now()
            
            # Move from active to completed tests
            session_state.active_tests = [t for t in session_state.active_tests if t.id != test_execution.id]
            session_state.completed_tests.append(test_execution)
            
            # Update plan status
            if await self._is_goal_achieved(plan.goal, session_state.environment_state):
                plan.status = "completed"
            else:
                plan.status = "failed"
                
        except Exception as e:
            test_execution.status = "failed"
            test_execution.end_time = datetime.now()
            
            # Move from active to completed tests
            session_state.active_tests = [t for t in session_state.active_tests if t.id != test_execution.id]
            session_state.completed_tests.append(test_execution)
            
            plan.status = "failed"

    async def _execute_action(self, action: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """
        Execute a single action.
        
        Args:
            action: The action to execute
            environment_state: Current environment state
            
        Returns:
            TaskResult of the execution
        """
        try:
            task_type = TaskType(action["task_type"])
            parameters = action.get("parameters", {})
            
            # Handle special task types
            if task_type == TaskType.CHECK_TOOL_AVAILABILITY:
                return await self._check_tools_availability(parameters)
            elif task_type == TaskType.INSTALL_TOOL:
                return await self._install_tool_task(parameters)
            elif task_type == TaskType.VALIDATE_GOAL:
                return await self._validate_goal_task(parameters, environment_state)
            else:
                # Execute through task service
                return await self.task_service.execute_task(task_type, parameters, environment_state)
                
        except Exception as e:
            return TaskResult(
                task_type=TaskType(action["task_type"]),
                success=False,
                error=f"Error executing action: {str(e)}",
                result={}
            )

    async def _check_tools_availability(self, parameters: Dict[str, Any]) -> TaskResult:
        """Check if required tools are available."""
        import subprocess
        import asyncio
        
        tools = parameters.get("tools", [])
        available_tools = []
        missing_tools = []
        
        for tool in tools:
            try:
                proc = await asyncio.create_subprocess_shell(
                    f"which {tool}", stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    available_tools.append(tool)
                else:
                    missing_tools.append(tool)
            except:
                missing_tools.append(tool)
        
        return TaskResult(
            task_type=TaskType.CHECK_TOOL_AVAILABILITY,
            success=True,
            result={
                "available_tools": available_tools,
                "missing_tools": missing_tools,
                "total_checked": len(tools)
            }
        )

    async def _install_tool(self, tool: str, session_state: SessionState) -> bool:
        """
        Install a cybersecurity tool on macOS.
        
        Args:
            tool: Name of the tool to install
            session_state: Current session state
            
        Returns:
            True if installation was successful
        """
        if tool in session_state.installed_tools:
            return True
        
        install_command = self.tool_install_commands.get(tool)
        if not install_command:
            return False
        
        try:
            import subprocess
            import asyncio
            
            # Execute installation command
            proc = await asyncio.create_subprocess_shell(
                install_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                session_state.installed_tools.append(tool)
                return True
            else:
                return False
                
        except Exception:
            return False

    async def _install_tool_task(self, parameters: Dict[str, Any]) -> TaskResult:
        """Install tool task implementation."""
        tool = parameters.get("tool", "")
        
        if not tool:
            return TaskResult(
                task_type=TaskType.INSTALL_TOOL,
                success=False,
                error="No tool specified",
                result={}
            )
        
        install_command = self.tool_install_commands.get(tool)
        if not install_command:
            return TaskResult(
                task_type=TaskType.INSTALL_TOOL,
                success=False,
                error=f"Installation method unknown for tool: {tool}",
                result={"tool": tool}
            )
        
        try:
            import subprocess
            import asyncio
            
            proc = await asyncio.create_subprocess_shell(
                install_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            output = stdout.decode()
            error_output = stderr.decode()
            
            if proc.returncode == 0:
                return TaskResult(
                    task_type=TaskType.INSTALL_TOOL,
                    success=True,
                    result={
                        "tool": tool,
                        "install_command": install_command,
                        "output": output[:500]  # Truncate long output
                    }
                )
            else:
                return TaskResult(
                    task_type=TaskType.INSTALL_TOOL,
                    success=False,
                    error=f"Installation failed: {error_output}",
                    result={
                        "tool": tool,
                        "install_command": install_command,
                        "output": output[:500],
                        "error_output": error_output[:500]
                    }
                )
                
        except Exception as e:
            return TaskResult(
                task_type=TaskType.INSTALL_TOOL,
                success=False,
                error=f"Error during installation: {str(e)}",
                result={"tool": tool}
            )

    async def _validate_goal_task(self, parameters: Dict[str, Any], environment_state: EnvironmentState) -> TaskResult:
        """Validate if a goal has been achieved."""
        goal = parameters.get("goal", "")
        
        # Use LLM to analyze if the goal has been achieved
        validation_prompt = f"""
        Analyze the current environment state to determine if this goal has been achieved:
        
        GOAL: {goal}
        
        CURRENT STATE:
        - Networks discovered: {len(environment_state.networks)}
        - Hosts discovered: {len(environment_state.discovered_hosts)}
        - Hosts compromised: {len(environment_state.compromised_hosts)}
        - Data exfiltrated: {len(environment_state.exfiltrated_data)}
        - Current host: {environment_state.current_host or 'None'}
        
        Respond with JSON:
        {{
            "achieved": true/false,
            "confidence": 0.0-1.0,
            "reasoning": "explanation of why goal is/isn't achieved",
            "next_steps": ["list", "of", "suggested", "next", "steps"] (if not achieved)
        }}
        """
        
        messages = [
            LLMMessage(role="system", content="You are a cybersecurity expert evaluating goal achievement."),
            LLMMessage(role="user", content=validation_prompt)
        ]
        
        try:
            response = await self.llm_service.generate_response(messages)
            
            import json
            result_json = response.content.strip()
            
            # Clean up the response
            if result_json.startswith("```json"):
                result_json = result_json.split("```json")[1].split("```")[0].strip()
            elif result_json.startswith("```"):
                result_json = result_json.split("```")[1].split("```")[0].strip()
            
            validation_result = json.loads(result_json)
            
            return TaskResult(
                task_type=TaskType.VALIDATE_GOAL,
                success=True,
                result=validation_result
            )
            
        except Exception as e:
            # Fallback validation based on simple heuristics
            achieved = False
            confidence = 0.5
            reasoning = "Unable to perform detailed analysis"
            
            if "compromise" in goal.lower() and environment_state.compromised_hosts:
                achieved = True
                confidence = 0.8
                reasoning = "Hosts have been compromised"
            elif "scan" in goal.lower() and environment_state.discovered_hosts:
                achieved = True
                confidence = 0.7
                reasoning = "Network scanning completed"
            
            return TaskResult(
                task_type=TaskType.VALIDATE_GOAL,
                success=True,
                result={
                    "achieved": achieved,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "next_steps": [] if achieved else ["continue_with_plan"]
                }
            )

    async def _is_goal_achieved(self, goal: str, environment_state: EnvironmentState) -> bool:
        """
        Check if a goal has been achieved.
        
        Args:
            goal: The goal to check
            environment_state: Current environment state
            
        Returns:
            True if goal is achieved
        """
        validation_result = await self._validate_goal_task({"goal": goal}, environment_state)
        
        if validation_result.success:
            result_data = validation_result.result
            return result_data.get("achieved", False) and result_data.get("confidence", 0) > 0.7
        
        return False

    async def _find_alternative_action(self, failed_action: Dict[str, Any], 
                                     environment_state: EnvironmentState, 
                                     goal: str) -> Optional[Dict[str, Any]]:
        """
        Find an alternative action when the original action fails.
        
        Args:
            failed_action: The action that failed
            environment_state: Current environment state
            goal: The overall goal
            
        Returns:
            Alternative action or None
        """
        task_type = failed_action["task_type"]
        
        # Define alternative strategies
        alternatives = {
            "scan_network": [
                {"task_type": "execute_command", "parameters": {"command": "ping -c 1 192.168.1.1"}},
                {"task_type": "execute_command", "parameters": {"command": "arp -a"}},
            ],
            "infect_host": [
                {"task_type": "brute_force_auth", "parameters": failed_action["parameters"]},
                {"task_type": "scan_vulnerabilities", "parameters": failed_action["parameters"]},
            ],
            "lateral_move": [
                {"task_type": "network_pivoting", "parameters": failed_action["parameters"]},
                {"task_type": "collect_system_info", "parameters": {}},
            ]
        }
        
        alt_actions = alternatives.get(task_type, [])
        if alt_actions:
            alt_action = alt_actions[0].copy()
            alt_action["description"] = f"Alternative to failed {task_type}"
            alt_action["required_tools"] = []
            alt_action["retry_count"] = 0
            return alt_action
        
        return None

    async def get_execution_status(self, session_state: SessionState) -> Dict[str, Any]:
        """
        Get the current status of all test executions.
        
        Args:
            session_state: Current session state
            
        Returns:
            Status information
        """
        return {
            "active_tests": len(session_state.active_tests),
            "completed_tests": len(session_state.completed_tests),
            "total_action_plans": len(session_state.action_plans),
            "installed_tools": session_state.installed_tools,
            "autonomous_mode": session_state.autonomous_mode,
            "current_goal": session_state.goal,
            "max_parallel_tests": session_state.max_parallel_tests
        }


# Create a singleton instance
action_planner_service = None

def get_action_planner_service(llm_service=None, task_service=None):
    """Get or create the action planner service instance."""
    global action_planner_service
    if action_planner_service is None and llm_service and task_service:
        action_planner_service = ActionPlannerService(llm_service, task_service)
    return action_planner_service