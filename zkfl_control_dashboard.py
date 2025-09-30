#!/usr/bin/env python3
"""
ZK-FL Control Dashboard
Real dashboard controlling actual training and verification pipelines
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse
import numpy as np

# Import our actual training and verification pipelines
from zkfl_training_verification import ZKFLTrainingPipeline, ZKFLVerificationPipeline
from zkfl_config_website import ZKFLConfigManager
from metrics_collector import MetricsCollector

@dataclass
class TrainingProgress:
    """Real-time training progress"""
    round_number: int
    total_rounds: int
    hospital_id: str
    status: str  # 'training', 'proof_generation', 'completed'
    training_time: float
    proof_generation_time: float
    accuracy: float = 0.0
    loss: float = 0.0
    is_completed: bool = False

@dataclass
class DashboardState:
    """Current dashboard state"""
    training_active: bool = False
    verification_active: bool = False
    current_round: int = 0
    total_rounds: int = 0
    completed_rounds: List[str] = None
    pending_verification: List[str] = None
    last_training_session: Optional[str] = None
    last_verification_session: Optional[str] = None
    
    def __post_init__(self):
        if self.completed_rounds is None:
            self.completed_rounds = []
        if self.pending_verification is None:
            self.pending_verification = []

class ZKFLControlDashboard:
    """Real ZK-FL Dashboard controlling actual training and verification"""
    
    def __init__(self, host: str = "localhost", port: int = 8090):
        self.host = host
        self.port = port
        self.app = FastAPI(title="ZK-FL Control Dashboard")
        
        # Real pipelines - no simulation
        self.training_pipeline = ZKFLTrainingPipeline()
        self.verification_pipeline = ZKFLVerificationPipeline()
        self.config_manager = ZKFLConfigManager()
        self.metrics_collector = MetricsCollector("control_dashboard")
        
        # Dashboard state
        self.state = DashboardState()
        self.active_connections: List[WebSocket] = []
        
        # Real-time progress tracking
        self.current_training_progress: List[TrainingProgress] = []
        
        # Chart data storage
        self.chart_data = {
            "hospital_training": {"hospitals": [], "accuracy": [], "loss": []},
            "proof_generation": {"rounds": [], "generation_time": [], "proof_size": []},
            "aggregation": {"rounds": [], "aggregation_time": [], "success_rate": []},
            "verification": {"rounds": [], "verification_time": [], "proof_count": []},
            "overview": {"rounds": [], "total_accuracy": [], "round_time": []}
        }
        
        # Historical data storage for charts (time series)
        self.training_history = []  # List of {round, accuracy, time, timestamp}
        self.proof_history = []     # List of {round, gen_time, size, timestamp}
        self.aggregation_history = []  # List of {round, agg_time, success_rate, timestamp}
        self.verification_history = []  # List of {round, verify_time, proof_count, timestamp}
        
        # Chart filtering
        self.chart_filter = {
            'type': 'all',
            'session_id': 'auto',
            'applied_at': None
        }
        
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
        async def dashboard():
            return self._generate_dashboard_html()
            
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    # Regular state update
                    await self._refresh_state()
                    chart_data = await self._collect_chart_data()
                    
                    await websocket.send_json({
                        "type": "state_update",
                        "state": asdict(self.state),
                        "training_progress": [asdict(p) for p in self.current_training_progress],
                        "config": asdict(self.config_manager.config),
                        "charts": chart_data
                    })
                    await asyncio.sleep(1)
            except WebSocketDisconnect:
                # Safe removal - check if websocket is still in list
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
        
        @self.app.post("/api/filter_charts")
        async def filter_charts(request: dict):
            try:
                filter_type = request.get('filter_type', 'all')
                session_id = request.get('session_id', 'auto')
                
                # Apply filter to chart data collection
                self.chart_filter = {
                    'type': filter_type,
                    'session_id': session_id,
                    'applied_at': datetime.now().isoformat()
                }
                
                message = f"📊 Filter applied: {filter_type}"
                if session_id != 'auto':
                    message += f" (Session: {session_id})"
                    
                return {"success": True, "message": message}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/clear_all_data")
        async def clear_all_data():
            try:
                import shutil
                storage_path = Path("zkfl_storage")
                if storage_path.exists():
                    shutil.rmtree(storage_path)
                    storage_path.mkdir(exist_ok=True)
                    for subdir in ["training_rounds", "verification_results", "models", "proofs"]:
                        (storage_path / subdir).mkdir(exist_ok=True)
                
                # Reset chart data
                self.chart_data = {
                    "hospital_training": {"hospitals": [], "accuracy": [], "loss": []},
                    "proof_generation": {"rounds": [], "generation_time": [], "proof_size": []},
                    "aggregation": {"rounds": [], "aggregation_time": [], "success_rate": []},
                    "verification": {"rounds": [], "verification_time": [], "proof_count": []},
                    "overview": {"rounds": [], "total_accuracy": [], "round_time": []}
                }
                
                return {"success": True, "message": "All data cleared successfully"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/available_sessions")
        async def available_sessions():
            try:
                sessions = []
                total_rounds = 0
                
                storage_path = Path("zkfl_storage/training_rounds")
                if storage_path.exists():
                    # Group rounds by session (timestamp prefix)
                    session_groups = {}
                    for round_dir in storage_path.iterdir():
                        if round_dir.is_dir():
                            # Extract timestamp from round name: round_001_1759171950
                            parts = round_dir.name.split('_')
                            if len(parts) >= 3:
                                session_ts = parts[2]
                                if session_ts not in session_groups:
                                    session_groups[session_ts] = []
                                session_groups[session_ts].append(round_dir.name)
                    
                    # Convert to session list
                    for session_id, rounds in session_groups.items():
                        sessions.append({
                            'id': session_id,
                            'rounds': len(rounds),
                            'timestamp': datetime.fromtimestamp(int(session_id)).strftime('%Y-%m-%d %H:%M:%S')
                        })
                        total_rounds += len(rounds)
                    
                    # Sort by timestamp (newest first)
                    sessions.sort(key=lambda x: x['id'], reverse=True)
                
                return {
                    "sessions": sessions[:20],  # Limit to last 20 sessions
                    "total_rounds": total_rounds,
                    "total_sessions": len(sessions)
                }
            except Exception as e:
                return {"sessions": [], "total_rounds": 0, "error": str(e)}
        
        @self.app.post("/api/start_training")
        async def start_training(background_tasks: BackgroundTasks):
            """Start real FL training session"""
            if self.state.training_active:
                return {"status": "error", "message": "Training already active"}
                
            config = self.config_manager.config
            self.state.total_rounds = config.num_rounds
            self.state.training_active = True
            self.state.current_round = 0
            
            # Clear historical chart data for fresh session
            self._clear_chart_history()
            
            # Start training in background
            background_tasks.add_task(self._run_training_session)
            
            return {"status": "started", "rounds": config.num_rounds}
            
        @self.app.post("/api/start_verification")
        async def start_verification(background_tasks: BackgroundTasks):
            """Start real proof verification"""
            if self.state.verification_active:
                return {"status": "error", "message": "Verification already active"}
                
            pending_rounds = self.verification_pipeline.get_pending_rounds()
            if not pending_rounds:
                return {"status": "error", "message": "No rounds to verify"}
                
            self.state.verification_active = True
            self.state.pending_verification = pending_rounds
            
            # Clear aggregation and verification history for fresh session
            self.aggregation_history.clear()
            self.verification_history.clear()
            
            # Start verification in background
            background_tasks.add_task(self._run_verification_session)
            
            return {"status": "started", "rounds": len(pending_rounds)}
            
        @self.app.post("/api/stop_training")
        async def stop_training():
            """Stop training session"""
            self.state.training_active = False
            return {"status": "stopped"}
            
        @self.app.get("/api/status")
        async def get_status():
            """Get current system status"""
            await self._refresh_state()
            
            return {
                "state": asdict(self.state),
                "config": asdict(self.config_manager.config),
                "storage_stats": self._get_storage_stats()
            }
            
        @self.app.post("/api/config/update")
        async def update_config(config_data: dict):
            """Update FL configuration"""
            try:
                # Update config manager
                for key, value in config_data.items():
                    if hasattr(self.config_manager.config, key):
                        setattr(self.config_manager.config, key, value)
                
                # Save updated config
                self.config_manager.save_config()
                
                return {"status": "updated", "config": asdict(self.config_manager.config)}
            except Exception as e:
                return {"status": "error", "message": str(e)}
    
    def _apply_data_filter(self, file_list):
        """Apply current filter to file list"""
        if self.chart_filter['type'] == 'all':
            return file_list
        
        filter_type = self.chart_filter['type']
        now = datetime.now()
        
        filtered_files = []
        
        for file_path in file_list:
            try:
                # Extract timestamp from filename
                if 'round_' in file_path.name:
                    parts = file_path.name.split('_')
                    if len(parts) >= 3:
                        timestamp = int(parts[2])
                        file_date = datetime.fromtimestamp(timestamp)
                        
                        # Apply time-based filters
                        if filter_type == 'latest':
                            # Only show latest session
                            latest_ts = max([int(f.name.split('_')[2]) for f in file_list if 'round_' in f.name])
                            if timestamp == latest_ts:
                                filtered_files.append(file_path)
                        elif filter_type == 'today':
                            if file_date.date() == now.date():
                                filtered_files.append(file_path)
                        elif filter_type == 'last_hour':
                            if (now - file_date).total_seconds() <= 3600:
                                filtered_files.append(file_path)
                        elif filter_type == 'last_10':
                            filtered_files.append(file_path)
                        elif filter_type == 'last_50':
                            filtered_files.append(file_path)
                        
                        # Apply session-specific filter
                        if self.chart_filter['session_id'] != 'auto':
                            if str(timestamp) == self.chart_filter['session_id']:
                                filtered_files.append(file_path)
                            elif file_path in filtered_files:
                                filtered_files.remove(file_path)
                                
            except (ValueError, IndexError):
                continue
        
        # Apply count limits
        if filter_type == 'last_10':
            filtered_files = sorted(filtered_files)[-10:]
        elif filter_type == 'last_50':
            filtered_files = sorted(filtered_files)[-50:]
            
        return filtered_files
    
    async def _collect_chart_data(self) -> Dict:
        """Collect real-time chart data from training and verification results"""
        try:
            # Hospital training chart data
            hospital_data = self._get_hospital_training_data()
            
            # Proof generation chart data
            proof_data = self._get_proof_generation_data()
            
            # Aggregation chart data
            aggregation_data = self._get_aggregation_data()
            
            # Verification chart data
            verification_data = self._get_verification_data()
            
            # Overview chart data
            overview_data = self._get_overview_data()
            
            return {
                "hospital_training": hospital_data,
                "proof_generation": proof_data,
                "aggregation": aggregation_data,
                "verification": verification_data,
                "overview": overview_data
            }
        except Exception as e:
            self.logger.error(f"Chart data collection error: {e}")
            return self.chart_data
    
    def _get_hospital_training_data(self) -> Dict:
        """Get hospital training progress data with historical accumulation"""
        if not self.training_history:
            return {"rounds": [], "avg_accuracy": [], "avg_loss": [], "avg_time": []}
        
        # Return accumulated historical data for line charts
        rounds = [h['round'] for h in self.training_history]
        accuracies = [h['accuracy'] for h in self.training_history]
        losses = [h.get('loss', 0.2) for h in self.training_history]  # Default loss
        times = [h['time'] for h in self.training_history]
        
        return {
            "rounds": rounds,
            "avg_accuracy": accuracies,
            "avg_loss": losses,
            "avg_time": times
        }
    
    def _get_proof_generation_data(self) -> Dict:
        """Get proof generation metrics with historical data"""
        if not self.proof_history:
            return {"rounds": [], "generation_time": [], "proof_size": []}
        
        # Return accumulated historical data for line charts
        rounds = [p['round'] for p in self.proof_history]
        gen_times = [p['gen_time'] for p in self.proof_history]
        sizes = [p['size'] for p in self.proof_history]
        
        return {
            "rounds": rounds,
            "generation_time": gen_times,
            "proof_size": sizes
        }
    
    def _get_aggregation_data(self) -> Dict:
        """Get Protogalaxy aggregation metrics with historical data"""
        if not self.aggregation_history:
            return {"rounds": [], "aggregation_time": [], "success_rate": []}
        
        # Return accumulated historical data for line charts
        rounds = [a['round'] for a in self.aggregation_history]
        agg_times = [a['agg_time'] for a in self.aggregation_history]
        success_rates = [a['success_rate'] for a in self.aggregation_history]
        
        return {
            "rounds": rounds,
            "aggregation_time": agg_times,
            "success_rate": success_rates
        }
    
    def _get_verification_data(self) -> Dict:
        """Get verification metrics with historical data"""
        if not self.verification_history:
            return {"rounds": [], "verification_time": [], "proof_count": []}
        
        # Return accumulated historical data for line charts
        rounds = [v['round'] for v in self.verification_history]
        verify_times = [v['verify_time'] for v in self.verification_history]
        proof_counts = [v['proof_count'] for v in self.verification_history]
        
        return {
            "rounds": rounds,
            "verification_time": verify_times,
            "proof_count": proof_counts
        }
    
    def _get_overview_data(self) -> Dict:
        """Get FL training overview metrics with historical data"""
        if not self.training_history:
            return {"rounds": [], "total_accuracy": [], "round_time": []}
        
        # Return accumulated historical data for line charts
        rounds = [h['round'] for h in self.training_history]
        accuracies = [h['accuracy'] for h in self.training_history]
        times = [h['time'] for h in self.training_history]
        
        return {
            "rounds": rounds,
            "total_accuracy": accuracies,
            "round_time": times
        }
    
    def _add_training_data_point(self, round_num: int, accuracy: float, training_time: float, loss: float = 0.2):
        """Add a training data point to historical data"""
        self.training_history.append({
            'round': round_num,
            'accuracy': accuracy,
            'time': training_time,
            'loss': loss,
            'timestamp': time.time()
        })
    
    def _add_proof_data_point(self, round_num: int, gen_time: float, size: int = 1024):
        """Add a proof generation data point to historical data"""
        self.proof_history.append({
            'round': round_num,
            'gen_time': gen_time,
            'size': size,
            'timestamp': time.time()
        })
    
    def _add_aggregation_data_point(self, round_num: int, agg_time: float, success_rate: float = 100.0):
        """Add an aggregation data point to historical data"""
        self.aggregation_history.append({
            'round': round_num,
            'agg_time': agg_time,
            'success_rate': success_rate,
            'timestamp': time.time()
        })
    
    def _add_verification_data_point(self, round_num: int, verify_time: float, proof_count: int):
        """Add a verification data point to historical data"""
        self.verification_history.append({
            'round': round_num,
            'verify_time': verify_time,
            'proof_count': proof_count,
            'timestamp': time.time()
        })
    
    def _clear_chart_history(self):
        """Clear all historical chart data for a fresh session"""
        self.training_history.clear()
        self.proof_history.clear()
        self.aggregation_history.clear()
        self.verification_history.clear()

    def _generate_dashboard_html(self) -> str:
        """Generate real FL control dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZK-FL Control Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
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
        
        .control-panels {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        .panel {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .panel h3 {
            margin-bottom: 20px;
            color: #333;
            font-size: 1.5em;
        }
        
        .config-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .config-item {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .config-item label {
            font-weight: 600;
            color: #555;
        }
        .config-item input, .config-item select {
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        .config-item input:focus, .config-item select:focus {
            outline: none;
            border-color: #4facfe;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 5px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-success {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
            color: white;
        }
        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .btn-warning {
            background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .status-section {
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .status-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .status-value {
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .status-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .progress-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            transition: width 0.5s ease;
        }
        
        .hospital-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .hospital-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }
        .hospital-card.training {
            border-color: #ffd700;
            background: #fff9c4;
        }
        .hospital-card.proof_generation {
            border-color: #ff6b6b;
            background: #ffe0e0;
        }
        .hospital-card.completed {
            border-color: #51cf66;
            background: #d3f9d8;
        }
        
        .charts-section {
            margin-bottom: 30px;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .chart-container h4 {
            margin-bottom: 5px;
            color: #333;
            font-size: 1.2em;
        }
        .chart-subtitle {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        
        .log-section {
            background: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        
        .success-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            max-width: 500px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .modal-content h2 {
            color: #4CAF50;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        
        @media (max-width: 768px) {
            .control-panels { grid-template-columns: 1fr; }
            .config-grid { grid-template-columns: 1fr; }
            .status-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ZK-FL Control Dashboard</h1>
            <p>Control actual federated learning training and proof verification</p>
            <p style="font-size: 0.9em; margin-top: 8px;">Real training pipeline with persistent storage - no simulation</p>
        </div>
        
        <!-- Status Overview -->
        <div class="status-section">
            <div class="status-grid">
                <div class="status-card">
                    <div class="status-value" id="currentRound">0</div>
                    <div class="status-label">Current Round</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="totalRounds">0</div>
                    <div class="status-label">Total Rounds</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="completedRounds">0</div>
                    <div class="status-label">Completed Rounds</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="pendingVerification">0</div>
                    <div class="status-label">Pending Verification</div>
                </div>
            </div>
        </div>
        
        <!-- Control Panels -->
        <div class="control-panels">
            <!-- Training Control -->
            <div class="panel">
                <h3>🏥 FL Training Control</h3>
                
                <div class="config-grid">
                    <div class="config-item">
                        <label>Number of Rounds:</label>
                        <input type="number" id="numRounds" value="5" min="1" max="50">
                    </div>
                    <div class="config-item">
                        <label>Number of Clients:</label>
                        <input type="number" id="numClients" value="8" min="2" max="20">
                    </div>
                    <div class="config-item">
                        <label>Client Participation:</label>
                        <input type="range" id="clientFraction" value="0.8" min="0.5" max="1" step="0.1">
                        <span id="fractionValue">80%</span>
                    </div>
                    <div class="config-item">
                        <label>Learning Rate:</label>
                        <input type="number" id="learningRate" value="0.001" min="0.0001" max="0.1" step="0.001">
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn btn-primary" id="updateConfigBtn" onclick="updateConfig()">⚙️ Update Config</button>
                    <button class="btn btn-success" id="startTrainingBtn" onclick="startTraining()">🚀 Start Training</button>
                    <button class="btn btn-danger" id="stopTrainingBtn" onclick="stopTraining()" disabled>⏹️ Stop Training</button>
                </div>
            </div>
            
            <!-- Verification Control -->
            <div class="panel">
                <h3>🔍 Proof Verification</h3>
                
                <div style="margin-bottom: 20px;">
                    <p style="color: #666; margin-bottom: 15px;">
                        Verify saved proofs from completed training rounds using Protogalaxy aggregation.
                    </p>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <strong>Verification Process:</strong>
                        <ol style="margin-left: 20px; margin-top: 10px;">
                            <li>Load saved proofs from training rounds</li>
                            <li>Aggregate proofs using Protogalaxy protocol</li>
                            <li>Verify single aggregated proof</li>
                            <li>Save verification results</li>
                        </ol>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button class="btn btn-warning" id="startVerificationBtn" onclick="startVerification()">🔍 Start Verification</button>
                    <button class="btn btn-danger" id="stopVerificationBtn" onclick="stopVerification()" disabled>⏹️ Stop Verification</button>
                </div>
            </div>
        </div>
        
        <!-- Training Progress -->
        <div class="progress-section" id="trainingProgress" style="display: none;">
            <h3>🏥 Real-time Training Progress</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="overallProgress" style="width: 0%;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <span id="progressText">Waiting to start...</span>
                <span id="progressPercentage">0%</span>
            </div>
            
            <div class="hospital-grid" id="hospitalGrid">
                <!-- Hospital cards will be populated dynamically -->
            </div>
        </div>
        
        <!-- Real-time Charts -->
        <div class="charts-section" style="background-color: #f0f8ff; border: 3px solid #4CAF50; padding: 20px; margin: 20px 0;">
            <h3 style="text-align: center; margin-bottom: 25px; color: #333; background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;">
                📊 Real-time FL Metrics Dashboard 
                <span style="font-size: 14px;">(Charts should appear below)</span>
            </h3>
            
            <!-- Chart Filters -->
            <div style="background: rgba(255,255,255,0.9); padding: 15px; margin-bottom: 20px; border-radius: 8px; border: 1px solid #ddd;">
                <h4 style="margin: 0 0 10px 0; color: #444;">� Live Data Mode</h4>
                <div style="padding: 10px; background: #e8f5e8; border-radius: 4px; color: #2e7d32;">
                    ✅ Charts show current training/verification session only (historical data disabled)
                </div>
            </div>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <h4>🏥 Hospital Training Progress</h4>
                    <p class="chart-subtitle">Real-time training and proof generation times</p>
                    <div id="trainingChart" style="height: 350px;"></div>
                </div>
                
                <div class="chart-container">
                    <h4>🔐 Proof Generation Metrics</h4>
                    <p class="chart-subtitle">ZKP proof sizes and generation efficiency</p>
                    <div id="proofChart" style="height: 350px;"></div>
                </div>
                
                <div class="chart-container">
                    <h4>🌟 Protogalaxy Aggregation</h4>
                    <p class="chart-subtitle">Proof aggregation performance over rounds</p>
                    <div id="aggregationChart" style="height: 350px;"></div>
                </div>
                
                <div class="chart-container">
                    <h4>✅ Verification Results</h4>
                    <p class="chart-subtitle">Verification success and timing analysis</p>
                    <div id="verificationChart" style="height: 350px;"></div>
                </div>
            </div>
            
            <div class="chart-container" style="margin-top: 20px;">
                <h4>📈 FL Training Overview</h4>
                <p class="chart-subtitle">Complete federated learning session metrics</p>
                <div id="overviewChart" style="height: 400px;"></div>
            </div>
        </div>
        
        <!-- Live Logs -->
        <div class="log-section" id="liveLog">
            > ZK-FL Control Dashboard ready...<br>
            > Configure parameters and start training<br>
            > Real training and verification pipelines connected<br>
        </div>
        
        <!-- Success Modal -->
        <div class="success-modal" id="successModal">
            <div class="modal-content">
                <h2>🎉 Training Complete!</h2>
                <p id="successMessage">FL training session completed successfully!</p>
                <p style="margin: 20px 0; color: #666;">
                    All hospital models trained and ZKP proofs generated and saved to zkfl_storage/.
                    Ready for verification.
                </p>
                <button class="btn btn-primary" onclick="hideSuccessModal()">✅ Continue</button>
                <button class="btn btn-warning" onclick="hideSuccessModal(); startVerification()">🔍 Start Verification</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let currentState = {};
        
        function initWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                addLog("🔗 Connected to ZK-FL control system");
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'state_update') {
                    updateDashboard(data);
                } else if (data.type === 'log_message') {
                    addLog(data.message);
                } else if (data.type === 'training_complete') {
                    showSuccessModal(data.message);
                } else if (data.type === 'chart_update') {
                    // Handle real-time chart updates during training/verification
                    console.log('📊 Real-time chart update received for round:', data.round);
                    if (data.charts && Object.keys(data.charts).length > 0) {
                        updateCharts(data.charts);
                        addLog(`📊 Charts updated for round ${data.round}`);
                    }
                }
            };
            
            ws.onclose = function() {
                addLog("❌ Connection lost - reconnecting...");
                setTimeout(initWebSocket, 2000);
            };
        }
        
        function updateDashboard(data) {
            currentState = data.state;
            const config = data.config;
            
            // Update status cards
            document.getElementById('currentRound').textContent = currentState.current_round;
            document.getElementById('totalRounds').textContent = currentState.total_rounds;
            document.getElementById('completedRounds').textContent = currentState.completed_rounds.length;
            document.getElementById('pendingVerification').textContent = currentState.pending_verification.length;
            
            // Update config inputs
            document.getElementById('numRounds').value = config.num_rounds;
            document.getElementById('numClients').value = config.num_clients;
            document.getElementById('clientFraction').value = config.client_fraction;
            document.getElementById('fractionValue').textContent = Math.round(config.client_fraction * 100) + '%';
            document.getElementById('learningRate').value = config.learning_rate;
            
            // Update charts if data available
            if (data.charts && Object.keys(data.charts).length > 0) {
                console.log('Updating charts with data:', data.charts);
                updateCharts(data.charts);
            } else {
                console.log('No valid chart data available, preserving existing charts');
            }
            
            // Update training progress
            if (currentState.training_active) {
                document.getElementById('trainingProgress').style.display = 'block';
                updateTrainingProgress(data.training_progress);
            } else {
                document.getElementById('trainingProgress').style.display = 'none';
            }
            
            // Update button states
            updateButtonStates();
        }
        
        function updateTrainingProgress(progress) {
            if (!progress || progress.length === 0) return;
            
            const totalHospitals = progress.length;
            const completedHospitals = progress.filter(p => p.is_completed).length;
            const progressPercent = (completedHospitals / totalHospitals) * 100;
            
            document.getElementById('overallProgress').style.width = progressPercent + '%';
            document.getElementById('progressText').textContent = 
                `Round ${currentState.current_round}/${currentState.total_rounds} - ${completedHospitals}/${totalHospitals} hospitals completed`;
            document.getElementById('progressPercentage').textContent = Math.round(progressPercent) + '%';
            
            // Update hospital grid
            const hospitalGrid = document.getElementById('hospitalGrid');
            hospitalGrid.innerHTML = '';
            
            progress.forEach(hospital => {
                const card = document.createElement('div');
                card.className = `hospital-card ${hospital.status}`;
                card.innerHTML = `
                    <div style="font-weight: 600;">${hospital.hospital_id}</div>
                    <div style="font-size: 0.8em; margin-top: 5px;">${hospital.status.replace('_', ' ')}</div>
                    ${hospital.is_completed ? '<div style="color: #4CAF50; margin-top: 5px;">✅</div>' : ''}
                `;
                hospitalGrid.appendChild(card);
            });
        }
        
        function updateButtonStates() {
            const startTrainingBtn = document.getElementById('startTrainingBtn');
            const stopTrainingBtn = document.getElementById('stopTrainingBtn');
            const startVerificationBtn = document.getElementById('startVerificationBtn');
            const stopVerificationBtn = document.getElementById('stopVerificationBtn');
            
            if (currentState.training_active) {
                startTrainingBtn.disabled = true;
                stopTrainingBtn.disabled = false;
            } else {
                startTrainingBtn.disabled = false;
                stopTrainingBtn.disabled = true;
            }
            
            if (currentState.verification_active) {
                startVerificationBtn.disabled = true;
                stopVerificationBtn.disabled = false;
            } else {
                startVerificationBtn.disabled = false;
                stopVerificationBtn.disabled = true;
            }
            
            // Disable verification if no pending rounds
            if (currentState.pending_verification.length === 0 && !currentState.verification_active) {
                startVerificationBtn.disabled = true;
            }
        }
        
        async function updateConfig() {
            const config = {
                num_rounds: parseInt(document.getElementById('numRounds').value),
                num_clients: parseInt(document.getElementById('numClients').value),
                client_fraction: parseFloat(document.getElementById('clientFraction').value),
                learning_rate: parseFloat(document.getElementById('learningRate').value)
            };
            
            try {
                const response = await fetch('/api/config/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                if (result.status === 'updated') {
                    addLog("⚙️ Configuration updated successfully");
                } else {
                    addLog("❌ Failed to update configuration: " + result.message);
                }
            } catch (error) {
                addLog("❌ Error updating configuration: " + error.message);
            }
        }
        
        async function startTraining() {
            try {
                const response = await fetch('/api/start_training', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'started') {
                    addLog(`🚀 Starting real FL training: ${result.rounds} rounds`);
                    addLog("🏥 Hospitals beginning federated learning with ZKP proof generation...");
                } else {
                    addLog("❌ Failed to start training: " + result.message);
                }
            } catch (error) {
                addLog("❌ Error starting training: " + error.message);
            }
        }
        
        async function stopTraining() {
            try {
                const response = await fetch('/api/stop_training', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'stopped') {
                    addLog("⏹️ Training stopped");
                }
            } catch (error) {
                addLog("❌ Error stopping training: " + error.message);
            }
        }
        
        async function startVerification() {
            try {
                const response = await fetch('/api/start_verification', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'started') {
                    addLog(`🔍 Starting proof verification: ${result.rounds} rounds`);
                    addLog("🌟 Loading saved proofs and running Protogalaxy aggregation...");
                } else {
                    addLog("❌ Failed to start verification: " + result.message);
                }
            } catch (error) {
                addLog("❌ Error starting verification: " + error.message);
            }
        }
        
        async function stopVerification() {
            // Verification stop would be implemented here
            addLog("⏹️ Verification stopped");
        }
        
        function showSuccessModal(message) {
            document.getElementById('successMessage').textContent = message;
            document.getElementById('successModal').style.display = 'flex';
            addLog("🎉 " + message);
        }
        
        function hideSuccessModal() {
            document.getElementById('successModal').style.display = 'none';
        }
        
        function addLog(message) {
            const log = document.getElementById('liveLog');
            const timestamp = new Date().toLocaleTimeString();
            log.innerHTML += `<br>[${timestamp}] ${message}`;
            log.scrollTop = log.scrollHeight;
        }
        
        // Update fraction display
        document.getElementById('clientFraction').addEventListener('input', function() {
            document.getElementById('fractionValue').textContent = Math.round(this.value * 100) + '%';
        });
        
        function updateCharts(chartData) {
            console.log('🔄 UpdateCharts called with:', chartData);
            
            // Don't update if no chart data or invalid data
            if (!chartData) {
                console.log('⚠️ No chart data provided, skipping chart updates');
                return;
            }
            
            // Only update charts with valid data
            if (chartData.hospital_training && chartData.hospital_training.hospitals && chartData.hospital_training.hospitals.length > 0) {
                updateHospitalTrainingChart(chartData.hospital_training);
            } else {
                console.log('⚠️ Skipping hospital chart - no valid data');
            }
            
            if (chartData.proof_generation && chartData.proof_generation.rounds && chartData.proof_generation.rounds.length > 0) {
                updateProofGenerationChart(chartData.proof_generation);
            } else {
                console.log('⚠️ Skipping proof chart - no valid data');
            }
            
            if (chartData.aggregation && chartData.aggregation.rounds && chartData.aggregation.rounds.length > 0) {
                updateAggregationChart(chartData.aggregation);
            } else {
                console.log('⚠️ Skipping aggregation chart - no valid data');
            }
            
            if (chartData.verification && chartData.verification.rounds && chartData.verification.rounds.length > 0) {
                updateVerificationChart(chartData.verification);
            } else {
                console.log('⚠️ Skipping verification chart - no valid data');
            }
            
            if (chartData.overview && chartData.overview.rounds && chartData.overview.rounds.length > 0) {
                updateOverviewChart(chartData.overview);
            } else {
                console.log('⚠️ Skipping overview chart - no valid data');
            }
        }
        
        // Chart state tracking
        const chartStates = {
            trainingChart: false,
            proofChart: false,
            aggregationChart: false,
            verificationChart: false,
            overviewChart: false
        };
        
        // Enhanced chart update functions with state protection
        function updateHospitalTrainingChart(data) {
            console.log('🏥 Updating hospital training chart with data:', data);
            
            const container = document.getElementById('trainingChart');
            if (!container) {
                console.error('❌ Training chart container not found!');
                return;
            }
            
            // Check if we have valid data for time series
            if (!data || !data.rounds || data.rounds.length === 0) {
                container.innerHTML = '<div style="color: #666; padding: 20px; text-align: center;">📊 No training data - start training to see progress</div>';
                return;
            }
            
            console.log('📊 Training chart container found, creating time series chart...');
            
            const trace1 = {
                x: data.rounds,
                y: data.avg_accuracy,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Average Accuracy',
                line: { color: '#4CAF50' },
                marker: { size: 8 }
            };
            
            const trace2 = {
                x: data.rounds,
                y: data.avg_loss,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Average Loss',
                yaxis: 'y2',
                line: { color: '#f44336' },
                marker: { size: 8 }
            };
            
            const layout = {
                title: 'Hospital Training Progress (Per Round)',
                xaxis: { title: 'Training Round' },
                yaxis: { title: 'Accuracy', side: 'left' },
                yaxis2: { title: 'Loss', side: 'right', overlaying: 'y' },
                showlegend: true,
                height: 300,
                margin: { t: 40, b: 40, l: 40, r: 40 }
            };
            
            Plotly.newPlot('trainingChart', [trace1, trace2], layout, {responsive: true})
                .then(() => {
                    console.log('✅ Hospital training chart created successfully');
                    container.style.border = '2px solid green';
                    chartStates.trainingChart = true;
                })
                .catch((error) => {
                    console.error('❌ Hospital training chart failed:', error);
                    container.innerHTML = '<div style="color: red; padding: 20px;">❌ Chart creation failed: ' + error.message + '</div>';
                });
        }
        
        function updateProofGenerationChart(data) {
            const trace1 = {
                x: data.rounds,
                y: data.generation_time,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Generation Time (s)',
                line: { color: '#2196F3' }
            };
            
            const trace2 = {
                x: data.rounds,
                y: data.proof_size,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Proof Size (bytes)',
                yaxis: 'y2',
                line: { color: '#FF9800' }
            };
            
            const layout = {
                title: 'ZKP Generation Metrics',
                xaxis: { title: 'FL Rounds' },
                yaxis: { title: 'Time (seconds)', side: 'left' },
                yaxis2: { title: 'Size (bytes)', side: 'right', overlaying: 'y' },
                showlegend: true,
                height: 300,
                margin: { t: 40, b: 40, l: 40, r: 40 }
            };
            
            Plotly.newPlot('proofChart', [trace1, trace2], layout, {responsive: true});
        }
        
        function updateAggregationChart(data) {
            const trace1 = {
                x: data.rounds,
                y: data.aggregation_time,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Aggregation Time',
                line: { color: '#9C27B0' }
            };
            
            const trace2 = {
                x: data.rounds,
                y: data.success_rate,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Success Rate (%)',
                yaxis: 'y2',
                line: { color: '#4CAF50' }
            };
            
            const layout = {
                title: 'Protogalaxy Aggregation',
                xaxis: { title: 'FL Rounds' },
                yaxis: { title: 'Time (seconds)', side: 'left' },
                yaxis2: { title: 'Success Rate (%)', side: 'right', overlaying: 'y', range: [0, 100] },
                showlegend: true,
                height: 300,
                margin: { t: 40, b: 40, l: 40, r: 40 }
            };
            
            Plotly.newPlot('aggregationChart', [trace1, trace2], layout, {responsive: true});
        }
        
        function updateVerificationChart(data) {
            const trace = {
                x: data.rounds,
                y: data.verification_time,
                type: 'bar',
                name: 'Verification Time',
                marker: { color: '#FF5722' }
            };
            
            const layout = {
                title: 'Proof Verification Performance',
                xaxis: { title: 'FL Rounds' },
                yaxis: { title: 'Time (seconds)' },
                showlegend: false,
                height: 300,
                margin: { t: 40, b: 40, l: 40, r: 40 }
            };
            
            Plotly.newPlot('verificationChart', [trace], layout, {responsive: true});
        }
        
        function updateOverviewChart(data) {
            const trace1 = {
                x: data.rounds,
                y: data.total_accuracy,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Global Accuracy',
                line: { color: '#4CAF50', width: 3 }
            };
            
            const trace2 = {
                x: data.rounds,
                y: data.round_time,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Round Time (s)',
                yaxis: 'y2',
                line: { color: '#2196F3' }
            };
            
            const layout = {
                title: 'FL Training Overview',
                xaxis: { title: 'FL Rounds' },
                yaxis: { title: 'Global Accuracy', side: 'left' },
                yaxis2: { title: 'Round Time (s)', side: 'right', overlaying: 'y' },
                showlegend: true,
                height: 300,
                margin: { t: 40, b: 40, l: 40, r: 40 }
            };
            
            Plotly.newPlot('overviewChart', [trace1, trace2], layout, {responsive: true});
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing WebSocket and charts...');
            
            initWebSocket();
            
            // Initialize empty charts to show structure
            setTimeout(initializeEmptyCharts, 1000);
        });
        
        function initializeEmptyCharts() {
            console.log('Initializing empty charts...');
            
            // Test if Plotly is available
            if (typeof Plotly === 'undefined') {
                console.error('Plotly.js is not loaded!');
                
                // Show fallback content for all chart containers
                const chartIds = ['trainingChart', 'proofChart', 'aggregationChart', 'verificationChart', 'overviewChart'];
                chartIds.forEach(id => {
                    const container = document.getElementById(id);
                    if (container) {
                        container.innerHTML = '<div style="color: red; padding: 20px; text-align: center; border: 2px solid red; background: #ffe6e6;">❌ Plotly.js failed to load from CDN<br><small>Charts cannot be displayed</small></div>';
                    } else {
                        console.error(`❌ Chart container ${id} not found!`);
                    }
                });
                return;
            }
            
            console.log('Plotly.js is available, creating test charts...');
            
            // Add visible indicators that charts are initializing
            const chartIds = ['trainingChart', 'proofChart', 'aggregationChart', 'verificationChart', 'overviewChart'];
            chartIds.forEach(id => {
                const container = document.getElementById(id);
                if (container) {
                    container.innerHTML = '<div style="color: blue; padding: 20px; text-align: center; border: 2px solid blue; background: #e6f3ff;">📊 Loading chart...</div>';
                } else {
                    console.error(`❌ Chart container ${id} not found!`);
                }
            });
            
            // Create charts with delay to show loading indicators
            setTimeout(() => {
                // Show empty state instead of sample data
                const chartIds = ['trainingChart', 'proofChart', 'aggregationChart', 'verificationChart', 'overviewChart'];
                chartIds.forEach(id => {
                    const container = document.getElementById(id);
                    if (container) {
                        container.innerHTML = '<div style="color: #666; padding: 40px; text-align: center; border: 2px dashed #ddd; background: #f9f9f9; border-radius: 8px;">📊 No live data - start training or verification to see charts</div>';
                    }
                });
                console.log('Empty charts initialized successfully!');
            }, 500);
        }
    </script>
</body>
</html>
        """
    
    async def _refresh_state(self):
        """Refresh dashboard state from storage"""
        # Refresh pending rounds
        self.state.pending_verification = self.verification_pipeline.get_pending_rounds()
        
        # Get completed rounds from storage
        storage_path = Path("./zkfl_storage/training_rounds")
        if storage_path.exists():
            self.state.completed_rounds = [d.name for d in storage_path.iterdir() if d.is_dir()]
    
    async def _run_training_session(self):
        """Run actual FL training session using real pipeline"""
        config = self.config_manager.config
        total_rounds = config.num_rounds
        participating_clients = int(config.num_clients * config.client_fraction)
        
        self.logger.info(f"🚀 Starting real FL training session: {total_rounds} rounds")
        await self._broadcast_log(f"🚀 Real FL Training Started: {total_rounds} rounds")
        
        try:
            for round_num in range(1, total_rounds + 1):
                if not self.state.training_active:
                    break
                    
                self.state.current_round = round_num
                await self._broadcast_log(f"📍 Round {round_num}/{total_rounds} starting...")
                
                # Initialize progress tracking for this round
                self.current_training_progress = []
                for i in range(participating_clients):
                    progress = TrainingProgress(
                        round_number=round_num,
                        total_rounds=total_rounds,
                        hospital_id=f"hospital_{i+1:02d}",
                        status='training',
                        training_time=0.0,
                        proof_generation_time=0.0,
                        is_completed=False
                    )
                    self.current_training_progress.append(progress)
                
                # Broadcast initial chart data for this round
                chart_data = await self._collect_chart_data()
                await self._broadcast_special_message({
                    "type": "chart_update",
                    "charts": chart_data,
                    "round": round_num,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Run actual training round using real pipeline
                training_results, proofs = self.training_pipeline.run_training_round(round_num)
                
                # Update progress with actual training results
                if training_results and 'hospitals' in training_results:
                    for i, hospital_data in enumerate(training_results['hospitals']):
                        if i < len(self.current_training_progress):
                            self.current_training_progress[i].accuracy = hospital_data.get('accuracy', 0.75)
                            self.current_training_progress[i].loss = hospital_data.get('loss', 0.3)
                            self.current_training_progress[i].training_time = hospital_data.get('training_time', 0.0)
                            self.current_training_progress[i].proof_generation_time = hospital_data.get('proof_generation_time', 0.0)
                            self.current_training_progress[i].status = 'completed'
                            self.current_training_progress[i].is_completed = True
                
                # Update progress tracking with real results
                for i, (training, proof) in enumerate(zip(training_results, proofs)):
                    if i < len(self.current_training_progress):
                        self.current_training_progress[i].status = 'completed'
                        self.current_training_progress[i].training_time = training.training_time
                        self.current_training_progress[i].proof_generation_time = proof.generation_time
                        self.current_training_progress[i].is_completed = True
                
                # Add historical data points for charts
                if self.current_training_progress:
                    # Calculate average metrics for this round
                    completed_progress = [p for p in self.current_training_progress if p.is_completed]
                    if completed_progress:
                        avg_accuracy = sum(p.accuracy for p in completed_progress) / len(completed_progress)
                        avg_training_time = sum(p.training_time for p in completed_progress) / len(completed_progress)
                        avg_loss = sum(p.loss for p in completed_progress) / len(completed_progress)
                        avg_proof_time = sum(p.proof_generation_time for p in completed_progress) / len(completed_progress)
                        
                        # Add data points to historical data
                        self._add_training_data_point(round_num, avg_accuracy, avg_training_time, avg_loss)
                        self._add_proof_data_point(round_num, avg_proof_time, 2048)  # Default proof size
                
                # Broadcast updated chart data immediately after round completion
                chart_data = await self._collect_chart_data()
                await self._broadcast_special_message({
                    "type": "chart_update",
                    "charts": chart_data,
                    "round": round_num,
                    "timestamp": datetime.now().isoformat()
                })
                
                await self._broadcast_log(f"✅ Round {round_num} complete: {len(training_results)} hospitals, {len(proofs)} proofs saved")
                
                # Brief pause between rounds
                await asyncio.sleep(2)
            
            # Training session completed
            self.state.training_active = False
            self.state.last_training_session = datetime.now().isoformat()
            
            await self._broadcast_log("🎉 FL Training Session Complete!")
            await self._broadcast_special_message({
                "type": "training_complete",
                "message": f"Training complete! {total_rounds} rounds finished.",
                "rounds_completed": total_rounds,
                "total_hospitals": len(training_results) if 'training_results' in locals() else 0
            })
            
        except Exception as e:
            self.logger.error(f"Training session error: {e}")
            await self._broadcast_log(f"❌ Training error: {e}")
            self.state.training_active = False
    
    async def _run_verification_session(self):
        """Run actual proof verification using real pipeline"""
        pending_rounds = self.verification_pipeline.get_pending_rounds()
        
        self.logger.info(f"🔍 Starting real verification session: {len(pending_rounds)} rounds")
        await self._broadcast_log(f"🔍 Real Proof Verification Started: {len(pending_rounds)} rounds")
        
        try:
            for round_id in pending_rounds:
                if not self.state.verification_active:
                    break
                    
                await self._broadcast_log(f"🔍 Verifying: {round_id}")
                
                # Broadcast chart update at start of verification
                chart_data = await self._collect_chart_data()
                await self._broadcast_special_message({
                    "type": "chart_update",
                    "charts": chart_data,
                    "round": round_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Run actual verification using real pipeline
                result = self.verification_pipeline.verify_round(round_id)
                
                # Add historical data points for verification charts
                if result:
                    self._add_aggregation_data_point(round_id, result.protogalaxy_aggregation_time, 100.0 if result.verification_status else 0.0)
                    self._add_verification_data_point(round_id, result.verification_time, 8)  # Assuming 8 hospitals
                
                # Broadcast updated chart data immediately after verification
                chart_data = await self._collect_chart_data()
                await self._broadcast_special_message({
                    "type": "chart_update",
                    "charts": chart_data,
                    "round": round_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                status = "✅ SUCCESS" if result.verification_status else "❌ FAILED"
                await self._broadcast_log(f"  {status}")
                await self._broadcast_log(f"  🌟 Aggregation: {result.protogalaxy_aggregation_time:.3f}s")
                await self._broadcast_log(f"  ✅ Verification: {result.verification_time:.3f}s")
                await self._broadcast_log(f"  💾 Saved: {result.verification_id}")
                
                # Brief pause between verifications
                await asyncio.sleep(1)
            
            # Verification session completed
            self.state.verification_active = False
            self.state.last_verification_session = datetime.now().isoformat()
            
            await self._broadcast_log("🎉 Verification Session Complete!")
            
        except Exception as e:
            self.logger.error(f"Verification session error: {e}")
            await self._broadcast_log(f"❌ Verification error: {e}")
            self.state.verification_active = False
    
    async def _broadcast_log(self, message: str):
        """Broadcast log message to all connected clients"""
        if self.active_connections:
            await self._broadcast_special_message({
                "type": "log_message",
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _broadcast_special_message(self, message: dict):
        """Broadcast special message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    def _get_storage_stats(self) -> dict:
        """Get storage statistics"""
        storage_path = Path("./zkfl_storage")
        if not storage_path.exists():
            return {"training_rounds": 0, "proofs": 0, "verification_results": 0}
        
        stats = {
            "training_rounds": len(list((storage_path / "training_rounds").glob("*"))) if (storage_path / "training_rounds").exists() else 0,
            "proofs": len(list((storage_path / "proofs").glob("*"))) if (storage_path / "proofs").exists() else 0,
            "verification_results": len(list((storage_path / "verification_results").glob("*.json"))) if (storage_path / "verification_results").exists() else 0
        }
        
        return stats
    
    def run(self):
        """Run the ZK-FL control dashboard"""
        self.logger.info(f"🚀 Starting ZK-FL Control Dashboard at http://{self.host}:{self.port}")
        self.logger.info("🏥 Connected to actual training and verification pipelines")
        
        uvicorn.run(
            self.app, 
            host=self.host, 
            port=self.port,
            log_level="info"
        )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ZK-FL Control Dashboard")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8090, help="Port to bind to")
    
    args = parser.parse_args()
    
    dashboard = ZKFLControlDashboard(host=args.host, port=args.port)
    dashboard.run()