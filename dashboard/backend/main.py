"""
ZKP-FL Dashboard Backend
========================
FastAPI backend with WebSocket support for real-time visualization
of Zero-Knowledge Proof Federated Learning operations.
"""

import asyncio
import json
import os
import sys
import time
import sqlite3
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Base paths - calculate properly
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
RESULTS_DIR = BASE_DIR / "production_zkp_fl_results_real"

# Add parent directory to path for imports
sys.path.insert(0, str(BASE_DIR))

app = FastAPI(title="ZKP-FL Dashboard", version="1.0.0")

# CORS for React frontend - allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class DashboardState:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.current_run: Optional[Dict] = None
        self.run_process: Optional[subprocess.Popen] = None
        self.message_queue = queue.Queue()
        self.is_running = False
        
state = DashboardState()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
RESULTS_DIR = BASE_DIR / "production_zkp_fl_results_real"


# ============== Pydantic Models ==============

class RunConfig(BaseModel):
    num_clients: int = 3
    num_rounds: int = 3
    local_epochs: int = 5
    batch_size: int = 64
    learning_rate: float = 0.01
    security_level: int = 128


class RunInfo(BaseModel):
    run_id: str
    timestamp: str
    config: Dict[str, Any]
    status: str
    metrics: Optional[Dict[str, Any]] = None


class CryptoEvent(BaseModel):
    event_type: str  # 'srs_progress', 'constraint_check', 'folding', 'pairing', etc.
    data: Dict[str, Any]
    timestamp: float


# ============== WebSocket Manager ==============

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        async with self._lock:
            connections = list(self.active_connections)
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)

manager = ConnectionManager()


# ============== Run History Database ==============

def init_db():
    """Initialize SQLite database for run history"""
    db_path = BASE_DIR / "dashboard" / "runs.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT,
            config TEXT,
            status TEXT,
            metrics TEXT,
            duration REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()


def save_run_to_db(run_info: Dict):
    """Save run info to database"""
    db_path = BASE_DIR / "dashboard" / "runs.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO runs (run_id, timestamp, config, status, metrics, duration)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        run_info['run_id'],
        run_info['timestamp'],
        json.dumps(run_info.get('config', {})),
        run_info['status'],
        json.dumps(run_info.get('metrics', {})),
        run_info.get('duration', 0)
    ))
    conn.commit()
    conn.close()


def get_runs_from_db() -> List[Dict]:
    """Get all runs from database"""
    db_path = BASE_DIR / "dashboard" / "runs.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM runs ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    runs = []
    for row in rows:
        runs.append({
            'run_id': row[0],
            'timestamp': row[1],
            'config': json.loads(row[2]) if row[2] else {},
            'status': row[3],
            'metrics': json.loads(row[4]) if row[4] else {},
            'duration': row[5]
        })
    return runs


# ============== Parse Existing Runs ==============

