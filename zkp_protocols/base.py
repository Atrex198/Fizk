"""
Base interfaces and data structures for ZKP protocols
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np


class ProtocolType(Enum):
    """Supported ZKP protocols"""
    PROTOSTAR = "protostar"
    PROTOGALAXY = "protogalaxy"
    PLONK = "plonk"
    GROTH16 = "groth16"
    BULLETPROOFS = "bulletproofs"
    NOVA = "nova"


@dataclass
class TrainingStatement:
    """Public statement about training computation"""
    model_architecture: str
    initial_weights_commitment: str
    final_weights_commitment: str
    dataset_commitment: str
    local_epochs: int
    batch_size: int
    learning_rate: float
    claimed_accuracy: float
    claimed_loss: float
    sample_count: int
    round_number: int
    client_id: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'model_architecture': self.model_architecture,
            'initial_weights_commitment': self.initial_weights_commitment,
            'final_weights_commitment': self.final_weights_commitment,
            'dataset_commitment': self.dataset_commitment,
            'local_epochs': self.local_epochs,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'claimed_accuracy': self.claimed_accuracy,
            'claimed_loss': self.claimed_loss,
            'sample_count': self.sample_count,
            'round_number': self.round_number,
            'client_id': self.client_id,
            'timestamp': self.timestamp
        }


@dataclass
class TrainingWitness:
    """Private witness for training computation"""
    initial_weights: Dict[str, np.ndarray]
    final_weights: Dict[str, np.ndarray]
    dataset_samples: np.ndarray
    dataset_labels: np.ndarray
    intermediate_gradients: Optional[List[Dict[str, np.ndarray]]] = None
    random_seed: Optional[int] = None
    
    def get_weight_commitment_randomness(self) -> Tuple[int, int]:
        """Get randomness for Pedersen commitments"""
        if self.random_seed is not None:
            np.random.seed(self.random_seed)
        r1 = np.random.randint(1, 2**128)
        r2 = np.random.randint(1, 2**128)
        return int(r1), int(r2)


@dataclass
class ProofObject:
    """Standardized proof object"""
    protocol_type: ProtocolType
    proof_data: Dict[str, Any]
    statement: TrainingStatement
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Allow dynamic attributes for internal protocol state
    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_internal_'):
            self.__dict__[name] = value
        else:
            object.__setattr__(self, name, value)
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith('_internal_'):
            return self.__dict__.get(name, None)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def get_size_bytes(self) -> int:
        """Get proof size in bytes"""
        import json
        return len(json.dumps(self.proof_data, default=str).encode('utf-8'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'protocol_type': self.protocol_type.value,
            'proof_data': self.proof_data,
            'statement': self.statement.to_dict(),
            'metadata': self.metadata
        }


@dataclass
class VerificationResult:
    """Result of proof verification"""
    is_valid: bool
    verification_time: float
    error_message: Optional[str] = None
    detailed_checks: Optional[Dict[str, bool]] = None
    message: Optional[str] = None  # Additional message field
    details: Optional[Dict[str, Any]] = None  # Additional details field
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'is_valid': self.is_valid,
            'verification_time': self.verification_time,
            'error_message': self.error_message,
            'message': self.message,
            'detailed_checks': self.detailed_checks or {},
            'details': self.details or {}
        }


class IZKPProtocol(ABC):
    """Interface for Zero-Knowledge Proof protocols"""
    
    @abstractmethod
    def setup(self, **kwargs) -> Dict[str, Any]:
        """
        Setup protocol parameters (trusted setup if needed)
        
        Returns:
            Dict containing setup parameters (e.g., SRS, proving/verifying keys)
        """
        pass
    
    @abstractmethod
    def generate_proof(
        self,
        statement: TrainingStatement,
        witness: TrainingWitness,
        **kwargs
    ) -> ProofObject:
        """
        Generate a zero-knowledge proof
        
        Args:
            statement: Public statement about the computation
            witness: Private witness (model weights, gradients, etc.)
            **kwargs: Protocol-specific parameters
        
        Returns:
            ProofObject containing the proof and metadata
        """
        pass
    
    @abstractmethod
    def verify_proof(
        self,
        proof: ProofObject,
        statement: Optional[TrainingStatement] = None,
        **kwargs
    ) -> VerificationResult:
        """
        Verify a zero-knowledge proof
        
        Args:
            proof: The proof to verify
            statement: Public statement (if not in proof)
            **kwargs: Protocol-specific parameters
        
        Returns:
            VerificationResult with validation status
        """
        pass
    
    @abstractmethod
    def aggregate_proofs(
        self,
        proofs: List[ProofObject],
        **kwargs
    ) -> Optional[ProofObject]:
        """
        Aggregate multiple proofs into one (if protocol supports it)
        
        Args:
            proofs: List of proofs to aggregate
            **kwargs: Protocol-specific parameters
        
        Returns:
            Aggregated proof or None if not supported
        """
        pass
    
    @abstractmethod
    def get_protocol_info(self) -> Dict[str, Any]:
        """
        Get information about the protocol
        
        Returns:
            Dict with protocol name, version, features, etc.
        """
        pass
    
    def serialize_proof(self, proof: ProofObject) -> bytes:
        """
        Serialize proof to bytes
        
        Args:
            proof: Proof to serialize
        
        Returns:
            Serialized proof bytes
        """
        import json
        return json.dumps(proof.to_dict(), default=str).encode('utf-8')
    
    def deserialize_proof(self, proof_bytes: bytes) -> ProofObject:
        """
        Deserialize proof from bytes
        
        Args:
            proof_bytes: Serialized proof
        
        Returns:
            ProofObject
        """
        import json
        data = json.loads(proof_bytes.decode('utf-8'))
        
        # Reconstruct statement
        statement = TrainingStatement(**data['statement'])
        
        # Reconstruct proof
        protocol_type = ProtocolType(data['protocol_type'])
        return ProofObject(
            protocol_type=protocol_type,
            proof_data=data['proof_data'],
            statement=statement,
            metadata=data.get('metadata', {})
        )
