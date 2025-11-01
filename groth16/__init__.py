#!/usr/bin/env python3
"""
Groth16 ZKP Protocol Implementation
====================================

Complete Groth16 SNARK implementation for ZKP-FL framework.
Follows FL_CIRCUIT_ENCODING_STANDARD.md and ARCHITECTURE.md.

Components:
- R1CS: Rank-1 Constraint System
- Trusted Setup: Key generation (development mode)
- Prover: 128-byte proof generation
- Verifier: O(1) verification with 3 pairing checks
- FL Circuit Builder: Neural network circuit encoding
- Protocol: IZKPProtocol interface implementation

Author: ZKP-FL Framework
Version: 1.0.0
"""

from .groth16_protocol import (
    Groth16Protocol,
    ProofObject,
    ProofMetadata,
    VerificationResult,
    ProtocolType
)
from .r1cs import R1CS, R1CSBuilder, R1CSConstraint
from .trusted_setup import Groth16TrustedSetup, ProvingKey, VerificationKey, generate_groth16_setup
from .prover import Groth16Prover, Groth16Proof
from .verifier import Groth16Verifier
from .fl_circuit_builder import FLCircuitBuilder
from .utils import (
    load_config,
    save_config,
    get_default_config,
    estimate_resources,
    validate_config,
    format_proof_size,
    format_time,
    setup_logging,
    Groth16Stats
)

__version__ = "1.0.0"

__all__ = [
    # Main protocol
    'Groth16Protocol',
    'ProofObject',
    'ProofMetadata',
    'VerificationResult',
    'ProtocolType',
    
    # R1CS
    'R1CS',
    'R1CSBuilder',
    'R1CSConstraint',
    
    # Setup
    'Groth16TrustedSetup',
    'ProvingKey',
    'VerificationKey',
    'generate_groth16_setup',
    
    # Prover
    'Groth16Prover',
    'Groth16Proof',
    
    # Verifier
    'Groth16Verifier',
    
    # Circuit builder
    'FLCircuitBuilder',
    
    # Utils
    'load_config',
    'save_config',
    'get_default_config',
    'estimate_resources',
    'validate_config',
    'format_proof_size',
    'format_time',
    'setup_logging',
    'Groth16Stats'
]

from .groth16_protocol import Groth16Protocol
from .r1cs import R1CS, R1CSBuilder
from .trusted_setup import Groth16TrustedSetup
from .prover import Groth16Prover
from .verifier import Groth16Verifier
from .fl_circuit_builder import FLCircuitBuilder

__all__ = [
    'Groth16Protocol',
    'R1CS',
    'R1CSBuilder',
    'Groth16TrustedSetup',
    'Groth16Prover',
    'Groth16Verifier',
    'FLCircuitBuilder'
]

__version__ = '1.0.0'
