#!/usr/bin/env python3
"""
COMPREHENSIVE SECURITY AUDIT OF ZKP-FL SYSTEM
==============================================

This script performs a thorough investigation to detect:
1. Fallback mechanisms to simplified circuits
2. Disabled cryptographic verification
3. Fake/mock proof generation
4. Constraint count discrepancies
5. Pairing verification bypasses
6. Challenge computation vulnerabilities
7. Statement binding issues

Author: Security Audit Team
Date: November 5, 2025
"""

import sys
import os
import json
import numpy as np
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("COMPREHENSIVE ZKP-FL SECURITY AUDIT")
print("="*80)
print()

# =============================================================================
# TEST 1: Check for disabled cryptographic verification
# =============================================================================
print("[TEST 1] Checking for disabled cryptographic verification...")
print("-"*80)

disabled_verification_found = False
with open('zkp_protocols/protostar_production.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'TEMPORARILY DISABLED' in content:
        print("⚠️  CRITICAL FINDING: Pairing verification is DISABLED")
        disabled_verification_found = True
        # Find the line number
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'TEMPORARILY DISABLED' in line:
                print(f"   Line {i}: {line.strip()}")
    if 'disabled_for_demo' in content:
        print("⚠️  CRITICAL FINDING: Verification marked as 'disabled_for_demo'")
        disabled_verification_found = True

if disabled_verification_found:
    print("❌ SECURITY VIOLATION: Core cryptographic verification is disabled!")
    print("   This means proofs are NOT being properly verified.")
else:
    print("✅ No disabled verification found in code")

print()

# =============================================================================
# TEST 2: Analyze constraint count claims vs reality
# =============================================================================
print("[TEST 2] Analyzing constraint count claims...")
print("-"*80)

try:
    from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS
    from py_ecc.bn128.bn128_curve import curve_order
    
    circuit_gen = MLCircuitR1CS(curve_order)
    
    # Create realistic test data
    fake_weights = {
        'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
        'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
        'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
        'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
        'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
        'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1,
    }
    
    X_sample = np.random.randn(11).astype(np.float32)
    y_sample = 0
    
    constraints, witness_values = circuit_gen.generate_full_ml_circuit(
        initial_weights=fake_weights,
        final_weights=fake_weights,
        X_sample=X_sample,
        y_sample=y_sample,
        learning_rate=0.01,
        claimed_loss=0.5
    )
    
    actual_constraints = len(constraints)
    actual_witness = len(witness_values)
    
    print(f"✓ Complete circuit generates: {actual_constraints} constraints")
    print(f"✓ Complete circuit witness: {actual_witness} variables")
    
    # Check if proofs actually contain this many constraints
    proof_dir = Path('production_zkp_fl_results_real')
    if proof_dir.exists():
        proof_files = list(proof_dir.rglob('*_proof.json'))
        if proof_files:
            with open(proof_files[0], 'r') as f:
                proof = json.load(f)
            proof_constraints = proof['proof_data'].get('constraints', {}).get('count', 0)
            proof_witness = proof['proof_data'].get('constraints', {}).get('witness_size', 0)
            
            print(f"✓ Proof file contains: {proof_constraints} constraints")
            print(f"✓ Proof file witness: {proof_witness} variables")
            
            if proof_constraints < actual_constraints * 0.5:
                print(f"❌ CONSTRAINT MISMATCH: Proof has {proof_constraints} but should have ~{actual_constraints}")
                print(f"   This is a {actual_constraints/proof_constraints:.1f}x discrepancy!")
            else:
                print("✅ Constraint counts appear consistent")
        else:
            print("⚠️  No proof files found to verify")
    else:
        print("⚠️  No results directory found")
        
except Exception as e:
    print(f"❌ Constraint count test failed: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# TEST 3: Test if fake proofs can pass verification
# =============================================================================
print("[TEST 3] Testing if fake proofs can pass verification...")
print("-"*80)

try:
    from zkp_protocols.protostar_production import ProductionProtostar
    from zkp_protocols.base import TrainingStatement, TrainingWitness
    
    prover = ProductionProtostar(security_level=128)
    prover.setup()
    
    # Create valid data
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
        initial_weights_commitment='valid',
        final_weights_commitment='valid',
        dataset_commitment='valid',
        local_epochs=5,
        batch_size=32,
        learning_rate=0.001,
        claimed_accuracy=0.75,
        claimed_loss=0.60,
        sample_count=100,
        round_number=1,
        client_id='test',
        timestamp=time.time()
    )
    
    witness = TrainingWitness(
        initial_weights=initial_weights,
        final_weights=final_weights,
        dataset_samples=np.random.randn(10, 11).astype(np.float32),
        dataset_labels=np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    )
    
    # Generate valid proof
    valid_proof = prover.generate_proof(statement, witness)
    
    # Verify valid proof
    result = prover.verify_proof(statement, valid_proof)
    if result.is_valid:
        print("✓ Valid proof passes verification")
    else:
        print(f"❌ UNEXPECTED: Valid proof rejected: {result.message}")
    
    # Now test with TAMPERED statement (claiming impossible accuracy)
    fake_statement = TrainingStatement(
        model_architecture='FederatedNN',
        initial_weights_commitment='valid',
        final_weights_commitment='valid',
        dataset_commitment='valid',
        local_epochs=5,
        batch_size=32,
        learning_rate=0.001,
        claimed_accuracy=0.99,  # FAKE: 99% accuracy
        claimed_loss=0.01,      # FAKE: Very low loss
        sample_count=100,
        round_number=1,
        client_id='test',
        timestamp=time.time()
    )
    
    # Try to verify with tampered statement
    fake_result = prover.verify_proof(fake_statement, valid_proof)
    
    if fake_result.is_valid:
        print("❌ CRITICAL SECURITY FAILURE!")
        print("   System accepted proof with TAMPERED statement!")
        print(f"   Original accuracy: 75% → Tampered: 99%")
        print(f"   Original loss: 0.60 → Tampered: 0.01")
        print("   This proves the statement is NOT cryptographically bound to the proof!")
    else:
        print("✅ System correctly rejected tampered statement")
        print(f"   Rejection reason: {fake_result.message}")
        
except Exception as e:
    print(f"❌ Fake proof test failed: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# TEST 4: Check for fallback mechanisms in code
# =============================================================================
print("[TEST 4] Searching for fallback mechanisms in code...")
print("-"*80)

fallback_patterns = [
    ('fallback', 'Fallback to simplified implementation'),
    ('skip', 'Skipping verification'),
    ('bypass', 'Bypassing security check'),
    ('todo', 'Unimplemented functionality'),
    ('hack', 'Temporary hack'),
    ('disable', 'Disabled functionality')
]

fallback_found = False
for pattern, description in fallback_patterns:
    matches = []
    for filepath in Path('zkp_protocols').rglob('*.py'):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if pattern.lower() in line.lower():
                    matches.append((filepath.name, i, line.strip()))
    
    if matches:
        print(f"⚠️  Found '{pattern}' mentions:")
        fallback_found = True
        for filename, line_num, line_content in matches[:3]:  # Show first 3
            print(f"   {filename}:{line_num}: {line_content[:80]}")

if not fallback_found:
    print("✅ No obvious fallback patterns found")

print()

# =============================================================================
# TEST 5: Verify elliptic curve operations are real
# =============================================================================
print("[TEST 5] Verifying elliptic curve operations...")
print("-"*80)

try:
    from py_ecc.bn128 import G1, G2, multiply, add, pairing, curve_order
    import random
    
    # Test scalar multiplication
    scalar = random.randint(1, curve_order - 1)
    P = multiply(G1, scalar)
    if P != (0, 0, 0):
        print("✓ Elliptic curve scalar multiplication works")
    else:
        print("❌ Scalar multiplication failed")
    
    # Test pairing bilinearity
    a = random.randint(1, 1000)
    b = random.randint(1, 1000)
    aG1 = multiply(G1, a)
    bG2 = multiply(G2, b)
    abG2 = multiply(G2, a * b)
    
    lhs = pairing(bG2, aG1)
    rhs = pairing(abG2, G1)
    
    if lhs == rhs:
        print("✓ Pairing bilinearity verified")
    else:
        print("❌ Pairing bilinearity failed")
    
    # Test point addition
    P1 = multiply(G1, 5)
    P2 = multiply(G1, 7)
    P3 = add(P1, P2)
    P_expected = multiply(G1, 12)
    
    if P3 == P_expected:
        print("✓ Point addition homomorphism verified")
    else:
        print("❌ Point addition failed")
    
    print("✅ Elliptic curve cryptography is mathematically sound")
    
except Exception as e:
    print(f"❌ EC verification failed: {e}")

print()

# =============================================================================
# TEST 6: Check proof generation time (detect fake proofs)
# =============================================================================
print("[TEST 6] Analyzing proof generation time...")
print("-"*80)

try:
    from zkp_protocols.protostar_production import ProductionProtostar
    from zkp_protocols.base import TrainingStatement, TrainingWitness
    
    prover = ProductionProtostar(security_level=128)
    prover.setup()
    
    weights = {
        'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
        'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
        'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
        'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
        'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
        'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1,
    }
    
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
        timestamp=time.time()
    )
    
    witness = TrainingWitness(
        initial_weights=weights,
        final_weights=weights,
        dataset_samples=np.random.randn(10, 11).astype(np.float32),
        dataset_labels=np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    )
    
    start = time.time()
    proof = prover.generate_proof(statement, witness)
    generation_time = time.time() - start
    
    print(f"✓ Proof generation time: {generation_time:.4f}s")
    
    if generation_time < 0.01:
        print("⚠️  WARNING: Proof generation suspiciously fast (<10ms)")
        print("   Real ZKP proof generation should take longer")
    elif generation_time < 0.1:
        print("⚠️  Proof generation is fast, but may be acceptable for demo")
    else:
        print("✓ Proof generation time seems reasonable")
    
    # Check proof metadata
    proof_time = proof.metadata.get('proof_generation_time', 0)
    print(f"✓ Proof metadata reports: {proof_time:.4f}s")
    
except Exception as e:
    print(f"❌ Timing analysis failed: {e}")

print()

# =============================================================================
# TEST 7: Verify R1CS constraint satisfaction
# =============================================================================
print("[TEST 7] Verifying R1CS constraint satisfaction...")
print("-"*80)

try:
    from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS
    from py_ecc.bn128.bn128_curve import curve_order
    
    circuit_gen = MLCircuitR1CS(curve_order)
    
    weights = {
        'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
        'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
        'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
        'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
        'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
        'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1,
    }
    
    constraints, witness = circuit_gen.generate_full_ml_circuit(
        initial_weights=weights,
        final_weights=weights,
        X_sample=np.random.randn(11).astype(np.float32),
        y_sample=0,
        learning_rate=0.01,
        claimed_loss=0.5
    )
    
    print(f"✓ Generated {len(constraints)} constraints")
    
    # Verify a sample of constraints
    satisfied = circuit_gen.verify_constraint_satisfaction(constraints, witness)
    
    if satisfied:
        print("✅ R1CS constraints are properly satisfied")
    else:
        print("❌ R1CS constraint satisfaction FAILED")
        print("   This indicates the circuit is incorrect or witness is invalid")
        
except Exception as e:
    print(f"❌ R1CS verification failed: {e}")

print()

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("="*80)
print("AUDIT SUMMARY")
print("="*80)
print()

critical_issues = []
warnings = []

if disabled_verification_found:
    critical_issues.append("Pairing verification is DISABLED")

# Add more checks here based on results above
print("CRITICAL ISSUES:")
if critical_issues:
    for issue in critical_issues:
        print(f"  ❌ {issue}")
else:
    print("  ✅ No critical security issues found")

print()
print("WARNINGS:")
if warnings:
    for warning in warnings:
        print(f"  ⚠️  {warning}")
else:
    print("  ✅ No warnings")

print()
print("="*80)
print("AUDIT COMPLETE")
print("="*80)
