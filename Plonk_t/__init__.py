"""
PLONK Zero-Knowledge Proof Protocol Implementation
For Federated Learning System

This module implements a complete PLONK protocol supporting:
- Universal trusted setup with KZG commitments
- Standard PLONK gates (addition, multiplication, constants)
- Federated learning circuit encoding
- Real BN254 cryptography (no dummy implementations)
- Full proof generation and verification
"""

from .plonk_protocol import PLONKProtocol
from .trusted_setup import PLONKTrustedSetup
from .kzg_commitment import KZGCommitment
from .circuit_builder import PLONKCircuit, PLONKGate
from .polynomial_utils import PolynomialArithmetic
from .fiat_shamir import FiatShamirTranscript

__version__ = "1.0.0"
__author__ = "ZKP-FL Research Team"

__all__ = [
    'PLONKProtocol',
    'PLONKTrustedSetup', 
    'KZGCommitment',
    'PLONKCircuit',
    'PLONKGate',
    'PolynomialArithmetic',
    'FiatShamirTranscript'
]