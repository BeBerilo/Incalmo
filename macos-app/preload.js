const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('api', {
  // Get the backend URL
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  
  // Send a message to the Python backend
  sendMessage: async (sessionId, message, autonomousMode = false) => {
    const backendUrl = await ipcRenderer.invoke('get-backend-url');
    const response = await fetch(`${backendUrl}/api/llm/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: message,
        autonomous_mode: autonomousMode
      }),
    });
    return response.json();
  },
  
  // Create a new session
  createSession: async (goal) => {
    const backendUrl = await ipcRenderer.invoke('get-backend-url');
    try {
      console.log(`Creating session with goal: ${goal}`);
      const response = await fetch(`${backendUrl}/api/llm/session/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          goal: goal,
          environment_config: null
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Session creation error: ${response.status} - ${errorText}`);
        throw new Error(`Server error: ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      console.error("Session creation failed:", error);
      throw error;
    }
  },
  
  // Execute a task
  executeTask: async (sessionId, taskType, parameters) => {
    const backendUrl = await ipcRenderer.invoke('get-backend-url');
    try {
      console.log(`Executing task ${taskType} for session ${sessionId}`);
      const response = await fetch(`${backendUrl}/api/sessions/${sessionId}/task`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_type: taskType,
          parameters,
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Task execution error: ${response.status} - ${errorText}`);
        throw new Error(`Server error: ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      console.error("Task execution failed:", error);
      throw error;
    }
  },
  
  // Get environment state
  getEnvironmentState: async (sessionId) => {
    const backendUrl = await ipcRenderer.invoke('get-backend-url');
    const response = await fetch(`${backendUrl}/api/environment/state/${sessionId}`);
    return response.json();
  },
  
  // Get attack graph
  getAttackGraph: async (sessionId) => {
    const backendUrl = await ipcRenderer.invoke('get-backend-url');
    const response = await fetch(`${backendUrl}/api/attack-graph/${sessionId}`);
    return response.json();
  },
  
  // Health check with retry logic
  healthCheck: async () => {
    const backendUrl = await ipcRenderer.invoke('get-backend-url');
    
    // Try multiple possible endpoints - this helps with localhost vs 127.0.0.1 issues
    async function tryEndpoint(url) {
      try {
        const response = await fetch(url, { timeout: 5000 });
        if (response.ok) {
          return await response.json();
        }
      } catch (err) {
        console.warn(`Health check failed for ${url}:`, err.message);
      }
      return null;
    }
    
    // Try both localhost and 127.0.0.1
    const urls = [
      `${backendUrl}/health`, 
      backendUrl.replace('localhost', '127.0.0.1') + '/health',
      backendUrl.replace('127.0.0.1', 'localhost') + '/health'
    ];
    
    for (const url of urls) {
      const result = await tryEndpoint(url);
      if (result) {
        return result;
      }
    }
    
    throw new Error('All health check attempts failed');
  }
});
