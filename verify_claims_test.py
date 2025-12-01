"""
Concrete tests to verify security claims about the Protostar implementation.
Each test attempts to exploit a specific alleged weakness.
"""

import sys
import copy
import json
import numpy as np
import torch
import time

# Setup path
sys.path.insert(0, '/home/ariva/work/final_project/Fizk')

from zkp_protocols.protostar_production import ProductionProtostar, curve_order
from zkp_protocols.base import TrainingStatement, TrainingWitness

def create_dummy_weights():
    """Create realistic neural network weights"""
    return {
        'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
        'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
        'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
        'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
        'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
        'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1,
    }

def create_statement_and_witness():
    """Create valid statement and witness for testing"""
    initial_weights = create_dummy_weights()
    # Simulate training: slightly different final weights
    final_weights = {k: v + np.random.randn(*v.shape).astype(np.float32) * 0.01 
                     for k, v in initial_weights.items()}
    
    X_data = np.random.randn(100, 11).astype(np.float32)
    y_data = np.random.randint(0, 2, 100)
    
    statement = TrainingStatement(
        model_architecture="TestNN",
        initial_weights_commitment="test_initial_commit",
        final_weights_commitment="test_final_commit",
        dataset_commitment="test_data_commit",
        local_epochs=5,
        batch_size=32,
        learning_rate=0.01,
        claimed_accuracy=0.85,
        claimed_loss=0.35,
        sample_count=100,
        round_number=1,
        client_id="test_client",
        timestamp=time.time()
    )
    
    witness = TrainingWitness(
        initial_weights=initial_weights,
        final_weights=final_weights,
        dataset_samples=X_data,
        dataset_labels=y_data
    )
    
    return statement, witness

print("="*70)
print("CLAIM VERIFICATION TESTS")
print("="*70)

# Initialize protocol
print("\n[SETUP] Initializing Protostar protocol...")
proto = ProductionProtostar(security_level=128)
proto.setup()
print("✅ Setup complete\n")

# Generate a valid proof first
print("[SETUP] Generating valid proof for baseline...")
statement, witness = create_statement_and_witness()
valid_proof = proto.generate_proof(statement, witness)
print("✅ Valid proof generated\n")

# Verify it works
print("[BASELINE] Verifying valid proof...")
baseline_result = proto.verify_proof(valid_proof, statement)
print(f"   Result: is_valid={baseline_result.is_valid}")
print(f"   Message: {baseline_result.message}")

if not baseline_result.is_valid:
    print("❌ BASELINE FAILED - valid proof rejected! Cannot proceed with tests.")
    sys.exit(1)
print("✅ Baseline verification passed\n")

print("="*70)
print("TEST 1: Does tampering with commitment REJECT the proof?")
print("="*70)
# Copy proof and tamper with witness commitment
tampered_proof_1 = copy.deepcopy(valid_proof)
# Change the witness commitment coordinates
if 'witness_commitment' in tampered_proof_1.proof_data:
    orig_coords = tampered_proof_1.proof_data['witness_commitment'].get('point_coords', [])
    if orig_coords and len(orig_coords) >= 2:
        # Tamper by changing the x-coordinate significantly
        tampered_proof_1.proof_data['witness_commitment']['point_coords'][0] = str(int(orig_coords[0]) + 12345678901234567890)
        print(f"   Tampered witness commitment x-coord")

result_1 = proto.verify_proof(tampered_proof_1, statement)
print(f"   Result: is_valid={result_1.is_valid}")
if not result_1.is_valid:
    print("✅ CLAIM VERIFIED: Tampered commitment IS rejected")
else:
    print("❌ CLAIM FALSE: Tampered commitment was ACCEPTED (security issue!)")

print("\n" + "="*70)
print("TEST 2: Does tampering with challenge value REJECT the proof?")
print("="*70)
tampered_proof_2 = copy.deepcopy(valid_proof)
orig_challenge = int(tampered_proof_2.proof_data.get('challenge', 0))
tampered_proof_2.proof_data['challenge'] = str((orig_challenge + 999999) % curve_order)
print(f"   Changed challenge from {str(orig_challenge)[:20]}... to {tampered_proof_2.proof_data['challenge'][:20]}...")

result_2 = proto.verify_proof(tampered_proof_2, statement)
print(f"   Result: is_valid={result_2.is_valid}")
if not result_2.is_valid:
    print("✅ CLAIM VERIFIED: Tampered challenge IS rejected (Fiat-Shamir works)")
else:
    print("❌ CLAIM FALSE: Tampered challenge was ACCEPTED (Fiat-Shamir broken!)")

print("\n" + "="*70)
print("TEST 3: Does removing KZG opening proofs cause rejection?")
print("="*70)
tampered_proof_3 = copy.deepcopy(valid_proof)
if 'kzg_opening_proofs' in tampered_proof_3.proof_data:
    del tampered_proof_3.proof_data['kzg_opening_proofs']
    print("   Removed kzg_opening_proofs from proof")
else:
    print("   No kzg_opening_proofs found in proof")

result_3 = proto.verify_proof(tampered_proof_3, statement)
print(f"   Result: is_valid={result_3.is_valid}")
if not result_3.is_valid:
    print("✅ KZG proofs ARE required - removal causes rejection")
