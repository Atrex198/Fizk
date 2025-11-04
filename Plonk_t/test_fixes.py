#!/usr/bin/env python3
"""
Quick test to validate the PLONK implementation fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from circuit_builder import PLONKCircuit, Wire

def test_wire_values():
    """Test that wire values are preserved correctly"""
    print("🧪 Testing Wire value preservation...")
    
    # Create a circuit
    circuit = PLONKCircuit("test_circuit")
    
    # Test values that were previously corrupted
    test_values = [22201, 149*149, 100*100, 50*50]
    
    for value in test_values:
        wire = circuit.create_wire(value, f"test_{value}")
        print(f"   Input: {value:>6} → Wire: {wire.value:>6} ✅" if wire.value == value % 21888242871839275222246405745257275088548364400416034343698204186575808495617 else f"   Input: {value:>6} → Wire: {wire.value:>6} ❌")
    
    print("✅ Wire value test complete\n")

def test_polynomial_division():
    """Test polynomial division algorithm"""
    print("🧪 Testing KZG polynomial division...")
    
    try:
        from kzg_commitment import KZGCommitment
        from polynomial_utils import Polynomial
        
        # Create a simple polynomial for testing
        coeffs = [1, 2, 3, 4]  # 1 + 2x + 3x² + 4x³
        poly = Polynomial(coeffs)
        
        # Test division by (x - 1)
        z = 1
        quotient, remainder = poly.synthetic_division(z)
        
        # Verify: poly(x) = quotient(x) * (x - z) + remainder
        # At x = z, poly(z) should equal remainder
        poly_at_z = poly.evaluate(z)
        
        print(f"   Polynomial: {poly}")
        print(f"   Division by (x - {z})")
        print(f"   Quotient: {quotient}")
        print(f"   Remainder: {remainder}")
        print(f"   poly({z}) = {poly_at_z}")
        print(f"   Remainder matches: {'✅' if remainder == poly_at_z else '❌'}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("✅ Polynomial division test complete\n")

def test_constraint_verification():
    """Test constraint verification with proper field arithmetic"""
    print("🧪 Testing constraint verification...")
    
    circuit = PLONKCircuit("constraint_test")
    
    # Test multiplication constraint: 149 * 149 = 22201
    a = 149
    b = 149
    c = 22201
    
    wire_a = circuit.create_wire(a, "a")
    wire_b = circuit.create_wire(b, "b") 
    wire_c = circuit.create_wire(c, "c")
    
    try:
        gate = circuit.add_multiplication_gate(wire_a, wire_b, wire_c)
        print(f"   Constraint {a} × {b} = {c}: ✅")
    except Exception as e:
        print(f"   Constraint {a} × {b} = {c}: ❌ {e}")
    
    # Test invalid constraint: 149 * 149 = 1000 (should fail)
    wire_d = circuit.create_wire(1000, "d")
    try:
        gate = circuit.add_multiplication_gate(wire_a, wire_b, wire_d)
        print(f"   Invalid constraint {a} × {b} = 1000: ❌ (should have failed)")
    except Exception as e:
        print(f"   Invalid constraint {a} × {b} = 1000: ✅ (correctly rejected)")
    
    print("✅ Constraint verification test complete\n")

if __name__ == "__main__":
    print("🔧 PLONK Implementation Fix Validation")
    print("=" * 50)
    
    test_wire_values()
    test_polynomial_division()
    test_constraint_verification()
    
    print("🎉 All tests completed!")