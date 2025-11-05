#!/usr/bin/env python3
"""
Test R1CS Verification Implementation
=====================================

Tests the enhanced Protostar verification with actual R1CS constraint checking.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness
import numpy as np
import hashlib
import time

def create_hash(data):
    """Create SHA256 hash for data commitment"""
    return hashlib.sha256(str(data).encode()).hexdigest()

def test_r1cs_verification():
    """Test the enhanced R1CS verification implementation"""
    print("🧪 Testing R1CS Verification Implementation")
    print("=" * 50)
    
    # Create a simple test dataset
    print("📊 Creating test dataset...")
    X_data = np.random.rand(50, 4).astype(np.float32)
    y_data = np.random.randint(0, 2, 50)
    
    # Create simple weight matrices 
    print("🧮 Creating weight matrices...")
    initial_weights = {
        'layer1.weight': np.random.rand(64, 4).astype(np.float32),
        'layer1.bias': np.random.rand(64).astype(np.float32),
        'layer2.weight': np.random.rand(2, 64).astype(np.float32),
        'layer2.bias': np.random.rand(2).astype(np.float32)
    }
    
    # Simulate training by slightly modifying weights
    final_weights = {
        'layer1.weight': initial_weights['layer1.weight'] + 0.01 * np.random.rand(64, 4).astype(np.float32),
        'layer1.bias': initial_weights['layer1.bias'] + 0.01 * np.random.rand(64).astype(np.float32),
        'layer2.weight': initial_weights['layer2.weight'] + 0.01 * np.random.rand(2, 64).astype(np.float32),
        'layer2.bias': initial_weights['layer2.bias'] + 0.01 * np.random.rand(2).astype(np.float32)
    }
    
    # Create training statement (public inputs)
    print("📋 Creating training statement...")
    statement = TrainingStatement(
        model_architecture='FederatedNN',
        initial_weights_commitment=create_hash(initial_weights),
        final_weights_commitment=create_hash(final_weights),
        dataset_commitment=create_hash(X_data.tobytes()),
        local_epochs=5,
        batch_size=32,
        learning_rate=0.001,
        claimed_accuracy=0.85,
        claimed_loss=0.25,
        sample_count=50,
        round_number=0,
        client_id=0,
        timestamp=time.time()
    )
    
    # Create training witness (private inputs)
    print("🔐 Creating training witness...")
    witness = TrainingWitness(
        initial_weights=initial_weights,
        final_weights=final_weights,
        dataset_samples=X_data,
        dataset_labels=y_data
    )
    
    print('✅ Created training statement and witness')
    
    # Initialize ZKP system
    print("🔧 Initializing ZKP system...")
    zkp = ProductionProtostar(security_level=128)
    print("⚙️  Setting up trusted parameters...")
    zkp.setup(statement)
    print('✅ ZKP setup complete')
    
    # Generate proof with R1CS constraints
    print("🔍 Generating proof with R1CS constraints...")
    proof_start = time.time()
    proof = zkp.generate_proof(statement, witness)
    proof_time = time.time() - proof_start
    print(f'✅ Proof generated in {proof_time:.2f}s')
    
    # Check if constraint matrices were stored
    if hasattr(zkp, '_last_constraints') and zkp._last_constraints:
        print(f"🧮 R1CS constraints stored: {len(zkp._last_constraints)} constraints")
        print(f"🧮 Witness values stored: {len(zkp._last_witness_values)} values")
    else:
        print("⚠️  No R1CS constraints stored")
    
    # Verify proof with enhanced R1CS verification
    print("🔍 Verifying proof with enhanced R1CS verification...")
    verify_start = time.time()
    is_valid = zkp.verify_proof(statement, proof)  # Correct order: statement, proof
    verify_time = time.time() - verify_start
    
    # Results
    print("=" * 50)
    print("🎯 VERIFICATION RESULTS:")
    print(f"✅ Proof Valid: {is_valid}")
    print(f"⏱️  Verification Time: {verify_time:.2f}s")
    print(f"📏 Proof Size: {proof.get_size_bytes()} bytes")
    
    if is_valid:
        print("🎉 SUCCESS: Enhanced R1CS verification passed!")
        print("   - R1CS constraint satisfaction verified")
        print("   - Error accumulation bounds checked") 
        print("   - Polynomial opening proofs validated")
        print("   - Relaxed R1CS equation verified")
    else:
        print("❌ FAILURE: Enhanced R1CS verification failed!")
    
    return is_valid

if __name__ == "__main__":
    try:
        success = test_r1cs_verification()
        exit_code = 0 if success else 1
        print(f"\n🏁 Test completed with exit code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)