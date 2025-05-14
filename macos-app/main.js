const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const { execSync } = require('child_process');

// Keep a global reference of the window object to avoid garbage collection
let mainWindow;
let pythonProcess;
let backendPort = 8713; // Default port, will be updated dynamically

// Path to the packaged Python executable and backend files
const getPythonExecutablePath = () => {
  if (process.env.NODE_ENV === 'development') {
    return 'python3'; // Use system Python in development
  } else {
    // In production, use the bundled Python executable
    if (process.platform === 'darwin') {
      return path.join(process.resourcesPath, 'backend/python/bin/python3');
    } else {
      return path.join(process.resourcesPath, 'backend/python/bin/python3');
    }
  }
};

// Path to the backend script
const getBackendScriptPath = () => {
  if (process.env.NODE_ENV === 'development') {
    return path.join(__dirname, '../src/backend/main.py');
  } else {
    return path.join(process.resourcesPath, 'backend/main.py');
  }
};

// Copy backend files to a temporary directory for development
function prepareBackendFiles() {
  const tempBackendDir = path.join(app.getPath('temp'), 'incalmo-backend');
  
  // Create temp directory if it doesn't exist
  if (!fs.existsSync(tempBackendDir)) {
    fs.mkdirSync(tempBackendDir, { recursive: true });
  }
  
  // Copy backend files from the original location
  const sourceBackendDir = path.join(__dirname, '../src/backend');
  if (fs.existsSync(sourceBackendDir)) {
    // Copy only if source exists (for development)
    try {
      execSync(`cp -r ${sourceBackendDir}/* ${tempBackendDir}`);
      console.log('Backend files copied to temp directory');
    } catch (error) {
      console.error('Error copying backend files:', error);
    }
  }
  
  return tempBackendDir;
}

// Function to check if a port is in use
function isPortInUse(port) {
  try {
    const net = require('net');
    const server = net.createServer();
    
    return new Promise((resolve) => {
      server.once('error', (err) => {
        if (err.code === 'EADDRINUSE') {
          resolve(true); // Port is in use
        } else {
          resolve(false);
        }
      });
      
      server.once('listening', () => {
        server.close();
        resolve(false); // Port is available
      });
      
      server.listen(port);
    });
  } catch (err) {
    return Promise.resolve(true); // Assume port is in use if there's an error
  }
}

// Function to find an available port
async function findAvailablePort(startPort, maxAttempts = 100) {
  for (let port = startPort; port < startPort + maxAttempts; port++) {
    const inUse = await isPortInUse(port);
    if (!inUse) {
      return port;
    }
  }
  throw new Error(`Could not find an available port after ${maxAttempts} attempts`);
}

