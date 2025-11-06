"""ZKP technique wrappers and interfaces.

This module provides real ZKP implementations using cryptographic libraries.
Mock implementations have been removed - all techniques use actual crypto.
"""

from .base import ZKPTechnique

# Real implementations using cryptographic libraries
from .stark_real import STARKWrapper
from .groth16_real import Groth16Wrapper

# Rust-based implementations (requires compilation)
try:
    from .plonk_real import PLONKWrapper
    from .bulletproofs_real import BulletproofsWrapper
    HAS_RUST = True
except ImportError:
    # Fallback: raise error when trying to use these
    class PLONKWrapper(ZKPTechnique):
        def __init__(self, *args, **kwargs):
            raise ImportError("PLONK requires Rust bindings. See docs/RUST_INTEGRATION.md")
    
    class BulletproofsWrapper(ZKPTechnique):
        def __init__(self, *args, **kwargs):
            raise ImportError("Bulletproofs requires Rust bindings. See docs/RUST_INTEGRATION.md")
    
    HAS_RUST = False

# Additional implementations
# Note: Halo2, Protostar, zkSNARK, and Nova require additional setup
# See docs/ZKP_LIBRARY_INTEGRATION.md for details

__all__ = [
    "ZKPTechnique",
    "STARKWrapper",
    "Groth16Wrapper",
    "PLONKWrapper",
    "BulletproofsWrapper",
]
