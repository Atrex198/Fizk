"""Base interface for ZKP techniques."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from dataclasses import dataclass


@dataclass
class ProofResult:
    """Result of proof generation."""
    proof: Any
    generation_time_ms: float
    proof_size_bytes: int
    memory_usage_mb: float
    setup_time_ms: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class VerificationResult:
    """Result of proof verification."""
    is_valid: bool
    verification_time_ms: float
    metadata: Dict[str, Any] = None


class ZKPTechnique(ABC):
    """Abstract base class for ZKP technique wrappers."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize ZKP technique.
        
        Args:
            name: Technique name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.is_setup = False
        self.setup_data = None

    @abstractmethod
    def setup(self, circuit_size: int, **kwargs) -> float:
        """Perform any necessary setup (e.g., trusted setup).
        
        Args:
            circuit_size: Size/complexity of the circuit
            **kwargs: Additional setup parameters
            
        Returns:
            Setup time in milliseconds
        """
        pass

    @abstractmethod
    def generate_proof(
        self,
        public_inputs: Any,
        private_inputs: Any,
        circuit_description: Any,
        **kwargs
    ) -> ProofResult:
        """Generate a zero-knowledge proof.
        
        Args:
            public_inputs: Public circuit inputs
            private_inputs: Private witness data
            circuit_description: Description of the computation
            **kwargs: Additional parameters
            
        Returns:
            ProofResult with proof and metrics
        """
        pass

    @abstractmethod
    def verify_proof(
        self,
        proof: Any,
        public_inputs: Any,
        **kwargs
    ) -> VerificationResult:
        """Verify a zero-knowledge proof.
        
        Args:
            proof: The proof to verify
            public_inputs: Public circuit inputs
            **kwargs: Additional parameters
            
        Returns:
            VerificationResult with validity and metrics
        """
        pass

    def get_proof_size(self, proof: Any) -> int:
        """Get size of proof in bytes.
        
        Args:
            proof: The proof object
            
        Returns:
            Size in bytes
        """
        import sys
        return sys.getsizeof(proof)

    def reset(self):
        """Reset the technique state."""
        self.is_setup = False
        self.setup_data = None

    def get_info(self) -> Dict[str, Any]:
        """Get information about this technique.
        
        Returns:
            Dictionary with technique metadata
        """
        return {
            "name": self.name,
            "requires_trusted_setup": self.requires_trusted_setup(),
            "is_transparent": self.is_transparent(),
            "is_post_quantum": self.is_post_quantum(),
            "proof_type": self.get_proof_type(),
        }

    @abstractmethod
    def requires_trusted_setup(self) -> bool:
        """Whether this technique requires trusted setup."""
        pass

    @abstractmethod
    def is_transparent(self) -> bool:
        """Whether this technique is transparent (no trusted setup)."""
        pass

    @abstractmethod
    def is_post_quantum(self) -> bool:
        """Whether this technique is post-quantum secure."""
        pass

    @abstractmethod
    def get_proof_type(self) -> str:
        """Get the proof system type (SNARK, STARK, etc.)."""
        pass
