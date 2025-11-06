"""Metrics collection utilities."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import time


@dataclass
class BenchmarkMetrics:
    """Container for benchmark metrics."""
    
    technique: str
    operation: str
    tensor_size: str
    
    # Timing metrics (ms)
    proof_gen_times: List[float] = field(default_factory=list)
    verification_times: List[float] = field(default_factory=list)
    setup_time: float = 0.0
    
    # Size metrics
    proof_sizes: List[int] = field(default_factory=list)
    memory_usages: List[float] = field(default_factory=list)
    
    # Metadata
    trials: int = 0
    successes: int = 0


class MetricsCollector:
    """Collect and aggregate benchmark metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, BenchmarkMetrics] = {}
    
    def add_result(self, result: Dict[str, Any]):
        """Add a benchmark result."""
        key = f"{result['technique']}_{result['tensor_size']}_{result['operation']}"
        
        if key not in self.metrics:
            self.metrics[key] = BenchmarkMetrics(
                technique=result['technique'],
                operation=result['operation'],
                tensor_size=result['tensor_size']
            )
        
        m = self.metrics[key]
        m.proof_gen_times.append(result['proof_gen_time_ms'])
        m.verification_times.append(result['verification_time_ms'])
        m.proof_sizes.append(result['proof_size_bytes'])
        m.memory_usages.append(result['memory_usage_mb'])
        m.trials += 1
        if result.get('is_valid', False):
            m.successes += 1
    
    def get_statistics(self, key: str) -> Dict[str, Any]:
        """Get statistics for a specific configuration."""
        import numpy as np
        
        m = self.metrics[key]
        
        return {
            "technique": m.technique,
            "operation": m.operation,
            "tensor_size": m.tensor_size,
            "trials": m.trials,
            "success_rate": m.successes / m.trials if m.trials > 0 else 0,
            "proof_gen_time": {
                "mean": np.mean(m.proof_gen_times),
                "median": np.median(m.proof_gen_times),
                "std": np.std(m.proof_gen_times),
                "min": np.min(m.proof_gen_times),
                "max": np.max(m.proof_gen_times),
            },
            "verification_time": {
                "mean": np.mean(m.verification_times),
                "median": np.median(m.verification_times),
                "std": np.std(m.verification_times),
            },
            "proof_size": {
                "mean": np.mean(m.proof_sizes),
                "std": np.std(m.proof_sizes),
            },
            "memory_usage": {
                "mean": np.mean(m.memory_usages),
                "peak": np.max(m.memory_usages),
            },
        }
