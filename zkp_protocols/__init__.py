"""
ZKP Protocol Implementations
Real cryptographic implementations for Federated Learning

Core modules:
- base.py: Protocol interfaces and data classes
- r1cs.py: R1CS constraint system
- kzg.py: KZG polynomial commitments with pairing verification
- complete_r1cs_circuit.py: ML training R1CS circuit
- protostar_production.py: Production Protostar+ProtoGalaxy implementation
- commitment_utils.py: Commitment helper functions
- nonce_store.py: Replay attack protection
"""

# Base interfaces
from .base import (
    IZKPProtocol, 
    ProtocolType, 
    ProofObject, 
    VerificationResult, 
    TrainingStatement, 
    TrainingWitness
)

# Production implementation
from .protostar_production import ProductionProtostar

# R1CS utilities
from .r1cs import (
    SparseMatrix,
    R1CSInstance,
    R1CSWitness,
    R1CSBuilder,
    check_r1cs_satisfaction,
    compute_hadamard_product,
    compute_linear_combination
)

# KZG polynomial commitments
from .kzg import (
    KZGParams,
    KZGCommitment,
    KZGOpening,
    KZGScheme,
    create_kzg_scheme
)

__all__ = [
    # Base interfaces
    'IZKPProtocol',
    'ProtocolType',
    'ProofObject',
    'VerificationResult',
    'TrainingStatement',
    'TrainingWitness',
    
    # Production
    'ProductionProtostar',
    
    # R1CS
    'SparseMatrix',
    'R1CSInstance',
    'R1CSWitness',
    'R1CSBuilder',
    'check_r1cs_satisfaction',
    'compute_hadamard_product',
    'compute_linear_combination',
    
    # KZG
    'KZGParams',
    'KZGCommitment',
    'KZGOpening',
    'KZGScheme',
    'create_kzg_scheme',
]

