"""Python wrapper for Rust-based PLONK (Halo2) implementation."""

from typing import Dict, Any
import time
import numpy as np
from loguru import logger

from ..zkp_techniques.base import ZKPTechnique, ProofResult, VerificationResult

try:
    from zkp_bindings import PlonkProver as RustPlonkProver
    HAS_RUST_BINDINGS = True
except ImportError:
    HAS_RUST_BINDINGS = False
    logger.warning("Rust ZKP bindings not available. Build with: cd rust_zkp && maturin develop")


class PLONKWrapper(ZKPTechnique):
    """PLONK implementation using Halo2 (Rust).
    
    PLONK is a universal SNARK with:
    - Custom gates
    - Lookup tables
    - Universal trusted setup (SRS)
    - Polynomial commitment schemes
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("PLONK", config)
        
        if not HAS_RUST_BINDINGS:
            raise ImportError("Rust ZKP bindings required. See docs/RUST_INTEGRATION.md")
        
        self.prover = None
    
    def setup(self, circuit_size: int, **kwargs) -> float:
        """Setup universal SRS for PLONK."""
        start = time.perf_counter()
        
        # Ensure circuit_size is a plain Python int and within safe bounds
        # PyO3 has issues converting very large numbers
        safe_circuit_size = min(int(circuit_size), 1_048_576)
        self.circuit_size = safe_circuit_size
        
        # Instantiate Rust prover without arguments
        self.prover = RustPlonkProver()
        
        # Generate proving and verifying keys
        self.keys = self.prover.setup(safe_circuit_size)
        
        self.is_setup = True
        
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"PLONK setup completed for circuit size {circuit_size}")
        return elapsed
    
    def generate_proof(
        self,
        public_inputs: Any,
        private_inputs: Any,
        circuit_description: Any,
        **kwargs
    ) -> ProofResult:
        """Generate PLONK proof using Halo2."""
        if not self.is_setup:
            raise RuntimeError("Must call setup() first")
        
        start = time.perf_counter()
        
        # Rust prove() takes no arguments - proof generated from pre-configured circuit
        proof_bytes = bytes(self.prover.prove())
        
        generation_time = (time.perf_counter() - start) * 1000
        
        # PLONK proof size is moderate (polynomial commitments + openings)
        proof_size = len(proof_bytes)
        
        # Estimate memory
        witness_size = self._get_witness_size(private_inputs)
        memory_mb = (witness_size * 8 + len(self.keys)) / (1024 * 1024)
        
        return ProofResult(
            proof=proof_bytes,
            generation_time_ms=generation_time,
            proof_size_bytes=proof_size,
            memory_usage_mb=memory_mb,
            setup_time_ms=0.0,
            metadata={"circuit_size": self.circuit_size}
        )
    
    def _get_witness_size(self, private_inputs: Any) -> int:
        """Get size of witness data."""
        if isinstance(private_inputs, np.ndarray):
            return private_inputs.size
        return 1
    
    def verify_proof(
        self,
        proof: bytes,
        public_inputs: Any,
        **kwargs
    ) -> VerificationResult:
        """Verify PLONK proof."""
        start = time.perf_counter()
        
        # Rust verify() takes proof_bytes and public_inputs
        public_vals = self._prepare_public_inputs(public_inputs)
        is_valid = self.prover.verify(list(proof), public_vals)
        
        verification_time = (time.perf_counter() - start) * 1000
        
        return VerificationResult(
            is_valid=is_valid,
            verification_time_ms=verification_time,
            metadata={}
        )
    
    def _prepare_witness(self, private_inputs: Any) -> list:
        """Convert private inputs to witness vector.
        
        For large arrays (>100k elements), we use a hash-based commitment.
        All values are mapped to u8 range (0-255) for Rust Vec<u8> compatibility.
        """
        if isinstance(private_inputs, np.ndarray):
            arr = private_inputs.flatten()
            
            # For very large arrays, use a hash-based commitment
            if arr.size > 100_000:
                import hashlib
                data_bytes = arr.tobytes()
                hash_digest = hashlib.sha256(data_bytes).digest()
                return [int(b) for b in hash_digest]
            else:
                # Map all values to u8 range to avoid overflow
                return [int(abs(x)) % 256 for x in arr]
        
        return [int(abs(private_inputs)) % 256]
    
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
    
    def requires_trusted_setup(self) -> bool:
        return True  # Universal SRS
    
    def is_transparent(self) -> bool:
        return False
    
    def is_post_quantum(self) -> bool:
        return False
    
    def get_proof_type(self) -> str:
        return "SNARK"
