"""
Fiat-Shamir Heuristic Implementation for PLONK
Provides cryptographic randomness from protocol transcript

This implements REAL cryptographic hashing for challenge generation.
NOT a dummy implementation.
"""

import hashlib
import logging
from typing import List, Dict, Any, Union, Optional
import json
import struct

logger = logging.getLogger(__name__)


class FiatShamirTranscript:
    """
    Fiat-Shamir Transcript for Non-Interactive Proofs
    
    Provides a way to generate verifiable randomness from the proof transcript
    using cryptographic hash functions. This eliminates the need for a trusted
    verifier to provide random challenges.
    """
    
    def __init__(self, protocol_name: str = "PLONK", domain_separator: bytes = b"ZKP_FL"):
        self.protocol_name = protocol_name
        self.domain_separator = domain_separator
        self.transcript_state = hashlib.sha256()
        self.challenge_counter = 0
        
        # Initialize with domain separator
        self._add_bytes(domain_separator)
        self._add_string(protocol_name)
        
        logger.info(f"🔒 Fiat-Shamir transcript initialized for {protocol_name}")
    
    def add_commitment(self, label: str, commitment: tuple) -> None:
        """
        Add a commitment (elliptic curve point) to the transcript
        
        Args:
            label: Description of the commitment
            commitment: G1 point (x, y) coordinates
        """
        self._add_string(f"commitment:{label}")
        
        if commitment is None:
            # Point at infinity
            self._add_bytes(b"infinity")
        else:
            # Serialize point coordinates
            x, y = commitment[0], commitment[1]
            self._add_field_element(x)
            self._add_field_element(y)
        
        logger.debug(f"📝 Added commitment '{label}' to transcript")
    
    def add_field_element(self, label: str, element: int) -> None:
        """Add a field element to the transcript"""
        self._add_string(f"field_element:{label}")
        self._add_field_element(element)
        logger.debug(f"📝 Added field element '{label}' to transcript")
    
    def add_field_elements(self, label: str, elements: List[int]) -> None:
        """Add multiple field elements to the transcript"""
        self._add_string(f"field_elements:{label}:{len(elements)}")
        for i, element in enumerate(elements):
            self._add_field_element(element)
        logger.debug(f"📝 Added {len(elements)} field elements '{label}' to transcript")
    
    def add_polynomial_commitment(self, label: str, commitment: tuple, degree: int) -> None:
        """Add a polynomial commitment with its degree"""
        self._add_string(f"poly_commitment:{label}:degree_{degree}")
        self.add_commitment(label, commitment)
    
    def add_public_inputs(self, public_inputs: List[Union[int, str]]) -> None:
        """Add public inputs to the transcript"""
        self._add_string(f"public_inputs:{len(public_inputs)}")
        for i, input_val in enumerate(public_inputs):
            if isinstance(input_val, int):
                self._add_field_element(input_val)
            else:
                self._add_string(str(input_val))
        logger.debug(f"📝 Added {len(public_inputs)} public inputs to transcript")
    
    def add_round_data(self, round_number: int, client_id: str, data: Dict[str, Any]) -> None:
        """Add round-specific data to transcript"""
        self._add_string(f"round:{round_number}:client:{client_id}")
        
        # Add data in deterministic order
        for key in sorted(data.keys()):
            self._add_string(f"{key}:{str(data[key])}")
        
        logger.debug(f"📝 Added round {round_number} data for client {client_id}")
    
    def get_challenge(self, label: str, field_modulus: int) -> int:
        """
        Generate a cryptographic challenge from the current transcript state
        
        Args:
            label: Description of the challenge
            field_modulus: Field modulus to reduce challenge to
            
        Returns:
            Challenge value in [0, field_modulus)
        """
        # Add challenge label and counter to ensure uniqueness
        challenge_transcript = self.transcript_state.copy()
        challenge_transcript.update(f"challenge:{label}:{self.challenge_counter}".encode())
        
        # Generate challenge from hash
        hash_output = challenge_transcript.digest()
        challenge = int.from_bytes(hash_output, byteorder='big') % field_modulus
        
        self.challenge_counter += 1
        
        # Add challenge back to transcript for next challenge generation
        self._add_string(f"challenge_generated:{label}")
        self._add_field_element(challenge)
        
        logger.debug(f"🎲 Generated challenge '{label}': {challenge}")
        return challenge
    
    def get_multiple_challenges(
        self,
        base_label: str,
        count: int,
        field_modulus: int
    ) -> List[int]:
        """Generate multiple independent challenges"""
        challenges = []
        for i in range(count):
            challenge = self.get_challenge(f"{base_label}_{i}", field_modulus)
            challenges.append(challenge)
        return challenges
    
    def get_random_linear_combination_coefficients(
        self,
        count: int,
        field_modulus: int,
        label: str = "random_lc"
    ) -> List[int]:
        """Generate random coefficients for linear combinations"""
        return self.get_multiple_challenges(label, count, field_modulus)
    
    def add_opening_proof(
        self,
        label: str,
        evaluation_point: int,
        claimed_value: int,
        proof: tuple
    ) -> None:
        """Add an opening proof to the transcript"""
        self._add_string(f"opening_proof:{label}")
        self._add_field_element(evaluation_point)
        self._add_field_element(claimed_value)
        self.add_commitment(f"{label}_proof", proof)
    
    def finalize_round(self, round_label: str) -> bytes:
        """
        Finalize a round and return the current transcript hash
        
        This can be used for proof verification or as input to the next round
        """
        self._add_string(f"round_finalized:{round_label}")
        current_hash = self.transcript_state.digest()
        
        logger.debug(f"🔒 Finalized round '{round_label}'")
        return current_hash
    
    def get_transcript_hash(self) -> bytes:
        """Get current transcript hash without modifying state"""
        return self.transcript_state.digest()
    
    def export_transcript(self) -> Dict[str, Any]:
        """Export transcript state for debugging/verification"""
        return {
            'protocol_name': self.protocol_name,
            'domain_separator': self.domain_separator.hex(),
            'challenge_counter': self.challenge_counter,
            'current_hash': self.transcript_state.hexdigest(),
            'timestamp': __import__('time').time()
        }
    
    def _add_string(self, s: str) -> None:
        """Add a string to the transcript"""
        # Add length prefix to prevent collision attacks
        data = s.encode('utf-8')
        self.transcript_state.update(struct.pack('<Q', len(data)))
        self.transcript_state.update(data)
    
    def _add_bytes(self, data: bytes) -> None:
        """Add raw bytes to the transcript"""
        self.transcript_state.update(struct.pack('<Q', len(data)))
        self.transcript_state.update(data)
    
    def _add_field_element(self, element):
        """Add a field element as 32 bytes (big endian)"""
        # Convert FQ object to integer if needed
        if hasattr(element, 'n'):  # FQ object
            element_int = element.n
        else:
            element_int = int(element)
        
        # Ensure element is in field range [0, curve_order)
        # Import curve_order from the right place
        try:
            from py_ecc.bn128 import curve_order
        except ImportError:
            # Fallback to a reasonable field size
            curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
        
        # Reduce modulo curve_order to handle negative values
        element_int = element_int % curve_order
        
        # Convert to 32-byte big-endian representation
        element_bytes = element_int.to_bytes(32, byteorder='big')
        self.transcript_state.update(element_bytes)
    
    def verify_transcript_consistency(self, expected_hash: bytes) -> bool:
        """Verify transcript produces expected hash"""
        current_hash = self.get_transcript_hash()
        return current_hash == expected_hash


