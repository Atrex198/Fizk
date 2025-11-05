#!/usr/bin/env python3
"""
Critical Security Test: Verify if pairing verification is actually performed
This test proves the expert's allegations are correct
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness
import numpy as np

print('=' * 70)
print('CRITICAL SECURITY TEST')
print('Testing if FAKE proofs can pass verification')
print('=' * 70)

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
    initial_weights_commitment='test',
    final_weights_commitment='test',
    dataset_commitment='test',
    local_epochs=5,
    batch_size=32,
    learning_rate=0.001,
    claimed_accuracy=0.75,
    claimed_loss=0.60,
    sample_count=100,
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

print('\n[TEST 1] Generate valid proof')
print('-' * 70)
valid_proof = prover.generate_proof(statement, witness)
print('✓ Valid proof generated')

print('\n[TEST 2] Verify valid proof')
print('-' * 70)
result = prover.verify_proof(statement, valid_proof)
print(f'Valid proof verification: {result.is_valid}')
if not result.is_valid:
    print(f'❌ UNEXPECTED: Valid proof rejected')
    sys.exit(1)

print('\n[TEST 3] Create FAKE proof with tampered data')
print('-' * 70)
# Create a fake statement claiming different accuracy
fake_statement = TrainingStatement(
    model_architecture='FederatedNN',
    initial_weights_commitment='test',
    final_weights_commitment='test',
    dataset_commitment='test',
    local_epochs=5,
    batch_size=32,
    learning_rate=0.001,
    claimed_accuracy=0.99,  # FAKE: Claim 99% accuracy!
    claimed_loss=0.01,       # FAKE: Claim very low loss!
    sample_count=100,
    round_number=1,
    client_id='test',
    timestamp=1234567890.0
)

print('Verifying proof with TAMPERED statement (claimed 99% accuracy)...')
fake_result = prover.verify_proof(fake_statement, valid_proof)

print('\n' + '=' * 70)
print('SECURITY TEST RESULTS')
print('=' * 70)

if fake_result.is_valid:
    print('❌ CRITICAL SECURITY FAILURE!')
    print('')
    print('The system accepted a FAKE proof claiming:')
    print(f'  - 99% accuracy (actual: 75%)')
    print(f'  - 0.01 loss (actual: 0.60)')
    print('')
    print('This proves:')
    print('  1. ❌ No actual pairing verification performed')
    print('  2. ❌ Statement is not cryptographically bound to proof')
    print('  3. ❌ System provides ZERO security')
    print('')
    print('👤 Your expert friend is 100% CORRECT')
    print('   The cryptographic verification is completely broken.')
    sys.exit(1)
else:
    print('✅ SECURITY CHECK PASSED')
    print('')
    print('The system correctly rejected the tampered statement.')
    print('This suggests some verification is working.')
    print(f'Rejection reason: {fake_result.message}')
    sys.exit(0)
