#!/usr/bin/env python3
"""
Verification test: Prove that weights really are unchanged in the attack test
"""

import numpy as np
import hashlib
import json

print('=' * 80)
print('VERIFICATION: Are weights REALLY unchanged in the test?')
print('=' * 80)
print()

# Create initial weights
initial_weights = {
    'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
    'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
}

print('[1] Created initial weights')
print(f'    network.0.weight shape: {initial_weights["network.0.weight"].shape}')
print(f'    network.0.weight[0,0] = {initial_weights["network.0.weight"][0,0]:.6f}')
print(f'    network.0.bias[0] = {initial_weights["network.0.bias"][0]:.6f}')
print()

# Copy weights (simulating the attack)
final_weights = {k: v.copy() for k, v in initial_weights.items()}

print('[2] Created final weights using .copy()')
print(f'    network.0.weight[0,0] = {final_weights["network.0.weight"][0,0]:.6f}')
print(f'    network.0.bias[0] = {final_weights["network.0.bias"][0]:.6f}')
print()

# Check if they are equal
print('[3] Checking equality...')
for key in initial_weights:
    are_equal = np.array_equal(initial_weights[key], final_weights[key])
    max_diff = np.max(np.abs(initial_weights[key] - final_weights[key]))
    print(f'    {key}:')
    print(f'      Equal: {are_equal}')
    print(f'      Max difference: {max_diff}')
    print(f'      Same memory address: {id(initial_weights[key]) == id(final_weights[key])}')
print()

# Check if they produce the same hash
print('[4] Computing cryptographic hashes...')
initial_hash = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in initial_weights.items()}, sort_keys=True).encode()
).hexdigest()

final_hash = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in final_weights.items()}, sort_keys=True).encode()
).hexdigest()

print(f'    Initial hash: {initial_hash}')
print(f'    Final hash:   {final_hash}')
print(f'    Hashes equal: {initial_hash == final_hash}')
print()

# Now modify one value and check again
print('[5] Modifying final_weights slightly...')
final_weights['network.0.weight'][0,0] += 0.001

modified_hash = hashlib.sha256(
    json.dumps({k: v.tolist() for k, v in final_weights.items()}, sort_keys=True).encode()
).hexdigest()

print(f'    Modified value: {final_weights["network.0.weight"][0,0]:.6f}')
print(f'    Modified hash:  {modified_hash}')
print(f'    Equal to initial: {modified_hash == initial_hash}')
print()

print('=' * 80)
print('CONCLUSION:')
print('=' * 80)
if initial_hash == final_hash:
    print('✗ Test setup ERROR: .copy() does NOT preserve equality')
    print('  This would invalidate my attack test')
else:
    print('✓ Test setup is CORRECT: .copy() creates identical arrays')
    print('  Initial and final weights ARE the same')
    print('  Hash verification would catch differences')
    print('  Attack test is valid')