class PLONKFiatShamir(FiatShamirTranscript):
    """
    PLONK-specific Fiat-Shamir implementation
    
    Provides convenience methods for PLONK protocol phases
    """
    
    def __init__(self):
        super().__init__("PLONK_ZKP_FL", b"PLONK_FL_2024")
        self.phase = "setup"
    
    def setup_phase(self, proving_key_hash: bytes, verification_key_hash: bytes) -> None:
        """Add setup phase data"""
        self.phase = "setup"
        self._add_string("setup_phase")
        self._add_bytes(proving_key_hash)
        self._add_bytes(verification_key_hash)
    
    def preprocessing_phase(self, circuit_description: Dict[str, Any]) -> None:
        """Add circuit preprocessing data"""
        self.phase = "preprocessing"
        self._add_string("preprocessing_phase")
        
        # Add circuit metadata in deterministic order
        for key in sorted(circuit_description.keys()):
            self._add_string(f"circuit_{key}:{str(circuit_description[key])}")
    
    def round_1_prover(
        self,
        wire_commitments: Dict[str, tuple],
        public_inputs: List[int]
    ) -> int:
        """PLONK Round 1: Wire commitments"""
        self.phase = "round_1_prover"
        self._add_string("plonk_round_1_prover")
        
        # Add public inputs
        self.add_public_inputs(public_inputs)
        
        # Add wire commitments in deterministic order
        for wire_label in sorted(wire_commitments.keys()):
            self.add_commitment(f"wire_{wire_label}", wire_commitments[wire_label])
        
        # Generate permutation challenge β
        try:
            from py_ecc.bn128 import curve_order
        except ImportError:
            curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
        beta = self.get_challenge("beta", curve_order)
        return beta
    
    def round_2_prover(self, permutation_commitment: tuple) -> int:
        """PLONK Round 2: Permutation commitment"""
        self.phase = "round_2_prover"
        self._add_string("plonk_round_2_prover")
        
        self.add_commitment("permutation", permutation_commitment)
        
        # Generate permutation challenge γ
        try:
            from py_ecc.bn128 import curve_order
        except ImportError:
            curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
        gamma = self.get_challenge("gamma", curve_order)
        return gamma
    
    def round_3_prover(self, quotient_commitment: tuple) -> int:
        """PLONK Round 3: Quotient polynomial commitment"""
        self.phase = "round_3_prover"
        self._add_string("plonk_round_3_prover")
        
        self.add_commitment("quotient", quotient_commitment)
        
        # Generate evaluation challenge α
        try:
            from py_ecc.bn128 import curve_order
        except ImportError:
            curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
        alpha = self.get_challenge("alpha", curve_order)
        return alpha
    
    def round_4_prover(
        self,
        evaluations: Dict[str, int],
        opening_proofs: Dict[str, tuple]
    ) -> int:
        """PLONK Round 4: Evaluations and opening proofs"""
        self.phase = "round_4_prover"
        self._add_string("plonk_round_4_prover")
        
        # Add evaluations in deterministic order
        for eval_label in sorted(evaluations.keys()):
            self.add_field_element(f"eval_{eval_label}", evaluations[eval_label])
        
        # Add opening proofs
        for proof_label in sorted(opening_proofs.keys()):
            self.add_commitment(f"opening_{proof_label}", opening_proofs[proof_label])
        
        # Generate final verification challenge ζ
        try:
            from py_ecc.bn128 import curve_order
        except ImportError:
            curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
        zeta = self.get_challenge("zeta", curve_order)
        return zeta
    
    def federated_learning_context(
        self,
        round_number: int,
        client_id: str,
        model_hash: bytes,
        training_config: Dict[str, Any]
    ) -> None:
        """Add federated learning specific context"""
        self._add_string("federated_learning_context")
        self._add_string(f"round_{round_number}")
        self._add_string(f"client_{client_id}")
        self._add_bytes(model_hash)
        
        # Add training configuration
        for key in sorted(training_config.keys()):
            self._add_string(f"config_{key}:{str(training_config[key])}")


