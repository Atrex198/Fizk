#!/usr/bin/env python3
"""
Step-by-step debugging of Groth16 verification failure.
Traces every computation with expected vs actual values.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py_ecc.bn128 import G1, G2, multiply, add, pairing, eq, curve_order, FQ, FQ2
from groth16.r1cs import R1CS
from groth16.qap import QAP
from groth16.trusted_setup import Groth16TrustedSetup
from groth16.prover import Groth16Prover
from groth16.verifier import Groth16Verifier

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_point(name, point, group="G1"):
    if group == "G1":
        print(f"{name}: ({point[0].n}, {point[1].n})")
    else:  # G2
        print(f"{name}: (({point[0].coeffs[0].n}, {point[1].coeffs[0].n}))")

def test_minimal_circuit():
    """Test a*b = c with witness [1, 3, 5, 15]"""
    
    print_section("1. CIRCUIT SETUP")
    
    # Build R1CS: a*b = c
    r1cs = R1CS(4)
    # Variable indices: 0=ONE, 1=a, 2=b, 3=c
    r1cs.add_multiplication_constraint(
        a_var=1,    # a
        b_var=2,   # b
        c_var=3   # c
    )
    
    print(f"Variables: 4 (ONE, a, b, c)")
    print(f"Constraints: 1 (a*b=c)")
    print(f"Public inputs: [ONE]")
    print(f"Private witness: [a, b, c]")
    
    # Set witness values
    witness = [1, 3, 5, 15]
    for i, val in enumerate(witness):
        r1cs.set_witness(i, val)
    
    print(f"\nWitness: {witness}")
    assert r1cs.verify_constraint_satisfaction(), "Constraint not satisfied!"
    print("✅ Constraint satisfied: 3 * 5 = 15")
    
    print_section("2. QAP CONSTRUCTION")
    
    qap = QAP(r1cs)
    print(f"QAP degree: {qap.degree}")
    print(f"Evaluation points: {qap.eval_points}")
    print(f"Target polynomial t(x) degree: {len(qap.t_poly) - 1}")
    
    # Check QAP at evaluation point
    A_at_1 = qap.evaluate_polynomial_at(qap.A_polys[1], qap.eval_points[0])
    B_at_1 = qap.evaluate_polynomial_at(qap.B_polys[2], qap.eval_points[0])
    C_at_1 = qap.evaluate_polynomial_at(qap.C_polys[3], qap.eval_points[0])
    print(f"\nAt evaluation point {qap.eval_points[0]}:")
    print(f"  A_1 = {A_at_1} (should be 1 for 'a')")
    print(f"  B_2 = {B_at_1} (should be 1 for 'b')")
    print(f"  C_3 = {C_at_1} (should be 1 for 'c')")
    
    # Check quotient polynomial
    h_poly = qap.compute_quotient_polynomial(witness)
    print(f"\nQuotient polynomial h(x) degree: {len(h_poly) - 1}")
    print(f"h(x) coefficients: {h_poly[:min(5, len(h_poly))]}")
    
    # Verify QAP divisibility
    A_poly = qap.compute_A_polynomial(witness)
    B_poly = qap.compute_B_polynomial(witness)
    C_poly = qap.compute_C_polynomial(witness)
    
    # Check at evaluation point
    eval_point = qap.eval_points[0]
    A_val = qap.evaluate_polynomial_at(A_poly, eval_point)
    B_val = qap.evaluate_polynomial_at(B_poly, eval_point)
    C_val = qap.evaluate_polynomial_at(C_poly, eval_point)
    t_val = qap.evaluate_polynomial_at(qap.t_poly, eval_point)
    
    print(f"\nAt evaluation point {eval_point}:")
    print(f"  A({eval_point}) = {A_val}")
    print(f"  B({eval_point}) = {B_val}")
    print(f"  C({eval_point}) = {C_val}")
    print(f"  A*B - C = {(A_val * B_val - C_val) % curve_order}")
    print(f"  t({eval_point}) = {t_val}")
    print(f"  (A*B - C) / t = {((A_val * B_val - C_val) * pow(t_val, -1, curve_order)) % curve_order}")
    
    if t_val == 0:
        print("✅ t(eval_point) = 0, so (A*B - C) should equal 0")
        assert (A_val * B_val - C_val) % curve_order == 0, "QAP not satisfied at root!"
    
    print_section("3. TRUSTED SETUP")
    
    public_indices = [0]  # Only ONE is public
    setup = Groth16TrustedSetup(r1cs, public_indices)
    pk, vk = setup.generate_keys()
    
    print(f"Toxic waste (secret τ): {setup.tau}")
    print(f"Toxic waste (α): {setup.alpha}")
    print(f"Toxic waste (β): {setup.beta}")
    print(f"Toxic waste (γ): {setup.gamma}")
    print(f"Toxic waste (δ): {setup.delta}")
    
    print(f"\nProving Key:")
    print(f"  A_query length: {len(pk.A_query)}")
    print(f"  B_query_G1 length: {len(pk.B_query_G1)}")
    print(f"  B_query_G2 length: {len(pk.B_query_G2)}")
    print(f"  L_query length: {len(pk.L_query)} (private variables)")
    print(f"  H_query length: {len(pk.H_query)}")
    
    print(f"\nVerification Key:")
    print(f"  IC_query length: {len(vk.IC_query)}")
    print_point("  alpha_G1", vk.alpha_G1)
    print_point("  beta_G2", vk.beta_G2, "G2")
    print_point("  gamma_G2", vk.gamma_G2, "G2")
    print_point("  delta_G2", vk.delta_G2, "G2")
    
    # Check some key elements
    print(f"\nKey element checks:")
    print_point("  A_query[0] (for ONE)", pk.A_query[0])
    print_point("  A_query[1] (for a)", pk.A_query[1])
    print_point("  B_query_G2[0] (for ONE)", pk.B_query_G2[0], "G2")
    print_point("  B_query_G2[1] (for a)", pk.B_query_G2[1], "G2")
    
    if len(pk.L_query) > 0:
        print_point("  L_query[0] (first private)", pk.L_query[0])
    if len(pk.H_query) > 0:
        print_point("  H_query[0]", pk.H_query[0])
    
    print_section("4. PROOF GENERATION")
    
    prover = Groth16Prover(setup)
    proof = prover.generate_proof(witness)
    
    print("Proof components:")
    print_point("  π_A", proof.pi_A)
    print_point("  π_B", proof.pi_B, "G2")
    print_point("  π_C", proof.pi_C)
    
    # Manually recompute proof components to debug
    print(f"\n--- Manual Proof Computation ---")
    
    # Random blinding factors (using prover's values)
    r = prover.r
    s = prover.s
    print(f"Blinding r: {r}")
    print(f"Blinding s: {s}")
    
    # π_A = [α]₁ + Σᵢwᵢ[Aᵢ(τ)]₁ + [rδ]₁
    print(f"\nπ_A computation:")
    pi_A_manual = pk.alpha_G1
    print_point("  Start: [α]₁", pi_A_manual)
    
    for i, w_i in enumerate(witness):
        term = multiply(pk.A_query[i], w_i)
        pi_A_manual = add(pi_A_manual, term)
        if i < 4:
            print(f"  + w[{i}] * A_query[{i}] = {w_i} * ...", )
    
    pi_A_manual = add(pi_A_manual, multiply(pk.delta_G1, r))
    print(f"  + [rδ]₁")
    print_point("  Result", pi_A_manual)
    print_point("  Prover's π_A", proof.pi_A)
    print(f"  Match: {eq(pi_A_manual, proof.pi_A)}")
    
    # π_B = [β]₂ + Σᵢwᵢ[Bᵢ(τ)]₂ + [sδ]₂
    print(f"\nπ_B computation:")
    pi_B_manual = pk.beta_G2
    print_point("  Start: [β]₂", pi_B_manual, "G2")
    
    for i, w_i in enumerate(witness):
        term = multiply(pk.B_query_G2[i], w_i)
        pi_B_manual = add(pi_B_manual, term)
        if i < 4:
            print(f"  + w[{i}] * B_query_G2[{i}] = {w_i} * ...")
    
    pi_B_manual = add(pi_B_manual, multiply(pk.delta_G2, s))
    print(f"  + [sδ]₂")
    print_point("  Result", pi_B_manual, "G2")
    print_point("  Prover's π_B", proof.pi_B, "G2")
    print(f"  Match: {eq(pi_B_manual, proof.pi_B)}")
    
    # π_C computation (most complex)
    print(f"\nπ_C computation:")
    
    # Step 1: B_g1 = [β]₁ + Σᵢwᵢ[Bᵢ(τ)]₁ + [sδ]₁
    B_g1 = pk.beta_G1
    for i, w_i in enumerate(witness):
        B_g1 = add(B_g1, multiply(pk.B_query_G1[i], w_i))
    B_g1 = add(B_g1, multiply(pk.delta_G1, s))
    print_point("  B_g1", B_g1)
    
    # Step 2: H(τ)/δ using H_query
    pi_C_manual = (1, 2)  # Neutral element
    print(f"  h(x) degree: {len(h_poly) - 1}")
    if len(h_poly) > 0 and h_poly[0] != 0:
        for i, h_i in enumerate(h_poly):
            if i < len(pk.H_query) and h_i % curve_order != 0:
                term = multiply(pk.H_query[i], h_i)
                pi_C_manual = add(pi_C_manual, term)
                if i < 3:
                    print(f"  + h[{i}] * H_query[{i}] = {h_i} * ...")
    else:
        print("  h(x) is zero or empty - no H term")
    
    # Step 3: Private witness Σ wᵢ·L_query[i]
    print(f"  Adding private witness terms:")
    private_start = max(public_indices) + 1
    for i in range(private_start, len(witness)):
        l_idx = i - private_start
        if l_idx < len(pk.L_query):
            term = multiply(pk.L_query[l_idx], witness[i])
            pi_C_manual = add(pi_C_manual, term)
            print(f"    + w[{i}] * L_query[{l_idx}] = {witness[i]} * ...")
    
    # Step 4: Blinding s·π_A
    term_s_pi_A = multiply(pi_A_manual, s)
    pi_C_manual = add(pi_C_manual, term_s_pi_A)
    print(f"  + s·π_A")
    
    # Step 5: Blinding r·B_g1
    term_r_B_g1 = multiply(B_g1, r)
    pi_C_manual = add(pi_C_manual, term_r_B_g1)
    print(f"  + r·B_g1")
    
    # Step 6: Blinding -rsδ
    rs_delta = (r * s * setup.delta) % curve_order
    term_rs_delta = multiply(G1, curve_order - rs_delta)
    pi_C_manual = add(pi_C_manual, term_rs_delta)
    print(f"  - rsδ (rs_delta = {rs_delta})")
    
    print_point("  Result", pi_C_manual)
    print_point("  Prover's π_C", proof.pi_C)
    print(f"  Match: {eq(pi_C_manual, proof.pi_C)}")
    
    print_section("5. VERIFICATION")
    
    verifier = Groth16Verifier(vk)
    
    # Compute vk_x (IC accumulator)
    public_inputs = [1]  # Only ONE
    vk_x = vk.IC_query[0]
    print(f"Public inputs: {public_inputs}")
    print_point("IC[0] (base)", vk_x)
    
    for i, x_i in enumerate(public_inputs):
        if i + 1 < len(vk.IC_query):
            term = multiply(vk.IC_query[i + 1], x_i)
            vk_x = add(vk_x, term)
            print(f"+ x[{i}] * IC[{i+1}] = {x_i} * ...")
    
    print_point("vk_x (final)", vk_x)
    
    # Compute pairings
    print(f"\nPairing computations:")
    
    left = pairing(proof.pi_B, proof.pi_A)
    print(f"LEFT = e(π_B, π_A)")
    print(f"  = {left}")
    
    term1 = pairing(vk.beta_G2, vk.alpha_G1)
    print(f"\nRIGHT term 1 = e(β, α)")
    print(f"  = {term1}")
    
    term2 = pairing(vk.gamma_G2, vk_x)
    print(f"\nRIGHT term 2 = e(γ, vk_x)")
    print(f"  = {term2}")
    
    term3 = pairing(vk.delta_G2, proof.pi_C)
    print(f"\nRIGHT term 3 = e(δ, π_C)")
    print(f"  = {term3}")
    
    right = term1 * term2 * term3
    print(f"\nRIGHT = term1 * term2 * term3")
    print(f"  = {right}")
    
    print(f"\n{'='*80}")
    print(f"LEFT == RIGHT: {left == right}")
    print(f"{'='*80}")
    
    # Try alternative verification equations
    print(f"\n--- Alternative Checks ---")
    
    # Check if any individual term is the issue
    print(f"\ne(π_A, π_B) * e(α, β)^-1 = e(vk_x, γ) * e(π_C, δ)?")
    alt_left = left * pow(term1, -1, curve_order)
    alt_right = term2 * term3
    print(f"  {alt_left == alt_right}")
    
    # Check the knowledge of exponent relationship
    print(f"\ne(π_A - [α]₁, G2) = e(G1, π_B - [β]₂)?")
    pi_A_minus_alpha = add(proof.pi_A, multiply(vk.alpha_G1, curve_order - 1))
    pi_B_minus_beta = add(proof.pi_B, multiply(vk.beta_G2, curve_order - 1))
    check1 = pairing(G2, pi_A_minus_alpha)
    check2 = pairing(pi_B_minus_beta, G1)
    print(f"  {check1 == check2}")
    
    return left == right

if __name__ == "__main__":
    result = test_minimal_circuit()
    print(f"\n{'='*80}")
    if result:
        print("✅ VERIFICATION PASSED!")
    else:
        print("❌ VERIFICATION FAILED!")
    print(f"{'='*80}")
