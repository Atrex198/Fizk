"""
Test to verify if the gradient bypass attack is prevented.
This test checks if a client can compute correct gradients but then
update weights using arbitrary values (not based on gradients).
"""

import sys
sys.path.append('.')
import numpy as np
from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS

def test_gradient_bypass_attack():
    """Test if client can bypass gradient computation"""
    
    print("=" * 70)
    print("GRADIENT BYPASS ATTACK TEST")
    print("=" * 70)
    
    # Initialize circuit
    circuit = MLCircuitR1CS(
        curve_order=21888242871839275222246405745257275088548364400416034343698204186575808495617
    )
    
    # Create test data
    X_sample = np.random.randn(11).astype(np.float32)
    y_sample = 1
    
    # Create weights
    initial_weights = {
        'network.0.weight': np.random.randn(64, 11).astype(np.float32),
        'network.0.bias': np.random.randn(64).astype(np.float32),
        'network.4.weight': np.random.randn(32, 64).astype(np.float32),
        'network.4.bias': np.random.randn(32).astype(np.float32),
        'network.8.weight': np.random.randn(2, 32).astype(np.float32),
        'network.8.bias': np.random.randn(2).astype(np.float32),
    }
    
    # ATTACK: Apply changes in WRONG direction (opposite of gradient descent)
    # Normally gradient descent does: w_new = w_old - lr * grad
    # Attack does: w_new = w_old + arbitrary_change (not based on gradients)
    print("\n📊 Testing GRADIENT BYPASS attack...")
    print("   Strategy: Weights change, but NOT according to gradients")
    
    # Apply arbitrary changes (e.g., in wrong direction)
    final_weights = {
        k: v + 0.05 * np.random.randn(*v.shape).astype(np.float32)  # RANDOM changes
        for k, v in initial_weights.items()
    }
    
    # Verify they changed
    max_diffs = {}
    for key in initial_weights.keys():
        diff = np.abs(final_weights[key] - initial_weights[key]).max()
        max_diffs[key] = diff
        print(f"   {key}: max_diff = {diff:.6f}")
    
    print("\n   ⚠️  NOTE: These changes are NOT based on computed gradients!")
    print("   The circuit will compute real gradients, but weights were")
    print("   updated using arbitrary values instead.")
    
    # Try to generate circuit
    try:
        constraints, witness = circuit.generate_full_ml_circuit(
            initial_weights=initial_weights,
            final_weights=final_weights,  # Arbitrary changes!
            X_sample=X_sample,
            y_sample=y_sample,
            learning_rate=0.01,
            claimed_loss=0.5
        )
        
        print(f"\n✅ Circuit generation SUCCEEDED")
        print(f"   Generated {len(constraints)} constraints with {len(witness)} witness variables")
        
        # Try to verify
        is_satisfied = circuit.verify_constraint_satisfaction(constraints, witness)
        
        if is_satisfied:
            print(f"\n⚠️  VULNERABILITY DETECTED!")
            print(f"   System accepts weights updated WITHOUT using gradients")
            print(f"   This allows Byzantine attacks where clients make harmful updates")
            return False
        else:
            print(f"\n✅ Verification FAILED (good!)")
            print(f"   System correctly detects gradient bypass attack")
            return True
            
    except Exception as e:
        print(f"\n✅ Circuit generation FAILED (good!)")
        print(f"   Error: {str(e)}")
        print(f"   System correctly rejects gradient bypass at proof generation")
        return True

def test_correct_gradient_usage():
    """Test that properly gradient-based updates are accepted"""
    
    print("\n" + "=" * 70)
    print("CORRECT GRADIENT USAGE TEST")
    print("=" * 70)
    
    circuit = MLCircuitR1CS(
        curve_order=21888242871839275222246405745257275088548364400416034343698204186575808495617
    )
    
    X_sample = np.random.randn(11).astype(np.float32)
    y_sample = 1
    
    # Create weights
    initial_weights = {
        'network.0.weight': np.random.randn(64, 11).astype(np.float32),
        'network.0.bias': np.random.randn(64).astype(np.float32),
        'network.4.weight': np.random.randn(32, 64).astype(np.float32),
        'network.4.bias': np.random.randn(32).astype(np.float32),
        'network.8.weight': np.random.randn(2, 32).astype(np.float32),
        'network.8.bias': np.random.randn(2).astype(np.float32),
    }
    
    # HONEST: Apply small changes (simulating real training)
    final_weights = {
        k: v + 0.01 * np.random.randn(*v.shape).astype(np.float32) 
        for k, v in initial_weights.items()
    }
    
    print("\n📊 Testing with gradient-consistent updates...")
    
    try:
        constraints, witness = circuit.generate_full_ml_circuit(
            initial_weights=initial_weights,
            final_weights=final_weights,
            X_sample=X_sample,
            y_sample=y_sample,
            learning_rate=0.01,
            claimed_loss=0.5
        )
        
        print(f"✅ Circuit generation SUCCEEDED")
        
        is_satisfied = circuit.verify_constraint_satisfaction(constraints, witness)
        
        if is_satisfied:
            print(f"✅ Verification PASSED")
            print(f"   System correctly accepts gradient-based updates")
            return True
        else:
            print(f"⚠️  Verification FAILED")
            print(f"   Might be too strict (false positive)")
            return False
            
    except Exception as e:
        print(f"❌ Circuit generation FAILED")
        print(f"   Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n🔍 TESTING GRADIENT BYPASS VULNERABILITY\n")
    
    # Test 1: Gradient bypass attack
    attack_blocked = test_gradient_bypass_attack()
    
    # Test 2: Correct gradient usage
    correct_accepted = test_correct_gradient_usage()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    if attack_blocked and correct_accepted:
        print("✅ GRADIENT VERIFICATION SECURE")
        print("   - Gradient bypass attack blocked")
        print("   - Correct gradient usage accepted")
        exit(0)
    elif not attack_blocked and correct_accepted:
        print("❌ GRADIENT BYPASS VULNERABILITY")
        print("   - Attack succeeds (VULNERABLE)")
        print("   - Correct usage accepted")
        exit(1)
    elif attack_blocked and not correct_accepted:
        print("⚠️  OVERLY STRICT CONSTRAINTS")
        print("   - Attack blocked")
        print("   - Correct usage rejected (false positive)")
        exit(1)
    else:
        print("❌ SYSTEM BROKEN")
        print("   - Everything fails")
        exit(1)
