#!/usr/bin/env python3
"""
Test circuit polynomial commitment
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_circuit_commitment():
    """Test circuit polynomial commitment"""
    print("CIRCUIT COMMITMENT TEST")
    print("=" * 30)
    
    try:
        from circuit_builder import PLONKCircuit
        from plonk_protocol import PLONKProtocol
        
        print("Step 1: Create circuit")
        circuit = PLONKCircuit("test")
        
        # Simple: x * 1 = x
        x = circuit.create_wire(5, "x")
        one = circuit.create_wire(1, "one") 
        result = circuit.create_wire(5, "result")
        circuit.add_multiplication_gate(x, one, result)
        
        print(f"   ✓ Circuit: {len(circuit.gates)} gates")
        print(f"   a_wires: {circuit.a_wires}")
        print(f"   b_wires: {circuit.b_wires}")
        print(f"   c_wires: {circuit.c_wires}")
        
        print("Step 2: Test polynomial interpolation")
        from polynomial_utils import PolynomialArithmetic
        
        # Test interpolating a_wires as polynomial
        poly_arith = PolynomialArithmetic()
        points = [(i, circuit.a_wires[i]) for i in range(len(circuit.a_wires))]
        a_poly = poly_arith.interpolate_lagrange(points)
        print(f"   a_polynomial coefficients: {a_poly}")
        
        print("Step 3: Test KZG commitment setup")
        plonk = PLONKProtocol({'trusted_setup_size': 8, 'security_level': 128, 'curve': 'bn254'})
        plonk.setup()
        print("   ✓ PLONK setup complete")
        
        print("Step 4: Test commitment directly")
        commitment = plonk.kzg_commitment.commit(a_poly)
        print(f"   ✓ Commitment: {commitment}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_circuit_commitment()
    if success:
        print("\n✓ CIRCUIT COMMITMENT TEST PASSED")
    else:
        print("\n✗ CIRCUIT COMMITMENT TEST FAILED")