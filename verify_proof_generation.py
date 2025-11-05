#!/usr/bin/env python3
"""
Deep verification: Does proof generation modify the weights?
"""

import sys
import numpy as np
from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness
import hashlib
import json

print('=' * 80)
print('DEEP VERIFICATION: Does proof generation modify weights?')
print('=' * 80)
print()

# Initialize prover
prover = ProductionProtostar(security_level=128)
prover.setup()
print('[1] Prover initialized')
print()

# Create weights
initial_weights = {
    'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
    'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
    'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
    'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
    'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
    'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1,
}

# Create identical final weights
final_weights = {k: v.copy() for k, v in initial_weights.items()}

print('[2] Computing BEFORE proof generation...')
initial_hash_before = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in initial_weights.items()}, sort_keys=True).encode()
).hexdigest()
final_hash_before = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in final_weights.items()}, sort_keys=True).encode()
).hexdigest()

print(f'    Initial hash: {initial_hash_before[:32]}...')
print(f'    Final hash:   {final_hash_before[:32]}...')
print(f'    Equal: {initial_hash_before == final_hash_before}')

# Save exact values
saved_initial_00 = initial_weights['network.0.weight'][0,0].copy()
saved_final_00 = final_weights['network.0.weight'][0,0].copy()
print(f'    initial[0,0] = {saved_initial_00:.10f}')
print(f'    final[0,0]   = {saved_final_00:.10f}')
print()

# Create statement and witness
statement = TrainingStatement(
    model_architecture='FederatedNN',
    initial_weights_commitment=initial_hash_before,
    final_weights_commitment=final_hash_before,
    dataset_commitment='test',
    local_epochs=5,
    batch_size=32,
    learning_rate=0.001,
    claimed_accuracy=0.5,
    claimed_loss=0.693,
    sample_count=10,
    round_number=1,
    client_id='test',
    timestamp=1234567890.0
)

witness = TrainingWitness(
    initial_weights=initial_weights,
    final_weights=final_weights,
    dataset_samples=np.random.randn(10, 11).astype(np.float32),
    dataset_labels=np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
)

print('[3] Generating proof...')
proof = prover.generate_proof(statement, witness)
print('    Proof generated')
print()

print('[4] Computing AFTER proof generation...')
initial_hash_after = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in initial_weights.items()}, sort_keys=True).encode()
).hexdigest()
final_hash_after = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in final_weights.items()}, sort_keys=True).encode()
).hexdigest()

print(f'    Initial hash: {initial_hash_after[:32]}...')
print(f'    Final hash:   {final_hash_after[:32]}...')
print(f'    Equal: {initial_hash_after == final_hash_after}')

current_initial_00 = initial_weights['network.0.weight'][0,0]
current_final_00 = final_weights['network.0.weight'][0,0]
print(f'    initial[0,0] = {current_initial_00:.10f}')
print(f'    final[0,0]   = {current_final_00:.10f}')
print()

print('[5] Checking for modifications...')
print(f'    Initial hash changed: {initial_hash_before != initial_hash_after}')
print(f'    Final hash changed: {final_hash_before != final_hash_after}')
print(f'    Initial value changed: {saved_initial_00 != current_initial_00}')
print(f'    Final value changed: {saved_final_00 != current_final_00}')
print(f'    Initial == Final (before): {initial_hash_before == final_hash_before}')
print(f'    Initial == Final (after): {initial_hash_after == final_hash_after}')
print()

# Check what's in the proof commitments
print('[6] Checking proof commitments...')
proof_initial_commit = proof.statement.initial_weights_commitment
proof_final_commit = proof.statement.final_weights_commitment
print(f'    Proof initial commitment: {proof_initial_commit[:32]}...')
print(f'    Proof final commitment:   {proof_final_commit[:32]}...')
print(f'    Commitments equal: {proof_initial_commit == proof_final_commit}')
print()

print('=' * 80)
print('ANALYSIS:')
print('=' * 80)

if initial_hash_after == final_hash_after:
    print('✓ Weights remain IDENTICAL after proof generation')
    print('✓ No modification occurred')
    print('✓ Test is VALID - system accepts unchanged weights')
    print()
    if proof_initial_commit == proof_final_commit:
        print('✓ PROOF CONTAINS IDENTICAL COMMITMENTS')
        print('  This proves the system DOES accept unchanged weights')
    else:
        print('✗ Proof commitments differ (possible error in proof generation)')
else:
    print('✗ Weights CHANGED during proof generation')
    print('  This would invalidate the test')
    print('  Need to investigate why weights were modified')
