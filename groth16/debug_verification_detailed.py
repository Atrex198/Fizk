#!/usr/bin/env python3
"""
Detailed verification debugging with manual computation inspection.
This will help identify which specific term in the pairing equation is wrong.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)

from py_ecc.bn128 import G1, G2, multiply, add, pairing, eq, curve_order, FQ, FQ2
from groth16.r1cs import R1CS
from groth16.trusted_setup import Groth16TrustedSetup
from groth16.prover import Groth16Prover
from groth16.verifier import Groth16Verifier

def print_point(name, point, group="G1"):
    """Print elliptic curve point"""
    if group == "G1":
        x_val = point[0].n if hasattr(point[0], 'n') else point[0]
        y_val = point[1].n if hasattr(point[1], 'n') else point[1]
        print(f"{name}: ({x_val}, {y_val})")
    else:  # G2
        x0 = point[0].coeffs[0].n if hasattr(point[0], 'coeffs') else point[0]
        y0 = point[1].coeffs[0].n if hasattr(point[1], 'coeffs') else point[1]
        print(f"{name}: (({x0}, ...), ({y0}, ...))")

def test_simple_multiplication():
    """Test simple a*b=c constraint with detailed verification"""
    
    print("\n" + "="*80)
    print(" SIMPLE MULTIPLICATION TEST: a * b = c")
    print("="*80 + "\n")
    
    # Build circuit: a * b = c
    r1cs = R1CS(num_variables=4)
    
    # Add constraint: a * b = c
    # Variables: 0=ONE, 1=a, 2=b, 3=c
    r1cs.add_multiplication_constraint(1, 2, 3)
    
    # Set witness: a=2, b=3, c=6
    r1cs.set_witness(0, 1)  # ONE
    r1cs.set_witness(1, 2)  # a
    r1cs.set_witness(2, 3)  # b
    r1cs.set_witness(3, 6)  # c
    
    print(f"Circuit:")
    print(f"  Variables: {r1cs.num_variables}")
    print(f"  Constraints: {r1cs.num_constraints}")
    print(f"  Public inputs: {len(r1cs.public_input_indices)}")
    print(f"  Witness: {r1cs.get_witness_vector()[:10]}")
    
    # Verify constraint
    assert r1cs.verify_constraint_satisfaction(), "Constraint not satisfied!"
    print(f"  ✅ Constraint satisfied: 2 * 3 = 6")
    
    print("\n" + "-"*80)
    print(" TRUSTED SETUP")
    print("-"*80 + "\n")
    
    setup = Groth16TrustedSetup(r1cs)
    pk, vk = setup.generate_keys()
    
    print(f"Setup complete")
    
    print(f"\nProving key sizes:")
    print(f"  A_query: {len(pk.A_query)}")
    print(f"  B_query_G1: {len(pk.B_query_G1)}")
    print(f"  B_query_G2: {len(pk.B_query_G2)}")
    print(f"  L_query: {len(pk.L_query)}")
    print(f"  H_query: {len(pk.H_query)}")
    
    print(f"\nVerification key sizes:")
    print(f"  IC_query: {len(vk.IC_query)}")
    
    print("\n" + "-"*80)
    print(" PROOF GENERATION")
    print("-"*80 + "\n")
    
    prover = Groth16Prover(pk, r1cs, setup)
    witness = r1cs.get_witness_vector()
    public_inputs = r1cs.get_public_inputs()
    
    print(f"Inputs:")
    print(f"  Witness: {witness[:10]}")
    print(f"  Public: {public_inputs}")
    
    proof = prover.generate_proof(witness, public_inputs)
    
    print(f"\nProof generated:")
    print_point("  π_A", proof.pi_A)
    print_point("  π_B", proof.pi_B, "G2")
    print_point("  π_C", proof.pi_C)
    
    print("\n" + "-"*80)
    print(" MANUAL VERIFICATION")
    print("-"*80 + "\n")
    
    # Compute IC term manually
    print("Computing IC term:")
    IC = vk.IC_query[0]
    print_point("  IC[0] (base)", IC)
    
    for i, x_i in enumerate(public_inputs):
        if i + 1 < len(vk.IC_query):
            term = multiply(vk.IC_query[i + 1], x_i)
            IC = add(IC, term)
            print(f"  + {x_i} * IC[{i+1}]")
    
    print_point("  IC (final)", IC)
    
    # Compute pairings individually
    print("\nComputing pairings:")
    print("  LEFT = e(π_B, π_A)")
    left = pairing(proof.pi_B, proof.pi_A)
    print(f"    Result: {str(left)[:80]}...")
    
    print("\n  RIGHT term 1 = e(β, α)")
    term1 = pairing(vk.beta_G2, vk.alpha_G1)
    print(f"    Result: {str(term1)[:80]}...")
    
    print("\n  RIGHT term 2 = e(γ, IC)")
    term2 = pairing(vk.gamma_G2, IC)
    print(f"    Result: {str(term2)[:80]}...")
    
    print("\n  RIGHT term 3 = e(δ, π_C)")
    term3 = pairing(vk.delta_G2, proof.pi_C)
    print(f"    Result: {str(term3)[:80]}...")
    
    print("\n  RIGHT = term1 * term2 * term3")
    right = term1 * term2 * term3
    print(f"    Result: {str(right)[:80]}...")
    
    print("\n" + "="*80)
    print(f" LEFT == RIGHT: {left == right}")
    print("="*80)
    
    if left == right:
        print("\n✅ VERIFICATION PASSED!")
        return True
    else:
        print("\n❌ VERIFICATION FAILED!")
        
        # Try to understand why
        print("\nDEBUGGING:")
        
        # Check if individual terms are correct
        print("\n1. Checking if e(π_A, G2) = e(G1, π_B) (knowledge of exponent)")
        check1_left = pairing(G2, proof.pi_A)
        check1_right = pairing(proof.pi_B, G1)
        print(f"   Match: {check1_left == check1_right}")
        
        # Check if π_A and π_B are on the correct curves
        print("\n2. Checking if proof points are valid:")
        try:
            # Try operations to verify they're valid points
            test_A = multiply(proof.pi_A, 2)
            test_B = multiply(proof.pi_B, 2)
            test_C = multiply(proof.pi_C, 2)
            print(f"   π_A valid: ✅")
            print(f"   π_B valid: ✅")
            print(f"   π_C valid: ✅")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Check QAP
        print("\n3. Checking QAP:")
        if hasattr(setup, 'qap'):
            qap = setup.qap
            h_poly = qap.compute_quotient_polynomial(witness)
            print(f"   h(x) degree: {len(h_poly) - 1}")
            print(f"   h(x) coefficients (first 5): {h_poly[:min(5, len(h_poly))]}")
            
            # Check if h(x) is zero
            h_is_zero = all(coeff == 0 for coeff in h_poly)
            print(f"   h(x) is zero: {h_is_zero}")
            
            if h_is_zero:
                print("\n   ⚠️  WARNING: Quotient polynomial is ZERO!")
                print("   This means (A*B - C) is divisible by t(x)")
                print("   For a single constraint, this might be expected")
        else:
            print("   QAP not accessible from setup")
        
        # Check specific computation: Does π_C include all required terms?
        print("\n4. Checking π_C computation:")
        print(f"   Private variables start at index: {max(r1cs.public_input_indices) + 1}")
        print(f"   Number of private variables: {len(witness) - max(r1cs.public_input_indices) - 1}")
        print(f"   L_query length: {len(pk.L_query)}")
        
        # Try recomputing π_C manually
        print("\n5. Manual π_C recomputation:")
        
        # Get blinding factors from prover
        r = prover.r
        s = prover.s
        print(f"   Blinding r: {r}")
        print(f"   Blinding s: {s}")
        
        # B_g1
        B_g1 = pk.beta_G1
        for i, w_i in enumerate(witness):
            B_g1 = add(B_g1, multiply(pk.B_query_G1[i], w_i))
        B_g1 = add(B_g1, multiply(pk.delta_G1, s))
        print_point("   B_g1", B_g1)
        
        # H(τ)/δ term
        H_term = (1, 2)  # identity
        if hasattr(setup, 'qap'):
            h_poly = setup.qap.compute_quotient_polynomial(witness)
            if len(h_poly) > 0:
                for i, h_i in enumerate(h_poly):
                    if i < len(pk.H_query) and h_i % curve_order != 0:
                        H_term = add(H_term, multiply(pk.H_query[i], h_i))
        print_point("   H(τ)/δ term", H_term)
        
        # Private witness term
        private_start = max(r1cs.public_input_indices) + 1
        L_term = (1, 2)  # identity
        for i in range(private_start, len(witness)):
            l_idx = i - private_start
            if l_idx < len(pk.L_query):
                L_term = add(L_term, multiply(pk.L_query[l_idx], witness[i]))
        print_point("   Private witness term", L_term)
        
        # Blinding terms
        term_s_pi_A = multiply(proof.pi_A, s)
        term_r_B_g1 = multiply(B_g1, r)
        # For -rsδ we can't compute it without delta, so skip
        
        print_point("   s·π_A", term_s_pi_A)
        print_point("   r·B_g1", term_r_B_g1)
        
        # Combine all terms (without -rsδ since we can't compute it)
        pi_C_manual = H_term
        pi_C_manual = add(pi_C_manual, L_term)
        pi_C_manual = add(pi_C_manual, term_s_pi_A)
        pi_C_manual = add(pi_C_manual, term_r_B_g1)
        
        print_point("   π_C (manual - missing -rsδ)", pi_C_manual)
        print_point("   π_C (proof)", proof.pi_C)
        print(f"   Note: Manual computation missing -rsδ term")
        
        return False

if __name__ == "__main__":
    result = test_simple_multiplication()
    sys.exit(0 if result else 1)
