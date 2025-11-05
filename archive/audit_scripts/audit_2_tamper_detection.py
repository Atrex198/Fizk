#!/usr/bin/env python3
"""
AUDIT 2: Tamper Detection Test
===============================
Verifies that the system REJECTS tampered proofs
(If it accepts tampered proofs, verification is fake!)
"""

import sys
sys.path.append('.')

import numpy as np
import hashlib
import time
from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness, ProofObject, ProtocolType

print("="*80)
print("AUDIT 2: TAMPER DETECTION TEST")
print("="*80)

# Initialize ZKP
print("\n🔧 Initializing ZKP protocol...")
zkp = ProductionProtostar(security_level=128)
zkp.setup()

# Create test data
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

print("\n📝 Generating valid proof...")
valid_proof = zkp.generate_proof(statement, witness)

print("\n✅ Test 1: Valid proof should PASS")
result1 = zkp.verify_proof(valid_proof, statement)
if result1.is_valid:
    print("   ✅ PASS: Valid proof accepted")
else:
    print("   ❌ FAIL: Valid proof rejected!")
    print(f"   Reason: {result1.message}")

print("\n🔨 Test 2: Tampered witness commitment should FAIL")
# Tamper with witness commitment
tampered_data = valid_proof.proof_data.copy()
if 'witness_commitment' in tampered_data and 'point_coords' in tampered_data['witness_commitment']:
    original_coord = tampered_data['witness_commitment']['point_coords'][0]
    tampered_data['witness_commitment']['point_coords'][0] = str(int(original_coord) + 12345)
    
    tampered_proof = ProofObject(
        protocol_type=ProtocolType.PROTOSTAR,
        proof_data=tampered_data,
        statement=statement,
        metadata={}
    )
    
    result2 = zkp.verify_proof(tampered_proof, statement)
    if not result2.is_valid:
        print("   ✅ PASS: Tampered proof rejected")
        print(f"   Reason: {result2.message}")
    else:
        print("   ❌ FAIL: Tampered proof ACCEPTED!")
        print("   🚨 CRITICAL: System accepts invalid proofs!")
else:
    print("   ⚠️  SKIP: Cannot tamper (commitment structure different)")

print("\n🎭 Test 3: Wrong statement should FAIL")
wrong_statement = TrainingStatement(
    model_architecture="FederatedNN",
    initial_weights_commitment="wrong_commitment",
    final_weights_commitment="wrong_commitment",
    dataset_commitment="wrong_commitment",
    local_epochs=5,
    batch_size=32,
    learning_rate=0.01,
    claimed_accuracy=0.99,
    claimed_loss=0.01,
    sample_count=50,
    round_number=0,
    client_id=0,
    timestamp=time.time()
)

result3 = zkp.verify_proof(valid_proof, wrong_statement)
if not result3.is_valid:
    print("   ✅ PASS: Wrong statement rejected")
    print(f"   Reason: {result3.message}")
else:
    print("   ❌ FAIL: Proof verified with WRONG statement!")
    print("   🚨 CRITICAL: Fiat-Shamir binding broken!")

print(f"\n{'='*80}")
if result1.is_valid and not result2.is_valid and not result3.is_valid:
    print("FINAL VERDICT: PASS")
    print("✅ System correctly detects tampered proofs")
    sys.exit(0)
else:
    print("FINAL VERDICT: FAIL")
    print("❌ System has verification vulnerabilities!")
    sys.exit(1)
