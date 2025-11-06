"""Memory profiling utilities."""

import psutil
import os
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class MemoryUsage:
    """Memory usage statistics."""
    peak_mb: float
    current_mb: float
    delta_mb: float


class MemoryProfiler:
    """Profile memory usage during operations."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
    
    def get_current_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    @contextmanager
    def profile(self):
        """Context manager for profiling memory usage.
        
        Usage:
            with profiler.profile() as usage:
                # code to profile
                pass
            print(f"Peak memory: {usage.peak_mb} MB")
        """
        start_mb = self.get_current_mb()
        peak_mb = start_mb
        
        class _MemoryTracker:
            def __init__(self, profiler):
                self.profiler = profiler
                self.peak_mb = start_mb
                self.current_mb = start_mb
                self.delta_mb = 0
            
            def update(self):
                self.current_mb = self.profiler.get_current_mb()
                self.peak_mb = max(self.peak_mb, self.current_mb)
                self.delta_mb = self.current_mb - start_mb
        
        tracker = _MemoryTracker(self)
        
        try:
            yield tracker
        finally:
            tracker.update()
