"""
Test script for session creation to diagnose the error
"""

import asyncio
import json
from services.environment_service import environment_state_service
from services.attack_graph_service import attack_graph_service
from services.llm_service import create_system_prompt
from models.models import SessionState
import os

async def test_session_creation():
    try:
        # Step 1: Create environment
        print("Creating initial environment...")
        environment_state = environment_state_service.create_initial_environment(None)
        print("Environment created successfully!")
        
        # Step 2: Generate attack graph
        print("Generating attack graph...")
        attack_graph = attack_graph_service.generate_attack_graph(environment_state)
        print("Attack graph generated successfully!")
        
        # Step 3: Create system prompt
        print("Creating system prompt...")
        environment_text = environment_state_service.get_environment_state_text(environment_state)
        attack_graph_text = attack_graph_service.get_attack_graph_text(attack_graph, environment_state)
        goal = "Scan and identify vulnerable devices on a lab network"
        system_prompt = create_system_prompt(goal, environment_text, attack_graph_text)
        print("System prompt created successfully!")
        
        # Step 4: Create session
        print("Creating session...")
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        session = SessionState(
            id=session_id,
            environment_state=environment_state,
            attack_graph=attack_graph,
            conversation_history=[],
            task_history=[],
            goal=goal
        )
        print("Session created successfully!")
        
        # Print result
        print(f"Session ID: {session.id}")
        print(f"Goal: {session.goal}")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_session_creation())