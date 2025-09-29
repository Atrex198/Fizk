"""
ZK-FL Metrics Collection System
Comprehensive performance, cost, and ML metrics tracking for benchmarking

Features:
- Real-time performance monitoring
- Cost analysis (computational, communication)
- ML convergence tracking
- Scalability metrics
- Export to multiple formats (JSON, CSV, plots)
"""

import time
import psutil
import json
import csv
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import threading
import os

logger = logging.getLogger(__name__)

@dataclass
class ProofMetrics:
    """Metrics for ZKP proof generation"""
    client_id: str
    proof_generation_time: float
    proof_size_bytes: int
    constraint_count: int
    variable_count: int
    verification_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float

@dataclass
class AggregationMetrics:
    """Metrics for proof aggregation"""
    round_number: int
    num_proofs: int
    aggregation_time: float
    aggregated_proof_size: int
    cross_terms_computed: int
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float

@dataclass
class MLMetrics:
    """Machine learning performance metrics"""
    client_id: str
    round_number: int
    initial_loss: float
    final_loss: float
    loss_improvement: float
    accuracy: Optional[float]
    training_time: float
    data_samples: int
    epochs: int
    learning_rate: float
    timestamp: float

@dataclass
class CommunicationMetrics:
    """Communication overhead metrics"""
    round_number: int
    client_id: str
    weights_size_bytes: int
    proof_size_bytes: int
    upload_time: float
    download_time: float
    total_bandwidth_bytes: int
    timestamp: float

@dataclass
class SystemMetrics:
    """Overall system performance metrics"""
    round_number: int
    total_clients: int
    active_clients: int
    round_duration: float
    total_memory_usage_mb: float
    peak_memory_usage_mb: float
    avg_cpu_usage_percent: float
    disk_usage_mb: float
    timestamp: float

