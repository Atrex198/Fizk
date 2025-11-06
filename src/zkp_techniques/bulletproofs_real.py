"""Python wrapper for Rust-based Bulletproofs implementation."""

from typing import Dict, Any
import time
import numpy as np
from loguru import logger

from ..zkp_techniques.base import ZKPTechnique, ProofResult, VerificationResult

try:
    from zkp_bindings import BulletproofsProver as RustBulletproofsProver
    HAS_RUST_BINDINGS = True
except ImportError:
    HAS_RUST_BINDINGS = False
    logger.warning("Rust ZKP bindings not available")


class BulletproofsWrapper(ZKPTechnique):
    """Bulletproofs implementation.
    
    Bulletproofs provide:
    - No trusted setup
    - Logarithmic proof size
    - Range proofs and R1CS
    - Based on inner product arguments
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Bulletproofs", config)
        
        if not HAS_RUST_BINDINGS:
            raise ImportError("Rust ZKP bindings required")
        
        self.bit_length = 64  # Default bit length for range proofs
    
    def setup(self, circuit_size: int, **kwargs) -> float:
        """Bulletproofs doesn't require trusted setup."""
        start = time.perf_counter()
        
        self.circuit_size = circuit_size
        self.bit_length = kwargs.get('bit_length', 64)
        
        # Instantiate without arguments
        self.prover = RustBulletproofsProver()
        self.is_setup = True
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def generate_proof(
        self,
        public_inputs: Any,
        private_inputs: Any,
        circuit_description: Any,
        **kwargs
    ) -> ProofResult:
        """Generate Bulletproof."""
        if not self.is_setup:
            raise RuntimeError("Must call setup() first")
        
        start = time.perf_counter()
        
        # Convert witness
        witness = self._prepare_witness(private_inputs)
        
        # Generate proof
        proof_bytes = self.prover.prove_r1cs(witness)
        
        generation_time = (time.perf_counter() - start) * 1000
        
        # Bulletproofs have O(log n) size
        proof_size = len(proof_bytes)
        
        memory_mb = len(witness) * 8 / (1024 * 1024)
        
        return ProofResult(
            proof=proof_bytes,
            generation_time_ms=generation_time,
            proof_size_bytes=proof_size,
            memory_usage_mb=memory_mb,
            setup_time_ms=0.0,
            metadata={"bit_length": self.bit_length}
        )
    
    def verify_proof(
        self,
        proof: bytes,
        public_inputs: Any,
        **kwargs
    ) -> VerificationResult:
        """Verify Bulletproof."""
        start = time.perf_counter()
        
        # Rust verify_range only takes proof_bytes argument
        is_valid = self.prover.verify_range(list(proof))
        
        verification_time = (time.perf_counter() - start) * 1000
        
        return VerificationResult(
            is_valid=is_valid,
            verification_time_ms=verification_time,
            metadata={}
        )
    
    def _prepare_witness(self, private_inputs: Any) -> list:
        """Convert inputs to witness."""
        if isinstance(private_inputs, np.ndarray):
            return private_inputs.flatten().astype(np.int64).tolist()
        return [int(private_inputs)]
    
    def requires_trusted_setup(self) -> bool:
        return False
    
    def is_transparent(self) -> bool:
        return True
    
    def is_post_quantum(self) -> bool:
        return False
    
    def get_proof_type(self) -> str:
        return "Bulletproofs"
