#!/usr/bin/env python3
"""
ZK-FL Parameter Configuration Website
Interactive web interface for tweaking all hardcoded parameters in the ZK-FL system
"""

import asyncio
import json
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import numpy as np

# Import our existing modules
from metrics_collector import MetricsCollector
from fl_server import FederatedServer
from advanced_circuit_optimizer import AdvancedCircuitOptimizer
from non_iid_data_engine import NonIIDDataEngine

@dataclass
class ZKFLConfig:
    """Complete configuration for ZK-FL system parameters"""
    # Federated Learning Parameters
    num_clients: int = 10
    num_rounds: int = 20
    client_fraction: float = 0.8
    local_epochs: int = 5
    learning_rate: float = 0.001
    batch_size: int = 32
    
    # Model Architecture
    input_size: int = 13
    hidden_sizes: List[int] = None
    dropout_rate: float = 0.3
    activation_function: str = "ReLU"
    
    # ZKP Circuit Parameters
    constraint_reduction_factor: float = 0.4
    parallel_workers: int = 4
    memory_optimization: bool = True
    batch_processing_size: int = 8
    proof_compression: bool = True
    
    # Non-IID Data Parameters
    alpha: float = 0.5  # Dirichlet concentration
    feature_skew_factor: float = 0.3
    quantity_imbalance_ratio: float = 0.7
    min_samples_per_client: int = 50
    
    # Protogalaxy Aggregation
    aggregation_threshold: int = 3
    verification_timeout: float = 30.0
    proof_batch_size: int = 5
    parallel_verification: bool = True
    
    # Performance Tuning
    websocket_timeout: float = 60.0
    metrics_retention_size: int = 1000
    update_frequency_ms: int = 2000
    max_concurrent_connections: int = 100
    
    # Security Parameters
    zkp_security_level: int = 128
    proof_verification_strictness: str = "high"
    client_authentication: bool = True
    encrypted_communication: bool = True
    
    # Dashboard Settings
    chart_update_interval: int = 5
    real_time_monitoring: bool = True
    static_report_generation: bool = True
    mobile_responsive: bool = True
    
    def __post_init__(self):
        if self.hidden_sizes is None:
            self.hidden_sizes = [64, 32, 16]

