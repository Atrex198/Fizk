"""
COMPREHENSIVE SECURITY AUDIT - ZKP-FL System
============================================

This tool performs a THOROUGH manual check and evaluation of the entire
ZKP Federated Learning system to detect:

1. FAKE/SIMULATED cryptographic operations
2. FALLBACK to simplified/toy circuits
3. CHEATING in verification
4. MOCKED proofs or commitments
5. INSUFFICIENT constraint systems
6. REPLAY attacks or nonce reuse
7. TAMPERED proofs
8. WEAK cryptographic primitives

GOAL: Verify the system delivers what it promises - NO SHORTCUTS!

Author: Security Audit Team
Date: 2025-11-05
"""

import sys
import os
import json
import hashlib
import time
import inspect
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import all system components for inspection
from zkp_protocols.protostar_production import ProductionProtostar, ECPointCommitment
from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS
from zkp_protocols.base import TrainingStatement, TrainingWitness
from real_ml_trainer import RealMLTrainer, TrainingConfig


@dataclass
class AuditResult:
    """Result of a security audit check"""
    check_name: str
    passed: bool
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'
    message: str
    evidence: Dict[str, Any]


class ComprehensiveSecurityAuditor:
    """
    Comprehensive security auditor for ZKP-FL system
    
    Performs deep inspection to find ANY cheating or simulation
    """
    
    def __init__(self):
        self.results: List[AuditResult] = []
        self.curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
        
    def log_result(self, check_name: str, passed: bool, severity: str, message: str, evidence: Dict = None):
        """Log an audit result"""
        result = AuditResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=message,
            evidence=evidence or {}
        )
        self.results.append(result)
        
        # Print immediately
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n[{severity}] {check_name}: {status}")
        print(f"  {message}")
        if evidence:
            for key, value in evidence.items():
                print(f"    {key}: {value}")
    
    # =====================================================================
    # AUDIT 1: Check for fake/simulated cryptographic operations
    # =====================================================================
    
    def audit_crypto_primitives(self):
        """
        CRITICAL: Verify all cryptographic primitives are REAL
        
        Checks:
        1. py_ecc library is actually used (not mocked)
        2. Pairing operations are real
        3. EC operations are on actual curves
        4. No simulation flags or fallbacks
        """
        print("\n" + "="*80)
        print("AUDIT 1: CRYPTOGRAPHIC PRIMITIVES")
        print("="*80)
        
        # Check 1.1: py_ecc import
        try:
            from py_ecc.bn128.bn128_curve import G1, G2, multiply, add, curve_order, neg
            from py_ecc.bn128.bn128_pairing import pairing
            
            self.log_result(
                "Crypto Library Import",
                True,
                "INFO",
                "py_ecc library successfully imported - REAL crypto available",
                {"library": "py_ecc", "curve": "BN254"}
            )
            
            # Check 1.2: Verify actual EC operations work
            test_point = multiply(G1, 42)
            test_add = add(G1, test_point)
            test_neg = neg(G1)
            
            # Verify these are actual EC points
            if not isinstance(test_point, tuple) or len(test_point) not in [2, 3]:
                self.log_result(
                    "EC Point Structure",
                    False,
                    "CRITICAL",
                    "EC operations return invalid point structure",
                    {"type": str(type(test_point)), "value": str(test_point)[:100]}
                )
            else:
                self.log_result(
                    "EC Point Operations",
                    True,
                    "INFO",
                    "EC operations produce valid points",
                    {"multiply": "works", "add": "works", "neg": "works"}
                )
            
            # Check 1.3: Verify pairing is REAL (not identity function)
            pairing_result = pairing(G2, G1)
            identity_pairing = pairing(G2, multiply(G1, 0))
            
            if pairing_result == identity_pairing:
                self.log_result(
                    "Pairing Non-Degeneracy",
                    False,
                    "CRITICAL",
                    "Pairing function appears degenerate - may be mocked!",
                    {"pairing_type": str(type(pairing_result))}
                )
            else:
                self.log_result(
                    "Pairing Function",
                    True,
                    "INFO",
                    "Pairing function is non-degenerate (REAL)",
                    {"result_type": str(type(pairing_result).__name__)}
                )
                
        except ImportError as e:
            self.log_result(
                "Crypto Library Import",
                False,
                "CRITICAL",
                f"py_ecc library NOT available - system using simulation! Error: {e}",
                {"error": str(e)}
            )
    
    # =====================================================================
    # AUDIT 2: Check for fallback to simplified/toy circuits
    # =====================================================================
    
    def audit_r1cs_circuit_complexity(self):
        """
        CRITICAL: Verify R1CS circuits are COMPLETE, not simplified
        
        Checks:
        1. Constraint count is large (not 19-constraint toy circuit)
        2. Witness size matches full ML computation
        3. All layers are included
        4. Gradients are computed, not faked
        """
        print("\n" + "="*80)
        print("AUDIT 2: R1CS CIRCUIT COMPLEXITY")
        print("="*80)
        
        # Create test ML weights
        initial_weights = {
            'network.0.weight': np.random.randn(64, 11).astype(np.float32),
            'network.0.bias': np.random.randn(64).astype(np.float32),
            'network.4.weight': np.random.randn(32, 64).astype(np.float32),
            'network.4.bias': np.random.randn(32).astype(np.float32),
            'network.8.weight': np.random.randn(2, 32).astype(np.float32),
            'network.8.bias': np.random.randn(2).astype(np.float32)
        }
        
        final_weights = {
            k: v + 0.01 * np.random.randn(*v.shape).astype(np.float32)
            for k, v in initial_weights.items()
        }
        
        X_sample = np.random.randn(11).astype(np.float32)
        y_sample = 1
        
        # Generate circuit
        circuit_gen = MLCircuitR1CS(self.curve_order)
        
        try:
            constraints, witness = circuit_gen.generate_full_ml_circuit(
                initial_weights=initial_weights,
                final_weights=final_weights,
                X_sample=X_sample,
                y_sample=y_sample,
                learning_rate=0.01,
                claimed_loss=0.5
            )
            
            # Check 2.1: Constraint count
            MINIMUM_PRODUCTION_CONSTRAINTS = 1000  # Production should have MANY constraints
            
            if len(constraints) < MINIMUM_PRODUCTION_CONSTRAINTS:
                self.log_result(
                    "R1CS Constraint Count",
                    False,
                    "CRITICAL",
                    f"Too few constraints! Only {len(constraints)} (expected >= {MINIMUM_PRODUCTION_CONSTRAINTS})",
                    {
                        "actual_constraints": len(constraints),
                        "minimum_expected": MINIMUM_PRODUCTION_CONSTRAINTS,
                        "suspicion": "FALLBACK TO SIMPLIFIED CIRCUIT"
                    }
                )
            else:
                self.log_result(
                    "R1CS Constraint Count",
                    True,
                    "INFO",
                    f"Sufficient constraints: {len(constraints)} (production-grade)",
                    {"constraint_count": len(constraints)}
                )
            
            # Check 2.2: Witness size
            MINIMUM_WITNESS_SIZE = 1000  # Should include all intermediate values
            
            if len(witness) < MINIMUM_WITNESS_SIZE:
                self.log_result(
                    "Witness Vector Size",
                    False,
                    "HIGH",
                    f"Witness too small! Only {len(witness)} variables (expected >= {MINIMUM_WITNESS_SIZE})",
                    {
                        "actual_witness_size": len(witness),
                        "minimum_expected": MINIMUM_WITNESS_SIZE,
                        "suspicion": "INCOMPLETE ML COMPUTATION"
                    }
                )
            else:
                self.log_result(
                    "Witness Vector Size",
                    True,
                    "INFO",
                    f"Sufficient witness size: {len(witness)} variables",
                    {"witness_size": len(witness)}
                )
            
            # Check 2.3: Constraint satisfaction
            is_satisfied = circuit_gen.verify_constraint_satisfaction(constraints, witness)
            
            if not is_satisfied:
                self.log_result(
                    "R1CS Constraint Satisfaction",
                    False,
                    "CRITICAL",
                    "R1CS constraints NOT satisfied - circuit is BROKEN!",
                    {"satisfied": False}
                )
            else:
                self.log_result(
                    "R1CS Constraint Satisfaction",
                    True,
                    "INFO",
                    "All R1CS constraints satisfied",
                    {"satisfied": True, "constraint_count": len(constraints)}
                )
            
            # Check 2.4: Verify gradients are computed
            # Look for gradient computation in circuit
            circuit_source = inspect.getsource(circuit_gen.real_gradient_computation)
            
            if "torch" not in circuit_source or "backward" not in circuit_source:
                self.log_result(
                    "Gradient Computation",
                    False,
                    "CRITICAL",
                    "Gradient computation does NOT use real ML framework!",
                    {"suspicion": "FAKE GRADIENTS"}
                )
            else:
                self.log_result(
                    "Gradient Computation",
                    True,
                    "INFO",
                    "Gradients computed using real ML framework (PyTorch)",
                    {"framework": "PyTorch", "method": "autograd"}
                )
                
        except Exception as e:
            self.log_result(
                "R1CS Circuit Generation",
                False,
                "CRITICAL",
                f"Circuit generation FAILED: {e}",
                {"error": str(e)}
            )
    
    # =====================================================================
    # AUDIT 3: Check for cheating in proof verification
    # =====================================================================
    
    def audit_proof_verification(self):
        """
        CRITICAL: Verify proof verification is REAL, not always returning True
        
        Checks:
        1. Verification rejects invalid proofs
        2. Fiat-Shamir challenge is properly computed
        3. Pairing checks are actually performed
        4. No "simulation mode" flags
        """
        print("\n" + "="*80)
        print("AUDIT 3: PROOF VERIFICATION INTEGRITY")
        print("="*80)
        
        # Initialize ZKP protocol
        zkp = ProductionProtostar(security_level=128)
        zkp.setup()
        
        # Create valid training data
        initial_weights = {
            'network.0.weight': np.random.randn(64, 11).astype(np.float32),
            'network.0.bias': np.random.randn(64).astype(np.float32),
            'network.4.weight': np.random.randn(32, 64).astype(np.float32),
            'network.4.bias': np.random.randn(32).astype(np.float32),
            'network.8.weight': np.random.randn(2, 32).astype(np.float32),
            'network.8.bias': np.random.randn(2).astype(np.float32)
        }
        
        final_weights = {
            k: v + 0.01 * np.random.randn(*v.shape).astype(np.float32)
            for k, v in initial_weights.items()
        }
        
        X_data = np.random.randn(50, 11).astype(np.float32)
        y_data = np.random.randint(0, 2, 50)
        
        # Create statement and witness
        statement = TrainingStatement(
            model_architecture="FederatedNN",
            initial_weights_commitment=hashlib.sha256(str(initial_weights).encode()).hexdigest(),
            final_weights_commitment=hashlib.sha256(str(final_weights).encode()).hexdigest(),
            dataset_commitment=hashlib.sha256(str(X_data.shape).encode()).hexdigest(),
            local_epochs=5,
            batch_size=32,
            learning_rate=0.01,
            claimed_accuracy=0.85,
            claimed_loss=0.25,
            sample_count=50,
            round_number=0,
            client_id=0,
            timestamp=time.time()
        )
        
        witness = TrainingWitness(
            initial_weights=initial_weights,
            final_weights=final_weights,
            dataset_samples=X_data,
            dataset_labels=y_data
        )
        
        # Generate valid proof
        valid_proof = zkp.generate_proof(statement, witness)
        
        # Check 3.1: Valid proof should verify
        verification_result = zkp.verify_proof(valid_proof, statement)
        
        if not verification_result.is_valid:
            self.log_result(
                "Valid Proof Verification",
                False,
                "CRITICAL",
                "Valid proof REJECTED - verifier is broken!",
                {"expected": "accept", "actual": "reject"}
            )
        else:
            self.log_result(
                "Valid Proof Verification",
                True,
                "INFO",
                "Valid proof correctly accepted",
                {"verification_time": f"{verification_result.verification_time:.4f}s"}
            )
        
        # Check 3.2: Tampered proof should be REJECTED
        # Tamper with proof by changing witness commitment
        tampered_proof_data = valid_proof.proof_data.copy()
        tampered_proof_data['witness_commitment']['point_coords'][0] = str(
            int(tampered_proof_data['witness_commitment']['point_coords'][0]) + 1
        )
        
        from zkp_protocols.base import ProofObject, ProtocolType
        tampered_proof = ProofObject(
            protocol_type=ProtocolType.PROTOSTAR,
            proof_data=tampered_proof_data,
            statement=statement,
            metadata={}
        )
        
        tampered_verification = zkp.verify_proof(tampered_proof, statement)
        
        if tampered_verification.is_valid:
            self.log_result(
                "Tampered Proof Detection",
                False,
                "CRITICAL",
                "TAMPERED PROOF ACCEPTED - VERIFIER IS CHEATING!",
                {
                    "expected": "reject",
                    "actual": "accept",
                    "SECURITY_BREACH": "System accepts invalid proofs!"
                }
            )
        else:
            self.log_result(
                "Tampered Proof Detection",
                True,
                "INFO",
                "Tampered proof correctly rejected",
                {"rejection_reason": tampered_verification.message}
            )
        
        # Check 3.3: Wrong statement should fail verification
        wrong_statement = TrainingStatement(
            model_architecture="FederatedNN",
            initial_weights_commitment="wrong_hash",
            final_weights_commitment="wrong_hash",
            dataset_commitment="wrong_hash",
            local_epochs=5,
            batch_size=32,
            learning_rate=0.01,
            claimed_accuracy=0.99,  # Different claim
            claimed_loss=0.01,
            sample_count=50,
            round_number=0,
            client_id=0,
            timestamp=time.time()
        )
        
        wrong_statement_verification = zkp.verify_proof(valid_proof, wrong_statement)
        
        if wrong_statement_verification.is_valid:
            self.log_result(
                "Statement Binding Check",
                False,
                "CRITICAL",
                "Proof verifies with WRONG STATEMENT - Fiat-Shamir is broken!",
                {
                    "expected": "reject",
                    "actual": "accept",
                    "SECURITY_BREACH": "Proof not bound to statement!"
                }
            )
        else:
            self.log_result(
                "Statement Binding Check",
                True,
                "INFO",
                "Proof correctly bound to statement (Fiat-Shamir working)",
                {"rejection_reason": wrong_statement_verification.message}
            )
    
    # =====================================================================
    # AUDIT 4: Check for EC point commitment validity
    # =====================================================================
    
    def audit_ec_commitments(self):
        """
        HIGH: Verify EC commitments are real points, not random data
        
        Checks:
        1. Commitments are valid EC points on the curve
        2. Commitments are non-trivial (not identity)
        3. Error commitments exist and are valid
        """
        print("\n" + "="*80)
        print("AUDIT 4: EC POINT COMMITMENT VALIDITY")
        print("="*80)
        
        zkp = ProductionProtostar(security_level=128)
        zkp.setup()
        
        # Generate a proof to inspect commitments
        initial_weights = {
            'network.0.weight': np.random.randn(64, 11).astype(np.float32),
            'network.0.bias': np.random.randn(64).astype(np.float32),
            'network.4.weight': np.random.randn(32, 64).astype(np.float32),
            'network.4.bias': np.random.randn(32).astype(np.float32),
            'network.8.weight': np.random.randn(2, 32).astype(np.float32),
            'network.8.bias': np.random.randn(2).astype(np.float32)
        }
        
        final_weights = {k: v + 0.01 * np.random.randn(*v.shape).astype(np.float32) for k, v in initial_weights.items()}
        X_data = np.random.randn(50, 11).astype(np.float32)
        y_data = np.random.randint(0, 2, 50)
        
        statement = TrainingStatement(
            model_architecture="FederatedNN",
            initial_weights_commitment=hashlib.sha256(str(initial_weights).encode()).hexdigest(),
            final_weights_commitment=hashlib.sha256(str(final_weights).encode()).hexdigest(),
            dataset_commitment=hashlib.sha256(str(X_data.shape).encode()).hexdigest(),
            local_epochs=5,
            batch_size=32,
            learning_rate=0.01,
            claimed_accuracy=0.85,
            claimed_loss=0.25,
            sample_count=50,
            round_number=0,
            client_id=0,
            timestamp=time.time()
        )
        
        witness = TrainingWitness(
            initial_weights=initial_weights,
            final_weights=final_weights,
            dataset_samples=X_data,
            dataset_labels=y_data
        )
        
        proof = zkp.generate_proof(statement, witness)
        
        # Check all commitments
        commitment_names = [
            'witness_commitment',
            'witness_error_commitment',
            'constraint_commitment',
            'constraint_error_commitment'
        ]
        
        for comm_name in commitment_names:
            comm_data = proof.proof_data.get(comm_name, {})
            
            # Check 4.1: Is it marked as EC point?
            if not comm_data.get('is_ec_point', False):
                self.log_result(
                    f"{comm_name} Structure",
                    False,
                    "CRITICAL",
                    f"{comm_name} is NOT an EC point!",
                    {"is_ec_point": False, "commitment_type": comm_data.get('type')}
                )
                continue
            
            # Check 4.2: Validate on curve
            commitment = ECPointCommitment.from_dict(comm_data)
            
            if not commitment.is_valid():
                self.log_result(
                    f"{comm_name} Validity",
                    False,
                    "HIGH",
                    f"{comm_name} FAILED curve validation!",
                    {"valid": False}
                )
            else:
                self.log_result(
                    f"{comm_name} Validity",
                    True,
                    "INFO",
                    f"{comm_name} is valid EC point",
                    {"valid": True}
                )
    
    # =====================================================================
    # AUDIT 5: Check for nonce reuse / replay attacks
    # =====================================================================
    
    def audit_replay_protection(self):
        """
        HIGH: Verify replay attack protection
        
        Checks:
        1. Proofs have unique nonces
        2. Nonces are cryptographically random
        3. Timestamp validation works
        """
        print("\n" + "="*80)
        print("AUDIT 5: REPLAY ATTACK PROTECTION")
        print("="*80)
        
        zkp = ProductionProtostar(security_level=128)
        zkp.setup()
        
        # Generate two proofs
        initial_weights = {
            'network.0.weight': np.random.randn(64, 11).astype(np.float32),
            'network.0.bias': np.random.randn(64).astype(np.float32),
            'network.4.weight': np.random.randn(32, 64).astype(np.float32),
            'network.4.bias': np.random.randn(32).astype(np.float32),
            'network.8.weight': np.random.randn(2, 32).astype(np.float32),
            'network.8.bias': np.random.randn(2).astype(np.float32)
        }
        
        final_weights = {k: v + 0.01 * np.random.randn(*v.shape).astype(np.float32) for k, v in initial_weights.items()}
        X_data = np.random.randn(50, 11).astype(np.float32)
        y_data = np.random.randint(0, 2, 50)
        
        statement = TrainingStatement(
            model_architecture="FederatedNN",
            initial_weights_commitment=hashlib.sha256(str(initial_weights).encode()).hexdigest(),
            final_weights_commitment=hashlib.sha256(str(final_weights).encode()).hexdigest(),
            dataset_commitment=hashlib.sha256(str(X_data.shape).encode()).hexdigest(),
            local_epochs=5,
            batch_size=32,
            learning_rate=0.01,
            claimed_accuracy=0.85,
            claimed_loss=0.25,
            sample_count=50,
            round_number=0,
            client_id=0,
            timestamp=time.time()
        )
        
        witness = TrainingWitness(
            initial_weights=initial_weights,
            final_weights=final_weights,
            dataset_samples=X_data,
            dataset_labels=y_data
        )
        
        proof1 = zkp.generate_proof(statement, witness)
        proof2 = zkp.generate_proof(statement, witness)
        
        # Check 5.1: Nonces should be unique
        nonce1 = proof1.proof_data.get('proof_nonce')
        nonce2 = proof2.proof_data.get('proof_nonce')
        
        if nonce1 == nonce2:
            self.log_result(
                "Nonce Uniqueness",
                False,
                "CRITICAL",
                "Proofs have IDENTICAL nonces - replay attacks possible!",
                {
                    "nonce1": nonce1[:16] if nonce1 else "None",
                    "nonce2": nonce2[:16] if nonce2 else "None",
                    "SECURITY_BREACH": "Replay protection broken!"
                }
            )
        else:
            self.log_result(
                "Nonce Uniqueness",
                True,
                "INFO",
                "Proofs have unique nonces",
                {
                    "nonce1": nonce1[:16] if nonce1 else "None",
                    "nonce2": nonce2[:16] if nonce2 else "None"
                }
            )
        
        # Check 5.2: Timestamps should be present
        timestamp1 = proof1.proof_data.get('proof_timestamp')
        timestamp2 = proof2.proof_data.get('proof_timestamp')
        
        if not timestamp1 or not timestamp2:
            self.log_result(
                "Timestamp Presence",
                False,
                "HIGH",
                "Proofs missing timestamps - no expiration protection!",
                {"timestamp1": timestamp1, "timestamp2": timestamp2}
            )
        else:
            self.log_result(
                "Timestamp Presence",
                True,
                "INFO",
                "Proofs have timestamps",
                {"timestamp1": timestamp1, "timestamp2": timestamp2}
            )
    
    # =====================================================================
    # AUDIT 6: Check constraint system for actual ML verification
    # =====================================================================
    
    def audit_ml_verification_completeness(self):
        """
        CRITICAL: Verify R1CS actually verifies ML training
        
        Checks:
        1. Forward pass is verified
        2. Loss computation is verified
        3. Gradients are verified
        4. Weight updates are verified
        """
        print("\n" + "="*80)
        print("AUDIT 6: ML VERIFICATION COMPLETENESS")
        print("="*80)
        
        # Inspect the R1CS circuit generation code
        circuit_source = inspect.getsource(MLCircuitR1CS.generate_full_ml_circuit)
        
        required_components = {
            "forward pass": ["forward", "layer", "matrix"],
            "loss computation": ["loss", "cross-entropy", "softmax"],
            "backward pass": ["gradient", "backward", "backprop"],
            "weight update": ["weight", "update", "optimizer"]
        }
        
        for component_name, keywords in required_components.items():
            found = any(keyword.lower() in circuit_source.lower() for keyword in keywords)
            
            if not found:
                self.log_result(
                    f"ML Component: {component_name}",
                    False,
                    "CRITICAL",
                    f"{component_name} NOT found in R1CS circuit!",
                    {
                        "component": component_name,
                        "keywords_searched": keywords,
                        "SUSPICION": "Incomplete ML verification"
                    }
                )
            else:
                self.log_result(
                    f"ML Component: {component_name}",
                    True,
                    "INFO",
                    f"{component_name} implementation found",
                    {"component": component_name}
                )
    
    # =====================================================================
    # AUDIT 7: Source code inspection for simulation flags
    # =====================================================================
    
    def audit_source_for_simulation_flags(self):
        """
        HIGH: Search source code for simulation/mock/fake flags
        
        Checks:
        1. No "simulation_mode" flags
        2. No "mock" or "fake" proof generation
        3. No "always return True" in verification
        """
        print("\n" + "="*80)
        print("AUDIT 7: SOURCE CODE SIMULATION FLAGS")
        print("="*80)
        
        suspicious_patterns = [
            ("simulation", "SIMULATION MODE"),
            ("mock", "MOCKED COMPONENTS"),
            ("fake", "FAKE OPERATIONS"),
            ("always True", "ALWAYS PASS"),
            ("bypass", "BYPASS CHECKS"),
            ("skip_verification", "SKIP VERIFICATION"),
            ("dummy", "DUMMY VALUES"),
            ("placeholder", "PLACEHOLDER CODE")
        ]
        
        files_to_check = [
            "zkp_protocols/protostar_production.py",
            "zkp_protocols/complete_r1cs_circuit.py",
            "zkp_protocols/pairing_verification.py"
        ]
        
        for filepath in files_to_check:
            full_path = Path(__file__).parent / filepath
            
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                source = f.read().lower()
            
            for pattern, description in suspicious_patterns:
                if pattern.lower() in source:
                    # Get context around match
                    lines = source.split('\n')
                    matching_lines = [
                        (i, line) for i, line in enumerate(lines)
                        if pattern.lower() in line.lower()
                    ]
                    
                    self.log_result(
                        f"Suspicious Pattern in {filepath}",
                        False,
                        "HIGH",
                        f"Found '{pattern}' - {description}",
                        {
                            "pattern": pattern,
                            "file": filepath,
                            "occurrences": len(matching_lines),
                            "first_match_line": matching_lines[0][0] if matching_lines else -1
                        }
                    )
    
    # =====================================================================
    # MAIN AUDIT EXECUTION
    # =====================================================================
    
    def run_full_audit(self) -> Dict[str, Any]:
        """
        Run complete security audit
        
        Returns:
            Audit report with all findings
        """
        print("\n" + "#"*80)
        print("# COMPREHENSIVE SECURITY AUDIT - ZKP-FL SYSTEM")
        print("#"*80)
        print("\nDate:", time.strftime("%Y-%m-%d %H:%M:%S"))
        print("Auditor: Comprehensive Security Auditor v1.0")
        print("\n" + "#"*80)
        
        start_time = time.time()
        
        # Run all audits
        self.audit_crypto_primitives()
        self.audit_r1cs_circuit_complexity()
        self.audit_proof_verification()
        self.audit_ec_commitments()
        self.audit_replay_protection()
        self.audit_ml_verification_completeness()
        self.audit_source_for_simulation_flags()
        
        # Generate report
        audit_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("AUDIT SUMMARY")
        print("="*80)
        
        critical_failures = [r for r in self.results if not r.passed and r.severity == "CRITICAL"]
        high_failures = [r for r in self.results if not r.passed and r.severity == "HIGH"]
        medium_failures = [r for r in self.results if not r.passed and r.severity == "MEDIUM"]
        
        total_checks = len(self.results)
        passed_checks = len([r for r in self.results if r.passed])
        
        print(f"\nTotal Checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {total_checks - passed_checks}")
        print(f"\nCRITICAL Failures: {len(critical_failures)}")
        print(f"HIGH Failures: {len(high_failures)}")
        print(f"MEDIUM Failures: {len(medium_failures)}")
        
        if critical_failures:
            print("\n⚠️  CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"  ❌ {failure.check_name}: {failure.message}")
        
        if high_failures:
            print("\n⚠️  HIGH SEVERITY ISSUES:")
            for failure in high_failures:
                print(f"  ⚠️  {failure.check_name}: {failure.message}")
        
        # Overall verdict
        print("\n" + "="*80)
        print("FINAL VERDICT")
        print("="*80)
        
        if len(critical_failures) > 0:
            print("\n🚨 SYSTEM FAILS AUDIT - CRITICAL SECURITY ISSUES DETECTED!")
            print("   The system is using FAKE/SIMULATED components or has BROKEN verification.")
            verdict = "FAIL - CRITICAL"
        elif len(high_failures) > 0:
            print("\n⚠️  SYSTEM HAS HIGH SEVERITY ISSUES")
            print("   The system may have incomplete or weak security.")
            verdict = "FAIL - HIGH"
        elif len(medium_failures) > 0:
            print("\n⚠️  SYSTEM HAS MEDIUM SEVERITY ISSUES")
            print("   The system works but has room for improvement.")
            verdict = "PASS WITH CONCERNS"
        else:
            print("\n✅ SYSTEM PASSES COMPREHENSIVE AUDIT!")
            print("   All cryptographic operations are REAL.")
            print("   No simulation, mocking, or cheating detected.")
            verdict = "PASS"
        
        print(f"\nAudit completed in {audit_time:.2f} seconds")
        print("="*80)
        
        # Generate detailed report
        report = {
            "audit_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "audit_duration_seconds": audit_time,
            "verdict": verdict,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "critical_failures": len(critical_failures),
            "high_failures": len(high_failures),
            "medium_failures": len(medium_failures),
            "all_results": [
                {
                    "check": r.check_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "evidence": r.evidence
                }
                for r in self.results
            ]
        }
        
        # Save report
        report_file = Path(__file__).parent / "SECURITY_AUDIT_REPORT.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return report


def main():
    """Run comprehensive security audit"""
    auditor = ComprehensiveSecurityAuditor()
    report = auditor.run_full_audit()
    
    # Exit with error code if audit fails
    if "FAIL" in report["verdict"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