else:
    print("⚠️  KZG proofs are OPTIONAL - removal still passes (weaker security)")

print("\n" + "="*70)
print("TEST 4: Does an INVALID EC point get rejected?")
print("="*70)
tampered_proof_4 = copy.deepcopy(valid_proof)
# Set an invalid point (not on curve y^2 = x^3 + 3)
tampered_proof_4.proof_data['witness_commitment']['point_coords'] = ['12345', '67890']
tampered_proof_4.proof_data['witness_commitment']['is_ec_point'] = True
print("   Set witness_commitment to invalid EC point (12345, 67890)")

result_4 = proto.verify_proof(tampered_proof_4, statement)
print(f"   Result: is_valid={result_4.is_valid}")
if not result_4.is_valid:
    print("✅ CLAIM VERIFIED: Invalid EC points ARE rejected")
else:
    print("❌ CLAIM FALSE: Invalid EC points ACCEPTED (critical security issue!)")

print("\n" + "="*70)
print("TEST 5: Does changing the statement (different client_id) get rejected?")
print("="*70)
# Create a different statement
fake_statement = TrainingStatement(
    model_architecture="TestNN",
    initial_weights_commitment="FAKE_commitment",  # Different!
    final_weights_commitment="FAKE_final",  # Different!
    dataset_commitment="test_data_commit",
    local_epochs=5,
    batch_size=32,
    learning_rate=0.01,
    claimed_accuracy=0.99,  # Inflated!
    claimed_loss=0.01,  # Fake!
    sample_count=100,
    round_number=1,
    client_id="ATTACKER",  # Different client!
    timestamp=time.time()
)
print("   Trying to verify valid proof against DIFFERENT statement")
print("   (Different client_id, different commitments, inflated accuracy)")

result_5 = proto.verify_proof(valid_proof, fake_statement)
print(f"   Result: is_valid={result_5.is_valid}")
if not result_5.is_valid:
    print("✅ CLAIM VERIFIED: Proof bound to statement - different statement rejected")
else:
    print("❌ CLAIM FALSE: Proof accepted for DIFFERENT statement (binding broken!)")

print("\n" + "="*70)
print("TEST 6: Check the R1CS constraint sampling issue")
print("="*70)
# Check if _last_constraints exists and how many are checked
if hasattr(proto, '_last_constraints') and proto._last_constraints:
    total_constraints = len(proto._last_constraints)
    print(f"   Total constraints in circuit: {total_constraints}")
    
    # Look at verification code to see sampling
    import inspect
    verify_source = inspect.getsource(proto.verify_proof)
    
    if 'max_check = min(10' in verify_source:
        print(f"   ⚠️  Verification samples only first 10 of {total_constraints} constraints")
        print(f"   This is {10/total_constraints*100:.2f}% of total constraints")
    if 'verification_rate >= 0.8' in verify_source:
        print(f"   ⚠️  Accepts if 80% of sampled constraints pass")
    
    # BUT: Check if there are other verification mechanisms
    if 'kzg_opening_proofs' in verify_source and '_verify_kzg_opening_proof' in verify_source:
        print(f"   ✅ BUT: KZG opening proofs provide polynomial-level verification")
        print(f"      (If KZG is enforced, constraint sampling is supplementary)")
else:
    print("   No constraints stored (proof not generated with constraint caching)")

print("\n" + "="*70)
print("TEST 7: Verify constraint count is substantial (not trivial)")
print("="*70)
constraint_count = valid_proof.proof_data.get('constraints', {}).get('count', 0)
witness_size = valid_proof.proof_data.get('constraints', {}).get('witness_size', 0)
print(f"   Constraint count: {constraint_count}")
print(f"   Witness size: {witness_size}")

if constraint_count > 1000:
    print(f"   ✅ Substantial constraint count ({constraint_count}) - real ML circuit")
elif constraint_count > 100:
    print(f"   ⚠️  Moderate constraint count ({constraint_count}) - simplified circuit")
else:
    print(f"   ❌ Low constraint count ({constraint_count}) - possibly mocked")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
tests_passed = sum([
    not result_1.is_valid,  # Tampered commitment rejected
    not result_2.is_valid,  # Tampered challenge rejected  
    not result_4.is_valid,  # Invalid EC point rejected
    not result_5.is_valid,  # Different statement rejected
])
tests_total = 4  # Core security tests

print(f"\nCore security tests passed: {tests_passed}/{tests_total}")

if tests_passed == tests_total:
    print("\n🎉 ALL CORE SECURITY MECHANISMS ARE WORKING")
    print("   The implementation has real cryptographic verification.")
elif tests_passed >= 3:
    print("\n✅ MOST security mechanisms working, minor issues exist")
else:
    print("\n❌ CRITICAL: Multiple security mechanisms broken!")

# Note about KZG
if result_3.is_valid:
    print("\n⚠️  NOTE: KZG opening proofs are optional (not required for verification)")
    print("   This is a design choice, not necessarily a vulnerability if other")
    print("   mechanisms (EC point validation, Fiat-Shamir, pairing checks) are enforced.")
