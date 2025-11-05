#!/usr/bin/env python3
"""
Demonstration: Why Pairing Verification Matters
================================================

This script demonstrates the difference between:
1. Verification WITH pairing checks (secure)
2. Verification WITHOUT pairing checks (current state)

It shows what attacks are possible when pairing is disabled.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import time
from zkp_protocols.protostar_production import ProductionProtostar, ECPointCommitment
from zkp_protocols.base import TrainingStatement, TrainingWitness, ProofObject, ProtocolType
from py_ecc.bn128 import G1, G2, multiply, add, pairing, curve_order
import hashlib
import json

print("="*80)
print("DEMONSTRATION: Why Pairing Verification Matters")
print("="*80)
print()

# Setup
prover = ProductionProtostar(security_level=128)
prover.setup()

# Create valid training data
initial_weights = {
    'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
    'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
    'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
    'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
    'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
    'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1,
}

final_weights = {k: v - 0.001 * np.random.randn(*v.shape).astype(np.float32) 
                 for k, v in initial_weights.items()}

statement = TrainingStatement(
    model_architecture='FederatedNN',
    initial_weights_commitment='honest',
    final_weights_commitment='honest',
    dataset_commitment='honest',
    local_epochs=5,
    batch_size=32,
    learning_rate=0.001,
    claimed_accuracy=0.75,
    claimed_loss=0.60,
    sample_count=100,
    round_number=1,
    client_id='honest_client',
    timestamp=time.time()
)

witness = TrainingWitness(
    initial_weights=initial_weights,
    final_weights=final_weights,
    dataset_samples=np.random.randn(10, 11).astype(np.float32),
    dataset_labels=np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
)

print("[STEP 1] Generate an HONEST proof")
print("-"*80)
honest_proof = prover.generate_proof(statement, witness)
print("✓ Honest proof generated")
print()

print("[STEP 2] Verify honest proof (current system)")
print("-"*80)
result = prover.verify_proof(statement, honest_proof)
print(f"Result: {result.is_valid}")
print(f"Message: {result.message}")
print()

print("[STEP 3] Create a MALICIOUS proof with wrong commitments")
print("-"*80)
print("Attack scenario: Attacker creates proof with fake commitments")
print("   but keeps the same Fiat-Shamir challenge structure")
print()

# Create a malicious proof with DIFFERENT commitments
# but structured to pass the current verification
malicious_proof_data = honest_proof.proof_data.copy()

# Replace commitments with FAKE ones (random EC points)
fake_witness_point = multiply(G1, np.random.randint(1, 1000))
fake_constraint_point = multiply(G1, np.random.randint(1, 1000))

fake_witness_comm = ECPointCommitment(fake_witness_point, 'FAKE_witness')
fake_constraint_comm = ECPointCommitment(fake_constraint_point, 'FAKE_constraint')

print("⚠️  Creating fake commitments:")
print(f"   Fake witness commitment: {fake_witness_comm.point[:2]}")
print(f"   Fake constraint commitment: {fake_constraint_comm.point[:2]}")
print()

# Build malicious proof that tries to bypass verification
malicious_proof_data['witness_commitment'] = fake_witness_comm.to_dict()
malicious_proof_data['constraint_commitment'] = fake_constraint_comm.to_dict()

# Keep the same challenge (this is the ATTACK - trying to reuse valid challenge)
# A proper pairing check would catch this!

malicious_proof = ProofObject(
    protocol_type=ProtocolType.PROTOSTAR,
    proof_data=malicious_proof_data,
    statement=statement,
    metadata={'attack_type': 'fake_commitments'}
)

print("[STEP 4] Try to verify MALICIOUS proof (current system)")
print("-"*80)
malicious_result = prover.verify_proof(statement, malicious_proof)
print(f"Result: {malicious_result.is_valid}")
print(f"Message: {malicious_result.message}")
print()

if malicious_result.is_valid:
    print("❌ CRITICAL: Malicious proof ACCEPTED!")
    print("   The fake commitments passed verification.")
    print("   This is because pairing checks are disabled.")
else:
    print("✅ Good: Malicious proof REJECTED")
    print("   The system caught the attack.")

print()
print("[STEP 5] What PROPER pairing verification would do")
print("-"*80)
print("A proper pairing verification would check:")
print()
print("   e(W, G2) = e(G1, constraint_commitment)")
print()
print("Where:")
print("   W = witness commitment")
print("   constraint_commitment = commitment to constraints")
print()
print("This equation MUST hold for a valid proof.")
print("If commitments are fake, the equation fails.")
print()

print("Let's manually check the pairing for honest proof:")
try:
    # Get honest commitments
    honest_w_comm = ECPointCommitment.from_dict(honest_proof.proof_data['witness_commitment'])
    honest_c_comm = ECPointCommitment.from_dict(honest_proof.proof_data['constraint_commitment'])
    
    # Compute pairings
    lhs = pairing(G2, honest_w_comm.point)
    rhs = pairing(G2, honest_c_comm.point)
    
    # Note: This is simplified - real verification is more complex
    print("✓ Pairing computation completed (simplified example)")
    print("   In reality, the pairing equation is more sophisticated")
    print()
except Exception as e:
    print(f"⚠️  Pairing computation: {e}")
    print()

print("="*80)
print("SUMMARY: Why Pairing Matters")
print("="*80)
print()
print("WITHOUT pairing verification:")
print("  ✓ Fiat-Shamir prevents SOME attacks (statement tampering)")
print("  ✗ Attackers can potentially forge commitments")
print("  ✗ Weakened security guarantees")
print()
print("WITH pairing verification:")
print("  ✓ Full zkSNARK security")
print("  ✓ Commitments are cryptographically verified")
print("  ✓ No way to forge proofs without witness")
print()
print("RECOMMENDATION: Enable pairing verification for production!")
print()