def scan_existing_runs() -> List[Dict]:
    """Scan the results directory for existing runs"""
    runs = []
    
    if not RESULTS_DIR.exists():
        return runs
    
    for run_dir in sorted(RESULTS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        
        run_id = run_dir.name
        
        # Parse run config
        config_file = run_dir / "run_config.json"
        config = {}
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
        
        # Parse results
        results_file = run_dir / "results" / "training_results.json"
        metrics = {}
        if results_file.exists():
            with open(results_file) as f:
                metrics = json.load(f)
        
        # Determine status
        status = "completed" if results_file.exists() else "incomplete"
        
        # Extract timestamp from run_id
        try:
            ts_part = run_id.split('_')[1] + run_id.split('_')[2][:6]
            timestamp = datetime.strptime(ts_part, "%Y%m%d%H%M%S").isoformat()
        except:
            timestamp = datetime.now().isoformat()
        
        runs.append({
            'run_id': run_id,
            'timestamp': timestamp,
            'config': config,
            'status': status,
            'metrics': metrics,
            'path': str(run_dir)
        })
    
    return runs


def get_run_details(run_id: str) -> Dict:
    """Get detailed information about a specific run"""
    run_dir = RESULTS_DIR / run_id
    
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    details = {
        'run_id': run_id,
        'config': {},
        'metrics': {},
        'proofs': [],
        'models': [],
        'rounds': []
    }
    
    # Load config
    config_file = run_dir / "run_config.json"
    if config_file.exists():
        with open(config_file) as f:
            details['config'] = json.load(f)
    
    # Load results
    results_file = run_dir / "results" / "training_results.json"
    if results_file.exists():
        with open(results_file) as f:
            details['metrics'] = json.load(f)
    
    # Scan proofs
    proofs_dir = run_dir / "proofs"
    if proofs_dir.exists():
        for client_dir in proofs_dir.iterdir():
            if client_dir.is_dir() and client_dir.name.startswith("client_"):
                for proof_file in client_dir.glob("*.json"):
                    with open(proof_file) as f:
                        proof_data = json.load(f)
                    details['proofs'].append({
                        'client': client_dir.name,
                        'file': proof_file.name,
                        'constraints': proof_data.get('proof_data', {}).get('constraints', {}),
                        'crypto_properties': proof_data.get('proof_data', {}).get('cryptographic_properties', {})
                    })
    
    # Scan models
    models_dir = run_dir / "models"
    if models_dir.exists():
        for model_file in models_dir.glob("*.json"):
            details['models'].append(model_file.name)
    
    # Build round-by-round data
    if details['metrics'].get('rounds'):
        for round_data in details['metrics']['rounds']:
            round_info = {
                'round_number': round_data.get('round_number'),
                'clients': [],
                'aggregation': round_data.get('aggregation', {})
            }
            
            for client_result in round_data.get('client_results', []):
                round_info['clients'].append({
                    'client_id': client_result.get('client_id'),
                    'accuracy': client_result.get('training_metrics', {}).get('accuracy'),
                    'loss': client_result.get('training_metrics', {}).get('loss'),
                    'proof_verified': client_result.get('proof_verified', False),
                    'proof_time': client_result.get('proof_metadata', {}).get('proof_generation_time')
                })
            
            details['rounds'].append(round_info)
    
    return details


# ============== API Endpoints ==============

@app.get("/")
async def root():
    return {"message": "ZKP-FL Dashboard API", "version": "1.0.0"}


@app.get("/api/runs")
async def get_runs():
    """Get list of all runs (from filesystem)"""
    return scan_existing_runs()


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """Get detailed information about a specific run"""
    return get_run_details(run_id)


@app.get("/api/runs/{run_id}/logs")
async def get_run_logs(run_id: str):
    """Get logs for a specific run"""
    run_dir = RESULTS_DIR / run_id
    
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    logs_dir = run_dir / "logs"
    logs = []
    
    if logs_dir.exists():
        for log_file in sorted(logs_dir.glob("*.log")):
            try:
                with open(log_file, 'r') as f:
                    logs.extend(f.read().strip().split('\n'))
            except Exception:
                pass
        
        for log_file in sorted(logs_dir.glob("*.txt")):
            try:
                with open(log_file, 'r') as f:
                    logs.extend(f.read().strip().split('\n'))
            except Exception:
                pass
    
    # Also check for aggregator log
    aggregator_log = run_dir / "aggregator.log"
    if aggregator_log.exists():
        try:
            with open(aggregator_log, 'r') as f:
                logs.extend(f.read().strip().split('\n'))
        except Exception:
            pass
    
    return {"logs": logs}


@app.get("/api/runs/{run_id}/compare/{other_run_id}")
async def compare_runs(run_id: str, other_run_id: str):
    """Compare two runs"""
    run1 = get_run_details(run_id)
    run2 = get_run_details(other_run_id)
    
    comparison = {
        'runs': [run_id, other_run_id],
        'configs': [run1['config'], run2['config']],
        'metrics_comparison': {},
        'rounds_comparison': []
    }
    
    # Compare final metrics - use correct field names from training_results.json
    m1 = run1['metrics']
    m2 = run2['metrics']
    
    if m1 and m2:
        # Get summary data (contains final_accuracy)
        s1 = m1.get('summary', {})
        s2 = m2.get('summary', {})
        
        # Get final round for loss (last round's avg_loss)
        r1_rounds = m1.get('rounds', [])
        r2_rounds = m2.get('rounds', [])
        
        final_loss1 = r1_rounds[-1].get('avg_loss', 0) if r1_rounds else 0
        final_loss2 = r2_rounds[-1].get('avg_loss', 0) if r2_rounds else 0
        
        comparison['metrics_comparison'] = {
            'final_accuracy': {
                run_id: s1.get('final_accuracy', 0),
                other_run_id: s2.get('final_accuracy', 0)
            },
            'final_loss': {
                run_id: final_loss1,
                other_run_id: final_loss2
            },
            'total_time': {
                run_id: m1.get('total_training_time', 0),
                other_run_id: m2.get('total_training_time', 0)
            }
        }
        
        # Compare round-by-round using actual round data
        max_rounds = max(len(r1_rounds), len(r2_rounds))
        for i in range(max_rounds):
            round_comp = {'round': i + 1}
            
            if i < len(r1_rounds):
                round_comp[run_id] = {
                    'accuracy': r1_rounds[i].get('avg_accuracy', 0),
                    'loss': r1_rounds[i].get('avg_loss', 0)
                }
            
            if i < len(r2_rounds):
                round_comp[other_run_id] = {
                    'accuracy': r2_rounds[i].get('avg_accuracy', 0),
                    'loss': r2_rounds[i].get('avg_loss', 0)
                }
            
            comparison['rounds_comparison'].append(round_comp)
    
    return comparison


@app.post("/api/runs/start")
async def start_run(config: RunConfig, background_tasks: BackgroundTasks):
    """Start a new ZKP-FL run with the given configuration"""
    if state.is_running:
        raise HTTPException(status_code=400, detail="A run is already in progress")
    
    state.is_running = True
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_clients{config.num_clients}_rounds{config.num_rounds}"
    
    state.current_run = {
        'run_id': run_id,
        'config': config.dict(),
        'status': 'starting',
        'start_time': time.time()
    }
    
    # Start the run in background
    background_tasks.add_task(execute_run, run_id)
    
    return {"message": "Run started", "run_id": run_id}


@app.post("/api/runs/stop")
async def stop_run():
    """Stop the current run"""
    if not state.is_running:
        raise HTTPException(status_code=400, detail="No run in progress")
    
    if state.run_process:
        state.run_process.terminate()
        state.run_process = None
    
    state.is_running = False
    state.current_run = None
    
    await manager.broadcast({
        'type': 'run_stopped',
        'message': 'Run stopped by user'
    })
    
    return {"message": "Run stopped"}


@app.get("/api/status")
async def get_status():
    """Get current dashboard status"""
    return {
        'is_running': state.is_running,
        'current_run': state.current_run,
        'connected_clients': len(manager.active_connections)
    }


# ============== Background Run Execution ==============

async def execute_run(run_id: str):
    """Execute a ZKP-FL run and stream updates via WebSocket"""
    try:
        config = state.current_run.get('config', {}) if state.current_run else {}
        
        await manager.broadcast({
            'type': 'run_started',
            'run_id': run_id,
            'config': config
        })
        
        # Run the production script with config passed via environment
        script_path = BASE_DIR / "production_zkp_fl_real.py"
        
        # Create environment with config - LITE MODE for fast execution
        env = os.environ.copy()
        env['ZKP_FL_NUM_CLIENTS'] = str(config.get('num_clients', 2))
        env['ZKP_FL_NUM_ROUNDS'] = str(config.get('num_rounds', 1))
        env['ZKP_FL_LOCAL_EPOCHS'] = str(config.get('local_epochs', 1))
        env['ZKP_FL_BATCH_SIZE'] = str(config.get('batch_size', 64))
        env['ZKP_FL_LEARNING_RATE'] = str(config.get('learning_rate', 0.001))
        env['ZKP_FL_SECURITY_LEVEL'] = '128'  # Minimum allowed security level
        env['ZKP_FL_SRS_SIZE'] = '64'  # Small SRS for fast generation
        env['ZKP_FL_LITE_MODE'] = 'true'  # Always use lite mode from dashboard
        env['PYTHONUNBUFFERED'] = '1'  # Disable Python output buffering
        
        # Use -u flag for unbuffered output
        cmd = [sys.executable, '-u', str(script_path)]
        
        print(f"🚀 Starting run: {' '.join(cmd)}")
        print(f"📁 Working directory: {BASE_DIR}")
        print(f"⚙️  Config: {config}")
        
        # Use asyncio subprocess for non-blocking execution
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(BASE_DIR),
            env=env
        )
        state.run_process = process
        
        # Stream output
        current_phase = "setup"
        
        while True:
            if not state.is_running:
                process.terminate()
                break
            
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            
            if not line:
                break
            
            line = line.decode('utf-8', errors='replace').strip()
            if not line:
                continue
            
            # Parse the output line and create appropriate event
            event = parse_output_line(line, current_phase)
            
            # Update phase tracking based on log content
            if "SRS generated" in line or "SRS setup" in line.lower():
                current_phase = "training"
            elif "Round" in line and "Starting" in line:
                current_phase = "training"
            elif "proof" in line.lower() and ("verify" in line.lower() or "generat" in line.lower()):
                current_phase = "verification"
            elif "aggregat" in line.lower():
                current_phase = "aggregation"
            
            await manager.broadcast({
                'type': 'log',
                'message': line,
                'phase': current_phase,
                'event': event
            })
        
        await process.wait()
        
        # Run completed
        state.is_running = False
        duration = time.time() - state.current_run['start_time'] if state.current_run else 0
        
        await manager.broadcast({
            'type': 'run_completed',
            'run_id': run_id,
            'duration': duration,
            'exit_code': process.returncode
        })
        
        # Save to database
        save_run_to_db({
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'config': config,
            'status': 'completed' if process.returncode == 0 else 'failed',
            'duration': duration
        })
        
    except Exception as e:
        import traceback
        print(f"❌ Run error: {e}")
        traceback.print_exc()
        state.is_running = False
        await manager.broadcast({
            'type': 'run_error',
            'error': str(e)
        })


