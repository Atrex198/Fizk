#!/usr/bin/env python3
"""
Groth16 Prover Implementation
===============================

Generates 128-byte Groth16 proofs: π = (π_A, π_B, π_C)

Based on GROTH16_IMPLEMENTATION.md Section 4 and production cryptography standards.

Author: ZKP-FL Framework
Version: 1.0.0
"""

import logging
import hashlib
import secrets
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# BN128 curve operations (same as Protostar)
# CRITICAL: Use py_ecc.bn128 for ALL types to avoid incompatibility
# bn128.FQ2 and optimized_bn128.FQ2 are DIFFERENT classes!
from py_ecc.bn128 import (
    G1, G2, multiply, add, curve_order, FQ, FQ2
)

from .r1cs import R1CS
from .trusted_setup import ProvingKey, Groth16TrustedSetup

logger = logging.getLogger(__name__)


@dataclass
class Groth16Proof:
    """
    Groth16 Proof: π = (π_A, π_B, π_C)
    
    Serialized size: 256 bytes (uncompressed affine coordinates)
    - π_A: 64 bytes (G1 element, x and y)
    - π_B: 128 bytes (G2 element, FQ2 x and y)  
    - π_C: 64 bytes (G1 element, x and y)
    
    Note: Standard Groth16 uses 128 bytes with point compression.
    Our implementation uses uncompressed format for simplicity and correctness.
    """
    pi_A: Tuple[FQ, FQ]  # G1 element (affine coordinates)
    pi_B: Tuple[FQ2, FQ2]  # G2 element (affine coordinates)
    pi_C: Tuple[FQ, FQ]  # G1 element (affine coordinates)
    
    # Metadata
    public_inputs: List[int]
    proof_generation_time_ms: float = 0.0


