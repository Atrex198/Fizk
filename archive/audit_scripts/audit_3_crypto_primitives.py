#!/usr/bin/env python3
"""
AUDIT 3: Cryptographic Primitives Test
=======================================
Verifies that py_ecc is actually being used (not simulated)
"""

import sys

print("="*80)
print("AUDIT 3: CRYPTOGRAPHIC PRIMITIVES VERIFICATION")
print("="*80)

print("\n🔍 Test 1: py_ecc library availability")
try:
    from py_ecc.bn128.bn128_curve import G1, G2, multiply, add, curve_order, neg
    from py_ecc.bn128.bn128_pairing import pairing
    print("   ✅ PASS: py_ecc library imported successfully")
except ImportError as e:
    print(f"   ❌ FAIL: py_ecc not available: {e}")
    print("   🚨 CRITICAL: System using simulation!")
    sys.exit(1)

print("\n🔍 Test 2: EC point operations")
try:
    # Test scalar multiplication
    p1 = multiply(G1, 42)
    print(f"   ✅ Scalar multiplication works: {type(p1)}")
    
    # Test point addition
    p2 = add(G1, p1)
    print(f"   ✅ Point addition works: {type(p2)}")
    
    # Test negation
    p3 = neg(G1)
    print(f"   ✅ Negation works: {type(p3)}")
    
    # Verify points are tuples (actual EC points, not mocked)
    if not isinstance(p1, tuple) or len(p1) not in [2, 3]:
        print("   ❌ FAIL: EC points have wrong structure!")
        sys.exit(1)
    
    print("   ✅ PASS: All EC operations produce valid points")
    
except Exception as e:
    print(f"   ❌ FAIL: EC operations error: {e}")
    sys.exit(1)

print("\n🔍 Test 3: Pairing non-degeneracy")
try:
    # Compute pairing
    e1 = pairing(G2, G1)
    
    # Compute pairing with identity (should be different)
    identity = multiply(G1, 0)
    e2 = pairing(G2, identity)
    
    if e1 == e2:
        print("   ❌ FAIL: Pairing is degenerate (possibly mocked)!")
        sys.exit(1)
    
    print(f"   ✅ PASS: Pairing is non-degenerate")
    print(f"   Result type: {type(e1).__name__}")
    
except Exception as e:
    print(f"   ❌ FAIL: Pairing error: {e}")
    sys.exit(1)

print("\n🔍 Test 4: Curve order validation")
expected_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
if curve_order != expected_order:
    print(f"   ❌ FAIL: Wrong curve order!")
    print(f"   Expected: {expected_order}")
    print(f"   Got: {curve_order}")
    sys.exit(1)

print(f"   ✅ PASS: Curve order correct (BN254)")

print("\n🔍 Test 5: Pairing bilinearity")
try:
    # Test: e(aP, bQ) = e(P, Q)^(ab)
    a = 5
    b = 7
    
    aP = multiply(G1, a)
    bQ = multiply(G2, b)
    
    # e(aP, bQ)
    left = pairing(bQ, aP)
    
    # e(P, Q)^(ab) = e(P, abQ) = e(abP, Q)
    abP = multiply(G1, a * b)
    right = pairing(G2, abP)
    
    if left != right:
        print("   ❌ FAIL: Pairing not bilinear!")
        sys.exit(1)
    
    print("   ✅ PASS: Pairing bilinearity verified")
    
except Exception as e:
    print(f"   ❌ FAIL: Bilinearity test error: {e}")
    sys.exit(1)

print(f"\n{'='*80}")
print("FINAL VERDICT: PASS")
print("✅ All cryptographic primitives are REAL (py_ecc)")
print(f"{'='*80}")
sys.exit(0)
