#!/usr/bin/env python3
"""
Critical Security Test: Can a client submit UNCHANGED weights and pass verification?

This tests the core claim:
- Identity constraint w_new * 1 = w_new proves nothing
- Malicious client can return initial weights as final weights
- System should REJECT this but might ACCEPT it
"""

import sys
import numpy as np
from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness
import hashlib
import json

print('=' * 80)
print('CRITICAL SECURITY TEST: UNCHANGED WEIGHTS ATTACK')
print('=' * 80)
print()
print('Attack Scenario:')
print('  - Malicious client receives initial weights from server')
print('  - Client does NOT train (returns initial weights as final weights)')
print('  - Client computes real forward pass and gradients on data')
print('  - Question: Does the proof verify?')
print()
print('Expected: REJECT (training did not happen)')
print('If ACCEPT: CRITICAL SECURITY VULNERABILITY')
print('=' * 80)
print()

# Initialize prover
print('[1] Initializing Protostar protocol...')
prover = ProductionProtostar(security_level=128)
prover.setup()
print('    ✓ Setup complete')
print()

# Create initial weights (simulating server's global model)
print('[2] Creating initial weights...')
initial_weights = {
    'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
    'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
    'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
    'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
    'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
    'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1,
}
print('    ✓ Initial weights created')
print()

# ATTACK: Use initial weights as final weights (NO TRAINING)
print('[3] ATTACK: Setting final_weights = initial_weights (NO TRAINING)...')
final_weights = {k: v.copy() for k, v in initial_weights.items()}
print('    ⚠️  Final weights are IDENTICAL to initial weights')
print('    ⚠️  No training occurred!')
print()

# Verify they are actually identical
print('[4] Verifying weights are identical...')
all_identical = True
for key in initial_weights:
    if not np.array_equal(initial_weights[key], final_weights[key]):
        all_identical = False
        break

if all_identical:
    print('    ✓ Confirmed: ALL weights unchanged')
else:
    print('    ✗ Error: Weights differ (test setup error)')
    sys.exit(1)
print()

# Generate commitments
print('[5] Generating weight commitments...')
initial_hash = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in initial_weights.items()}, sort_keys=True).encode()
).hexdigest()

final_hash = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in final_weights.items()}, sort_keys=True).encode()
).hexdigest()

print(f'    Initial commitment: {initial_hash[:16]}...')
print(f'    Final commitment:   {final_hash[:16]}...')

if initial_hash == final_hash:
    print('    ⚠️  Commitments are IDENTICAL (weights unchanged)')
else:
    print('    ✗ Error: Commitments differ despite identical weights')
print()

# Create training data
print('[6] Creating training data...')
dataset_samples = np.random.randn(10, 11).astype(np.float32)
dataset_labels = np.random.randint(0, 2, size=10)
print('    ✓ Dataset created (10 samples)')
print()

# Create statement
print('[7] Creating training statement...')
statement = TrainingStatement(
    model_architecture='FederatedNN',
    initial_weights_commitment=initial_hash,
    final_weights_commitment=final_hash,
    dataset_commitment='test_dataset',
    local_epochs=5,
    batch_size=32,
    learning_rate=0.001,
    claimed_accuracy=0.5,  # Random guess (no training)
    claimed_loss=0.693,     # -ln(0.5) for binary classification
    sample_count=10,
    round_number=1,
    client_id='malicious_client',
    timestamp=1234567890.0
)
print('    ✓ Statement created')
print()

# Create witness with UNCHANGED weights
print('[8] Creating witness with unchanged weights...')
witness = TrainingWitness(
    initial_weights=initial_weights,
    final_weights=final_weights,  # SAME AS INITIAL!
    dataset_samples=dataset_samples,
    dataset_labels=dataset_labels
)
print('    ✓ Witness created')
print()

# Generate proof
print('[9] Generating ZK proof...')
print('    (This will compute real forward pass and gradients)')
print('    (But final weights are unchanged)')
try:
    proof = prover.generate_proof(statement, witness)
    print('    ✓ Proof generation succeeded')
except Exception as e:
    print(f'    ✗ Proof generation failed: {e}')
    print()
    print('RESULT: System rejected at proof generation stage')
    print('This is GOOD - attack prevented early')
    sys.exit(0)
print()

# Verify proof
print('[10] Verifying proof...')
print('     This is the CRITICAL moment...')
print()

try:
    result = prover.verify_proof(proof, statement)
    
    print('=' * 80)
    print('VERIFICATION RESULT')
    print('=' * 80)
    print()
    
    if result.is_valid:
        print('❌ CRITICAL SECURITY VULNERABILITY CONFIRMED')
        print()
        print('The system ACCEPTED a proof where:')
        print('  • Initial weights == Final weights')
        print('  • NO training occurred')
        print('  • Client can freeload in federated learning')
        print()
        print('This proves:')
        print('  1. ❌ Weight update constraint is meaningless (identity only)')
        print('  2. ❌ System cannot detect unchanged weights')
        print('  3. ❌ Malicious client can fake training and contribute nothing')
        print()
        print('ROOT CAUSE:')
        print('  Line 455 in complete_r1cs_circuit.py:')
        print('    constraints.append(self._make_constraint(')
        print('        witness, w_new_idx, const_idx, w_new_idx')
        print('    ))')
        print('  This creates: w_new * 1 = w_new (identity, always true)')
        print('  Missing: Constraint relating w_new to w_old and gradients')
        print()
        print('SEVERITY: CRITICAL')
        print('EXPLOITABILITY: TRIVIAL')
        print('IMPACT: Complete bypass of training verification')
        print()
        sys.exit(1)
    else:
        print('✅ ATTACK PREVENTED')
        print()
        print('The system correctly rejected unchanged weights.')
        print(f'Rejection reason: {result.message}')
        print()
        print('This indicates some verification mechanism caught the attack.')
        print('The identity constraint concern may be mitigated by other checks.')
        print()
        sys.exit(0)
        
except Exception as e:
    print(f'❌ Verification crashed: {e}')
    import traceback
    traceback.print_exc()
    print()
    print('System failed during verification (implementation bug)')
    sys.exit(1)
