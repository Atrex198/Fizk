#!/usr/bin/env python3
"""
Test: Verify that build_full_fl_round works without training_data
=================================================================

This test verifies the fix for the issue where build_full_fl_round
would create 0 constraints when called without training_data, causing
tests to fail.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from groth16 import R1CSBuilder, FLCircuitBuilder, Groth16TrustedSetup, Groth16Prover, Groth16Verifier

def test_without_training_data():
    """Test that circuit can be built without training data (placeholder constraints)"""
    print("\n" + "="*70)
    print("TEST: Build FL Circuit Without Training Data")
    print("="*70)
    
    # Create circuit builder (it creates its own R1CSBuilder internally)
    circuit_builder = FLCircuitBuilder()
    
    # Build circuit WITHOUT training_data
    print("\n📊 Building circuit without training data...")
    var_indices = circuit_builder.build_full_fl_round(
        num_params=10,
        num_clients=2,
        round_number=1
        # NOTE: No training_data parameter!
    )
    
    r1cs = circuit_builder.finalize_circuit()
    
    print(f"\n✅ Circuit built:")
    print(f"   Constraints: {r1cs.num_constraints}")
    print(f"   Variables: {r1cs.num_variables}")
    
    # Verify we have at least 1 constraint (placeholder)
    if r1cs.num_constraints == 0:
        print("❌ FAILED: Circuit has 0 constraints!")
        return False
    
    print(f"✅ Has {r1cs.num_constraints} constraint(s) (placeholder for setup)")
    
    # Try to run setup with this circuit
    print("\n⏳ Testing trusted setup with placeholder circuit...")
    try:
        setup = Groth16TrustedSetup(r1cs)
        pk, vk = setup.generate_keys()
        print("✅ Trusted setup succeeded!")
        print(f"   PK A_query: {len(pk.A_query)} elements")
        print(f"   VK IC_query: {len(vk.IC_query)} elements")
        
        # Try to generate a proof
        print("\n⏳ Testing proof generation...")
        prover = Groth16Prover(pk, r1cs, setup)
        witness = r1cs.get_witness_vector()
        proof = prover.generate_proof(witness, [])
        print("✅ Proof generated!")
        
        # Try to verify
        print("\n⏳ Testing proof verification...")
        verifier = Groth16Verifier(vk)
        is_valid = verifier.verify_proof(proof, [])
        
        if is_valid:
            print("✅ Proof VALID!")
            print("\n✅ TEST PASSED: Circuit works without training data (placeholder)")
            return True
        else:
            print("❌ Proof INVALID")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_training_data():
    """Test that circuit works WITH training data (real constraints)"""
    print("\n" + "="*70)
    print("TEST: Build FL Circuit With Training Data")
    print("="*70)
    
    import torch
    import torch.nn as nn
    import numpy as np
    
    # Create simple model
    model = nn.Sequential(
        nn.Linear(11, 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 2)
    )
    
    # Create training data (single sample)
    X = torch.randn(11)  # Single sample, not batch
    y = 1  # Single label
    
    # Get initial weights
    initial_state = {k: v.clone().detach().cpu().numpy() for k, v in model.state_dict().items()}
    
    # Train one step
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    loss_fn = nn.CrossEntropyLoss()
    
    outputs = model(X.unsqueeze(0))  # Add batch dimension
    loss = loss_fn(outputs, torch.tensor([y]))
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # Get final weights
    final_state = {k: v.clone().detach().cpu().numpy() for k, v in model.state_dict().items()}
    
    training_data = {
        'initial_weights': initial_state,
        'final_weights': final_state,
        'X_sample': X.numpy(),  # 1D array
        'y_sample': y,  # Integer label
        'learning_rate': 0.01
    }
    
    # Create circuit builder (it creates its own R1CSBuilder internally)
    circuit_builder = FLCircuitBuilder()
    
    # Build circuit WITH training_data
    print("\n📊 Building circuit with training data...")
    var_indices = circuit_builder.build_full_fl_round(
        num_params=10,
        num_clients=1,
        round_number=1,
        training_data=training_data  # Provide training data!
    )
    
    r1cs = circuit_builder.finalize_circuit()
    
    print(f"\n✅ Circuit built:")
    print(f"   Constraints: {r1cs.num_constraints}")
    print(f"   Variables: {r1cs.num_variables}")
    
    if r1cs.num_constraints > 1:
        print(f"✅ Has {r1cs.num_constraints} REAL ML constraints!")
        print("\n✅ TEST PASSED: Circuit works with training data")
        return True
    else:
        print("❌ Expected more than 1 constraint with training data")
        return False


def main():
    """Run both tests"""
    print("\n" + "="*70)
    print("TESTING FIX FOR ZERO-CONSTRAINT ISSUE")
    print("="*70)
    print("\nIssue: build_full_fl_round() would create 0 constraints without training_data")
    print("Fix: Add minimal placeholder constraint when no training_data provided")
    
    results = []
    
    # Test 1: Without training data (placeholder)
    results.append(("Without training data", test_without_training_data()))
    
    # Test 2: With training data (real constraints)  
    results.append(("With training data", test_with_training_data()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(p for _, p in results)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED - Fix is working!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
