#!/usr/bin/env python3
"""
ZK-FL Main Portal - Unified Entry Point
Single entry point to start and manage the entire ZK-FL system
"""

import asyncio
import subprocess
import threading
import time
import webbrowser
from typing import Dict, Optional
import logging
import signal
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

class ZKFLMainPortal:
    """Main portal to launch and manage all ZK-FL components"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.app = FastAPI(title="ZK-FL Main Portal")
        
        # Component processes
        self.processes: Dict[str, subprocess.Popen] = {}
        self.component_ports = {
            'dashboard': 8080,
            'config': 8081
        }
        
        # Setup routes
        self._setup_routes()
        self._setup_logging()
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def main_portal():
            return self._generate_main_portal_html()
            
        @self.app.get("/dashboard")
        async def redirect_dashboard():
            await self._ensure_component_running('dashboard')
            return RedirectResponse(url=f"http://{self.host}:{self.component_ports['dashboard']}")
            
        @self.app.get("/config")
        async def redirect_config():
            await self._ensure_component_running('config')
            return RedirectResponse(url=f"http://{self.host}:{self.component_ports['config']}")
            
        @self.app.post("/api/start/{component}")
        async def start_component(component: str):
            success = await self._start_component(component)
            return {"status": "started" if success else "failed", "component": component}
            
        @self.app.post("/api/stop/{component}")
        async def stop_component(component: str):
            success = self._stop_component(component)
            return {"status": "stopped" if success else "failed", "component": component}
            
        @self.app.get("/api/status")
        async def get_status():
            return {
                "components": {
                    name: self._is_component_running(name) 
                    for name in self.component_ports.keys()
                },
                "ports": self.component_ports
            }
    
    def _generate_main_portal_html(self) -> str:
        """Generate the main portal HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZK-FL System Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 15px;
            color: white;
        }
        .header h1 { font-size: 3em; margin-bottom: 15px; }
        .header p { font-size: 1.3em; opacity: 0.9; }
        .components-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        .component-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 3px solid transparent;
        }
        .component-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        .component-card.dashboard {
            border-color: #4facfe;
        }
        .component-card.config {
            border-color: #43e97b;
        }
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .card-icon {
            font-size: 3em;
            margin-right: 20px;
        }
        .card-title {
            font-size: 1.8em;
            font-weight: 700;
            color: #333;
        }
        .card-description {
            font-size: 1.1em;
            color: #666;
            margin-bottom: 25px;
            line-height: 1.6;
        }
        .card-features {
            list-style: none;
            margin-bottom: 25px;
        }
        .card-features li {
            padding: 8px 0;
            color: #555;
        }
        .card-features li:before {
            content: "✓";
            color: #4CAF50;
            font-weight: bold;
            margin-right: 10px;
        }
        .card-actions {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-secondary {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 10px;
        }
        .status-running { background: #4CAF50; }
        .status-stopped { background: #f44336; }
        .system-info {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
        }
        .system-info h3 {
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .info-item {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
        }
        .info-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .info-value {
            font-size: 1.2em;
            font-weight: 700;
            margin-top: 5px;
        }
        @media (max-width: 768px) {
            .components-grid { grid-template-columns: 1fr; }
            .card-actions { justify-content: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 ZK-FL System Portal</h1>
            <p>Zero-Knowledge Federated Learning Platform</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Unified entry point for all ZK-FL components</p>
        </div>
        
        <div class="components-grid">
            <!-- Production Dashboard -->
            <div class="component-card dashboard">
                <div class="card-header">
                    <div class="card-icon">📊</div>
                    <div>
                        <div class="card-title">Production Dashboard</div>
                        <span class="status-indicator status-stopped" id="dashboard-status"></span>
                    </div>
                </div>
                <div class="card-description">
                    Real-time monitoring of ZK-FL experiments with live metrics visualization and system performance tracking.
                </div>
                <ul class="card-features">
                    <li>Real hospital client proof generation</li>
                    <li>Protogalaxy aggregation monitoring</li>
                    <li>100% valid proof verification (no attacks)</li>
                    <li>Configurable FL rounds and participants</li>
                    <li>Live performance charts and metrics</li>
                </ul>
                <div class="card-actions">
                    <a href="/dashboard" class="btn btn-primary">📊 Open Dashboard</a>
                    <button class="btn btn-secondary" onclick="startComponent('dashboard')">🚀 Start</button>
                </div>
            </div>
            
            <!-- Configuration Portal -->
            <div class="component-card config">
                <div class="card-header">
                    <div class="card-icon">⚙️</div>
                    <div>
                        <div class="card-title">Configuration Portal</div>
                        <span class="status-indicator status-stopped" id="config-status"></span>
                    </div>
                </div>
                <div class="card-description">
                    Interactive web interface for tweaking all ZK-FL system parameters in real-time.
                </div>
                <ul class="card-features">
                    <li>Federated learning parameters (rounds, clients)</li>
                    <li>ZKP circuit optimization settings</li>
                    <li>Non-IID data distribution controls</li>
                    <li>Protogalaxy aggregation configuration</li>
                    <li>Export/Import configuration files</li>
                </ul>
                <div class="card-actions">
                    <a href="/config" class="btn btn-secondary">⚙️ Open Config</a>
                    <button class="btn btn-primary" onclick="startComponent('config')">🚀 Start</button>
                </div>
            </div>
        </div>
        
        <div class="system-info">
            <h3>🏥 ZK-FL System Architecture</h3>
            <p>Correct federated learning flow: Training → Proof Generation → Collection → Protogalaxy Aggregation → Single Verification</p>
            
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Portal Port</div>
                    <div class="info-value">:8000</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Dashboard Port</div>
                    <div class="info-value">:8080</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Config Port</div>
                    <div class="info-value">:8081</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Architecture</div>
                    <div class="info-value">Correct ZK-FL</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update status indicators
                for (const [component, isRunning] of Object.entries(data.components)) {
                    const indicator = document.getElementById(`${component}-status`);
                    if (indicator) {
                        indicator.className = `status-indicator ${isRunning ? 'status-running' : 'status-stopped'}`;
                    }
                }
            } catch (error) {
                console.error('Failed to update status:', error);
            }
        }
        
        async function startComponent(component) {
            try {
                const response = await fetch(`/api/start/${component}`, { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'started') {
                    console.log(`${component} started successfully`);
                    setTimeout(updateStatus, 2000); // Update status after delay
                }
            } catch (error) {
                console.error(`Failed to start ${component}:`, error);
            }
        }
        
        // Update status on load and periodically
        document.addEventListener('DOMContentLoaded', updateStatus);
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
        """
    
    async def _ensure_component_running(self, component: str):
        """Ensure a component is running before redirecting"""
        if not self._is_component_running(component):
            await self._start_component(component)
            # Wait a moment for the component to start
            await asyncio.sleep(2)
    
    async def _start_component(self, component: str) -> bool:
        """Start a specific component"""
        if self._is_component_running(component):
            self.logger.info(f"{component} is already running")
            return True
            
        try:
            if component == 'dashboard':
                cmd = ['python3', 'production_dashboard.py', '--host', self.host, '--port', str(self.component_ports['dashboard'])]
            elif component == 'config':
                cmd = ['python3', 'zkfl_config_website.py', '--port', str(self.component_ports['config'])]
            else:
                self.logger.error(f"Unknown component: {component}")
                return False
                
            # Start process in background
            process = subprocess.Popen(
                cmd,
                cwd=Path.cwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes[component] = process
            self.logger.info(f"Started {component} on port {self.component_ports[component]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start {component}: {e}")
            return False
    
    def _stop_component(self, component: str) -> bool:
        """Stop a specific component"""
        if component in self.processes:
            try:
                self.processes[component].terminate()
                self.processes[component].wait(timeout=5)
                del self.processes[component]
                self.logger.info(f"Stopped {component}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to stop {component}: {e}")
                # Force kill if needed
                try:
                    self.processes[component].kill()
                    del self.processes[component]
                    return True
                except:
                    return False
        return True
    
    def _is_component_running(self, component: str) -> bool:
        """Check if a component is running"""
        if component not in self.processes:
            return False
        return self.processes[component].poll() is None
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Shutting down ZK-FL Portal...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Shutdown all components"""
        for component in list(self.processes.keys()):
            self._stop_component(component)
    
    def run(self):
        """Run the main portal"""
        self.logger.info(f"🚀 Starting ZK-FL Main Portal at http://{self.host}:{self.port}")
        self.logger.info("Available components:")
        self.logger.info(f"  📊 Dashboard: http://{self.host}:{self.component_ports['dashboard']}")
        self.logger.info(f"  ⚙️  Config: http://{self.host}:{self.component_ports['config']}")
        
        # Auto-open browser
        threading.Timer(2, lambda: webbrowser.open(f"http://{self.host}:{self.port}")).start()
        
        try:
            uvicorn.run(
                self.app, 
                host=self.host, 
                port=self.port,
                log_level="info"
            )
        except KeyboardInterrupt:
            self.shutdown()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ZK-FL Main Portal")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    portal = ZKFLMainPortal(host=args.host, port=args.port)
    portal.run()