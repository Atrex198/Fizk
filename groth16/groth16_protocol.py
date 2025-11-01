#!/usr/bin/env python3
"""
Groth16 Protocol Implementation
=================================

Implements IZKPProtocol interface for Groth16.
Provides complete integration with FL system.

Based on ARCHITECTURE.md and GROTH16_IMPLEMENTATION.md.

Author: ZKP-FL Framework
Version: 1.0.0
"""

import logging
import time
import json
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .r1cs import R1CS
from .trusted_setup import Groth16TrustedSetup, ProvingKey, VerificationKey, generate_groth16_setup
from .prover import Groth16Prover, Groth16Proof
from .verifier import Groth16Verifier
from .fl_circuit_builder import FLCircuitBuilder

logger = logging.getLogger(__name__)


# Import standard interfaces from ARCHITECTURE.md
class ProtocolType(Enum):
    """Supported ZKP protocols"""
    PROTOSTAR = "protostar_ivc"
    PLONK = "plonk_kzg"
    GROTH16 = "groth16"
    BULLETPROOFS = "bulletproofs"
    NOVA = "nova_folding"


@dataclass
class ProofMetadata:
    """Standardized metadata for all proofs"""
    protocol_name: str
    protocol_type: ProtocolType
    proof_version: str
    
    # Proof characteristics
    proof_size_bytes: int
    constraint_count: int
    security_level: int
    
    # Generation info
    generation_time: float
    round_number: int
    client_id: str
    timestamp: float
    
    # Verification components
    verification_method: str
    requires_trusted_setup: bool
    trusted_setup_size: Optional[int]
    
    # Cryptographic details
    curve_name: Optional[str]
    field_modulus: Optional[str]
    commitment_scheme: Optional[str]
    
    # Optional aggregation info
    supports_aggregation: bool
    aggregation_method: Optional[str]


@dataclass
class VerificationResult:
    """Standardized verification result"""
    is_valid: bool
    verification_time: float
    error_message: Optional[str]
    
    # Detailed verification info
    constraint_satisfaction: bool
    commitment_verification: bool
    cryptographic_soundness: bool
    
    # Performance metrics
    verification_complexity: str  # e.g., "O(1)", "O(log n)"
    gas_cost_estimate: Optional[int]  # For blockchain deployment


@dataclass
class ProofObject:
    """Standardized proof structure"""
    metadata: ProofMetadata
    proof_data: Dict[str, Any]  # Protocol-specific proof
    public_inputs: List[str]    # Public parameters
    auxiliary_data: Dict[str, Any]  # Extra protocol-specific data


