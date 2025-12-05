"""
ProtoGalaxy Folding Event Emitter

Streams real-time folding events during proof aggregation
for visualization in the dashboard
"""

import asyncio
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class FoldingEvent:
    """Event emitted during ProtoGalaxy folding"""
    type: str  # 'lagrange_compute', 'cross_term', 'witness_fold', 'commitment_fold', 'complete'
    step: int
    total_steps: int
    data: Dict[str, Any]
    timestamp: float

class FoldingEventEmitter:
    """
    Singleton event emitter for ProtoGalaxy folding events
    
    Usage in protostar_production.py:
        emitter = FoldingEventEmitter.get_instance()
        emitter.emit('cross_term', step=1, total=5, data={'proof_pair': (0,1)})
    """
    
    _instance: Optional['FoldingEventEmitter'] = None
    _callback: Optional[Callable] = None
    
    @classmethod
    def get_instance(cls) -> 'FoldingEventEmitter':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_callback(cls, callback: Callable[[FoldingEvent], None]):
        """Set callback to receive folding events (for WebSocket broadcasting)"""
        instance = cls.get_instance()
        instance._callback = callback
    
    @classmethod
    def clear_callback(cls):
        """Clear callback"""
        instance = cls.get_instance()
        instance._callback = None
    
    def emit(self, event_type: str, step: int, total_steps: int, data: Dict[str, Any]):
        """Emit a folding event"""
        import time
        
        event = FoldingEvent(
            type=event_type,
            step=step,
            total_steps=total_steps,
            data=data,
            timestamp=time.time()
        )
        
        if self._callback:
            # Call callback (should be async-safe)
            try:
                self._callback(asdict(event))
            except Exception as e:
                print(f"Error in folding event callback: {e}")
