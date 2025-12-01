"""
ZKP-FL Dashboard - Sleek Visualization for Federated Learning with Zero-Knowledge Proofs
========================================================================================

A modern Flask application to visualize and compare ZKP-FL training runs.
Features:
- Real-time metrics comparison across runs
- Interactive charts for FL and ZKP metrics
- Detailed proof analysis
- Run comparison highlighting
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Configuration
RESULTS_DIR = Path(__file__).parent.parent / "production_zkp_fl_results_real"


def parse_run_timestamp(run_name: str) -> datetime:
    """Parse timestamp from run folder name."""
    try:
        # Format: run_YYYYMMDD_HHMMSS_clientsN_roundsN
        parts = run_name.split('_')
        date_str = parts[1]
        time_str = parts[2]
        return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
    except (IndexError, ValueError):
        return datetime.min


def load_run_data(run_path: Path) -> Optional[Dict[str, Any]]:
    """Load all data for a single run."""
    try:
        results_file = run_path / "results" / "training_results.json"
        config_file = run_path / "run_config.json"
        
        if not results_file.exists():
            return None
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        config = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        
        # Count proof files
        proofs_dir = run_path / "proofs"
        total_proofs = 0
        client_proofs = {}
        
        if proofs_dir.exists():
            for client_dir in proofs_dir.iterdir():
                if client_dir.is_dir() and client_dir.name.startswith("client_"):
                    proof_files = list(client_dir.glob("*.json"))
                    client_proofs[client_dir.name] = len(proof_files)
                    total_proofs += len(proof_files)
        
        # Load aggregated proof info
        aggregated_proofs = []
        agg_dir = proofs_dir / "aggregated" if proofs_dir.exists() else None
        if agg_dir and agg_dir.exists():
            for agg_file in agg_dir.glob("*.json"):
                try:
                    with open(agg_file, 'r') as f:
                        agg_data = json.load(f)
                        aggregated_proofs.append({
                            'file': agg_file.name,
                            'ec_operations': agg_data.get('aggregation_metadata', {}).get('ec_operations_performed', 0),
                            'cross_terms': agg_data.get('aggregation_metadata', {}).get('cross_terms_computed', 0)
                        })
                except:
                    pass
        
        return {
            'run_name': run_path.name,
            'timestamp': parse_run_timestamp(run_path.name),
            'results': results,
            'config': config,
            'total_proofs': total_proofs,
            'client_proofs': client_proofs,
            'aggregated_proofs': aggregated_proofs,
            'path': str(run_path)
        }
    except Exception as e:
        print(f"Error loading run {run_path}: {e}")
        return None


def get_all_runs() -> List[Dict[str, Any]]:
    """Get all runs sorted by timestamp (newest first)."""
    runs = []
    
    if not RESULTS_DIR.exists():
        return runs
    
    for run_dir in RESULTS_DIR.iterdir():
        if run_dir.is_dir() and run_dir.name.startswith("run_"):
            run_data = load_run_data(run_dir)
            if run_data:
                runs.append(run_data)
    
    # Sort by timestamp (newest first)
    runs.sort(key=lambda x: x['timestamp'], reverse=True)
    return runs


def compute_comparative_metrics(runs: List[Dict]) -> Dict[str, Any]:
    """Compute comparative metrics across all runs."""
    if not runs:
        return {}
    
    metrics = {
        'accuracy': {
            'values': [],
            'labels': [],
            'best': None,
            'worst': None,
            'avg': 0
        },
        'loss': {
            'values': [],
            'labels': [],
            'best': None,
            'worst': None,
            'avg': 0
        },
        'proof_time': {
            'values': [],
            'labels': [],
            'best': None,
            'worst': None,
            'avg': 0
        },
        'proof_size': {
            'values': [],
            'labels': [],
            'best': None,
            'worst': None,
            'avg': 0
        },
        'total_time': {
            'values': [],
            'labels': [],
            'best': None,
            'worst': None,
            'avg': 0
        },
        'verification_rate': {
            'values': [],
            'labels': [],
            'best': None,
            'worst': None,
            'avg': 0
        }
    }
    
    for run in runs:
        results = run.get('results', {})
        summary = results.get('summary', {})
        rounds = results.get('rounds', [])
        
        label = run['timestamp'].strftime("%m/%d %H:%M")
        
        # Final accuracy
        final_acc = summary.get('final_accuracy', 0)
        metrics['accuracy']['values'].append(final_acc * 100)
        metrics['accuracy']['labels'].append(label)
        
        # Final loss (from last round)
        if rounds:
            final_loss = rounds[-1].get('avg_loss', 0)
            metrics['loss']['values'].append(final_loss)
            metrics['loss']['labels'].append(label)
        
        # Avg proof time
        avg_proof_time = summary.get('avg_proof_size_bytes', 0)
        if rounds:
            proof_times = [r.get('avg_proof_time', 0) for r in rounds if r.get('avg_proof_time')]
            if proof_times:
                avg_proof_time = sum(proof_times) / len(proof_times)
        metrics['proof_time']['values'].append(avg_proof_time)
        metrics['proof_time']['labels'].append(label)
        
        # Avg proof size
        avg_size = summary.get('avg_proof_size_bytes', 0)
        metrics['proof_size']['values'].append(avg_size)
        metrics['proof_size']['labels'].append(label)
        
        # Total time
        total_time = results.get('total_training_time', 0)
        metrics['total_time']['values'].append(total_time / 60)  # Convert to minutes
        metrics['total_time']['labels'].append(label)
        
        # Verification rate
        if rounds:
            total_verified = sum(r.get('num_verified', 0) for r in rounds)
            total_clients = sum(r.get('num_clients', 0) for r in rounds)
            ver_rate = (total_verified / total_clients * 100) if total_clients > 0 else 0
            metrics['verification_rate']['values'].append(ver_rate)
            metrics['verification_rate']['labels'].append(label)
    
    # Compute stats for each metric
    for key in metrics:
        values = metrics[key]['values']
        if values:
            metrics[key]['avg'] = sum(values) / len(values)
            if key in ['loss', 'proof_time', 'proof_size', 'total_time']:
                # Lower is better
                metrics[key]['best'] = min(values)
                metrics[key]['worst'] = max(values)
            else:
                # Higher is better
                metrics[key]['best'] = max(values)
                metrics[key]['worst'] = min(values)
    
    return metrics


@app.route('/')
def index():
    """Main dashboard page."""
    runs = get_all_runs()
    current_run = runs[0] if runs else None
    comparative = compute_comparative_metrics(runs)
    
    return render_template('index.html', 
                         runs=runs, 
                         current_run=current_run,
                         comparative=comparative,
                         total_runs=len(runs))


@app.route('/api/runs')
def api_runs():
    """API endpoint for all runs."""
    runs = get_all_runs()
    
    # Convert datetime to string for JSON
    for run in runs:
        run['timestamp'] = run['timestamp'].isoformat()
    
    return jsonify(runs)


@app.route('/api/run/<run_name>')
def api_run_detail(run_name: str):
    """API endpoint for specific run details."""
    run_path = RESULTS_DIR / run_name
    if not run_path.exists():
        return jsonify({'error': 'Run not found'}), 404
    
    run_data = load_run_data(run_path)
    if not run_data:
        return jsonify({'error': 'Could not load run data'}), 500
    
    run_data['timestamp'] = run_data['timestamp'].isoformat()
    return jsonify(run_data)


@app.route('/api/compare')
def api_compare():
    """API endpoint for comparative metrics."""
    runs = get_all_runs()
    return jsonify(compute_comparative_metrics(runs))


@app.route('/api/run/<run_name>/proofs')
def api_run_proofs(run_name: str):
    """API endpoint for proof details of a run."""
    run_path = RESULTS_DIR / run_name / "proofs"
    if not run_path.exists():
        return jsonify({'error': 'Proofs not found'}), 404
    
    proofs = {
        'clients': {},
        'aggregated': []
    }
    
    # Load client proofs
    for client_dir in run_path.iterdir():
        if client_dir.is_dir() and client_dir.name.startswith("client_"):
            client_proofs = []
            for proof_file in sorted(client_dir.glob("*.json")):
                try:
                    with open(proof_file, 'r') as f:
                        proof_data = json.load(f)
                        client_proofs.append({
                            'file': proof_file.name,
                            'round': proof_file.stem.split('_')[1] if '_' in proof_file.stem else '?',
                            'protocol': proof_data.get('protocol_type', 'unknown'),
                            'has_kzg': 'kzg_opening_proofs' in proof_data.get('proof_data', {}),
                            'challenge': str(proof_data.get('proof_data', {}).get('challenge', ''))[:16] + '...'
                        })
                except:
                    pass
            proofs['clients'][client_dir.name] = client_proofs
    
    # Load aggregated proofs
    agg_dir = run_path / "aggregated"
    if agg_dir.exists():
        for agg_file in sorted(agg_dir.glob("*.json")):
            try:
                with open(agg_file, 'r') as f:
                    agg_data = json.load(f)
                    metadata = agg_data.get('aggregation_metadata', {})
                    proofs['aggregated'].append({
                        'file': agg_file.name,
                        'original_proofs': metadata.get('original_proof_count', 0),
                        'ec_operations': metadata.get('ec_operations_performed', 0),
                        'cross_terms': metadata.get('cross_terms_computed', 0),
                        'lagrange_degree': metadata.get('polynomial_degree', 0)
                    })
            except:
                pass
    
    return jsonify(proofs)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
