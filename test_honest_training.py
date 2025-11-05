#!/usr/bin/env python3
"""
Control test: Verify system DOES work when weights actually change (honest training)
"""

import sys
import numpy as np
from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness
import hashlib
import json

print('=' * 80)
print('CONTROL TEST: Honest training with CHANGED weights')
print('=' * 80)
print()

# Initialize prover
prover = ProductionProtostar(security_level=128)
prover.setup()
print('[1] Prover initialized\n')

# Create weights
initial_weights = {
    'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
    'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
    'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
    'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
    'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
    'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1,
}

# Simulate training: Update weights with gradient descent
print('[2] Simulating honest training (SGD step)...')
final_weights = {}
learning_rate = 0.001
for key in initial_weights:
    gradient = np.random.randn(*initial_weights[key].shape).astype(np.float32) * 0.1
    final_weights[key] = initial_weights[key] - learning_rate * gradient
    
# Verify weights changed
print('[3] Verifying weights changed...')
all_different = True
total_diff = 0
for key in initial_weights:
    diff = np.max(np.abs(initial_weights[key] - final_weights[key]))
    total_diff += diff
    if diff == 0:
        all_different = False
    print(f'    {key}: max_diff = {diff:.6f}')

if all_different and total_diff > 0:
    print('    ✓ All weights changed\n')
else:
    print('    ✗ Weights did not change\n')
    sys.exit(1)

# Compute hashes
initial_hash = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in initial_weights.items()}, sort_keys=True).encode()
).hexdigest()
final_hash = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in final_weights.items()}, sort_keys=True).encode()
).hexdigest()

print(f'[4] Hashes:')
print(f'    Initial: {initial_hash[:32]}...')
print(f'    Final:   {final_hash[:32]}...')
print(f'    Different: {initial_hash != final_hash}\n')

# Create statement and witness
statement = TrainingStatement(
    model_architecture='FederatedNN',
    initial_weights_commitment=initial_hash,
    final_weights_commitment=final_hash,
    dataset_commitment='test',
    local_epochs=5,
    batch_size=32,
    learning_rate=learning_rate,
    claimed_accuracy=0.7,
    claimed_loss=0.5,
    sample_count=10,
    round_number=1,
    client_id='honest_client',
    timestamp=1234567890.0
)

witness = TrainingWitness(
    initial_weights=initial_weights,
    final_weights=final_weights,
    dataset_samples=np.random.randn(10, 11).astype(np.float32),
    dataset_labels=np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
)

print('[5] Generating proof with CHANGED weights...')
try:
    proof = prover.generate_proof(statement, witness)
    print('    ✓ Proof generated\n')
except Exception as e:
    print(f'    ✗ Proof generation failed: {e}\n')
    sys.exit(1)

print('[6] Verifying proof...')
try:
    result = prover.verify_proof(proof, statement)
    
    print('\n' + '=' * 80)
    print('RESULT: Honest Training (weights CHANGED)')
    print('=' * 80)
    
    if result.is_valid:
        print('✅ Proof ACCEPTED (as expected for honest training)')
        print('   This confirms the system works for legitimate cases')
    else:
        print(f'❌ Proof REJECTED: {result.message}')
        print('   This would be unexpected - honest training should pass')
        
except Exception as e:
    print(f'❌ Verification error: {e}')
    import traceback
    traceback.print_exc()
