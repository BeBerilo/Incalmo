"""
Updated backend configuration to securely handle API keys.
This file ensures the Anthropic API key is only used server-side.
"""

import os
import datetime
import socket
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

# Get API key from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

# Create FastAPI app
app = FastAPI(
    title="Incalmo",
    description="An LLM-agnostic high-level attack abstraction layer using Claude 3.7 Sonnet",
    version="0.1.0"
)

# Configure CORS for frontend - will be updated with the exposed port URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted to the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routers import llm, tasks, environment, attack_graph

# Include routers
app.include_router(llm.router, prefix="/api/llm", tags=["LLM Integration"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Task Translation"])
app.include_router(environment.router, prefix="/api/environment", tags=["Environment State"])
app.include_router(attack_graph.router, prefix="/api/attack-graph", tags=["Attack Graph"])

# Import and set up core functionality
from core import setup_core_routes
setup_core_routes(app)

# Import and set up WebSocket functionality
from websocket import setup_websocket_routes, websocket_manager
setup_websocket_routes(app)

# Add middleware to check for API key in requests
@app.middleware("http")
async def check_api_key(request: Request, call_next):
    # Skip API key check for certain endpoints
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"] or request.url.path.startswith("/static"):
        return await call_next(request)
    
    # For all other endpoints, ensure we have the API key in the environment
    if not ANTHROPIC_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"detail": "API key configuration error"}
        )
    
    return await call_next(request)

@app.get("/")
async def root():
    """Root endpoint that returns basic API information."""
    return {
        "name": "Incalmo API",
        "version": "0.1.0",
        "description": "An LLM-agnostic high-level attack abstraction layer using Claude Sonnet 3.7"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

# Add configuration endpoint to provide frontend with necessary config
# WITHOUT exposing sensitive information
@app.get("/api/config")
async def get_config():
    """Get frontend configuration without exposing sensitive information."""
    return {
        "apiReady": bool(ANTHROPIC_API_KEY),
        "wsEnabled": True,
        "version": "0.1.0"
    }

def find_available_port(start_port=8713, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                # Try to bind to both the wildcard address and localhost specifically
                s.bind(('', port))
                s.close()
                
                # Double-check with a connect test
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                        test_socket.settimeout(0.1)
                        test_socket.connect(('127.0.0.1', port))
                        # If we can connect, the port is actually in use
                        continue
                except socket.error:
                    # Connection failed, which is good - port is available
                    return port
            except socket.error:
                continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

if __name__ == "__main__":
    import uvicorn
    
    # Get preferred port from environment variable
    preferred_port = int(os.getenv("PORT", 8713))
    
    # Find an available port starting from the preferred port
    port = find_available_port(start_port=preferred_port)
    
    # If we had to use a different port, print a message
    if port != preferred_port:
        print(f"Port {preferred_port} is in use, using port {port} instead")
    
    # Write the actual port to a file that the Electron app can read
    port_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'port.txt')
    with open(port_file, 'w') as f:
        f.write(str(port))
    
    print(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