def parse_output_line(line: str, current_phase: str) -> Dict:
    """Parse output line and extract structured event data"""
    event = {'type': 'log', 'raw': line}
    
    # SRS Generation
    if "G1 progress:" in line or "G2 progress:" in line:
        parts = line.split(":")[-1].strip().split("/")
        if len(parts) == 2:
            try:
                current, total = int(parts[0]), int(parts[1])
                group = "G1" if "G1" in line else "G2"
                event = {
                    'type': 'srs_progress',
                    'group': group,
                    'current': current,
                    'total': total,
                    'percentage': (current / total) * 100
                }
            except ValueError:
                pass
    
    # Constraint verification
    elif "constraints" in line.lower() or "R1CS" in line:
        if "R1CS circuit satisfied" in line or "constraints verified" in line or "satisfied" in line.lower():
            match = re.search(r'(\d+)\s*constraints', line)
            if match:
                event = {
                    'type': 'constraints_verified',
                    'count': int(match.group(1)),
                    'status': 'satisfied'
                }
            else:
                event = {
                    'type': 'constraints_verified',
                    'count': 0,
                    'status': 'satisfied'
                }
        elif "constraint" in line and ("FAILED" in line or "violation" in line):
            event = {
                'type': 'constraint_failed',
                'message': line
            }
    
    # Proof generation
    elif "Generating" in line and "proof" in line.lower():
        event = {'type': 'proof_generating'}
    elif "proof generated" in line.lower() or "Proof generation complete" in line:
        event = {'type': 'proof_generated'}
    elif "proof verified" in line.lower() or "✓" in line or "PASSED" in line:
        event = {'type': 'proof_verified'}
    
    # Folding/Aggregation
    elif "folding" in line.lower() or "Folding" in line or "accumulator" in line.lower():
        event = {'type': 'folding_progress', 'message': line}
    elif "aggregat" in line.lower():
        event = {'type': 'aggregation_progress', 'message': line}
    
    # Pairing checks  
    elif "pairing" in line.lower():
        if "PASSED" in line or "✅" in line or "✓" in line:
            event = {'type': 'pairing_check', 'status': 'passed'}
        elif "FAILED" in line or "❌" in line:
            event = {'type': 'pairing_check', 'status': 'failed'}
        else:
            event = {'type': 'pairing_check', 'status': 'in_progress'}
    
    # KZG
    elif "KZG" in line:
        event = {'type': 'kzg_operation', 'message': line}
    
    # Client training
    elif "Client" in line and ("Train" in line or "train" in line):
        match = re.search(r'[Cc]lient[_\s]*(\w+)', line)
        client_id = match.group(1) if match else "unknown"
        event = {'type': 'client_training', 'client_id': client_id}
    
    # Round info
    elif "Round" in line:
        match = re.search(r'[Rr]ound\s*(\d+)', line)
        round_num = int(match.group(1)) if match else 0
        event = {'type': 'round_info', 'round': round_num, 'message': line}
    
    # Accuracy/Loss metrics
    elif "acc" in line.lower() or "loss" in line.lower():
        acc_match = re.search(r'acc(?:uracy)?[=:\s]*([\d.]+)', line, re.IGNORECASE)
        loss_match = re.search(r'loss[=:\s]*([\d.]+)', line, re.IGNORECASE)
        if acc_match or loss_match:
            event = {
                'type': 'metrics_update',
                'accuracy': float(acc_match.group(1)) if acc_match else None,
                'loss': float(loss_match.group(1)) if loss_match else None
            }
    
    # Security/Crypto events
    elif "security" in line.lower() or "🔐" in line or "🔒" in line:
        event = {'type': 'security_info', 'message': line}
    
    # SRS setup
    elif "SRS" in line:
        event = {'type': 'srs_info', 'message': line}
    
    return event


# ============== WebSocket Endpoint ==============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send current state on connect - handle serialization issues
    try:
        current_run_safe = None
        if state.current_run:
            current_run_safe = {
                'run_id': state.current_run.get('run_id'),
                'status': state.current_run.get('status'),
                'config': state.current_run.get('config', {}),
                'start_time': state.current_run.get('start_time')
            }
        
        await websocket.send_json({
            'type': 'connection_established',
            'is_running': state.is_running,
            'current_run': current_run_safe
        })
    except Exception as e:
        print(f"Error sending initial state: {e}")
        # Don't disconnect, just continue
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                if message.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong'})
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({'type': 'heartbeat'})
                except Exception:
                    break
            except json.JSONDecodeError:
                continue  # Ignore malformed messages
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ZKP-FL Dashboard Backend...")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"📊 Results directory: {RESULTS_DIR}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
