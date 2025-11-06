"""
Test to verify if the freeloading attack vulnerability exists.
This test checks if unchanged weights can pass ZKP verification.
"""

import sys
sys.path.append('.')
import numpy as np
from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS

def test_freeloading_attack():
    """Test if unchanged weights pass verification"""
    
    print("=" * 70)
    print("FREELOADING ATTACK TEST")
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
    
    # ATTACK: Use UNCHANGED weights
    final_weights = {k: v.copy() for k, v in initial_weights.items()}
    
    print("\n📊 Testing with UNCHANGED weights (freeloading attack)...")
    print(f"   Initial weights hash: {hash(initial_weights['network.0.weight'].tobytes())}")
    print(f"   Final weights hash:   {hash(final_weights['network.0.weight'].tobytes())}")
    
    # Verify they are actually identical
    all_identical = True
    for key in initial_weights.keys():
        if not np.array_equal(initial_weights[key], final_weights[key]):
            all_identical = False
            print(f"   ❌ {key} changed (unexpected)")
    
    if all_identical:
        print("   ✅ Confirmed: All weights are IDENTICAL (no training)")
    
    # Try to generate circuit
    try:
        constraints, witness = circuit.generate_full_ml_circuit(
            initial_weights=initial_weights,
            final_weights=final_weights,
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
            print(f"\n❌ VULNERABILITY CONFIRMED!")
            print(f"   ⚠️  Unchanged weights passed ALL {len(constraints)} constraints")
            print(f"   ⚠️  System is VULNERABLE to freeloading attack")
            print(f"\n   Attack scenario:")
            print(f"   1. Client receives global weights")
            print(f"   2. Client does NO training (keeps weights unchanged)")
            print(f"   3. Client generates valid ZKP proof")
            print(f"   4. Server accepts proof (thinks client trained)")
            print(f"   5. Global model doesn't improve (poisoned by lazy clients)")
            return False
        else:
            print(f"\n✅ Verification FAILED (good!)")
            print(f"   System correctly rejects unchanged weights")
            return True
            
    except Exception as e:
        print(f"\n✅ Circuit generation FAILED (good!)")
        print(f"   Error: {str(e)}")
        print(f"   System correctly rejects unchanged weights at proof generation stage")
        return True

def test_honest_training():
    """Test if changed weights pass verification"""
    
    print("\n" + "=" * 70)
    print("HONEST TRAINING TEST")
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
    
    # HONEST: Apply small changes (simulating training)
    final_weights = {
        k: v + 0.01 * np.random.randn(*v.shape).astype(np.float32) 
        for k, v in initial_weights.items()
    }
    
    print("\n📊 Testing with CHANGED weights (honest training)...")
    
    # Verify they changed
    max_diffs = {}
    for key in initial_weights.keys():
        diff = np.abs(final_weights[key] - initial_weights[key]).max()
        max_diffs[key] = diff
        print(f"   {key}: max_diff = {diff:.6f}")
    
    try:
        constraints, witness = circuit.generate_full_ml_circuit(
            initial_weights=initial_weights,
            final_weights=final_weights,
            X_sample=X_sample,
            y_sample=y_sample,
            learning_rate=0.01,
            claimed_loss=0.5
        )
        
        print(f"\n✅ Circuit generation SUCCEEDED")
        
        is_satisfied = circuit.verify_constraint_satisfaction(constraints, witness)
        
        if is_satisfied:
            print(f"✅ Verification PASSED")
            print(f"   System correctly accepts honest training")
            return True
        else:
            print(f"❌ Verification FAILED")
            print(f"   System incorrectly rejects honest training (false positive)")
            return False
            
    except Exception as e:
        print(f"❌ Circuit generation FAILED")
        print(f"   Error: {str(e)}")
        print(f"   System incorrectly rejects honest training")
        return False

if __name__ == "__main__":
    print("\n🔍 TESTING ZKP SECURITY VULNERABILITIES\n")
    
    # Test 1: Freeloading attack
    attack_blocked = test_freeloading_attack()
    
    # Test 2: Honest training
    honest_accepted = test_honest_training()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    if attack_blocked and honest_accepted:
        print("✅ SYSTEM SECURE")
        print("   - Freeloading attack blocked")
        print("   - Honest training accepted")
        exit(0)
    elif not attack_blocked and honest_accepted:
        print("❌ CRITICAL VULNERABILITY")
        print("   - Freeloading attack succeeds (VULNERABLE)")
        print("   - Honest training accepted")
        print("\n   RECOMMENDATION: Re-apply commit 5bd5aa0 to fix vulnerability")
        exit(1)
    elif attack_blocked and not honest_accepted:
        print("⚠️  FALSE POSITIVES")
        print("   - Freeloading attack blocked")
        print("   - Honest training rejected (too strict)")
        exit(1)
    else:
        print("❌ SYSTEM BROKEN")
        print("   - Both attacks and honest training fail")
        exit(1)
