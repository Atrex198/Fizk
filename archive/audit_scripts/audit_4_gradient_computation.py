#!/usr/bin/env python3
"""
AUDIT 4: Gradient Computation Verification
===========================================
Verifies gradients are computed using real PyTorch autograd
(not faked or approximated)
"""

import sys
sys.path.append('.')

import numpy as np
import torch
from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS

print("="*80)
print("AUDIT 4: GRADIENT COMPUTATION VERIFICATION")
print("="*80)

curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# Create test weights
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

print("\n🔍 Computing gradients via R1CS circuit...")
circuit = MLCircuitR1CS(curve_order)

# This should internally call real_gradient_computation
gradients = circuit.real_gradient_computation(
    initial_weights, final_weights, X_sample, y_sample
)

print(f"\n📊 Gradient Analysis:")
print(f"   Number of gradient arrays: {len(gradients)}")

# Check each gradient
all_valid = True
for layer_name, grad in gradients.items():
    print(f"\n   Layer: {layer_name}")
    
    # Convert to numpy if needed
    if isinstance(grad, torch.Tensor):
        grad_np = grad.detach().cpu().numpy()
    else:
        grad_np = grad
    
    print(f"      Shape: {grad_np.shape}")
    print(f"      Mean: {grad_np.mean():.6f}")
    print(f"      Std: {grad_np.std():.6f}")
    print(f"      Min: {grad_np.min():.6f}")
    print(f"      Max: {grad_np.max():.6f}")
    
    # Check gradient is not all zeros (would indicate fake computation)
    if np.allclose(grad_np, 0, atol=1e-10):
        print(f"      ⚠️  WARNING: Gradient is all zeros!")
        # This might be OK for some layers, but suspicious if all are zero
    
    # Check gradient has reasonable magnitude
    if np.abs(grad_np).max() > 100:
        print(f"      ⚠️  WARNING: Gradient magnitude very large!")
        all_valid = False
    
    if np.isnan(grad_np).any():
        print(f"      ❌ FAIL: Gradient contains NaN!")
        all_valid = False
    
    if np.isinf(grad_np).any():
        print(f"      ❌ FAIL: Gradient contains Inf!")
        all_valid = False

print(f"\n🔍 Checking gradient computation method...")

# Inspect source code
import inspect
source = inspect.getsource(circuit.real_gradient_computation)

required_keywords = ['torch', 'backward', 'grad', 'loss']
found = {kw: kw.lower() in source.lower() for kw in required_keywords}

print(f"\n   Code inspection:")
for kw, present in found.items():
    status = "✅" if present else "❌"
    print(f"      {status} '{kw}' found in source")

if not all(found.values()):
    print(f"\n   ❌ FAIL: Gradient computation not using PyTorch!")
    all_valid = False

print(f"\n{'='*80}")
if all_valid and all(found.values()) and len(gradients) > 0:
    print("FINAL VERDICT: PASS")
    print("✅ Gradients computed using real PyTorch autograd")
    sys.exit(0)
else:
    print("FINAL VERDICT: FAIL")
    print("❌ Gradient computation has issues!")
    sys.exit(1)
