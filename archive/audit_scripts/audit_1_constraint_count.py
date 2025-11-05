#!/usr/bin/env python3
"""
AUDIT 1: Verify R1CS Constraint Count
======================================
Checks if system falls back to simplified circuit (19 constraints)
or uses full production circuit (8000+ constraints)
"""

import sys
sys.path.append('.')

import numpy as np
from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS

print("="*80)
print("AUDIT 1: R1CS CONSTRAINT COUNT VERIFICATION")
print("="*80)

# Test parameters
curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# Create realistic ML weights
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

X_sample = np.random.randn(11).astype(np.float32)
y_sample = 1

print("\n🔍 Generating R1CS circuit...")
circuit = MLCircuitR1CS(curve_order)

constraints, witness = circuit.generate_full_ml_circuit(
    initial_weights=initial_weights,
    final_weights=final_weights,
    X_sample=X_sample,
    y_sample=y_sample,
    learning_rate=0.01,
    claimed_loss=0.5
)

print(f"\n📊 Circuit Statistics:")
print(f"   Constraints: {len(constraints)}")
print(f"   Witness size: {len(witness)}")

# Thresholds
SIMPLIFIED_THRESHOLD = 100  # Simplified circuits have < 100 constraints
PRODUCTION_THRESHOLD = 5000  # Production should have > 5000

print(f"\n🎯 Evaluation:")

if len(constraints) < SIMPLIFIED_THRESHOLD:
    print(f"   ❌ FAIL: Using SIMPLIFIED circuit ({len(constraints)} constraints)")
    print(f"   🚨 SECURITY ISSUE: System falling back to toy circuit!")
    verdict = "FAIL"
elif len(constraints) < PRODUCTION_THRESHOLD:
    print(f"   ⚠️  WARNING: Intermediate circuit ({len(constraints)} constraints)")
    print(f"   Expected production-grade: > {PRODUCTION_THRESHOLD}")
    verdict = "WARNING"
else:
    print(f"   ✅ PASS: Production-grade circuit ({len(constraints)} constraints)")
    verdict = "PASS"

# Verify constraint satisfaction
print(f"\n🔐 Verifying constraint satisfaction...")
is_satisfied = circuit.verify_constraint_satisfaction(constraints, witness)

if is_satisfied:
    print(f"   ✅ All constraints satisfied")
else:
    print(f"   ❌ Constraints NOT satisfied - circuit broken!")
    verdict = "FAIL"

print(f"\n{'='*80}")
print(f"FINAL VERDICT: {verdict}")
print(f"{'='*80}")

sys.exit(0 if verdict == "PASS" else 1)
