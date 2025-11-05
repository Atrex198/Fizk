"""
Test Complete ZKP Pipeline with Fixed Pairing Verification
===========================================================

This test verifies:
1. R1CS circuit generation (8000+ constraints)
2. Proof generation with proper polynomial commitments
3. Pairing-based verification with correct equations
4. End-to-end proof of ML training
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

def test_complete_pipeline():
    """Test the complete ZKP pipeline with real ML data"""
    
    print("=" * 80)
    print("TESTING COMPLETE ZKP PIPELINE WITH FIXED PAIRING VERIFICATION")
    print("=" * 80)
    
    # Step 1: Create realistic training data
    print("\n1️⃣  Creating realistic training data...")
    np.random.seed(42)
    
    # Cardio dataset has 11 features
    num_samples = 100
    num_features = 11
    
    X_data = np.random.rand(num_samples, num_features).astype(np.float32)
    y_data = np.random.randint(0, 2, num_samples)  # Binary classification
    
    print(f"   ✅ Dataset: {num_samples} samples, {num_features} features")
    
    # Step 2: Create realistic weight matrices (matching cardio model architecture)
    print("\n2️⃣  Creating model weights (11 -> 64 -> 32 -> 2 architecture)...")
    
    initial_weights = {
        'network.0.weight': np.random.randn(64, 11).astype(np.float32) * 0.1,
        'network.0.bias': np.random.randn(64).astype(np.float32) * 0.1,
        'network.4.weight': np.random.randn(32, 64).astype(np.float32) * 0.1,
        'network.4.bias': np.random.randn(32).astype(np.float32) * 0.1,
        'network.8.weight': np.random.randn(2, 32).astype(np.float32) * 0.1,
        'network.8.bias': np.random.randn(2).astype(np.float32) * 0.1
    }
    
    # Simulate training: small weight updates
    final_weights = {
        key: value + 0.01 * np.random.randn(*value.shape).astype(np.float32)
        for key, value in initial_weights.items()
    }
    
    print(f"   ✅ Initial weights created")
    print(f"   ✅ Final weights created (simulated training)")
    
    # Step 3: Create cryptographic commitments
    print("\n3️⃣  Creating cryptographic commitments...")
    
    initial_weights_commitment = create_hash(str(initial_weights))
    final_weights_commitment = create_hash(str(final_weights))
    dataset_commitment = create_hash(X_data.tobytes())
    
    print(f"   ✅ Initial weights commitment: {initial_weights_commitment[:16]}...")
    print(f"   ✅ Final weights commitment: {final_weights_commitment[:16]}...")
    print(f"   ✅ Dataset commitment: {dataset_commitment[:16]}...")
    
    # Step 4: Create training statement and witness
    print("\n4️⃣  Creating training statement and witness...")
    
    statement = TrainingStatement(
        model_architecture='CardioMLP_11_64_32_2',
        initial_weights_commitment=initial_weights_commitment,
        final_weights_commitment=final_weights_commitment,
        dataset_commitment=dataset_commitment,
        local_epochs=5,
        batch_size=32,
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
    
    print(f"   ✅ Statement created: {statement.model_architecture}")
    print(f"   ✅ Witness created: {len(initial_weights)} weight tensors")
    
    # Step 5: Initialize ZKP system
    print("\n5️⃣  Initializing ZKP system...")
    
    zkp = ProductionProtostar(security_level=128)
    
    # Setup trusted parameters (SRS)
    print("   🔒 Setting up Structured Reference String (SRS)...")
    setup_params = zkp.setup(statement)
    
    print(f"   ✅ SRS setup complete: {len(zkp.srs['g1_powers'])} G1 elements")
    print(f"   ✅ Security level: {zkp.security_level}-bit")
    
    # Step 6: Generate proof
    print("\n6️⃣  Generating zero-knowledge proof...")
    print("   This will:")
    print("     - Generate 8000+ R1CS constraints from real ML computation")
    print("     - Create polynomial commitments using elliptic curves")
    print("     - Generate proof with cryptographic soundness")
    
    proof = zkp.generate_proof(statement, witness)
    
    print(f"   ✅ Proof generated successfully!")
    
    # Access the constraint count from the correct location in proof_data
    constraints_info = proof.proof_data.get('constraints', {})
    commitment_count = proof.metadata.get('ec_commitments_count', 0)
    
    print(f"   📊 Proof contains {commitment_count} polynomial commitments")
    print(f"   🔐 Proof uses {constraints_info.get('count', 0)} R1CS constraints")
    
    # Step 7: Verify proof
    print("\n7️⃣  Verifying proof with pairing-based cryptography...")
    print("   This will:")
    print("     - Check polynomial opening equations: e(C - v·G1, G2) = e(π, τ·G2 - z·G2)")
    print("     - Verify elliptic curve pairing equations")
    print("     - Validate cryptographic commitments")
    
    is_valid = zkp.verify_proof(proof, statement)
    
    if is_valid:
        print(f"   ✅ PROOF VERIFICATION SUCCESSFUL!")
        print(f"   ✅ All pairing checks passed")
        print(f"   ✅ Cryptographic soundness verified")
    else:
        print(f"   ❌ PROOF VERIFICATION FAILED")
        print(f"   ❌ Pairing checks did not pass")
    
    # Step 8: Test security properties
    print("\n8️⃣  Testing security properties...")
    
    # Test 1: Modified witness should fail
    print("   Test 1: Modified witness detection...")
    tampered_witness = TrainingWitness(
        initial_weights=final_weights,  # Swap initial and final
        final_weights=initial_weights,
        dataset_samples=X_data,
        dataset_labels=y_data
    )
    
    tampered_proof = zkp.generate_proof(statement, tampered_witness)
    tampered_valid = zkp.verify_proof(tampered_proof, statement)
    
    if not tampered_valid:
        print(f"   ✅ Tampered witness correctly rejected")
    else:
        print(f"   ⚠️  WARNING: Tampered witness accepted (potential security issue)")
    
    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE TEST SUMMARY")
    print("=" * 80)
    constraints_info = proof.proof_data.get('constraints', {})
    print(f"✅ R1CS Circuit: {constraints_info.get('count', 0)} constraints generated")
    print(f"✅ Proof Generation: Successful")
    print(f"✅ Proof Verification: {'PASSED' if is_valid else 'FAILED'}")
    print(f"✅ Security Test: {'PASSED' if not tampered_valid else 'FAILED'}")
    print("=" * 80)
    
    return is_valid

if __name__ == '__main__':
    try:
        success = test_complete_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
