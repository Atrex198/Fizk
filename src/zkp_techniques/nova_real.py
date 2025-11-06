"""Python wrapper for Rust-based Nova implementation."""

from typing import Dict, Any
import time
import numpy as np
from loguru import logger

from ..zkp_techniques.base import ZKPTechnique, ProofResult, VerificationResult

try:
    from zkp_bindings import NovaProver as RustNovaProver
    HAS_RUST_BINDINGS = True
except ImportError:
    HAS_RUST_BINDINGS = False
    logger.warning("Rust ZKP bindings not available")


class NovaWrapper(ZKPTechnique):
    """Nova folding scheme implementation.
    
    Nova provides:
    - Recursive SNARKs without trusted setup
    - Folding scheme for incremental computation
    - Constant-size proof overhead
    - Efficient for iterative computations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Nova", config)
        
        if not HAS_RUST_BINDINGS:
            raise ImportError("Rust ZKP bindings required")
        
        self.prover = None
    
    def setup(self, circuit_size: int, **kwargs) -> float:
        """Setup Nova prover (no trusted setup required)."""
        start = time.perf_counter()
        
        # Ensure circuit_size is a plain Python int and within safe bounds
        safe_circuit_size = min(int(circuit_size), 1_000_000)
        self.circuit_size = safe_circuit_size
        
        # Instantiate without arguments
        self.prover = RustNovaProver()
        self.is_setup = True
        
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"Nova setup completed for circuit size {safe_circuit_size}")
        return elapsed
    
    def generate_proof(
        self,
        public_inputs: Any,
        private_inputs: Any,
        circuit_description: Any,
        **kwargs
    ) -> ProofResult:
        """Generate Nova proof using folding scheme."""
        if not self.is_setup:
            raise RuntimeError("Must call setup() first")
        
        start = time.perf_counter()
        
        # Convert witness
        witness = self._prepare_witness(private_inputs)
        
        # Nova requires num_iters parameter (number of folding steps)
        # Ensure it's a plain Python int, not numpy type
        num_iters = int(max(1, np.log2(self.circuit_size + 1)))
        
        # Generate folded proof - Rust prove() takes witness and num_iters
        proof_bytes = bytes(self.prover.prove(witness, num_iters))
        
        generation_time = (time.perf_counter() - start) * 1000
        
        # Nova has constant-size overhead
        proof_size = len(proof_bytes)
        
        memory_mb = len(witness) * 8 / (1024 * 1024)
        
        return ProofResult(
            proof=proof_bytes,
            generation_time_ms=generation_time,
            proof_size_bytes=proof_size,
            memory_usage_mb=memory_mb,
            setup_time_ms=0.0,
            metadata={"circuit_size": self.circuit_size, "folding_steps": num_iters}
        )
    
    def verify_proof(
        self,
        proof: bytes,
        public_inputs: Any,
        **kwargs
    ) -> VerificationResult:
        """Verify Nova proof."""
        start = time.perf_counter()
        
        # Rust verify() takes proof_bytes, public_inputs, and num_iters
        public_vals = self._prepare_public_inputs(public_inputs)
        num_iters = max(1, int(np.log2(self.circuit_size + 1)))
        
        is_valid = self.prover.verify(list(proof), public_vals, num_iters)
        
        verification_time = (time.perf_counter() - start) * 1000
        
        return VerificationResult(
            is_valid=is_valid,
            verification_time_ms=verification_time,
            metadata={}
        )
    
    def _prepare_public_inputs(self, public_inputs: Any) -> list:
        """Convert public inputs to field elements.
        
        All values mapped to u8 range (0-255) for Rust Vec<u8> compatibility.
        """
        if isinstance(public_inputs, (list, tuple)):
            if len(public_inputs) > 1000:
                # For very large public inputs, use hash
                import hashlib
                data_str = str(public_inputs).encode()
                hash_digest = hashlib.sha256(data_str).digest()
                return [int(b) for b in hash_digest[:8]]
            return [int(abs(x)) % 256 for x in public_inputs]
        if isinstance(public_inputs, np.ndarray):
            if public_inputs.size > 1000:
                import hashlib
                data_bytes = public_inputs.tobytes()
                hash_digest = hashlib.sha256(data_bytes).digest()
                return [int(b) for b in hash_digest[:8]]
            return [int(abs(x)) % 256 for x in public_inputs.flatten()]
        return [1]  # Default
    
    def _prepare_witness(self, private_inputs: Any) -> list:
        """Convert inputs to witness.
        
        For large arrays (>100k elements), we use a hash-based commitment.
        For all arrays, we ensure values fit in u8 range (0-255) for Rust Vec<u8>.
        """
        if isinstance(private_inputs, np.ndarray):
            arr = private_inputs.flatten()
            
            # For very large arrays, use a hash-based commitment
            if arr.size > 100_000:
                import hashlib
                data_bytes = arr.tobytes()
                hash_digest = hashlib.sha256(data_bytes).digest()
                # Convert hash bytes to list of u8 values
                return [int(b) for b in hash_digest]
            else:
                # For smaller arrays, we need to ensure all values fit in u8 range (0-255)
                # since Rust expects Vec<u8>. Use modulo to map large values into u8 range.
                return [int(abs(x)) % 256 for x in arr]
        
        # For scalar inputs
        return [int(abs(private_inputs)) % 256]
    
    def requires_trusted_setup(self) -> bool:
        return False
    
    def is_transparent(self) -> bool:
        return True
    
    def is_post_quantum(self) -> bool:
        return False
    
    def get_proof_type(self) -> str:
        return "Recursive SNARK"
