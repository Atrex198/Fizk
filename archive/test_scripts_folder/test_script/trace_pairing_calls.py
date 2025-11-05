#!/usr/bin/env python3
"""
Trace if pairing() function is ever actually called during verification
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Monkey-patch to detect pairing calls
pairing_called = []

from py_ecc import bn128
original_pairing = bn128.pairing

def traced_pairing(*args, **kwargs):
    pairing_called.append(True)
    print(f"🔍 PAIRING FUNCTION CALLED with args: {len(args)} arguments")
    return original_pairing(*args, **kwargs)

bn128.pairing = traced_pairing

# Now run proof generation and verification
from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness
import numpy as np

print('=' * 70)
print('PAIRING CALL TRACE TEST')
print('Monitoring if pairing() function is ever called')
print('=' * 70)

prover = ProductionProtostar(security_level=128)
prover.setup()

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

print('\nGenerating proof...')
proof = prover.generate_proof(statement, witness)
print(f'Pairing calls during proof generation: {len(pairing_called)}')

pairing_called.clear()
print('\nVerifying proof...')
result = prover.verify_proof(statement, proof)
print(f'Pairing calls during verification: {len(pairing_called)}')

print('\n' + '=' * 70)
if len(pairing_called) == 0:
    print('❌ CRITICAL: pairing() function was NEVER called!')
    print('')
    print('Your expert friend is CORRECT:')
    print('  - No actual pairing verification happens')
    print('  - System relies only on Fiat-Shamir challenge')
    print('  - This is NOT a complete ZKP implementation')
else:
    print(f'✅ pairing() was called {len(pairing_called)} times')
    print('Pairing verification is actually performed')