// Start the Python backend process
async function startPythonBackend() {
  // Prepare backend files
  const tempBackendDir = prepareBackendFiles();
  
  // Create a .env file with the API key
  const envFilePath = path.join(tempBackendDir, '.env');
  fs.writeFileSync(envFilePath, `ANTHROPIC_API_KEY=${process.env.ANTHROPIC_API_KEY || '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'}\n`);
  
  const pythonExecutable = getPythonExecutablePath();
  const scriptPath = path.join(tempBackendDir, 'main.py');
  
  // Don't try to find an available port here - let the Python backend handle it
  // We'll read the actual port from port.txt later
  backendPort = 8713; // Initial value, will be updated if needed
  console.log(`Starting with default port ${backendPort}, will update if needed`);
  
  // Environment variables for the Python process
  const env = {
    ...process.env,
    PYTHONUNBUFFERED: '1', // Ensure Python output is not buffered
    PORT: backendPort.toString(),
    HOST: '127.0.0.1'
  };

  console.log(`Starting Python backend: ${pythonExecutable} ${scriptPath}`);
  
  // Spawn the Python process
  pythonProcess = spawn(pythonExecutable, [scriptPath], { 
    env,
    cwd: tempBackendDir
  });
  
  // Handle Python process output
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
    
    // Check if the backend has started on a different port
    const portMatch = data.toString().match(/using port (\d+) instead/i);
    if (portMatch && portMatch[1]) {
      const newPort = parseInt(portMatch[1], 10);
      if (newPort !== backendPort) {
        console.log(`Backend using different port: ${newPort}`);
        backendPort = newPort;
      }
    }
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    if (code !== 0 && !app.isQuitting) {
      console.error('Python process crashed, restarting...');
      startPythonBackend();
    }
  });
  
  // Wait for backend to start
  return new Promise((resolve, reject) => {
    let startupTimeout = setTimeout(() => {
      reject(new Error('Backend startup timeout'));
    }, 30000); // Increased timeout to 30 seconds
    
    let checkAttempts = 0;
    const MAX_ATTEMPTS = 60; // Increased max attempts
    
    const checkBackend = () => {
      checkAttempts++;
      
      // Check if port.txt file exists and read the port from it
      const portFilePath = path.join(tempBackendDir, 'port.txt');
      if (fs.existsSync(portFilePath)) {
        try {
          const portFromFile = parseInt(fs.readFileSync(portFilePath, 'utf8').trim(), 10);
          if (portFromFile && portFromFile !== backendPort) {
            console.log(`Detected backend port change from ${backendPort} to ${portFromFile}`);
            backendPort = portFromFile;
            // Reset check attempts after port change
            checkAttempts = 0;
          }
        } catch (err) {
          console.error('Error reading port file:', err);
        }
      }
      
      // Try multiple ways to check if the backend is up
      const checkWithHttp = () => {
        try {
          const http = require('http');
          const req = http.get(`http://localhost:${backendPort}/health`, (res) => {
            if (res.statusCode === 200) {
              clearTimeout(startupTimeout);
              console.log('Backend started successfully on port', backendPort);
              resolve();
            } else {
              tryAgainOrFail();
            }
          });
          
          req.on('error', (err) => {
            console.log(`Backend not ready yet (${err.message}), retrying...`);
            // Also try with 127.0.0.1 if localhost fails
            if (err.message.includes('ECONNREFUSED') && !err.message.includes('127.0.0.1')) {
              checkWith127();
            } else {
              tryAgainOrFail();
            }
          });
          
          req.setTimeout(2000, () => {
            req.abort();
            console.log('Connection timeout, retrying...');
            tryAgainOrFail();
          });
          
          req.end();
        } catch (error) {
          console.error('Error checking backend with localhost:', error);
          tryAgainOrFail();
        }
      };
      
      const checkWith127 = () => {
        try {
          const http = require('http');
          const req = http.get(`http://127.0.0.1:${backendPort}/health`, (res) => {
            if (res.statusCode === 200) {
              clearTimeout(startupTimeout);
              console.log('Backend started successfully on 127.0.0.1:', backendPort);
              resolve();
            } else {
              tryAgainOrFail();
            }
          });
          
          req.on('error', (err) => {
            console.log(`Backend not ready on 127.0.0.1 (${err.message}), retrying...`);
            tryAgainOrFail();
          });
          
          req.setTimeout(2000, () => {
            req.abort();
            tryAgainOrFail();
          });
          
          req.end();
        } catch (error) {
          console.error('Error checking backend with 127.0.0.1:', error);
          tryAgainOrFail();
        }
      };
      
      const tryAgainOrFail = () => {
        if (checkAttempts >= MAX_ATTEMPTS) {
          console.error(`Failed to connect to backend after ${MAX_ATTEMPTS} attempts`);
          reject(new Error(`Failed to connect to backend on port ${backendPort} after ${MAX_ATTEMPTS} attempts`));
          return;
        }
        setTimeout(checkBackend, 500);
      };
      
      // Start with localhost check
      checkWithHttp();
    };
    
    // Start checking after a short delay
    setTimeout(checkBackend, 1000);
  });
}

// Create the main application window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    title: 'Incalmo - LLM-powered Network Attack Tool',
    backgroundColor: '#f5f5f7'
  });

  // Load the index.html file
  mainWindow.loadFile(path.join(__dirname, 'index.html'));
  
  // Disable DevTools to avoid debug output
  // mainWindow.webContents.openDevTools();

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Initialize the app when Electron is ready
app.whenReady().then(async () => {
  try {
    // Start the Python backend
    await startPythonBackend();
    
    // Create the main window
    createWindow();
    
    // On macOS, recreate the window when the dock icon is clicked
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  } catch (error) {
    console.error('Error during app initialization:', error);
    app.quit();
  }
});

// Quit the app when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Clean up the Python process when the app is quitting
app.on('before-quit', () => {
  app.isQuitting = true;
  if (pythonProcess) {
    console.log('Terminating Python backend process...');
    pythonProcess.kill();
  }
});

// IPC handlers for communication with the renderer process
ipcMain.handle('get-backend-url', () => {
  return `http://localhost:${backendPort}`;
});