class Groth16Protocol:
    """
    Groth16 ZKP Protocol Implementation
    
    Implements IZKPProtocol interface from ARCHITECTURE.md
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Groth16 protocol
        
        Args:
            config: Protocol-specific configuration
                - trusted_setup_size: int
                - security_level: int (default: 128)
                - curve_name: str (default: "BN128")
                - optimization_level: str (default: "balanced")
                - num_model_params: int (required for setup)
                - num_clients: int (required for setup)
        """
        self.config = config
        
        # Protocol info
        self.protocol_name = "Groth16 SNARK"
        self.protocol_type = ProtocolType.GROTH16
        self.protocol_version = "1.0.0"
        
        # Configuration
        self.security_level = config.get('security_level', 128)
        self.curve_name = config.get('curve_name', 'BN128')
        self.optimization_level = config.get('optimization_level', 'balanced')
        
        # FL-specific
        self.num_model_params = config.get('num_model_params')
        self.num_clients = config.get('num_clients', 1)
        self.num_rounds = config.get('num_rounds', 1)
        
        if not self.num_model_params:
            raise ValueError("num_model_params required in config")
        
        # Setup artifacts (populated by setup())
        self.proving_key: Optional[ProvingKey] = None
        self.verification_key: Optional[VerificationKey] = None
        self.r1cs: Optional[R1CS] = None
        
        # Components
        self.circuit_builder = FLCircuitBuilder()
        self.prover: Optional[Groth16Prover] = None
        self.verifier: Optional[Groth16Verifier] = None
        
        logger.info(f"✅ Groth16 Protocol initialized")
        logger.info(f"   Security level: {self.security_level} bits")
        logger.info(f"   Curve: {self.curve_name}")
        logger.info(f"   Model params: {self.num_model_params}")
    
    def setup(self) -> Dict[str, Any]:
        """
        Perform Groth16 trusted setup
        
        CRITICAL: This is development setup only.
        Production requires secure MPC ceremony.
        
        Returns:
            setup_artifacts with keys and timing
        
        From ARCHITECTURE.md Section 3.1.1
        """
        logger.info("🔧 Starting Groth16 trusted setup...")
        start_time = time.time()
        
        # Step 1: Build R1CS circuit
        logger.info("  Building R1CS circuit...")
        var_indices = self.circuit_builder.build_full_fl_round(
            num_params=self.num_model_params,
            num_clients=self.num_clients,
            round_number=1
        )
        
        self.r1cs = self.circuit_builder.finalize_circuit()
        
        logger.info(f"  ✅ R1CS built: {self.r1cs.num_constraints} constraints")
        
        # Step 2: Generate keys
        logger.info("  Generating proving/verification keys...")
        self.proving_key, self.verification_key, self.setup = generate_groth16_setup(self.r1cs)
        
        # Step 3: Initialize prover and verifier
        self.prover = Groth16Prover(self.proving_key, self.r1cs, self.setup)
        self.verifier = Groth16Verifier(self.verification_key)
        
        setup_time = time.time() - start_time
        
        logger.info(f"✅ Groth16 setup complete in {setup_time:.2f}s")
        
        return {
            'proving_key': self.proving_key,
            'verification_key': self.verification_key,
            'public_parameters': self.r1cs.export_for_setup(),
            'setup_time': setup_time,
            'constraint_count': self.r1cs.num_constraints,
            'variable_count': self.r1cs.num_variables
        }
    
    def generate_proof(
        self,
        statement: Dict[str, Any],
        witness: Dict[str, Any],
        round_number: int,
        client_id: str
    ) -> ProofObject:
        """
        Generate Groth16 proof for FL computation
        
        Args:
            statement: Public statement
                - model_architecture: str
                - initial_weights_commitment: str
                - final_weights_commitment: str
                - training_config: Dict
            witness: Private witness
                - model_weights: Dict[str, List[float]]
                - training_history: List[Dict]
            round_number: FL round
            client_id: Client ID
        
        Returns:
            ProofObject
        
        From ARCHITECTURE.md Section 3.1.1
        """
        if not self.prover or not self.r1cs:
            raise ValueError("Setup not performed. Call setup() first.")
        
        logger.info(f"🔐 Generating proof for client {client_id}, round {round_number}")
        start_time = time.time()
        
        # Step 1: Encode witness
        witness_vector = self._encode_witness(witness)
        
        # Step 2: Extract public inputs
        public_inputs = self._extract_public_inputs(statement)
        
        # Step 3: Set witness in R1CS
        for i, val in enumerate(witness_vector):
            if i < len(self.r1cs.witness):
                self.r1cs.witness[i] = val
        
        # Step 4: Generate Groth16 proof
        groth16_proof = self.prover.generate_proof(
            witness=witness_vector,
            public_inputs=public_inputs
        )
        
        generation_time = time.time() - start_time
        
        # Step 5: Create metadata
        metadata = ProofMetadata(
            protocol_name=self.protocol_name,
            protocol_type=self.protocol_type,
            proof_version=self.protocol_version,
            proof_size_bytes=128,
            constraint_count=self.r1cs.num_constraints,
            security_level=self.security_level,
            generation_time=generation_time,
            round_number=round_number,
            client_id=client_id,
            timestamp=time.time(),
            verification_method="3_pairing_checks",
            requires_trusted_setup=True,
            trusted_setup_size=self.r1cs.num_constraints,
            curve_name=self.curve_name,
            field_modulus=str(self.proving_key.num_constraints) if self.proving_key else None,
            commitment_scheme="None (Groth16 native)",
            supports_aggregation=False,
            aggregation_method=None
        )
        
        # Step 6: Create ProofObject
        proof_object = ProofObject(
            metadata=metadata,
            proof_data=self.prover.proof_to_dict(groth16_proof),
            public_inputs=[str(x) for x in public_inputs],
            auxiliary_data={
                'witness_size': len(witness_vector),
                'constraint_satisfaction': True
            }
        )
        
        logger.info(f"✅ Proof generated in {generation_time:.3f}s")
        
        return proof_object
    
    def verify_proof(
        self,
        proof: ProofObject,
        statement: Dict[str, Any]
    ) -> VerificationResult:
        """
        Verify Groth16 proof
        
        Args:
            proof: ProofObject to verify
            statement: Public statement
        
        Returns:
            VerificationResult
        
        From ARCHITECTURE.md Section 3.1.1
        """
        if not self.verifier:
            raise ValueError("Setup not performed. Call setup() first.")
        
        logger.info("🔍 Verifying Groth16 proof...")
        start_time = time.time()
        
        try:
            # Extract public inputs
            public_inputs = [int(x) for x in proof.public_inputs]
            
            # Reconstruct Groth16Proof from proof_data
            groth16_proof = self._reconstruct_proof(proof.proof_data)
            
            # Verify
            is_valid = self.verifier.verify_proof(groth16_proof, public_inputs)
            
            verification_time = time.time() - start_time
            
            result = VerificationResult(
                is_valid=is_valid,
                verification_time=verification_time,
                error_message=None if is_valid else "Proof verification failed",
                constraint_satisfaction=is_valid,
                commitment_verification=is_valid,
                cryptographic_soundness=is_valid,
                verification_complexity="O(1)",
                gas_cost_estimate=280000  # Typical Groth16 gas cost on Ethereum
            )
            
            logger.info(f"{'✅ VALID' if is_valid else '❌ INVALID'} (verified in {verification_time:.3f}s)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Verification error: {e}")
            return VerificationResult(
                is_valid=False,
                verification_time=time.time() - start_time,
                error_message=str(e),
                constraint_satisfaction=False,
                commitment_verification=False,
                cryptographic_soundness=False,
                verification_complexity="O(1)",
                gas_cost_estimate=None
            )
    
    def aggregate_proofs(
        self,
        proofs: List[ProofObject],
        aggregation_method: str = "default"
    ) -> Optional[ProofObject]:
        """
        Aggregate proofs (NOT supported by standard Groth16)
        
        Returns None as Groth16 doesn't support native aggregation.
        
        From ARCHITECTURE.md Section 3.1.1
        """
        logger.warning("⚠️  Groth16 does not support native proof aggregation")
        return None
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """
        Get Groth16 protocol information
        
        From ARCHITECTURE.md Section 3.1.1
        """
        return {
            'protocol_name': self.protocol_name,
            'protocol_type': self.protocol_type.value,
            'protocol_version': self.protocol_version,
            'supports_ivc': False,
            'supports_aggregation': False,
            'trusted_setup_required': True,
            'quantum_resistant': False,
            'typical_proof_size_kb': 0.128,  # 128 bytes
            'typical_verification_time_ms': 2.5,
            'security_level': self.security_level,
            'curve': self.curve_name,
            'constraint_count': self.r1cs.num_constraints if self.r1cs else None,
            'verification_complexity': 'O(1)',
            'pairing_checks': 3,
            'gas_cost_eth': 280000
        }
    
    def serialize_proof(self, proof: ProofObject) -> bytes:
        """
        Serialize proof to bytes
        
        From ARCHITECTURE.md Section 3.1.1
        """
        # Serialize to JSON then encode
        proof_dict = {
            'metadata': asdict(proof.metadata),
            'proof_data': proof.proof_data,
            'public_inputs': proof.public_inputs,
            'auxiliary_data': proof.auxiliary_data
        }
        
        # Convert Enum to string
        proof_dict['metadata']['protocol_type'] = proof.metadata.protocol_type.value
        
        json_str = json.dumps(proof_dict, default=str)
        return json_str.encode('utf-8')
    
    def _encode_witness(self, witness: Dict[str, Any]) -> List[int]:
        """Encode FL witness into field elements"""
        witness_vector = [1]  # Start with constant 1
        
        # Encode model weights
        if 'model_weights' in witness:
            for layer_name, weights in witness['model_weights'].items():
                for w in weights:
                    encoded = self.circuit_builder.encode_weight(w)
                    witness_vector.append(encoded)
        
        return witness_vector
    
    def _extract_public_inputs(self, statement: Dict[str, Any]) -> List[int]:
        """Extract public inputs from statement"""
        public_inputs = []
        
        # Hash commitments to field elements
        if 'initial_weights_commitment' in statement:
            commitment = statement['initial_weights_commitment']
            hash_int = int(hashlib.sha256(commitment.encode()).hexdigest(), 16)
            from py_ecc.bn128.bn128_curve import curve_order
            public_inputs.append(hash_int % curve_order)
        
        return public_inputs
    
    def _reconstruct_proof(self, proof_data: Dict[str, Any]) -> Groth16Proof:
        """Reconstruct Groth16Proof from dictionary"""
        # CRITICAL: Must use bn128 (not optimized_bn128) to match types from multiply/add
        # multiply(G2, x) returns py_ecc.fields.bn128_FQ2
        # optimized_bn128.FQ2 returns py_ecc.fields.optimized_bn128_FQ2 (incompatible!)
        from py_ecc.bn128 import FQ, FQ2
        
        # Proper point deserialization from affine coordinates
        def hex_to_G1(hex_list):
            """Reconstruct G1 point from hex affine coordinates [x, y]"""
            if len(hex_list) != 2:
                raise ValueError(f"Invalid G1 point: expected 2 coordinates, got {len(hex_list)}")
            
            x = int(hex_list[0], 16)
            y = int(hex_list[1], 16)
            
            # Return point in affine coordinates (FQ, FQ)
            return (FQ(x), FQ(y))
        
        def hex_to_G2(hex_list):
            """Reconstruct G2 point from hex affine coordinates [[x0, x1], [y0, y1]]"""
            if len(hex_list) != 2 or len(hex_list[0]) != 2 or len(hex_list[1]) != 2:
                raise ValueError(f"Invalid G2 point format")
            
            # x coordinate is FQ2(x0, x1)
            x0 = int(hex_list[0][0], 16)
            x1 = int(hex_list[0][1], 16)
            x = FQ2([x0, x1])
            
            # y coordinate is FQ2(y0, y1)
            y0 = int(hex_list[1][0], 16)
            y1 = int(hex_list[1][1], 16)
            y = FQ2([y0, y1])
            
            # Return point in affine coordinates (FQ2, FQ2)
            return (x, y)
        
        pi_A = hex_to_G1(proof_data['pi_A'])
        pi_B = hex_to_G2(proof_data['pi_B'])
        pi_C = hex_to_G1(proof_data['pi_C'])
        
        return Groth16Proof(
            pi_A=pi_A,
            pi_B=pi_B,
            pi_C=pi_C,
            public_inputs=[int(x) for x in proof_data['public_inputs']]
        )
