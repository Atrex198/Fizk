"""
Quick Test for Pairing Verification Fix
========================================

Tests that the polynomial opening equation is correctly implemented:
e(C - v·G1, G2) = e(π, τ·G2 - z·G2)

Uses reduced security parameters for fast testing.
"""

import sys
import numpy as np
import hashlib
import time
from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness

def create_hash(data):
    """Create cryptographic hash for commitment"""
    if isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(str(data).encode()).hexdigest()

def test_pairing_verification():
    """Test pairing verification with small dataset"""
    
    print("=" * 80)
    print("QUICK PAIRING VERIFICATION TEST")
    print("=" * 80)
    
    # Step 1: Create minimal training data
    print("\n1️⃣  Creating minimal training data...")
    np.random.seed(42)
    
    num_samples = 10  # Very small for speed
    num_features = 11
    
    X_data = np.random.rand(num_samples, num_features).astype(np.float32)
    y_data = np.random.randint(0, 2, num_samples)
    
    print(f"   ✅ Dataset: {num_samples} samples, {num_features} features")
    
    # Step 2: Create model weights
    print("\n2️⃣  Creating model weights...")
    
    initial_weights = {
        'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
        'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
        'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
        'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
        'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
        'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1
    }
    
    final_weights = {
        key: value + 0.01 * np.random.randn(*value.shape).astype(np.float32)
        for key, value in initial_weights.items()
    }
    
    print(f"   ✅ Weights created")
    
    # Step 3: Create statement and witness
    print("\n3️⃣  Creating statement and witness...")
    
    statement = TrainingStatement(
        model_architecture='CardioMLP',
        initial_weights_commitment=create_hash(str(initial_weights)),
        final_weights_commitment=create_hash(str(final_weights)),
        dataset_commitment=create_hash(X_data.tobytes()),
        local_epochs=1,
        batch_size=10,
        learning_rate=0.001,
        claimed_accuracy=0.75,
        claimed_loss=0.45,
        sample_count=num_samples,
        round_number=0,
        client_id=0,
        timestamp=time.time()
    )
    
    witness = TrainingWitness(
        initial_weights=initial_weights,
        final_weights=final_weights,
        dataset_samples=X_data,
        dataset_labels=y_data
    )
    
    print(f"   ✅ Statement and witness created")
    
    # Step 4: Initialize ZKP with minimum security
    print("\n4️⃣  Initializing ZKP (minimum security = 128-bit)...")
    print("   ⏱️  Note: SRS generation may take 1-2 minutes...")
    
    zkp = ProductionProtostar(security_level=128)  # Minimum required security
    
    setup_params = zkp.setup(statement)
    
    print(f"   ✅ SRS setup complete: {len(zkp.srs['g1_powers'])} G1 elements")
    
    # Step 5: Generate proof
    print("\n5️⃣  Generating proof...")
    
    proof = zkp.generate_proof(statement, witness)
    
    print(f"   ✅ Proof generated: {proof.proof_data.get('constraint_count', 0)} constraints")
    
    # Step 6: Verify proof with pairing checks
    print("\n6️⃣  Verifying proof with pairing-based cryptography...")
    print("   Checking polynomial opening equation:")
    print("   e(C - v·G1, G2) = e(π, τ·G2 - z·G2)")
    
    result = zkp.verify_proof(proof, statement)
    is_valid = result.is_valid if hasattr(result, 'is_valid') else result
    
    if is_valid:
        print(f"   ✅ PROOF VERIFICATION SUCCESSFUL!")
        print(f"   ✅ Pairing equation satisfied")
        print(f"   ✅ Polynomial opening verified")
    else:
        print(f"   ❌ PROOF VERIFICATION FAILED")
        if hasattr(result, 'message'):
            print(f"   📝 Reason: {result.message}")
    
    # Step 7: Test with tampered proof
    print("\n7️⃣  Testing tampered proof detection...")
    
    # Create tampered witness
    tampered_witness = TrainingWitness(
        initial_weights=final_weights,  # Swap
        final_weights=initial_weights,
        dataset_samples=X_data,
        dataset_labels=y_data
    )
    
    tampered_proof = zkp.generate_proof(statement, tampered_witness)
    tampered_result = zkp.verify_proof(tampered_proof, statement)
    tampered_valid = tampered_result.is_valid if hasattr(tampered_result, 'is_valid') else tampered_result
    
    if not tampered_valid:
        print(f"   ✅ Tampered proof correctly rejected")
    else:
        print(f"   ⚠️  WARNING: Tampered proof accepted")
        if hasattr(tampered_result, 'message'):
            print(f"   📝 Details: {tampered_result.message}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Proof Generation: SUCCESS")
    print(f"✅ Proof Verification: {'PASS' if is_valid else 'FAIL'}")
    print(f"✅ Tamper Detection: {'PASS' if not tampered_valid else 'FAIL'}")
    # Get constraint count from nested structure
    constraint_count = proof.proof_data.get('constraints', {}).get('count', 0)
    print(f"✅ R1CS Constraints: {constraint_count}")
    print(f"✅ Pairing Checks: {'WORKING' if is_valid else 'BROKEN'}")
    print("=" * 80)
    
    return is_valid and not tampered_valid

if __name__ == '__main__':
    try:
        success = test_pairing_verification()
        if success:
            print("\n🎉 All pairing verification tests PASSED!")
            sys.exit(0)
        else:
            print("\n❌ Some tests FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