class ZKFLConfigManager:
    """Manages ZK-FL system configuration and parameter updates"""
    
    def __init__(self, config_file: str = "zkfl_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.active_connections: List[WebSocket] = []
        
    def load_config(self) -> ZKFLConfig:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return ZKFLConfig(**data)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        
        return ZKFLConfig()
    
    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            for key, value in updates.items():
                if hasattr(self.config, key):
                    # Type conversion based on current type
                    current_type = type(getattr(self.config, key))
                    if current_type == list:
                        if isinstance(value, str):
                            value = [int(x.strip()) for x in value.split(',')]
                    else:
                        value = current_type(value)
                    
                    setattr(self.config, key, value)
            
            self.save_config()
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def get_parameter_categories(self) -> Dict[str, List[str]]:
        """Get parameters organized by category"""
        return {
            "Federated Learning": [
                "num_clients", "num_rounds", "client_fraction", 
                "local_epochs", "learning_rate", "batch_size"
            ],
            "Model Architecture": [
                "input_size", "hidden_sizes", "dropout_rate", "activation_function"
            ],
            "ZKP Circuit": [
                "constraint_reduction_factor", "parallel_workers", 
                "memory_optimization", "batch_processing_size", "proof_compression"
            ],
            "Non-IID Data": [
                "alpha", "feature_skew_factor", "quantity_imbalance_ratio", 
                "min_samples_per_client"
            ],
            "Protogalaxy": [
                "aggregation_threshold", "verification_timeout", 
                "proof_batch_size", "parallel_verification"
            ],
            "Performance": [
                "websocket_timeout", "metrics_retention_size", 
                "update_frequency_ms", "max_concurrent_connections"
            ],
            "Security": [
                "zkp_security_level", "proof_verification_strictness", 
                "client_authentication", "encrypted_communication"
            ],
            "Dashboard": [
                "chart_update_interval", "real_time_monitoring", 
                "static_report_generation", "mobile_responsive"
            ]
        }

class ZKFLConfigWebsite:
    """Web interface for ZK-FL parameter configuration"""
    
    def __init__(self, host: str = "localhost", port: int = 8081):
        self.host = host
        self.port = port
        self.app = FastAPI(title="ZK-FL Configuration Portal")
        self.config_manager = ZKFLConfigManager()
        
        self._setup_routes()
        self._setup_logging()
        
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
        async def config_portal():
            return self._generate_config_html()
            
        @self.app.get("/api/config")
        async def get_config():
            """Get current configuration"""
            return {
                "config": asdict(self.config_manager.config),
                "categories": self.config_manager.get_parameter_categories()
            }
            
        @self.app.post("/api/config")
        async def update_config(request: Request):
            """Update configuration"""
            form_data = await request.form()
            updates = dict(form_data)
            
            success = self.config_manager.update_config(updates)
            if success:
                # Broadcast update to connected clients
                await self._broadcast_config_update()
                return {"status": "success", "message": "Configuration updated successfully"}
            else:
                return {"status": "error", "message": "Failed to update configuration"}
                
        @self.app.post("/api/reset")
        async def reset_config():
            """Reset to default configuration"""
            self.config_manager.config = ZKFLConfig()
            self.config_manager.save_config()
            await self._broadcast_config_update()
            return {"status": "success", "message": "Configuration reset to defaults"}
            
        @self.app.get("/api/export")
        async def export_config():
            """Export current configuration as JSON"""
            return JSONResponse(
                content=asdict(self.config_manager.config),
                headers={"Content-Disposition": "attachment; filename=zkfl_config.json"}
            )
            
        @self.app.post("/api/import")
        async def import_config(request: Request):
            """Import configuration from JSON"""
            try:
                data = await request.json()
                self.config_manager.config = ZKFLConfig(**data)
                self.config_manager.save_config()
                await self._broadcast_config_update()
                return {"status": "success", "message": "Configuration imported successfully"}
            except Exception as e:
                return {"status": "error", "message": f"Import failed: {str(e)}"}
                
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.config_manager.active_connections.append(websocket)
            try:
                while True:
                    await asyncio.sleep(1)
            except WebSocketDisconnect:
                self.config_manager.active_connections.remove(websocket)
                
        @self.app.get("/api/validate")
        async def validate_config():
            """Validate current configuration"""
            validation_results = self._validate_configuration()
            return {"validation": validation_results}
            
    def _generate_config_html(self) -> str:
        """Generate the configuration portal HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZK-FL Configuration Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 10px;
            color: white;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-success { background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); color: white; }
        .btn-warning { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
        .btn-info { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .config-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .config-category {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .category-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 5px;
        }
        .param-group {
            margin-bottom: 15px;
        }
        .param-label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #555;
        }
        .param-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .param-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
        }
        .param-description {
            font-size: 12px;
            color: #666;
            margin-top: 3px;
        }
        .status-message {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            display: none;
        }
        .status-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .validation-panel {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .validation-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        .validation-icon {
            margin-right: 8px;
            font-weight: bold;
        }
        .valid { color: #28a745; }
        .invalid { color: #dc3545; }
        .warning { color: #ffc107; }
        @media (max-width: 768px) {
            .config-grid { grid-template-columns: 1fr; }
            .controls { flex-direction: column; align-items: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚙️ ZK-FL Configuration Portal</h1>
            <p>Tweak all system parameters in real-time</p>
        </div>
        
        <div class="controls">
            <button class="btn btn-success" onclick="saveConfiguration()">💾 Save Configuration</button>
            <button class="btn btn-warning" onclick="resetConfiguration()">🔄 Reset to Defaults</button>
            <button class="btn btn-info" onclick="exportConfiguration()">📤 Export Config</button>
            <button class="btn btn-primary" onclick="validateConfiguration()">✅ Validate</button>
            <button class="btn btn-primary" onclick="loadDashboard()" target="_blank">📊 Open Dashboard</button>
        </div>
        
        <div id="statusMessage" class="status-message"></div>
        
        <form id="configForm">
            <div class="config-grid" id="configGrid">
                <!-- Configuration categories will be populated here -->
            </div>
        </form>
        
        <div id="validationPanel" class="validation-panel" style="display: none;">
            <h4>🔍 Configuration Validation</h4>
            <div id="validationResults"></div>
        </div>
    </div>
    
    <script>
        let currentConfig = {};
        let ws = null;
        
        // Parameter descriptions and constraints
        const paramDescriptions = {
            'num_clients': 'Number of federated learning clients (hospitals)',
            'num_rounds': 'Total training rounds for federated learning',
            'client_fraction': 'Fraction of clients participating per round (0.0-1.0)',
            'local_epochs': 'Local training epochs per client',
            'learning_rate': 'Learning rate for model training',
            'batch_size': 'Batch size for training',
            'input_size': 'Input dimension for the model',
            'hidden_sizes': 'Hidden layer sizes (comma-separated)',
            'dropout_rate': 'Dropout rate for regularization (0.0-1.0)',
            'activation_function': 'Activation function (ReLU, Tanh, Sigmoid)',
            'constraint_reduction_factor': 'ZKP constraint reduction factor (0.0-1.0)',
            'parallel_workers': 'Number of parallel workers for proof generation',
            'memory_optimization': 'Enable memory optimization',
            'batch_processing_size': 'Batch size for proof processing',
            'proof_compression': 'Enable proof compression',
            'alpha': 'Dirichlet concentration parameter for non-IID data',
            'feature_skew_factor': 'Feature distribution skew factor',
            'quantity_imbalance_ratio': 'Data quantity imbalance ratio',
            'min_samples_per_client': 'Minimum samples per client',
            'aggregation_threshold': 'Minimum proofs for aggregation',
            'verification_timeout': 'Proof verification timeout (seconds)',
            'proof_batch_size': 'Batch size for proof aggregation',
            'parallel_verification': 'Enable parallel proof verification',
            'websocket_timeout': 'WebSocket connection timeout',
            'metrics_retention_size': 'Number of metrics to retain',
            'update_frequency_ms': 'Dashboard update frequency (milliseconds)',
            'max_concurrent_connections': 'Maximum concurrent connections',
            'zkp_security_level': 'ZKP security level in bits',
            'proof_verification_strictness': 'Verification strictness (low, medium, high)',
            'client_authentication': 'Enable client authentication',
            'encrypted_communication': 'Enable encrypted communication',
            'chart_update_interval': 'Chart update interval (seconds)',
            'real_time_monitoring': 'Enable real-time monitoring',
            'static_report_generation': 'Enable static report generation',
            'mobile_responsive': 'Enable mobile responsive design'
        };
        
        async function loadConfiguration() {
            try {
                const response = await fetch('/api/config');
                const data = await response.json();
                currentConfig = data.config;
                renderConfigurationForm(data.config, data.categories);
                initWebSocket();
            } catch (error) {
                showStatus('Error loading configuration: ' + error.message, 'error');
            }
        }
        
        function renderConfigurationForm(config, categories) {
            const grid = document.getElementById('configGrid');
            grid.innerHTML = '';
            
            for (const [categoryName, paramNames] of Object.entries(categories)) {
                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'config-category';
                
                const title = document.createElement('div');
                title.className = 'category-title';
                title.textContent = categoryName;
                categoryDiv.appendChild(title);
                
                paramNames.forEach(paramName => {
                    const paramDiv = document.createElement('div');
                    paramDiv.className = 'param-group';
                    
                    const label = document.createElement('label');
                    label.className = 'param-label';
                    label.textContent = paramName.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                    
                    const input = document.createElement('input');
                    input.className = 'param-input';
                    input.name = paramName;
                    input.id = paramName;
                    
                    const value = config[paramName];
                    if (typeof value === 'boolean') {
                        input.type = 'checkbox';
                        input.checked = value;
                    } else if (Array.isArray(value)) {
                        input.type = 'text';
                        input.value = value.join(', ');
                    } else {
                        input.type = typeof value === 'number' ? 'number' : 'text';
                        input.value = value;
                        if (typeof value === 'number') {
                            input.step = value % 1 === 0 ? '1' : '0.001';
                        }
                    }
                    
                    const description = document.createElement('div');
                    description.className = 'param-description';
                    description.textContent = paramDescriptions[paramName] || '';
                    
                    paramDiv.appendChild(label);
                    paramDiv.appendChild(input);
                    paramDiv.appendChild(description);
                    categoryDiv.appendChild(paramDiv);
                });
                
                grid.appendChild(categoryDiv);
            }
        }
        
        async function saveConfiguration() {
            try {
                const formData = new FormData(document.getElementById('configForm'));
                const response = await fetch('/api/config', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                showStatus(result.message, result.status);
                if (result.status === 'success') {
                    loadConfiguration(); // Reload to reflect changes
                }
            } catch (error) {
                showStatus('Error saving configuration: ' + error.message, 'error');
            }
        }
        
        async function resetConfiguration() {
            if (confirm('Are you sure you want to reset all parameters to defaults?')) {
                try {
                    const response = await fetch('/api/reset', { method: 'POST' });
                    const result = await response.json();
                    showStatus(result.message, result.status);
                    loadConfiguration();
                } catch (error) {
                    showStatus('Error resetting configuration: ' + error.message, 'error');
                }
            }
        }
        
        async function exportConfiguration() {
            try {
                const response = await fetch('/api/export');
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'zkfl_config.json';
                a.click();
                window.URL.revokeObjectURL(url);
                showStatus('Configuration exported successfully', 'success');
            } catch (error) {
                showStatus('Error exporting configuration: ' + error.message, 'error');
            }
        }
        
        async function validateConfiguration() {
            try {
                const response = await fetch('/api/validate');
                const data = await response.json();
                displayValidationResults(data.validation);
            } catch (error) {
                showStatus('Error validating configuration: ' + error.message, 'error');
            }
        }
        
        function displayValidationResults(validation) {
            const panel = document.getElementById('validationPanel');
            const results = document.getElementById('validationResults');
            
            results.innerHTML = '';
            validation.forEach(item => {
                const div = document.createElement('div');
                div.className = 'validation-item';
                
                const icon = document.createElement('span');
                icon.className = 'validation-icon ' + item.status;
                icon.textContent = item.status === 'valid' ? '✓' : 
                                 item.status === 'invalid' ? '✗' : '⚠';
                
                const text = document.createElement('span');
                text.textContent = item.message;
                
                div.appendChild(icon);
                div.appendChild(text);
                results.appendChild(div);
            });
            
            panel.style.display = 'block';
        }
        
        function loadDashboard() {
            window.open('http://localhost:8080', '_blank');
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.textContent = message;
            statusDiv.className = 'status-message status-' + type;
            statusDiv.style.display = 'block';
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
        
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            ws.onopen = () => console.log('WebSocket connected');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'config_update') {
                    loadConfiguration();
                }
            };
            ws.onclose = () => {
                console.log('WebSocket disconnected');
                setTimeout(initWebSocket, 5000);
            };
        }
        
        // Load configuration on page load
        document.addEventListener('DOMContentLoaded', loadConfiguration);
    </script>
</body>
</html>
        """
        
    async def _broadcast_config_update(self):
        """Broadcast configuration updates to connected clients"""
        if not self.config_manager.active_connections:
            return
            
        message = json.dumps({
            "type": "config_update",
            "config": asdict(self.config_manager.config)
        })
        
        failed_connections = []
        for connection in self.config_manager.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                failed_connections.append(connection)
                
        for connection in failed_connections:
            self.config_manager.active_connections.remove(connection)
            
    def _validate_configuration(self) -> List[Dict[str, str]]:
        """Validate current configuration parameters"""
        validation_results = []
        config = self.config_manager.config
        
        # Federated Learning validation
        if config.num_clients < 2:
            validation_results.append({"status": "invalid", "message": "Number of clients must be at least 2"})
        elif config.num_clients > 100:
            validation_results.append({"status": "warning", "message": "Large number of clients may impact performance"})
        else:
            validation_results.append({"status": "valid", "message": f"Client count ({config.num_clients}) is optimal"})
            
        if not 0.1 <= config.client_fraction <= 1.0:
            validation_results.append({"status": "invalid", "message": "Client fraction must be between 0.1 and 1.0"})
        else:
            validation_results.append({"status": "valid", "message": "Client fraction is valid"})
            
        if config.learning_rate <= 0 or config.learning_rate > 1:
            validation_results.append({"status": "warning", "message": "Learning rate seems unusual"})
        else:
            validation_results.append({"status": "valid", "message": "Learning rate is reasonable"})
            
        # ZKP Circuit validation
        if not 0.1 <= config.constraint_reduction_factor <= 0.8:
            validation_results.append({"status": "warning", "message": "Constraint reduction factor may be suboptimal"})
        else:
            validation_results.append({"status": "valid", "message": "Constraint reduction is well-tuned"})
            
        if config.parallel_workers < 1 or config.parallel_workers > 16:
            validation_results.append({"status": "warning", "message": "Parallel workers count may not be optimal"})
        else:
            validation_results.append({"status": "valid", "message": "Parallel workers count is appropriate"})
            
        # Non-IID validation
        if config.alpha <= 0:
            validation_results.append({"status": "invalid", "message": "Dirichlet alpha must be positive"})
        elif config.alpha < 0.1:
            validation_results.append({"status": "warning", "message": "Very low alpha creates extreme non-IID data"})
        else:
            validation_results.append({"status": "valid", "message": "Dirichlet alpha is appropriate"})
            
        # Security validation
        if config.zkp_security_level < 80:
            validation_results.append({"status": "invalid", "message": "Security level too low for production"})
        elif config.zkp_security_level > 256:
            validation_results.append({"status": "warning", "message": "Very high security level may impact performance"})
        else:
            validation_results.append({"status": "valid", "message": "Security level is appropriate"})
            
        return validation_results
        
    async def start_server(self):
        """Start the configuration website server"""
        self.logger.info(f"Starting ZK-FL Configuration Portal on {self.host}:{self.port}")
        
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

def main():
    """Main entry point for the configuration website"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ZK-FL Configuration Portal")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    
    args = parser.parse_args()
    
    website = ZKFLConfigWebsite(host=args.host, port=args.port)
    
    print(f"🔧 Starting ZK-FL Configuration Portal at http://{args.host}:{args.port}")
    print("Features:")
    print("  • Interactive parameter tweaking")
    print("  • Real-time configuration validation")
    print("  • Export/Import configuration files")
    print("  • Live synchronization with dashboard")
    
    asyncio.run(website.start_server())

if __name__ == "__main__":
    main()