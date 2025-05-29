"""
Action Planner Router

API endpoints for the action planner service that provides:
- Goal-based action planning
- Multi-test execution
- Tool management
- Autonomous cybersecurity automation
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import uuid

from models.models import (
    ActionPlan, TestExecution, TaskType, SessionState,
    EnvironmentState, LLMMessage
)
from services.action_planner_service import get_action_planner_service
from services.llm_service import llm_service
from services.task_service import task_translation_service

router = APIRouter(prefix="/action-planner", tags=["action-planner"])

# Global session storage (in production, use a proper database)
sessions: Dict[str, SessionState] = {}


class CreatePlanRequest(BaseModel):
    """Request model for creating an action plan."""
    goal: str
    session_id: Optional[str] = None


class StartTestRequest(BaseModel):
    """Request model for starting a test execution."""
    plan_id: str
    test_name: str
    session_id: str


class SetGoalRequest(BaseModel):
    """Request model for setting a session goal."""
    goal: str
    autonomous_mode: bool = False


class InstallToolRequest(BaseModel):
    """Request model for installing a tool."""
    tool: str


@router.post("/sessions", response_model=Dict[str, str])
async def create_session():
    """Create a new cybersecurity automation session."""
    session_id = str(uuid.uuid4())
    
    session = SessionState(
        id=session_id,
        environment_state=EnvironmentState(),
        autonomous_mode=False,
        max_parallel_tests=3
    )
    
    sessions[session_id] = session
    
    return {
        "session_id": session_id,
        "status": "created",
        "message": "New cybersecurity automation session created"
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    planner = get_action_planner_service(llm_service, task_translation_service)
    
    if planner:
        status = await planner.get_execution_status(session)
        return {
            "session_id": session_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "goal": session.goal,
            "autonomous_mode": session.autonomous_mode,
            "execution_status": status,
            "environment_summary": {
                "networks": len(session.environment_state.networks),
                "discovered_hosts": len(session.environment_state.discovered_hosts),
                "compromised_hosts": len(session.environment_state.compromised_hosts),
                "exfiltrated_data": len(session.environment_state.exfiltrated_data)
            }
        }
    else:
        raise HTTPException(status_code=500, detail="Action planner service not available")


@router.post("/sessions/{session_id}/goal")
async def set_goal(session_id: str, request: SetGoalRequest):
    """Set the goal for a session and optionally enable autonomous mode."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.goal = request.goal
    session.autonomous_mode = request.autonomous_mode
    
    return {
        "session_id": session_id,
        "goal": session.goal,
        "autonomous_mode": session.autonomous_mode,
        "message": "Goal set successfully"
    }


@router.post("/plans", response_model=ActionPlan)
async def create_action_plan(request: CreatePlanRequest):
    """Create an action plan to achieve a cybersecurity goal."""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get or create session
    if session_id not in sessions:
        session = SessionState(
            id=session_id,
            environment_state=EnvironmentState(),
            autonomous_mode=False
        )
        sessions[session_id] = session
    else:
        session = sessions[session_id]
    
    # Get action planner service
    planner = get_action_planner_service(llm_service, task_translation_service)
    if not planner:
        raise HTTPException(status_code=500, detail="Action planner service not available")
    
    try:
        # Create the action plan
        plan = await planner.create_action_plan(request.goal, session.environment_state)
        
        # Add plan to session
        session.action_plans.append(plan)
        session.goal = request.goal
        
        return plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create action plan: {str(e)}")


@router.get("/sessions/{session_id}/plans")
async def get_action_plans(session_id: str):
    """Get all action plans for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "action_plans": session.action_plans,
        "total_plans": len(session.action_plans)
    }


@router.post("/tests", response_model=TestExecution)
async def start_test_execution(request: StartTestRequest):
    """Start a new test execution based on an action plan."""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[request.session_id]
    
    # Find the plan
    plan = None
    for p in session.action_plans:
        if p.id == request.plan_id:
            plan = p
            break
    
    if not plan:
        raise HTTPException(status_code=404, detail="Action plan not found")
    
    # Check if we can start more tests
    if len(session.active_tests) >= session.max_parallel_tests:
        raise HTTPException(status_code=429, detail="Maximum parallel tests reached")
    
    # Get action planner service
    planner = get_action_planner_service(llm_service, task_translation_service)
    if not planner:
        raise HTTPException(status_code=500, detail="Action planner service not available")
    
    try:
        # Start the test execution
        test_execution = await planner.start_test_execution(session, plan, request.test_name)
        return test_execution
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start test execution: {str(e)}")


@router.get("/sessions/{session_id}/tests")
async def get_test_executions(session_id: str):
    """Get all test executions for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return {
        "session_id": session_id,
        "active_tests": session.active_tests,
        "completed_tests": session.completed_tests,
        "total_active": len(session.active_tests),
        "total_completed": len(session.completed_tests)
    }


@router.get("/tests/{test_id}")
async def get_test_execution(test_id: str):
    """Get details of a specific test execution."""
    # Search all sessions for the test
    for session in sessions.values():
        for test in session.active_tests + session.completed_tests:
            if test.id == test_id:
                return test
    
    raise HTTPException(status_code=404, detail="Test execution not found")


