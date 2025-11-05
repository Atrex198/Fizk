"""
Minimal Test: Verify Tampered Proof Detection
==============================================

Tests that the Fiat-Shamir challenge binds the proof to the witness,
preventing acceptance of tampered proofs.
"""

import sys
import numpy as np
import hashlib
import time
from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness

def create_hash(data):
    if isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(str(data).encode()).hexdigest()

print("=" * 80)
print("TESTING: Tampered Proof Detection with Fiat-Shamir Challenge")
print("=" * 80)

# Minimal dataset
np.random.seed(42)
X_data = np.random.rand(5, 11).astype(np.float32)
y_data = np.array([0, 1, 0, 1, 0])

# Create two different sets of weights
weights_A = {
    'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
    'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
    'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
    'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
    'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
    'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1
}

weights_B = {
    key: value + 0.05 * np.random.randn(*value.shape).astype(np.float32)
    for key, value in weights_A.items()
}

# Statement claims to prove training from weights_A to weights_B
statement = TrainingStatement(
    model_architecture='CardioMLP',
    initial_weights_commitment=create_hash(str(weights_A)),
    final_weights_commitment=create_hash(str(weights_B)),
    dataset_commitment=create_hash(X_data.tobytes()),
    local_epochs=1,
    batch_size=5,
    learning_rate=0.001,
    claimed_accuracy=0.6,
    claimed_loss=0.5,
    sample_count=5,
    round_number=0,
    client_id=0,
    timestamp=time.time()
)

print("\n1️⃣  Test 1: Valid Proof (weights_A → weights_B)")
print("   Creating witness with correct weights...")

valid_witness = TrainingWitness(
    initial_weights=weights_A,
    final_weights=weights_B,
    dataset_samples=X_data,
    dataset_labels=y_data
)

print("   Initializing ZKP system (reduced SRS for speed)...")
zkp = ProductionProtostar(security_level=128)  # Use minimum required
zkp.srs_size = 256  # Much smaller SRS for testing
zkp.setup(statement)

print("   Generating proof...")
valid_proof = zkp.generate_proof(statement, valid_witness)

print("   Verifying proof...")
valid_result = zkp.verify_proof(valid_proof, statement)

if valid_result.is_valid:
    print("   ✅ PASS: Valid proof accepted")
else:
    print(f"   ❌ FAIL: Valid proof rejected - {valid_result.message}")

print("\n2️⃣  Test 2: Tampered Proof (weights_B → weights_A, but claims weights_A → weights_B)")
print("   Creating witness with SWAPPED weights (tampered)...")

tampered_witness = TrainingWitness(
    initial_weights=weights_B,  # SWAPPED!
    final_weights=weights_A,    # SWAPPED!
    dataset_samples=X_data,
    dataset_labels=y_data
)

print("   Generating proof with tampered witness...")
tampered_proof = zkp.generate_proof(statement, tampered_witness)

print("   Verifying tampered proof...")
tampered_result = zkp.verify_proof(tampered_proof, statement)

if not tampered_result.is_valid:
    print(f"   ✅ PASS: Tampered proof rejected - {tampered_result.message}")
else:
    print("   ❌ FAIL: Tampered proof accepted (SECURITY VULNERABILITY!)")

print("\n" + "=" * 80)
print("TEST RESULTS")
print("=" * 80)
print(f"Valid Proof Test: {'PASS' if valid_result.is_valid else 'FAIL'}")
print(f"Tampered Proof Test: {'PASS' if not tampered_result.is_valid else 'FAIL'}")
print(f"\nOverall: {'✅ ALL TESTS PASSED' if (valid_result.is_valid and not tampered_result.is_valid) else '❌ TESTS FAILED'}")
print("=" * 80)

# Exit with appropriate code
if valid_result.is_valid and not tampered_result.is_valid:
    sys.exit(0)
else:
    sys.exit(1)
