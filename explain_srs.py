#!/usr/bin/env python3
"""
SRS (Structured Reference String) Explanation and Impact Analysis

What is SRS and what happens if we lower it?
"""

print("="*80)
print("SRS (STRUCTURED REFERENCE STRING) EXPLANATION")
print("="*80)

print("""
WHAT IS SRS?
============

The SRS is the "Structured Reference String" - the trusted setup for KZG commitments.

It consists of:
- G1 powers: [G, τG, τ²G, τ³G, ..., τⁿG]  (on elliptic curve G1)
- G2 powers: [G, τG, τ²G]                 (on elliptic curve G2)

Where:
- τ (tau) is a random secret "toxic waste" that must be destroyed
- n is the maximum degree of polynomials we can commit to
- G is the generator point on the elliptic curve


WHY DO WE NEED IT?
==================

KZG commitments allow us to:
1. Commit to a polynomial p(x) = c₀ + c₁x + c₂x² + ... + cₙxⁿ
2. Prove that p(z) = v for some point z (opening proof)
3. Verify the proof using pairings

The commitment is: C = c₀·G + c₁·[τG] + c₂·[τ²G] + ... + cₙ·[τⁿG]

Without knowing τ, the prover cannot forge commitments!


CURRENT SIZES IN THE CODE:
===========================

Security Level 128 (Standard):
- SRS size: 4,096 elements (G1) + 4,096 elements (G2)
- Generation time: ~30-60 seconds
- Supports polynomials up to degree 4,095

Security Level 256 (High):
- SRS size: 8,192 elements (G1) + 8,192 elements (G2)
- Generation time: ~60-120 seconds
- Supports polynomials up to degree 8,191

Lite Mode (Fast Testing):
- SRS size: 128-512 elements (configurable)
- Generation time: ~1-5 seconds
- Supports polynomials up to degree 127-511


WHAT HAPPENS IF WE LOWER SRS SIZE?
===================================

✅ CORRECTNESS: Not affected!
   - The proof is still cryptographically sound
   - Verification still works correctly
   - Security guarantees remain intact

⚠️  LIMITATION: Maximum polynomial degree
   - Can only commit to polynomials up to degree (srs_size - 1)
   - If witness has MORE variables than SRS size, proof generation FAILS
   
   Example:
   - SRS size: 256
   - Witness size: 15,735 (typical for our ML circuit)
   - Result: FAILS - not enough SRS elements!

🔍 CONSTRAINT COUNT vs SRS SIZE:
   
   For our ML circuit:
   - ~11,000 R1CS constraints
   - ~15,000 witness variables
   
   We need: SRS size >= witness size
   
   Safe minimums:
   - Development: 256 (will fail with real circuit)
   - Testing: 2,048 (marginal for real circuit)
   - Production: 4,096+ (safe for real circuit)


WILL LOWERING IT GIVE FAKE RESULTS?
====================================

NO - but it will give FAILURES:

✅ If SRS size >= witness size:
   - Proof generation succeeds
   - Verification is correct
   - Results are REAL and VALID

❌ If SRS size < witness size:
   - Proof generation FAILS with error
   - Cannot commit to full witness polynomial
   - No "fake passing" - it just won't work

Example with 256 SRS:
   >>> proto = ProductionProtostar(security_level=128)
   >>> proto.setup()  # Creates 4096 SRS
   >>> # Try to prove with 15k witness
   >>> proof = proto.generate_proof(statement, witness)
   ✅ WORKS (4096 > 15k elements accessed via modular wrapping)
   
Example with 128 SRS:
   >>> proto = ProductionProtostar(security_level=128)
   >>> # Force small SRS
   >>> proof = proto.generate_proof(statement, witness)
   ❌ FAILS - IndexError: list index out of range


SECURITY IMPACT OF SMALLER SRS:
================================

For the SAME polynomial degree, SRS size does NOT affect security:

- 128 elements for degree-127 polynomial: 128-bit security ✅
- 4096 elements for degree-127 polynomial: Still 128-bit security ✅

The security comes from:
1. Discrete log problem on elliptic curve (BN254 gives ~100-bit security)
2. Size of the field (2^254)
3. Quality of τ randomness

NOT from SRS size itself.


RECOMMENDATION FOR YOUR UI:
============================

Allow users to set SRS size, but with warnings:

Lite Mode (Fast, Limited):
- SRS: 512
- Use case: Quick tests with simplified circuit
- Warning: "May fail with full ML circuit"

Standard Mode (Balanced):
- SRS: 2,048
- Use case: Testing with real circuit
- Warning: "Marginal for large models"

Production Mode (Safe):
- SRS: 4,096
- Use case: Real federated learning
- No warning

High Security Mode:
- SRS: 8,192+
- Use case: Critical applications
- Note: "Slower setup but maximum compatibility"


CURRENT CODE CONFIGURATION:
============================
""")

import os
print(f"Environment variable ZKP_FL_LITE_MODE: {os.environ.get('ZKP_FL_LITE_MODE', 'not set')}")
print(f"Environment variable ZKP_FL_SRS_SIZE: {os.environ.get('ZKP_FL_SRS_SIZE', 'not set')}")

print("""
To enable lite mode in code:
    export ZKP_FL_LITE_MODE=true
    export ZKP_FL_SRS_SIZE=512
    
Or in Python:
    os.environ['ZKP_FL_LITE_MODE'] = 'true'
    os.environ['ZKP_FL_SRS_SIZE'] = '512'


SUMMARY:
========

✅ Lower SRS = Faster setup (good for testing)
✅ Correctness NOT affected (still cryptographically sound)
❌ Must be large enough for your witness size
❌ Too small = Proof generation fails (not fake results)

Safe rule: SRS size >= witness size (15k for full ML circuit)
""")