def test_fiat_shamir():
    """Test Fiat-Shamir functionality"""
    print("🔒 Testing Fiat-Shamir Transcript")
    print("=" * 40)
    
    # Create transcript
    transcript = PLONKFiatShamir()
    
    # Simulate PLONK protocol
    public_inputs = [123, 456, 789]
    transcript.add_public_inputs(public_inputs)
    
    # Add some commitments (using dummy points)
    wire_commitments = {
        'a': (12345, 67890),
        'b': (11111, 22222),
        'c': (33333, 44444)
    }
    
    # Round 1
    beta = transcript.round_1_prover(wire_commitments, public_inputs)
    print(f"β challenge: {beta}")
    
    # Round 2  
    gamma = transcript.round_2_prover((55555, 66666))
    print(f"γ challenge: {gamma}")
    
    # Round 3
    alpha = transcript.round_3_prover((77777, 88888))
    print(f"α challenge: {alpha}")
    
    # Verify determinism - same inputs should give same challenges
    transcript2 = PLONKFiatShamir()
    transcript2.add_public_inputs(public_inputs)
    beta2 = transcript2.round_1_prover(wire_commitments, public_inputs)
    
    deterministic = (beta == beta2)
    print(f"✅ Deterministic challenges: {deterministic}")
    
    # Export transcript
    export_data = transcript.export_transcript()
    print(f"📊 Transcript hash: {export_data['current_hash'][:16]}...")
    
    return deterministic


if __name__ == "__main__":
    # Run tests
    test_success = test_fiat_shamir()
    print(f"\n🎯 Fiat-Shamir Test: {'PASSED' if test_success else 'FAILED'}")