class MetricsCollector:
    """
    Comprehensive metrics collection system for ZK-FL benchmarking
    """
    
    def __init__(self, experiment_name: str, output_dir: str = "./metrics"):
        self.experiment_name = experiment_name
        self.output_dir = output_dir
        self.start_time = time.time()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Metrics storage
        self.proof_metrics: List[ProofMetrics] = []
        self.aggregation_metrics: List[AggregationMetrics] = []
        self.ml_metrics: List[MLMetrics] = []
        self.communication_metrics: List[CommunicationMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        
        # Real-time monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.system_snapshots = []
        
        # Performance baselines
        self.baseline_memory = psutil.virtual_memory().used / (1024**2)
        
        logger.info(f"📊 Metrics collector initialized: {experiment_name}")
        logger.info(f"📁 Output directory: {output_dir}")
    
    def start_monitoring(self, interval: float = 1.0):
        """Start real-time system monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_system, 
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"🔄 Started system monitoring (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop real-time system monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        logger.info("⏹️ Stopped system monitoring")
    
    def _monitor_system(self, interval: float):
        """Background system monitoring thread"""
        while self.monitoring_active:
            try:
                snapshot = {
                    'timestamp': time.time(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_mb': psutil.virtual_memory().used / (1024**2),
                    'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                    'network_io': psutil.net_io_counters()._asdict()
                }
                self.system_snapshots.append(snapshot)
                time.sleep(interval)
            except Exception as e:
                logger.warning(f"System monitoring error: {e}")
                time.sleep(interval)
    
    def record_proof_generation(self, 
                              client_id: str,
                              start_time: float,
                              end_time: float,
                              proof_data: Dict[str, Any],
                              process_info: Optional[Dict] = None) -> ProofMetrics:
        """Record ZKP proof generation metrics"""
        
        # Calculate metrics
        generation_time = end_time - start_time
        proof_size = len(json.dumps(proof_data).encode())
        
        # Extract circuit info
        circuit_info = proof_data.get('circuit_info', {})
        constraint_count = circuit_info.get('constraints_count', 0)
        variable_count = circuit_info.get('variables_count', 0)
        
        # Memory and CPU usage
        if process_info:
            memory_mb = process_info.get('memory_mb', 0)
            cpu_percent = process_info.get('cpu_percent', 0)
        else:
            memory_mb = psutil.virtual_memory().used / (1024**2) - self.baseline_memory
            cpu_percent = psutil.cpu_percent()
        
        # Verification time (simplified - would need actual verification)
        verification_time = generation_time * 0.1  # Typically ~10% of generation time
        
        metrics = ProofMetrics(
            client_id=client_id,
            proof_generation_time=generation_time,
            proof_size_bytes=proof_size,
            constraint_count=constraint_count,
            variable_count=variable_count,
            verification_time=verification_time,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
            timestamp=end_time
        )
        
        self.proof_metrics.append(metrics)
        
        logger.info(f"📊 Proof metrics recorded for {client_id}: "
                   f"{generation_time:.3f}s, {proof_size} bytes")
        
        return metrics
    
    def record_aggregation(self,
                          round_number: int,
                          num_proofs: int,
                          start_time: float,
                          end_time: float,
                          aggregated_proof: Dict[str, Any],
                          cross_terms: int) -> AggregationMetrics:
        """Record proof aggregation metrics"""
        
        aggregation_time = end_time - start_time
        proof_size = len(json.dumps(aggregated_proof).encode())
        
        memory_mb = psutil.virtual_memory().used / (1024**2) - self.baseline_memory
        cpu_percent = psutil.cpu_percent()
        
        metrics = AggregationMetrics(
            round_number=round_number,
            num_proofs=num_proofs,
            aggregation_time=aggregation_time,
            aggregated_proof_size=proof_size,
            cross_terms_computed=cross_terms,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
            timestamp=end_time
        )
        
        self.aggregation_metrics.append(metrics)
        
        logger.info(f"📊 Aggregation metrics recorded for round {round_number}: "
                   f"{aggregation_time:.3f}s, {num_proofs} proofs")
        
        return metrics
    
    def record_ml_performance(self,
                            client_id: str,
                            round_number: int,
                            initial_loss: float,
                            final_loss: float,
                            accuracy: Optional[float],
                            training_time: float,
                            data_samples: int,
                            epochs: int,
                            learning_rate: float) -> MLMetrics:
        """Record ML training performance metrics"""
        
        loss_improvement = initial_loss - final_loss
        
        metrics = MLMetrics(
            client_id=client_id,
            round_number=round_number,
            initial_loss=initial_loss,
            final_loss=final_loss,
            loss_improvement=loss_improvement,
            accuracy=accuracy,
            training_time=training_time,
            data_samples=data_samples,
            epochs=epochs,
            learning_rate=learning_rate,
            timestamp=time.time()
        )
        
        self.ml_metrics.append(metrics)
        
        logger.info(f"📊 ML metrics recorded for {client_id} round {round_number}: "
                   f"loss {initial_loss:.4f}→{final_loss:.4f}")
        
        return metrics
    
    def record_communication(self,
                           round_number: int,
                           client_id: str,
                           weights_size: int,
                           proof_size: int,
                           upload_time: float,
                           download_time: float) -> CommunicationMetrics:
        """Record communication overhead metrics"""
        
        total_bandwidth = weights_size + proof_size
        
        metrics = CommunicationMetrics(
            round_number=round_number,
            client_id=client_id,
            weights_size_bytes=weights_size,
            proof_size_bytes=proof_size,
            upload_time=upload_time,
            download_time=download_time,
            total_bandwidth_bytes=total_bandwidth,
            timestamp=time.time()
        )
        
        self.communication_metrics.append(metrics)
        
        logger.info(f"📊 Communication metrics recorded for {client_id}: "
                   f"{total_bandwidth} bytes")
        
        return metrics
    
    def record_system_state(self,
                          round_number: int,
                          total_clients: int,
                          active_clients: int,
                          round_duration: float) -> SystemMetrics:
        """Record overall system state metrics"""
        
        memory_info = psutil.virtual_memory()
        current_memory = memory_info.used / (1024**2)
        
        # Calculate peak memory from snapshots
        peak_memory = max([s['memory_mb'] for s in self.system_snapshots[-10:]], 
                         default=current_memory)
        
        # Calculate average CPU from recent snapshots
        avg_cpu = np.mean([s['cpu_percent'] for s in self.system_snapshots[-10:]]) \
                 if self.system_snapshots else psutil.cpu_percent()
        
        disk_usage = psutil.disk_usage('/').used / (1024**2)
        
        metrics = SystemMetrics(
            round_number=round_number,
            total_clients=total_clients,
            active_clients=active_clients,
            round_duration=round_duration,
            total_memory_usage_mb=current_memory,
            peak_memory_usage_mb=peak_memory,
            avg_cpu_usage_percent=avg_cpu,
            disk_usage_mb=disk_usage,
            timestamp=time.time()
        )
        
        self.system_metrics.append(metrics)
        
        logger.info(f"📊 System metrics recorded for round {round_number}")
        
        return metrics
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics"""
        
        total_duration = time.time() - self.start_time
        
        # Proof generation stats
        if self.proof_metrics:
            proof_times = [m.proof_generation_time for m in self.proof_metrics]
            proof_sizes = [m.proof_size_bytes for m in self.proof_metrics]
            proof_stats = {
                'count': len(self.proof_metrics),
                'avg_time': np.mean(proof_times),
                'min_time': np.min(proof_times),
                'max_time': np.max(proof_times),
                'std_time': np.std(proof_times),
                'avg_size_bytes': np.mean(proof_sizes),
                'total_time': np.sum(proof_times)
            }
        else:
            proof_stats = {}
        
        # Aggregation stats
        if self.aggregation_metrics:
            agg_times = [m.aggregation_time for m in self.aggregation_metrics]
            agg_stats = {
                'count': len(self.aggregation_metrics),
                'avg_time': np.mean(agg_times),
                'total_time': np.sum(agg_times),
                'total_proofs_aggregated': sum(m.num_proofs for m in self.aggregation_metrics)
            }
        else:
            agg_stats = {}
        
        # ML performance stats
        if self.ml_metrics:
            improvements = [m.loss_improvement for m in self.ml_metrics]
            final_losses = [m.final_loss for m in self.ml_metrics]
            ml_stats = {
                'total_training_rounds': len(set(m.round_number for m in self.ml_metrics)),
                'avg_loss_improvement': np.mean(improvements),
                'final_avg_loss': np.mean(final_losses),
                'convergence_rate': np.mean(improvements) / total_duration if total_duration > 0 else 0
            }
        else:
            ml_stats = {}
        
        return {
            'experiment_name': self.experiment_name,
            'total_duration': total_duration,
            'timestamp': datetime.now().isoformat(),
            'proof_generation': proof_stats,
            'aggregation': agg_stats,
            'ml_performance': ml_stats,
            'system_snapshots_count': len(self.system_snapshots)
        }
    
    def export_metrics(self, formats: List[str] = ['json', 'csv']):
        """Export collected metrics to various formats"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{self.experiment_name}_{timestamp}"
        
        # Export to JSON
        if 'json' in formats:
            json_file = os.path.join(self.output_dir, f"{base_filename}_metrics.json")
            metrics_data = {
                'summary': self.get_summary_stats(),
                'proof_metrics': [asdict(m) for m in self.proof_metrics],
                'aggregation_metrics': [asdict(m) for m in self.aggregation_metrics],
                'ml_metrics': [asdict(m) for m in self.ml_metrics],
                'communication_metrics': [asdict(m) for m in self.communication_metrics],
                'system_metrics': [asdict(m) for m in self.system_metrics],
                'system_snapshots': self.system_snapshots
            }
            
            with open(json_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            logger.info(f"📁 Exported JSON metrics: {json_file}")
        
        # Export to CSV
        if 'csv' in formats:
            self._export_csv(base_filename)
        
        # Generate plots
        if 'plots' in formats:
            self._generate_plots(base_filename)
    
    def _export_csv(self, base_filename: str):
        """Export metrics to CSV files"""
        
        # Proof metrics CSV
        if self.proof_metrics:
            csv_file = os.path.join(self.output_dir, f"{base_filename}_proof_metrics.csv")
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.proof_metrics[0]).keys())
                writer.writeheader()
                for metrics in self.proof_metrics:
                    writer.writerow(asdict(metrics))
            logger.info(f"📁 Exported proof metrics CSV: {csv_file}")
        
        # ML metrics CSV
        if self.ml_metrics:
            csv_file = os.path.join(self.output_dir, f"{base_filename}_ml_metrics.csv")
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.ml_metrics[0]).keys())
                writer.writeheader()
                for metrics in self.ml_metrics:
                    writer.writerow(asdict(metrics))
            logger.info(f"📁 Exported ML metrics CSV: {csv_file}")
    
    def _generate_plots(self, base_filename: str):
        """Generate visualization plots"""
        
        plt.style.use('seaborn-v0_8')
        
        # Proof generation time plot
        if self.proof_metrics:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Proof generation times
            times = [m.proof_generation_time for m in self.proof_metrics]
            clients = [m.client_id for m in self.proof_metrics]
            
            ax1.bar(range(len(times)), times)
            ax1.set_title('Proof Generation Times')
            ax1.set_xlabel('Proof Index')
            ax1.set_ylabel('Time (seconds)')
            ax1.grid(True, alpha=0.3)
            
            # Memory usage
            memory = [m.memory_usage_mb for m in self.proof_metrics]
            ax2.plot(memory, marker='o')
            ax2.set_title('Memory Usage During Proof Generation')
            ax2.set_xlabel('Proof Index')
            ax2.set_ylabel('Memory (MB)')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plot_file = os.path.join(self.output_dir, f"{base_filename}_proof_performance.png")
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Generated proof performance plot: {plot_file}")
        
        # ML convergence plot
        if self.ml_metrics:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Group by round
            rounds = {}
            for m in self.ml_metrics:
                if m.round_number not in rounds:
                    rounds[m.round_number] = []
                rounds[m.round_number].append(m.final_loss)
            
            round_nums = sorted(rounds.keys())
            avg_losses = [np.mean(rounds[r]) for r in round_nums]
            
            ax.plot(round_nums, avg_losses, marker='o', linewidth=2, markersize=8)
            ax.set_title('FL Convergence - Average Loss per Round')
            ax.set_xlabel('Round Number')
            ax.set_ylabel('Average Loss')
            ax.grid(True, alpha=0.3)
            
            plot_file = os.path.join(self.output_dir, f"{base_filename}_ml_convergence.png")
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Generated ML convergence plot: {plot_file}")
    
    def __del__(self):
        """Cleanup when collector is destroyed"""
        self.stop_monitoring()


# Context manager for easy metrics collection
class MetricsContext:
    """Context manager for automatic metrics collection"""
    
    def __init__(self, collector: MetricsCollector, operation: str, **kwargs):
        self.collector = collector
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        
        if self.operation == 'proof_generation':
            self.collector.record_proof_generation(
                start_time=self.start_time,
                end_time=end_time,
                **self.kwargs
            )
        elif self.operation == 'aggregation':
            self.collector.record_aggregation(
                start_time=self.start_time,
                end_time=end_time,
                **self.kwargs
            )


if __name__ == "__main__":
    # Example usage
    collector = MetricsCollector("test_experiment")
    collector.start_monitoring()
    
    # Simulate some metrics
    time.sleep(2)
    
    collector.record_proof_generation(
        client_id="test_client",
        start_time=time.time() - 1,
        end_time=time.time(),
        proof_data={"circuit_info": {"constraints_count": 1000}},
    )
    
    collector.record_ml_performance(
        client_id="test_client",
        round_number=1,
        initial_loss=0.8,
        final_loss=0.6,
        accuracy=0.85,
        training_time=5.0,
        data_samples=1000,
        epochs=3,
        learning_rate=0.01
    )
    
    collector.stop_monitoring()
    collector.export_metrics(['json', 'csv', 'plots'])
    
    print("📊 Metrics collection demo completed!")
    print(f"📁 Check {collector.output_dir} for exported metrics")