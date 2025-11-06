"""Halo2 wrapper (uses PLONK implementation with Halo2)."""

from typing import Dict, Any
from loguru import logger

from ..zkp_techniques.plonk_real import PLONKWrapper


class Halo2Wrapper(PLONKWrapper):
    """Halo2 implementation (alias for PLONK with Halo2 backend).
    
    Halo2 provides:
    - Recursive proof composition
    - No trusted setup
    - IPA-based polynomial commitment
    - Used in Zcash Orchard
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "Halo2"
    
    def get_proof_type(self) -> str:
        return "Recursive SNARK"
