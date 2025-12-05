#!/usr/bin/env python3
"""
Quick test to verify constraint format handling
"""
import sys
import numpy as np
from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS
from py_ecc.bn128.bn128_curve import curve_order

def test_constraint_format():
    print("=" * 80)
    print("Testing Constraint Format Handling")
    print("=" * 80)
    
    # Create circuit generator
    circuit = MLCircuitR1CS(curve_order)
    
    # Create dummy weights for a tiny network
    initial_weights = {
        'network.0.weight': np.random.randn(2, 3) * 0.01,  # 2 neurons, 3 inputs
        'network.0.bias': np.random.randn(2) * 0.01,
        'network.4.weight': np.random.randn(2, 2) * 0.01,
        'network.4.bias': np.random.randn(2) * 0.01,
        'network.8.weight': np.random.randn(2, 2) * 0.01,
        'network.8.bias': np.random.randn(2) * 0.01,
    }
    
    final_weights = {k: v + np.random.randn(*v.shape) * 0.001 for k, v in initial_weights.items()}
    
    X_sample = np.random.randn(3)
    y_sample = 0
    
    print("\n1. Generating R1CS circuit...")
    try:
        constraints, witness = circuit.generate_full_ml_circuit(
            initial_weights=initial_weights,
            final_weights=final_weights,
            X_sample=X_sample,
            y_sample=y_sample,
            learning_rate=0.01,
            claimed_loss=0.5
        )
        
        print(f"✅ Generated {len(constraints)} constraints with {len(witness)} witness values")
        
        # Check first constraint format
        if len(constraints) > 0:
            first = constraints[0]
            print("\n2. Checking constraint format...")
            print(f"   Keys in first constraint: {list(first.keys())}")
            
            if 'A' in first:
                print(f"   ✅ Has sparse 'A' format: {type(first['A'])} with {len(first['A'])} entries")
                print(f"      Sample: {dict(list(first['A'].items())[:3])}")
            
            if 'a' in first:
                print(f"   ✅ Has dense 'a' format: {type(first['a'])} with {len(first['a'])} entries")
                
            if 'a_coefficients' in first:
                print(f"   ✅ Has guide-compliant format: {type(first['a_coefficients'])}")
        
        # Verify constraints can be checked
        print("\n3. Verifying constraint satisfaction...")
        is_satisfied = circuit.verify_constraint_satisfaction(constraints, witness)
        
        if is_satisfied:
            print("✅ All constraints satisfied!")
            return True
        else:
            print("❌ Some constraints NOT satisfied")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_constraint_format()
    sys.exit(0 if success else 1)