class Groth16Prover:
    """
    Groth16 Proof Generator
    
    Generates succinct proofs using proving key and witness.
    
    Standard from GROTH16_IMPLEMENTATION.md Section 4
    """
    
    def __init__(self, proving_key: ProvingKey, r1cs: R1CS, setup: Optional[Groth16TrustedSetup] = None):
        """
        Initialize prover with proving key
        
        Args:
            proving_key: Proving key from trusted setup
            r1cs: R1CS constraint system (for witness access)
            setup: Trusted setup instance (for QAP access)
        """
        self.pk = proving_key
        self.r1cs = r1cs
        self.setup = setup
        
        logger.info(f"Groth16 Prover initialized")
        logger.info(f"  Variables: {proving_key.num_variables}")
        logger.info(f"  Constraints: {proving_key.num_constraints}")
        logger.info(f"  Public inputs: {proving_key.num_public_inputs}")
    
    def generate_proof(
        self,
        witness: List[int],
        public_inputs: List[int]
    ) -> Groth16Proof:
        """
        Generate Groth16 proof
        
        Args:
            witness: Complete witness vector [1, public, private]
            public_inputs: Public input values
        
        Returns:
            Groth16Proof object
        
        From GROTH16_IMPLEMENTATION.md Section 4.2
        """
        import time
        start_time = time.time()
        
        logger.info(f"🔐 Generating Groth16 proof...")
        
        # Validate inputs
        if not isinstance(witness, list):
            raise TypeError(f"Witness must be a list, got {type(witness)}")
        
        if not isinstance(public_inputs, list):
            raise TypeError(f"Public inputs must be a list, got {type(public_inputs)}")
        
        if len(witness) == 0:
            raise ValueError("Witness cannot be empty")
        
        if witness[0] != 1:
            raise ValueError(f"First witness element must be 1 (constant), got {witness[0]}")
        
        if len(witness) > self.pk.num_variables:
            raise ValueError(f"Witness length {len(witness)} exceeds num_variables {self.pk.num_variables}")
        
        # Validate all witness elements are integers in field
        for i, w in enumerate(witness):
            if not isinstance(w, int):
                raise TypeError(f"Witness[{i}] must be integer, got {type(w)}")
        
        # Step 1: Verify witness satisfies R1CS
        self.r1cs.witness = witness
        if not self.r1cs.verify_constraint_satisfaction():
            raise ValueError("Witness does not satisfy R1CS constraints")
        
        # Step 2: Sample random blinding factors r, s
        r = secrets.randbelow(curve_order)
        s = secrets.randbelow(curve_order)
        
        logger.debug(f"  Blinding factors: r={r % 1000000}, s={s % 1000000}")
        
        # Step 3: Compute π_A
        # π_A = α + Σᵢ wᵢ·Aᵢ(τ) + r·δ
        pi_A = self._compute_pi_A(witness, r)
        
        # Step 4: Compute π_B
        # π_B = β + Σᵢ wᵢ·Bᵢ(τ) + s·δ
        pi_B = self._compute_pi_B(witness, s)
        
        # Step 5: Compute π_C
        # π_C = Σᵢ wᵢ·[(β·Aᵢ(τ) + α·Bᵢ(τ) + Cᵢ(τ))/δ] + H(τ)/δ + s·π_A + r·π_B - rs·δ
        pi_C = self._compute_pi_C(witness, r, s, pi_A, pi_B)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        proof = Groth16Proof(
            pi_A=pi_A,
            pi_B=pi_B,
            pi_C=pi_C,
            public_inputs=public_inputs,
            proof_generation_time_ms=elapsed_ms
        )
        
        logger.info(f"✅ Proof generated in {elapsed_ms:.2f}ms")
        logger.info(f"   Proof size: 256 bytes (64 + 128 + 64, uncompressed)")
        
        return proof
    
    def _compute_pi_A(self, witness: List[int], r: int) -> Tuple[FQ, FQ]:
        """
        Compute π_A = [α]₁ + Σᵢ wᵢ[Aᵢ(τ)]₁ + [rδ]₁
        
        Libsnark specification from LIBSNARK_GROTH16_SPEC.md
        """
        # Start with [α]₁
        result = self.pk.alpha_G1
        
        # Add Σᵢ wᵢ·[Aᵢ(τ)]₁ for all witness elements
        for i in range(min(len(witness), len(self.pk.A_query))):
            w_i = witness[i] % curve_order
            if w_i != 0:
                term = multiply(self.pk.A_query[i], w_i)
                result = add(result, term)
        
        # Add [rδ]₁ blinding factor
        r_delta = multiply(self.pk.delta_G1, r)
        result = add(result, r_delta)
        
        return result
    
    def _compute_pi_B(self, witness: List[int], s: int) -> Tuple[FQ2, FQ2]:
        """
        Compute π_B = [β]₂ + Σᵢ wᵢ[Bᵢ(τ)]₂ + [sδ]₂
        
        Libsnark specification from LIBSNARK_GROTH16_SPEC.md
        """
        # Start with [β]₂
        result = self.pk.beta_G2
        
        # Add Σᵢ wᵢ·[Bᵢ(τ)]₂ for all witness elements
        for i in range(min(len(witness), len(self.pk.B_query_G2))):
            w_i = witness[i] % curve_order
            if w_i != 0:
                term = multiply(self.pk.B_query_G2[i], w_i)
                result = add(result, term)
        
        # Add [sδ]₂ blinding factor
        s_delta = multiply(self.pk.delta_G2, s)
        result = add(result, s_delta)
        
        return result
    
    def _compute_pi_C(
        self,
        witness: List[int],
        r: int,
        s: int,
        pi_A: Tuple[FQ, FQ],
        pi_B: Tuple[FQ2, FQ2]
    ) -> Tuple[FQ, FQ]:
        """
        Compute π_C = H(τ)/δ + Σᵢ₌ₗ₊₁ᵐ wᵢ·L_query[i] + s·π_A + r·B_g1 - rsδ
        
        Where:
        - H(τ) = h(τ) is the quotient polynomial evaluation
        - L_query contains [(βAᵢ + αBᵢ + Cᵢ)/δ]₁ for private witness
        - B_g1 = [β]₁ + Σᵢ wᵢ[Bᵢ(τ)]₁ + [sδ]₁
        
        Libsnark specification from LIBSNARK_GROTH16_SPEC.md
        """
        # Step 1: Compute B_g1 (B evaluation in G1, needed for r·B_g1 term)
        B_g1 = self.pk.beta_G1
        for i in range(min(len(witness), len(self.pk.B_query_G1))):
            w_i = witness[i] % curve_order
            if w_i != 0:
                term = multiply(self.pk.B_query_G1[i], w_i)
                B_g1 = add(B_g1, term)
        
        s_delta_g1 = multiply(self.pk.delta_G1, s)
        B_g1 = add(B_g1, s_delta_g1)
        
        # Step 2: Compute H(τ)/δ using quotient polynomial
        # h(x) such that A(x)·B(x) - C(x) = h(x)·t(x)
        result = multiply(G1, 0)  # Start with identity
        
        if self.setup is not None and hasattr(self.setup, 'qap'):
            # Compute quotient polynomial h(x)
            h_poly = self.setup.qap.compute_quotient_polynomial(witness)
            
            # Evaluate h(τ)/δ using H_query which contains [τⁱ/δ]₁
            for i in range(min(len(h_poly), len(self.pk.H_query))):
                if h_poly[i] != 0:
                    term = multiply(self.pk.H_query[i], h_poly[i])
                    result = add(result, term)
            
            logger.debug(f"  H(τ) term computed with {len(h_poly)} coefficients")
        
        # Step 3: Add private witness contribution: Σᵢ₌ₗ₊₁ᵐ wᵢ·L_query[i-(l+1)]
        # L_query is indexed from 0 for first private variable
        private_start_idx = max(self.r1cs.public_input_indices) + 1
        
        for idx in range(private_start_idx, min(len(witness), self.pk.num_variables)):
            w_i = witness[idx] % curve_order
            l_query_idx = idx - private_start_idx
            if w_i != 0 and l_query_idx < len(self.pk.L_query):
                term = multiply(self.pk.L_query[l_query_idx], w_i)
                result = add(result, term)
        
        # Step 4: Add s·π_A
        s_pi_A = multiply(pi_A, s)
        result = add(result, s_pi_A)
        
        # Step 5: Add r·B_g1
        r_B_g1 = multiply(B_g1, r)
        result = add(result, r_B_g1)
        
        # Step 6: Subtract rsδ
        rs = (r * s) % curve_order
        rs_delta = multiply(self.pk.delta_G1, rs)
        # Subtraction = adding negation
        rs_delta_neg = multiply(rs_delta, curve_order - 1)
        result = add(result, rs_delta_neg)
        
        return result
    
    def serialize_proof(self, proof: Groth16Proof) -> bytes:
        """
        Serialize proof to compact format
        
        Note: This uses a simplified serialization that stores affine coordinates
        directly. For standard Groth16 interoperability, proper point compression
        with sign bits should be used.
        
        Format (custom, compatible with our verifier):
        - Bytes 0-31: π_A x-coordinate
        - Bytes 32-63: π_A y-coordinate  
        - Bytes 64-95: π_B x-coefficient 0
        - Bytes 96-127: π_B x-coefficient 1
        - Bytes 128-159: π_B y-coefficient 0
        - Bytes 160-191: π_B y-coefficient 1
        - Bytes 192-223: π_C x-coordinate
        - Bytes 224-255: π_C y-coordinate
        
        Total: 256 bytes (uncompressed for simplicity and correctness)
        """
        # Serialize G1 points (64 bytes each - full affine coordinates)
        def serialize_G1(point) -> bytes:
            x = int(point[0])
            y = int(point[1])
            return x.to_bytes(32, 'big') + y.to_bytes(32, 'big')
        
        # Serialize G2 point (128 bytes - full affine coordinates)
        def serialize_G2(point) -> bytes:
            x0 = int(point[0].coeffs[0])
            x1 = int(point[0].coeffs[1])
            y0 = int(point[1].coeffs[0])
            y1 = int(point[1].coeffs[1])
            return (x0.to_bytes(32, 'big') + 
                   x1.to_bytes(32, 'big') +
                   y0.to_bytes(32, 'big') +
                   y1.to_bytes(32, 'big'))
        
        proof_bytes = (
            serialize_G1(proof.pi_A) +
            serialize_G2(proof.pi_B) +
            serialize_G1(proof.pi_C)
        )
        
        assert len(proof_bytes) == 256, f"Proof size must be 256 bytes, got {len(proof_bytes)}"
        
        return proof_bytes
    
    def proof_to_dict(self, proof: Groth16Proof) -> Dict:
        """Export proof to dictionary format"""
        return {
            'pi_A': self._serialize_G1_to_hex(proof.pi_A),
            'pi_B': self._serialize_G2_to_hex(proof.pi_B),
            'pi_C': self._serialize_G1_to_hex(proof.pi_C),
            'public_inputs': proof.public_inputs,
            'proof_generation_time_ms': proof.proof_generation_time_ms,
            'protocol': 'Groth16',
            'proof_size_bytes': 256  # Uncompressed (128 with compression)
        }
    
    def _serialize_G1_to_hex(self, point: Tuple[FQ, FQ]) -> List[str]:
        """Serialize G1 point to hex strings (affine coordinates)"""
        # py_ecc.bn128 uses affine coordinates (x, y)
        return [
            hex(int(point[0])),
            hex(int(point[1]))
        ]
    
    def _serialize_G2_to_hex(self, point: Tuple[FQ2, FQ2]) -> List[List[str]]:
        """Serialize G2 point to hex strings (affine coordinates)"""
        # py_ecc.bn128 uses affine coordinates (x, y)
        return [
            [hex(int(point[0].coeffs[0])), hex(int(point[0].coeffs[1]))],
            [hex(int(point[1].coeffs[0])), hex(int(point[1].coeffs[1]))]
        ]