@router.post("/sessions/{session_id}/tools/install")
async def install_tool(session_id: str, request: InstallToolRequest):
    """Install a cybersecurity tool."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    try:
        # Execute install tool task
        result = await task_translation_service.execute_task(
            TaskType.INSTALL_TOOL,
            {"tool": request.tool},
            session.environment_state
        )
        
        if result.success:
            # Add to installed tools list
            if request.tool not in session.installed_tools:
                session.installed_tools.append(request.tool)
        
        return {
            "tool": request.tool,
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "installed_tools": session.installed_tools
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to install tool: {str(e)}")


@router.get("/sessions/{session_id}/tools")
async def get_installed_tools(session_id: str):
    """Get list of installed tools for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Check availability of common tools
    common_tools = ["nmap", "hydra", "nikto", "metasploit", "wireshark", "burpsuite"]
    
    try:
        availability_result = await task_translation_service.execute_task(
            TaskType.CHECK_TOOL_AVAILABILITY,
            {"tools": common_tools},
            session.environment_state
        )
        
        return {
            "session_id": session_id,
            "installed_tools": session.installed_tools,
            "tool_availability": availability_result.result if availability_result.success else {},
            "total_installed": len(session.installed_tools)
        }
        
    except Exception as e:
        return {
            "session_id": session_id,
            "installed_tools": session.installed_tools,
            "tool_availability": {},
            "total_installed": len(session.installed_tools),
            "error": f"Could not check tool availability: {str(e)}"
        }


@router.post("/sessions/{session_id}/autonomous/start")
async def start_autonomous_mode(session_id: str):
    """Start autonomous goal achievement mode."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if not session.goal:
        raise HTTPException(status_code=400, detail="No goal set for the session")
    
    if session.autonomous_mode:
        raise HTTPException(status_code=400, detail="Autonomous mode already active")
    
    # Get action planner service
    planner = get_action_planner_service(llm_service, task_translation_service)
    if not planner:
        raise HTTPException(status_code=500, detail="Action planner service not available")
    
    try:
        # Create action plan if none exists
        if not session.action_plans:
            plan = await planner.create_action_plan(session.goal, session.environment_state)
            session.action_plans.append(plan)
        
        # Enable autonomous mode
        session.autonomous_mode = True
        
        # Start test execution automatically
        plan = session.action_plans[0]
        test_name = f"Autonomous Goal Achievement - {session.goal[:50]}"
        test_execution = await planner.start_test_execution(session, plan, test_name)
        
        return {
            "session_id": session_id,
            "autonomous_mode": True,
            "goal": session.goal,
            "action_plan_id": plan.id,
            "test_execution_id": test_execution.id,
            "message": "Autonomous mode started successfully"
        }
        
    except Exception as e:
        session.autonomous_mode = False
        raise HTTPException(status_code=500, detail=f"Failed to start autonomous mode: {str(e)}")


@router.post("/sessions/{session_id}/autonomous/stop")
async def stop_autonomous_mode(session_id: str):
    """Stop autonomous goal achievement mode."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.autonomous_mode = False
    
    # Note: Active tests will continue running but no new tests will be started
    
    return {
        "session_id": session_id,
        "autonomous_mode": False,
        "active_tests": len(session.active_tests),
        "message": "Autonomous mode stopped"
    }


@router.get("/task-types")
async def get_available_task_types():
    """Get all available task types for manual execution."""
    task_categories = {
        "Network & Discovery": [
            TaskType.SCAN_NETWORK.value,
            TaskType.SCAN_PORT.value,
            TaskType.DISCOVER_SERVICES.value,
            TaskType.ENUMERATE_USERS.value
        ],
        "Vulnerability Assessment": [
            TaskType.SCAN_VULNERABILITIES.value,
            TaskType.ANALYZE_WEB_APP.value,
            TaskType.TEST_DEFAULT_CREDS.value,
            TaskType.CHECK_MISCONFIGURATIONS.value
        ],
        "Exploitation & Access": [
            TaskType.INFECT_HOST.value,
            TaskType.LATERAL_MOVE.value,
            TaskType.ESCALATE_PRIVILEGE.value,
            TaskType.BRUTE_FORCE_AUTH.value,
            TaskType.EXPLOIT_VULNERABILITY.value
        ],
        "Data Operations": [
            TaskType.EXFILTRATE_DATA.value,
            TaskType.COLLECT_SYSTEM_INFO.value,
            TaskType.DUMP_CREDENTIALS.value,
            TaskType.ACCESS_FILES.value
        ],
        "Network Operations": [
            TaskType.NETWORK_PIVOTING.value,
            TaskType.TRAFFIC_ANALYSIS.value,
            TaskType.MITM_ATTACK.value
        ],
        "Tools Management": [
            TaskType.INSTALL_TOOL.value,
            TaskType.CHECK_TOOL_AVAILABILITY.value,
            TaskType.UPDATE_TOOLS.value
        ],
        "System Operations": [
            TaskType.EXECUTE_COMMAND.value,
            TaskType.MONITOR_SYSTEM.value,
            TaskType.SETUP_PERSISTENCE.value
        ]
    }
    
    return {
        "task_categories": task_categories,
        "total_task_types": sum(len(tasks) for tasks in task_categories.values())
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its data."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Clean up any running processes/tests if needed
    # In a production environment, you'd want to properly cleanup background tasks
    
    del sessions[session_id]
    
    return {
        "session_id": session_id,
        "message": "Session deleted successfully"
    }