// Renderer process script for Incalmo desktop application

// Extract command from action tags - only handle actual commands
function extractCommandFromAction(content) {
    try {
        // Look for action tags
        const actionMatch = content.match(/<action>([\s\S]*?)<\/action>/);
        if (!actionMatch) return null;
        
        const actionContent = actionMatch[1];
        
        // Try to parse as JSON
        try {
            const actionJson = JSON.parse(actionContent);
            
            // Check if it's a direct command
            if (actionJson.command) {
                return actionJson.command;
            }
            
            // Check if it's a task with command parameter
            if (actionJson.task === "execute_command" && actionJson.parameters && actionJson.parameters.command) {
                return actionJson.parameters.command;
            }
            
            // Ignore all other action types
            return null;
        } catch (e) {
            console.error("Error parsing JSON in action tag:", e);
            return null;
        }
    } catch (error) {
        console.error("Error extracting command:", error);
        return null;
    }
}

// Function to filter out all JSON and action tags
function filterJsonContent(content) {
    // Safety check for null/undefined content
    if (!content) return '';
    
    try {
        let result = content;
        
        // Remove action tags and their content
        if (content.includes("<action>")) {
            console.log("Content has action tags, filtering...");
            result = result.replace(/<action>[\s\S]*?<\/action>/g, '');
        }
        
        // Checks for any known task type patterns
        const hasTaskSpecification = 
            content.includes('"task"') || 
            content.includes('"command"') ||
            content.includes('scan_network') ||
            content.includes('infect_host') ||
            content.includes('lateral_move') ||
            content.includes('escalate_privilege') ||
            content.includes('exfiltrate_data') ||
            content.includes('EXECUTE_COMMAND') ||
            content.includes('parameters');
        
        if (hasTaskSpecification) {
            console.log("Content has JSON objects, filtering...");
            
            // More comprehensive pattern to match JSON task specifications
            // Match both lowercase and uppercase task names
            result = result.replace(/\{\s*"task"[\s\S]*?\}/g, '');
            result = result.replace(/\{\s*"TASK"[\s\S]*?\}/g, '');
            result = result.replace(/\{\s*"command"[\s\S]*?\}/g, '');
            result = result.replace(/\{\s*"COMMAND"[\s\S]*?\}/g, '');
            
            // Match any JSON that includes parameters
            result = result.replace(/\{\s*[^{}]*"parameters"[\s\S]*?\}/g, '');
            
            // Last resort: more aggressive JSON removal for any remaining task-like specifications
            // This pattern looks for JSON blocks with newlines that might be task specifications
            result = result.replace(/\{\s*[\n\r][^\{\}]*\}/g, '');
            
            // Clean up any empty lines created by the filtering
            result = result.replace(/\n\s*\n\s*\n/g, '\n\n');
            
            // Clean up any leftover JSON formatting
            result = result.replace(/[\n\r]\s*\}/g, '');
            
            // Clean up any additional formatting issues that might be left
            result = result.replace(/^\s*\n/, ''); // Remove empty lines at start
            result = result.replace(/\n\s*$/, ''); // Remove empty lines at end
            result = result.replace(/\n\s*,\s*\n/g, '\n'); // Remove dangling commas
        }
        
        // Log after filtering
        console.log("After filtering content:", result.substring(0, 50) + "...");
        
        return result;
    } catch (error) {
        // If any error occurs during filtering, return original content
        console.error("Error during content filtering:", error);
        return content;
    }
}

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize application state
    const appState = {
        sessionId: null,
        sessionActive: false,
        autonomousMode: false,
        conversationStarted: false,  // Track if conversation has been initiated
        backendStatus: 'unknown',
        backendUrl: null,
        currentView: 'dashboard',
        logs: [],
        chatMode: 'auto'  // Can be 'auto', 'always', or 'never'
    };

    // DOM Elements
    const elements = {
        // Session controls
        goalInput: document.getElementById('goal-input'),
        createSessionBtn: document.getElementById('create-session-btn'),
        sessionInfo: document.getElementById('session-info'),
        sessionIdSpan: document.getElementById('session-id'),
        sessionStatusSpan: document.getElementById('session-status'),
        loadingIndicator: document.getElementById('loading-indicator'),
        autonomousModeIndicator: document.getElementById('autonomous-mode-indicator'),
        
        // Backend status
        backendStatusSpan: document.getElementById('backend-status'),
        backendUrlSpan: document.getElementById('backend-url'),
        
        // Chat elements
        chatMessages: document.getElementById('chat-messages'),
        chatInput: document.getElementById('chat-input'),
        sendMessageBtn: document.getElementById('send-message-btn'),
        clearChatBtn: document.getElementById('clear-chat-btn'),
        toggleChatModeBtn: document.getElementById('toggle-chat-mode-btn'),
        inputLoadingIndicator: document.getElementById('input-loading-indicator'),
        
        // Terminal elements
        terminalWindow: document.getElementById('terminal-window'),
        terminalOutput: document.getElementById('terminal-output'),
        toggleTerminalBtn: document.getElementById('toggle-terminal-btn'),
        clearTerminalBtn: document.getElementById('clear-terminal-btn'),
        
        // Log elements
        logEntries: document.getElementById('log-entries'),
        
        // Footer loading indicator
        footerLoadingIndicator: document.getElementById('footer-loading-indicator')
    };

    // Initialize the application
    async function initializeApp() {
        try {
            // Get backend URL from main process
            appState.backendUrl = await window.api.getBackendUrl();
            elements.backendUrlSpan.textContent = appState.backendUrl;
            
            // Check backend status
            await checkBackendStatus();
            
            // Set up event listeners
            setupEventListeners();
            
            // Set up auto-scrolling with MutationObserver
            setupAutoScroll();
            
            // Add initial log entry
            addLogEntry('Application initialized', 'info');
            
        } catch (error) {
            console.error('Error initializing app:', error);
            elements.backendStatusSpan.textContent = 'Error';
            elements.backendStatusSpan.style.color = 'red';
            addLogEntry(`Initialization error: ${error.message}`, 'error');
        }
    }
    
    // Set up auto-scroll observer - removing this since it doesn't work correctly
    function setupAutoScroll() {
        // This function was causing issues with autoscroll, so we're removing its functionality
        console.log("Auto-scroll functionality removed due to issues");
    }

    // Check backend status
    async function checkBackendStatus() {
        try {
            const healthCheck = await window.api.healthCheck();
            if (healthCheck.status === 'healthy') {
                elements.backendStatusSpan.textContent = 'Connected';
                elements.backendStatusSpan.style.color = 'green';
                appState.backendStatus = 'connected';
                addLogEntry('Connected to backend successfully', 'success');
                elements.createSessionBtn.disabled = false;
            } else {
                elements.backendStatusSpan.textContent = 'Error';
                elements.backendStatusSpan.style.color = 'red';
                appState.backendStatus = 'error';
                addLogEntry('Backend health check failed', 'error');
            }
        } catch (error) {
            console.error('Backend health check error:', error);
            elements.backendStatusSpan.textContent = 'Disconnected';
            elements.backendStatusSpan.style.color = 'red';
            appState.backendStatus = 'disconnected';
            addLogEntry(`Backend connection error: ${error.message}`, 'error');
        }
    }

    // Set up event listeners
    function setupEventListeners() {
        // Create session button
        elements.createSessionBtn.addEventListener('click', createSession);
        
        // No navigation links needed in the simplified UI
        
        // Chat input
        elements.sendMessageBtn.addEventListener('click', sendChatMessage);
        elements.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
        
        // Clear chat button
        elements.clearChatBtn.addEventListener('click', clearChat);
        
        // Terminal controls
        elements.toggleTerminalBtn.addEventListener('click', toggleTerminal);
        elements.clearTerminalBtn.addEventListener('click', clearTerminal);
        
        // Chat mode toggle
        elements.toggleChatModeBtn.addEventListener('click', toggleChatMode);
        
        // Note: Log controls are hidden in the simplified UI
        // These log-related elements don't exist in this version of the app
    }

    // No need for view switching in simplified UI

    // Create a new session and auto-start execution
    async function createSession() {
        const goal = elements.goalInput.value.trim();
        
        if (!goal) {
            addChatMessage('System', `⚠️ Please enter a security goal to proceed.`);
            return;
        }
        
        // Set up autonomous mode session
        try {
            // Show loading indicators
            elements.createSessionBtn.disabled = true;
            elements.loadingIndicator.classList.remove('hidden');
            // Goal can still be changed but session creation is disabled while loading
            // elements.goalInput.disabled = true;
            
            addLogEntry(`Creating autonomous session with goal: ${goal}`, 'info');
            
            // Remove the initial welcome message when starting
            clearChat();
            
            const response = await window.api.createSession(goal);
            console.log("Session creation response:", response);
            
            if (!response || !response.id) {
                throw new Error("Invalid response from server. Missing session ID.");
            }
            
            appState.sessionId = response.id;
            appState.sessionActive = true;
            appState.autonomousMode = true;
            
            // Update UI
            elements.sessionIdSpan.textContent = appState.sessionId;
            elements.sessionStatusSpan.textContent = 'Active';
            elements.sessionInfo.classList.remove('hidden');
            
            // Enable chat elements
            elements.chatInput.disabled = false;
            elements.sendMessageBtn.disabled = false;
            
            // Update UI to indicate autonomous mode
            elements.autonomousModeIndicator.classList.remove('hidden');
            // Add a message explaining the autonomous execution
            addChatMessage('System', `🎓 **Autonomous Analysis**\n\nYour goal: "${goal}"\n\nIncalmo will now automatically execute a series of tasks to achieve your goal.`)
            
            // Add log entry
            addLogEntry(`Session created successfully. ID: ${appState.sessionId}`, 'success');
            
            // Setup WebSocket connection for real-time updates
            setupWebSocket(appState.sessionId);
            
            // Hide loading indicator and re-enable the create button
            elements.loadingIndicator.classList.add('hidden');
            elements.createSessionBtn.disabled = false;
            elements.createSessionBtn.textContent = "Change Goal";
            
            // Automatically start execution with 'start' message
            await sendAutomaticStartMessage();
            
        } catch (error) {
            console.error('Error creating session:', error);
            elements.createSessionBtn.disabled = false;
            elements.loadingIndicator.classList.add('hidden');
            elements.goalInput.disabled = false;
            addLogEntry(`Error creating session: ${JSON.stringify(error)}`, 'error');
            addChatMessage('System', `❌ **Error creating session**\n\nDetails: ${error.message || JSON.stringify(error)}\n\nPlease check the backend logs for more details.`);
        }
    }
    
    // Helper function to display a task result - moved outside to make it globally available
    function displayTaskResult(taskType, taskResult, stepPrefix) {
        let resultMessage = "";
        
        // Check if we have a valid taskResult object
        if (!taskResult || typeof taskResult !== 'object') {
            console.error('Invalid taskResult object in displayTaskResult:', taskResult);
            return;
        }
        
        try {
            // Create a readable message about what happened
            if (taskResult.success) {
                resultMessage = `✅ **${stepPrefix}${taskType.toUpperCase()} executed successfully**\n\n`;
                
                // Make sure result exists
                if (!taskResult.result) taskResult.result = {};
                
                // Add task-specific details
                switch (taskType) {
                    case 'execute_command':
                        const command = taskResult.result.command || "unknown command";
                        const exitCode = taskResult.result.exit_code;
                        const commandOutput = taskResult.result.output || "";
                        
                        resultMessage += `**Command Execution:**\n`;
                        resultMessage += `- Command: \`${command}\`\n`;
                        resultMessage += `- Exit Code: ${exitCode}\n\n`;
                        
                        // Show command output
                        resultMessage += "**Terminal Output:**\n";
                        resultMessage += "```\n";
                        resultMessage += commandOutput || "No output captured";
                        resultMessage += "\n```\n";
                        
                        // Also add to terminal window
                        addToTerminal(command, commandOutput || "No output captured", false);
                        break;
                        
                    case 'scan_network':
                        const discoveredHosts = taskResult.result.discovered_hosts || [];
                        const scanType = taskResult.result.scan_type || 'basic';
                        const targetNetwork = taskResult.result.target_network || 'Unknown';
                        
                        const toolUsed = taskResult.result.tool_used || "unknown";
                        const commandExecuted = taskResult.result.command_executed || "unknown command";
                        const rawOutput = taskResult.result.raw_output || "";
                        
                        resultMessage += `**Network Scan Results (${scanType.toUpperCase()}):**\n`;
                        resultMessage += `- Target: ${targetNetwork}\n`;
                        resultMessage += `- Tool used: ${toolUsed}\n`;
                        resultMessage += `- Command executed: \`${commandExecuted}\`\n`;
                        resultMessage += `- Discovered ${taskResult.result.total_discovered || 0} hosts\n\n`;
                        
                        // Always show raw output to see what's happening on the terminal
                        resultMessage += "**Terminal Output:**\n";
                        resultMessage += "```\n";
                        resultMessage += rawOutput || "No output captured";
                        resultMessage += "\n```\n\n";
                        
                        // Also add to terminal window
                        addToTerminal(commandExecuted, rawOutput || "No output captured", false);
                        
                        if (discoveredHosts.length > 0) {
                            resultMessage += "**Hosts:**\n";
                            discoveredHosts.forEach(host => {
                                const services = host.services ? host.services.map(s => `${s.name}:${s.port} (${s.version || 'unknown version'})`).join(', ') : 'None';
                                resultMessage += `- ${host.hostname || 'Unknown'} (${host.ip_address})\n`;
                                resultMessage += `  OS: ${host.os_type || 'Unknown'}\n`;
                                resultMessage += `  Services: ${services}\n`;
                            });
                        } else {
                            resultMessage += "**No hosts discovered in this scan.**\n";
                            resultMessage += "Try running with different parameters or scan a different network.\n";
                        }
                        break;
                        
                    case 'infect_host':
                        resultMessage += `**Host Infection Results:**\n`;
                        resultMessage += `- Host: ${taskResult.result.host_id || 'unknown'} (${taskResult.result.ip_address || 'unknown'})\n`;
                        resultMessage += `- Access Level: ${taskResult.result.access_level || 'unknown'}\n`;
                        resultMessage += `- Status: ${taskResult.result.message || 'No status message'}\n`;
                        break;
                        
                    case 'lateral_move':
                        resultMessage += `**Lateral Movement Results:**\n`;
                        resultMessage += `- From: ${taskResult.result.source_host_id || 'unknown'}\n`;
                        resultMessage += `- To: ${taskResult.result.target_host_id || 'unknown'} (${taskResult.result.ip_address || 'unknown'})\n`;
                        resultMessage += `- Access Level: ${taskResult.result.access_level || 'unknown'}\n`;
                        resultMessage += `- Method: ${taskResult.result.method || 'Default'}\n`;
                        resultMessage += `- Status: ${taskResult.result.message || 'No status message'}\n`;
                        break;
                        
                    case 'escalate_privilege':
                        resultMessage += `**Privilege Escalation Results:**\n`;
                        resultMessage += `- Host: ${taskResult.result.host_id || 'unknown'} (${taskResult.result.ip_address || 'unknown'})\n`;
                        resultMessage += `- Previous Level: ${taskResult.result.previous_access_level || 'unknown'}\n`;
                        resultMessage += `- New Level: ${taskResult.result.new_access_level || 'unknown'}\n`;
                        resultMessage += `- Method: ${taskResult.result.method || 'Default'}\n`;
                        resultMessage += `- Status: ${taskResult.result.message || 'No status message'}\n`;
                        break;
                        
                    case 'exfiltrate_data':
                        resultMessage += `**Data Exfiltration Results:**\n`;
                        resultMessage += `- Host: ${taskResult.result.host_id || 'unknown'} (${taskResult.result.ip_address || 'unknown'})\n`;
                        resultMessage += `- Data Type: ${taskResult.result.data_type || 'unknown'}\n`;
                        resultMessage += `- Size: ${taskResult.result.size || 'unknown'} bytes\n`;
                        resultMessage += `- Status: ${taskResult.result.message || 'No status message'}\n`;
                        break;
                        
                    case 'finished':
                        // Goal completion message
                        if (taskResult.result.goal_achieved) {
                            resultMessage = `🎯 **GOAL ACHIEVED!**\n\n`;
                            
                            if (taskResult.result.summary) {
                                resultMessage += taskResult.result.summary;
                            } else {
                                resultMessage += `**Reason:** ${taskResult.result.reason || "Goal has been successfully achieved."}\n`;
                            }
                        } else {
                            resultMessage += `**Task Completed:**\n`;
                            resultMessage += `- Reason: ${taskResult.result.reason || "Task completed successfully"}\n`;
                        }
                        break;
                        
                    default:
                        // Generic success message for other task types
                        resultMessage += `**Result:** ${JSON.stringify(taskResult.result, null, 2)}`;
                }
            } else {
                // Task failed
                resultMessage = `❌ **${stepPrefix}${taskType.toUpperCase()} failed:**\n\n`;
                resultMessage += `**Error:** ${taskResult.error || 'Unknown error'}\n`;
                
                // Add more detailed information for failed commands
                if (taskType === 'execute_command' && taskResult.result) {
                    if (taskResult.result.command) {
                        resultMessage += `**Command:** \`${taskResult.result.command}\`\n`;
                        
                        // Add to terminal with error flag
                        const errorOutput = taskResult.error || "Command failed";
                        addToTerminal(taskResult.result.command, errorOutput, true);
                    }
                    
                    if (taskResult.result.suggestion) {
                        resultMessage += `\n**Suggestion:** ${taskResult.result.suggestion}\n`;
                    }
                    
                    // Show stdout/stderr if available
                    if (taskResult.result.stdout || taskResult.result.stderr) {
                        if (taskResult.result.stdout) {
                            resultMessage += "\n**Standard Output:**\n```\n";
                            resultMessage += taskResult.result.stdout || "No output";
                            resultMessage += "\n```\n";
                        }
                        
                        if (taskResult.result.stderr) {
                            resultMessage += "\n**Standard Error:**\n```\n";
                            resultMessage += taskResult.result.stderr || "No error output";
                            resultMessage += "\n```\n";
                        }
                    }
                } else if (taskType === 'scan_network' && taskResult.result && taskResult.result.command_executed) {
                    // Add failed scan to terminal
                    addToTerminal(taskResult.result.command_executed, taskResult.error || "Scan failed", true);
                }
                
                // For command failures, add a message that we're going to try again with alternatives
                resultMessage += '\n**⚠️ Attempting to recover with an alternative approach...**\n';
                resultMessage += '\nThe assistant will automatically try a different method to achieve the same goal.\n';
            }
            
            // Add task result to chat as a system message - add immediately for real-time feedback
            addChatMessage('System', resultMessage);
        } catch (err) {
            console.error('Error processing task result:', err);
            addChatMessage('System', `⚠️ **Error displaying task result**\n\nAn error occurred while trying to display the task result. See console for details.`);
        }
    }
    
    // Check for autonomous steps in response (helper function)
    function checkForAutonomousSteps(response) {
        if (!response) return;
        
        // Check if autonomous steps were executed
        if (response.autonomous_steps && response.autonomous_steps > 0) {
            const stepsExecuted = response.autonomous_steps;
            let autonomyMessage = `🤖 **Autonomous Mode: ${stepsExecuted} additional steps executed**\n\n`;
            autonomyMessage += `Incalmo automatically executed ${stepsExecuted} additional steps to reach the goal.`;
            
            addChatMessage('System', autonomyMessage);
        }
    }
    
    // Automatically send "start" message to begin execution with retry capability
    async function sendAutomaticStartMessage(retryCount = 0) {
        try {
            // Show sending indicators
            elements.inputLoadingIndicator.classList.remove('hidden');
            elements.footerLoadingIndicator.classList.remove('hidden');
            
            // Use "start" as the trigger message
            const startMessage = "start";
            
            // Add user message to chat (but with system label since it's automatic)
            if (retryCount === 0) {
                addChatMessage('System', `🚀 **Autonomous execution started**\n\nIncalmo will now execute a sequence of high-level tasks to work toward the goal. Each step will be shown below as it executes. The system will automatically adapt its strategy based on the results of each task.`);
            } else {
                addChatMessage('System', `🔄 **Retrying execution (attempt ${retryCount + 1})**`);
            }
            
            // Add log entry
            addLogEntry(`Auto-sending start message (try #${retryCount + 1})`, 'info');
            
            // Set conversation as started
            appState.conversationStarted = true;
            
            // Send message to backend with autonomousMode flag
            console.log("Auto-sending message to session:", appState.sessionId, "Autonomous mode:", appState.autonomousMode);
            const response = await window.api.sendMessage(appState.sessionId, startMessage, appState.autonomousMode);
            console.log("Received response from auto-start:", response);
            
            if (!response) {
                throw new Error("No response received from server");
            }
            
            // First show the immediate response to the user
            if (response.response) {
                addChatMessage('Assistant', response.response);
            } else if (response.content) {
                addChatMessage('Assistant', response.content);
            }

            // Check for autonomous mode steps
            checkForAutonomousSteps(response);
            
            // Process each task result separately and immediately
            if (response.all_task_results && response.all_task_results.length > 0) {
                // Process task results immediately
                
                // Process each result with step numbering and retry indicators
                let retryCount = 0;
                let currentStep = 1;
                
                response.all_task_results.forEach((taskResult, index) => {
                    if (!taskResult) return;
                    
                    const taskType = taskResult.task_type;
                    const showStepNumber = response.all_task_results.length > 1;
                    
                    // Check if this is a retry attempt by looking at previous result
                    const isRetryAttempt = index > 0 && 
                                         response.all_task_results[index-1] && 
                                         !response.all_task_results[index-1].success;
                    
                    let stepLabel = "";
                    
                    if (isRetryAttempt) {
                        retryCount++;
                        stepLabel = showStepNumber ? `Step ${currentStep-1} (Retry ${retryCount}): ` : "Retry: ";
                    } else {
                        // Reset retry counter for new steps
                        retryCount = 0;
                        stepLabel = showStepNumber ? `Step ${currentStep++}: ` : "";
                    }
                    
                    displayTaskResult(taskType, taskResult, stepLabel);
                });
            } 
            // Otherwise show single task result if available
            else if (response.task_result && response.task_type) {
                const taskType = response.task_type;
                const taskResult = response.task_result;
                displayTaskResult(taskType, taskResult, "");
            }
            
            // Hide sending indicators
            elements.inputLoadingIndicator.classList.add('hidden');
            elements.footerLoadingIndicator.classList.add('hidden');
            
        } catch (error) {
            console.error('Error auto-starting session:', error);
            elements.inputLoadingIndicator.classList.add('hidden');
            elements.footerLoadingIndicator.classList.add('hidden');
            addLogEntry(`Error auto-starting: ${error.message}`, 'error');
            
            // Retry up to 3 times if we get an error
            if (retryCount < 3) {
                addLogEntry(`Will retry in 1 second...`, 'info');
                setTimeout(() => sendAutomaticStartMessage(retryCount + 1), 1000);
            } else {
                // After 3 tries, show error to user
                addChatMessage('System', `❌ **Error starting execution after multiple attempts**\n\n${error.message}\n\nPlease try typing "start" manually.`);
            }
        }
    }

    // Execute a task
    async function executeTask(taskType, parameters) {
        if (!appState.sessionActive) {
            addLogEntry('No active session. Please create a session first.', 'warning');
            return;
        }
        
        try {
            addLogEntry(`Executing task: ${taskType}`, 'info');
            
            const response = await window.api.executeTask(appState.sessionId, taskType, parameters);
            
            // Update UI based on task result
            addLogEntry(`Task ${taskType} completed successfully`, 'success');
            
            // Add to log instead of activity list (which doesn't exist in this UI)
            addLogEntry(`Task ${taskType} executed: ${response.result || 'Completed'}`, 'success');
            
            // Update dashboard with new data
            if (response.environment_state) {
                updateDashboard(response.environment_state);
            }
            
        } catch (error) {
            console.error(`Error executing task ${taskType}:`, error);
            addLogEntry(`Error executing task ${taskType}: ${error.message}`, 'error');
        }
    }

    // Send a chat message
    async function sendChatMessage() {
        const message = elements.chatInput.value.trim();
        if (!message) return;
        
        if (!appState.sessionActive) {
            addLogEntry('No active session. Please create a session first.', 'warning');
            return;
        }
        
        // If this is the first message in an autonomous session and the message is very short,
        // automatically convert it to an explicit start command
        if (appState.autonomousMode && appState.conversationStarted === false) {
            const simpleStartTriggers = ['start', 'begin', 'go', 'run', 'execute'];
            if (message.length < 10 && simpleStartTriggers.includes(message.toLowerCase())) {
                addLogEntry('Converting simple start command to autonomous mode trigger', 'info');
                // Mark conversation as started
                appState.conversationStarted = true;
            }
        }

        // We don't need to modify the message - it goes straight to the LLM
        // which can respond either conversationally or with command execution
        let finalMessage = message;
        
        try {
            // Add user message to chat
            addChatMessage('User', message);
            
            // Clear input
            elements.chatInput.value = '';
            
            // Disable input and show loading indicators
            elements.chatInput.disabled = true;
            elements.sendMessageBtn.disabled = true;
            elements.inputLoadingIndicator.classList.remove('hidden');
            elements.footerLoadingIndicator.classList.remove('hidden');
            
            // Add log entry
            addLogEntry(`Sent message to LLM: ${message.substring(0, 50)}${message.length > 50 ? '...' : ''}`, 'info');
            
            // Send message to backend with autonomousMode flag
            console.log("Sending message to session:", appState.sessionId, "Autonomous mode:", appState.autonomousMode, "Chat mode:", chatMode);
            const response = await window.api.sendMessage(appState.sessionId, finalMessage, appState.autonomousMode);
            console.log("Received response:", response);
            
            if (!response) {
                throw new Error("No response received from server");
            }
            
            // First show the immediate response to the user
            if (response.response) {
                addChatMessage('Assistant', response.response);
            } else if (response.content) {
                addChatMessage('Assistant', response.content);
            } else {
                // Add a default message if no response content is available
                addChatMessage('Assistant', "I've processed your request. Here are the results:");
            }
            
            // Process each task result separately and immediately
            if (response.all_task_results && response.all_task_results.length > 0) {
                // Process each result with step numbering and retry indicators
                let retryCount = 0;
                let currentStep = 1;
                
                response.all_task_results.forEach((taskResult, index) => {
                    if (!taskResult) return;
                    
                    const taskType = taskResult.task_type;
                    const showStepNumber = response.all_task_results.length > 1;
                    
                    // Check if this is a retry attempt by looking at previous result
                    const isRetryAttempt = index > 0 && 
                                         response.all_task_results[index-1] && 
                                         !response.all_task_results[index-1].success;
                    
                    let stepLabel = "";
                    
                    if (isRetryAttempt) {
                        retryCount++;
                        stepLabel = showStepNumber ? `Step ${currentStep-1} (Retry ${retryCount}): ` : "Retry: ";
                    } else {
                        // Reset retry counter for new steps
                        retryCount = 0;
                        stepLabel = showStepNumber ? `Step ${currentStep++}: ` : "";
                    }
                    
                    displayTaskResult(taskType, taskResult, stepLabel);
                });
            } 
            // Otherwise show single task result if available
            else if (response.task_result && response.task_type) {
                const taskType = response.task_type;
                const taskResult = response.task_result;
                displayTaskResult(taskType, taskResult, "");
            }
            
            // Re-enable input and hide all loading indicators
            elements.chatInput.disabled = false;
            elements.sendMessageBtn.disabled = false;
            elements.inputLoadingIndicator.classList.add('hidden');
            elements.footerLoadingIndicator.classList.add('hidden');
            elements.chatInput.focus();
            
            // Add log entry
            addLogEntry('Received response from LLM', 'success');
            
            // Update dashboard if environment state changed
            if (response.environment_state) {
                updateDashboard(response.environment_state);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            addLogEntry(`Error sending message: ${error.message}`, 'error');
            
            // Add error message to chat for better visibility
            addChatMessage('System', `❌ **Error processing your request**\n\nDetails: ${error.message || JSON.stringify(error)}\n\nTry simplifying your request or checking the backend logs for more information.`);
            
            elements.chatInput.disabled = false;
            elements.sendMessageBtn.disabled = false;
            elements.inputLoadingIndicator.classList.add('hidden');
            elements.footerLoadingIndicator.classList.add('hidden');
        }
    }

    // Add a message to the chat
    function addChatMessage(sender, message) {
        console.log(`Adding chat message from ${sender}, message length: ${message?.length || 0}`);
        
        // Add a safety check in case message is undefined or null
        if (!message) {
            console.error("Received empty message to display");
            message = "[No content available]";
        }
        
        const messageDiv = document.createElement('div');
        
        // Determine message class based on sender and content
        if (sender === 'User') {
            messageDiv.className = 'user-message';
        } else if (sender === 'System') {
            messageDiv.className = 'system-message';
            
            // Simple filter for action tags
            message = filterJsonContent(message);
            
            // Check if this is a task result message
            if (message.includes('executed successfully')) {
                messageDiv.classList.add('task-result');
            } else if (message.includes('failed:')) {
                messageDiv.classList.add('task-error');
            }
        } else {
            messageDiv.className = 'assistant-message';
            
            // Simple filter for action tags
            message = filterJsonContent(message);
        }
        
        const senderSpan = document.createElement('strong');
        senderSpan.textContent = `${sender}: `;
        
        // Parse markdown in messages
        const messageContent = document.createElement('div');
        
        // Convert markdown to HTML
        let htmlContent = message;
        
        // Convert code blocks with ```
        htmlContent = htmlContent.replace(/```([^`]*?)```/g, '<pre>$1</pre>');
        
        // Convert inline code with `
        htmlContent = htmlContent.replace(/`([^`]*?)`/g, '<code>$1</code>');
        
        // Convert bold text
        htmlContent = htmlContent.replace(/\*\*([^*]*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert italic text
        htmlContent = htmlContent.replace(/\*([^*]*?)\*/g, '<em>$1</em>');
        
        // Convert newlines to <br>
        htmlContent = htmlContent.replace(/\n/g, '<br>');
        
        messageContent.innerHTML = htmlContent;
        
        messageDiv.appendChild(senderSpan);
        messageDiv.appendChild(messageContent);
        
        elements.chatMessages.appendChild(messageDiv);
        scrollChatToBottom();
    }

    // Function to scroll the chat to the bottom
    function scrollChatToBottom() {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    // Add a log entry
    function addLogEntry(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            message,
            type
        };
        
        appState.logs.push(logEntry);
        
        const logElement = document.createElement('p');
        logElement.className = `log-entry ${type}`;
        logElement.textContent = `[${timestamp}] ${message}`;
        
        elements.logEntries.appendChild(logElement);
        elements.logEntries.scrollTop = elements.logEntries.scrollHeight;
    }

    // Clear chat messages
    function clearChat(skipWelcome = false) {
        elements.chatMessages.innerHTML = '';
        
        // Only add welcome message if requested (default) and not in a session
        if (!skipWelcome && !appState.sessionActive) {
            // Re-add a minimal welcome message
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'system-message';
            
            const senderSpan = document.createElement('strong');
            senderSpan.textContent = 'System: ';
            
            const messageContent = document.createElement('div');
            messageContent.innerHTML = '<p>Enter your security goal above and click "Start" to begin.</p>';
            
            welcomeDiv.appendChild(senderSpan);
            welcomeDiv.appendChild(messageContent);
            elements.chatMessages.appendChild(welcomeDiv);
        }
        
        addLogEntry('Chat cleared', 'info');
    }

    // Clear logs
    function clearLogs() {
        elements.logEntries.innerHTML = '';
        appState.logs = [];
        addLogEntry('Logs cleared', 'info');
    }
    
    // Toggle between terminal and chat view
    function toggleTerminal() {
        const isTerminalMode = elements.terminalWindow.classList.contains('full-screen');
        
        if (isTerminalMode) {
            // Switch back to chat view
            elements.terminalWindow.classList.add('hidden');
            elements.terminalWindow.classList.remove('full-screen');
            elements.chatMessages.classList.remove('hidden');
            elements.chatInput.classList.remove('hidden');
            elements.sendMessageBtn.classList.remove('hidden');
            document.querySelector('.suggested-actions').classList.remove('hidden');
            document.querySelector('.chat-input-container').classList.remove('terminal-mode');
            // Reset chat controls z-index
            document.querySelector('.chat-controls').style.zIndex = '';
            elements.toggleTerminalBtn.textContent = 'Toggle Terminal';
        } else {
            // Switch to full screen terminal
            elements.terminalWindow.classList.add('full-screen');
            elements.terminalWindow.classList.remove('hidden');
            elements.chatMessages.classList.add('hidden');
            elements.chatInput.classList.add('hidden');
            elements.sendMessageBtn.classList.add('hidden');
            document.querySelector('.suggested-actions').classList.add('hidden');
            document.querySelector('.chat-input-container').classList.add('terminal-mode');
            // Keep chat controls visible
            document.querySelector('.chat-controls').style.zIndex = '20';
            elements.toggleTerminalBtn.textContent = 'Toggle Chat';
        }
    }
    
    // Clear terminal output
    function clearTerminal() {
        elements.terminalOutput.innerHTML = '';
        addLogEntry('Terminal cleared', 'info');
    }
    
    // Toggle chat mode button now shows command mode status
    function toggleChatMode() {
        addChatMessage('System', 'The assistant can respond conversationally or execute commands in our simulated environment. To run a command, ask the assistant to execute specific commands for you.');
        elements.toggleChatModeBtn.textContent = 'Command Mode: Enabled';
    }
    
    // Add command to terminal
    function addToTerminal(command, output, isError = false) {
        // Create command element
        const cmdElement = document.createElement('div');
        cmdElement.className = 'terminal-cmd';
        
        // Add command prompt
        const promptSpan = document.createElement('span');
        promptSpan.className = 'prompt';
        promptSpan.textContent = '$ ';
        
        // Add command text
        const commandSpan = document.createElement('span');
        commandSpan.className = 'command';
        commandSpan.textContent = command;
        
        // Add command line
        cmdElement.appendChild(promptSpan);
        cmdElement.appendChild(commandSpan);
        
        // Create output element
        const outputElement = document.createElement('div');
        outputElement.className = isError ? 'terminal-error' : 'terminal-output';
        outputElement.textContent = output;
        
        // Add to terminal
        elements.terminalOutput.appendChild(cmdElement);
        elements.terminalOutput.appendChild(outputElement);
        
        // Scroll terminal to bottom with improved reliability
        scrollTerminalToBottom();
    }

    // Function to scroll terminal to the bottom
    function scrollTerminalToBottom() {
        elements.terminalOutput.scrollTop = elements.terminalOutput.scrollHeight;
    }

    // Note: Filter logs functionality is not available in simplified UI
    // Keeping this as a stub for future implementation if needed
    function filterLogs() {
        // Log filtering is disabled in simplified UI
        console.log("Log filtering is not available in this version");
    }

    // Update dashboard with environment state
    // Note: In this simplified UI, dashboard elements are not visible
    // This function is kept as a stub for future implementation
    function updateDashboard(environmentState) {
        if (!environmentState) return;
        
        // Log the environment state for debugging
        console.log("Environment state updated:", environmentState);
        
        // In this simplified UI, we don't display dashboard metrics
        // If dashboard elements are added in the future, update them here
    }

    // Format bytes to human-readable format
    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Initialize WebSocket connection
    function setupWebSocket(sessionId) {
        if (!sessionId) return;
        
        // Get backend URL from main process
        window.api.getBackendUrl().then(backendUrl => {
            const wsUrl = backendUrl.replace('http://', 'ws://') + `/ws/${sessionId}`;
            const socket = new WebSocket(wsUrl);
            
            socket.onopen = () => {
                addLogEntry(`WebSocket connection established for session ${sessionId}`, 'info');
            };
            
            // Variables for handling streaming messages
            let currentStreamingMessage = null;
            let streamingMessageDiv = null;
            let streamingMessageContent = null;
            let actionTagProcessed = false; // Track if we've already processed an action tag
            
            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    // Handle different update types
                    if (data.type === 'task_result') {
                        addLogEntry(`Task ${data.task_type} completed: ${data.success ? 'success' : 'failure'}`, data.success ? 'success' : 'error');
                        
                        // Log the task completion instead of adding to activity list
                        addLogEntry(`WebSocket: ${data.task_type} - ${data.result.message || 'Completed'}`, data.success ? 'success' : 'error');
                    } else if (data.type === 'environment_update') {
                        updateDashboard(data.environment_state);
                        addLogEntry('Environment state updated', 'info');
                    } else if (data.type === 'attack_graph_update') {
                        // Handle attack graph update
                        addLogEntry('Attack graph updated', 'info');
                    } else if (data.type === 'llm_response') {
                        // Filter JSON content from message
                        let content = data.message.content;
                        content = filterJsonContent(content);
                        addChatMessage('Assistant', content);
                        addLogEntry('Received response from LLM', 'success');
                    } else if (data.type === 'llm_streaming_chunk') {
                        // Handle streaming chunks
                        console.log(`Received streaming chunk: length=${data.chunk?.length || 0}, is_done=${data.is_done}`);
                        if (data.chunk?.length > 0) {
                            console.log(`Chunk preview: ${data.chunk.substring(0, 50)}...`);
                        }
                        
                        if (!currentStreamingMessage) {
                            // Start a new streaming message
                            currentStreamingMessage = "";
                            console.log("Starting new streaming message");
                            
                            // Create message elements
                            streamingMessageDiv = document.createElement('div');
                            streamingMessageDiv.className = 'assistant-message streaming';
                            
                            const senderSpan = document.createElement('strong');
                            senderSpan.textContent = 'Assistant: ';
                            
                            streamingMessageContent = document.createElement('div');
                            streamingMessageContent.className = 'streaming-content';
                            
                            streamingMessageDiv.appendChild(senderSpan);
                            streamingMessageDiv.appendChild(streamingMessageContent);
                            
                            // Add to chat container
                            elements.chatMessages.appendChild(streamingMessageDiv);
                            addLogEntry('Started streaming response from LLM', 'info');
                        }
                        
                        // Add the chunk to the current message
                        if (data.chunk) {
                            console.log("Received chunk:", data.chunk.substring(0, 50) + "...");
                            
                            // Only process command actions
                            if (!actionTagProcessed && data.chunk.includes("<action>")) {
                                // If we detect the beginning of an action tag, we should save it
                                // to process when we have the complete action
                                const openingTagPos = data.chunk.indexOf("<action>");
                                const closingTagPos = data.chunk.indexOf("</action>");
                                
                                // If we have both opening and closing tags in the same chunk, we can process it now
                                if (closingTagPos > openingTagPos) {
                                    // Extract only command actions
                                    const command = extractCommandFromAction(data.chunk);
                                    if (command) {
                                        // Only display system message for actual commands
                                        addChatMessage('System', `🔄 **Running:** \`${command}\``);
                                        actionTagProcessed = true;
                                    }
                                }
                            }
                            
                            // Filter all JSON content and action tags
                            const filteredChunk = filterJsonContent(data.chunk);
                            
                            // Add to the current message
                            currentStreamingMessage += filteredChunk;
                            
                            // Convert markdown to HTML
                            let htmlContent = currentStreamingMessage;
                            
                            // Basic markdown conversion for streaming chunks
                            // Convert code blocks with ```
                            htmlContent = htmlContent.replace(/```([^`]*?)```/g, '<pre>$1</pre>');
                            
                            // Convert inline code with `
                            htmlContent = htmlContent.replace(/`([^`]*?)`/g, '<code>$1</code>');
                            
                            // Convert bold text
                            htmlContent = htmlContent.replace(/\*\*([^*]*?)\*\*/g, '<strong>$1</strong>');
                            
                            // Convert italic text
                            htmlContent = htmlContent.replace(/\*([^*]*?)\*/g, '<em>$1</em>');
                            
                            // Convert newlines to <br>
                            htmlContent = htmlContent.replace(/\n/g, '<br>');
                            
                            // Update the content
                            streamingMessageContent.innerHTML = htmlContent;
                            
                            // Scroll to bottom with each chunk
                            elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
                        }
                        
                        // If this is the last chunk, finalize the message
                        if (data.is_done) {
                            console.log("Finalized streaming message");
                            if (streamingMessageDiv) {
                                // Remove streaming class to stop any animation
                                streamingMessageDiv.classList.remove('streaming');
                            }
                            
                            // Check for command action tags in the complete message
                            if (!actionTagProcessed && currentStreamingMessage && currentStreamingMessage.includes("<action>")) {
                                const command = extractCommandFromAction(currentStreamingMessage);
                                if (command) {
                                    // Only display system message for actual commands
                                    addChatMessage('System', `🔄 **Running:** \`${command}\``);
                                    actionTagProcessed = true;
                                }
                            }
                            
                            // Reset streaming state
                            currentStreamingMessage = null;
                            streamingMessageDiv = null;
                            streamingMessageContent = null;
                            actionTagProcessed = false;
                            
                            addLogEntry('Completed streaming response from LLM', 'success');
                        }
                    }
                } catch (error) {
                    console.error('Error processing WebSocket message:', error);
                }
            };
            
            socket.onclose = () => {
                addLogEntry(`WebSocket connection closed for session ${sessionId}`, 'warning');
                // Try to reconnect after a delay
                setTimeout(() => setupWebSocket(sessionId), 5000);
            };
            
            socket.onerror = (error) => {
                addLogEntry(`WebSocket error: ${error.message}`, 'error');
            };
            
            // Store socket in appState
            appState.webSocket = socket;
        });
    }

    // Initialize the application
    initializeApp();
});