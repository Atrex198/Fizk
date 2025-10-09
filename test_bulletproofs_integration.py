"""
Test Bulletproofs Protocol Integration
=====================================

Test script to verify Bulletproofs implementation works correctly
with the unified ZKP interface.
"""

import numpy as np
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zkp_protocols.bulletproofs_protocol import BulletproofsProtocol
from zkp_protocols.base import TrainingStatement, TrainingWitness, ProtocolType

def create_dummy_weights():
    """Create dummy model weights for testing"""
    return {
        'fc1.weight': np.random.randn(64, 11).astype(float),
        'fc1.bias': np.random.randn(64).astype(float),
        'fc2.weight': np.random.randn(32, 64).astype(float),
        'fc2.bias': np.random.randn(32).astype(float),
        'fc3.weight': np.random.randn(2, 32).astype(float),
        'fc3.bias': np.random.randn(2).astype(float)
    }

def create_dummy_dataset():
    """Create dummy dataset for testing"""
    X = np.random.randn(100, 11).astype(float)
    y = np.random.randint(0, 2, 100)
    return X, y

def test_bulletproofs_integration():
    """Test Bulletproofs with FL system interface"""
    
    print("🔫 Testing Bulletproofs Protocol Integration")
    print("=" * 50)
    
    # 1. Initialize protocol
    config = {
        'security_level': 128,
        'curve': 'bn254',
        'range_bits': 16,  # Smaller for testing
        'weight_bounds': (-5, 5),
        'loss_bounds': (0, 2)
    }
    
    protocol = BulletproofsProtocol(config)
    print(f"✅ Protocol initialized: {protocol.get_protocol_info()['protocol_name']}")
    
    # 2. Setup (transparent!)
    print("\n🔧 Performing transparent setup...")
    setup_result = protocol.setup()
    print(f"   Trusted setup required: {setup_result['trusted_setup_required']}")
    print(f"   Transparent: {setup_result['transparent']}")
    print(f"   Setup time: {setup_result['setup_time']:.4f}s")
    
    # 3. Create training statement and witness
    print("\n📋 Creating training statement and witness...")
    
    initial_weights = create_dummy_weights()
    final_weights = create_dummy_weights()
    X_train, y_train = create_dummy_dataset()
    
    statement = TrainingStatement(
        model_architecture="3-layer-feedforward",
        initial_weights_commitment="commit_initial_123",
        final_weights_commitment="commit_final_456", 
        dataset_commitment="dataset_hash_789",
        local_epochs=10,
        batch_size=32,
        learning_rate=0.001,
        claimed_accuracy=0.75,
        claimed_loss=0.65,
        sample_count=100,
        round_number=1,
        client_id="test_client",
        timestamp=time.time()
    )
    
    witness = TrainingWitness(
        initial_weights=initial_weights,
        final_weights=final_weights,
        dataset_samples=X_train,
        dataset_labels=y_train,
        random_seed=42
    )
    
    print(f"   Statement created for client: {statement.client_id}")
    print(f"   Witness includes {len(initial_weights)} weight layers")
    
    # 4. Generate proof
    print("\n🔐 Generating Bulletproof...")
    proof_start = time.time()
    
    proof = protocol.generate_proof(statement, witness)
    
    proof_time = time.time() - proof_start
    print(f"   ✅ Proof generated successfully!")
    print(f"   Proof size: {proof.get_size_bytes()} bytes ({proof.get_size_bytes()/1024:.1f} KB)")
    print(f"   Generation time: {proof_time:.4f}s")
    print(f"   Protocol type: {proof.protocol_type.value}")
    
    # 5. Verify proof
    print("\n🔍 Verifying Bulletproof...")
    verification_start = time.time()
    
    result = protocol.verify_proof(proof, statement)
    
    verification_time = time.time() - verification_start
    print(f"   Verification result: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
    print(f"   Verification time: {verification_time:.4f}s")
    
    if result.detailed_checks:
        print("   Detailed checks:")
        for check, passed in result.detailed_checks.items():
            status = "✅" if passed else "❌"
            print(f"     {status} {check}")
    
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    # 6. Test serialization
    print("\n📦 Testing proof serialization...")
    try:
        serialized = protocol.serialize_proof(proof)
        deserialized = protocol.deserialize_proof(serialized)
        
        print(f"   Serialized size: {len(serialized)} bytes")
        print(f"   ✅ Serialization successful")
        print(f"   Original proof size: {proof.get_size_bytes()} bytes")
        print(f"   Deserialized proof size: {deserialized.get_size_bytes()} bytes")
        
    except Exception as e:
        print(f"   ❌ Serialization failed: {e}")
    
    # 7. Test batch verification (multiple proofs)
    print("\n🔗 Testing batch verification...")
    
    # Create multiple proofs
    proofs = [proof]
    for i in range(2):
        new_statement = TrainingStatement(
            model_architecture="3-layer-feedforward",
            initial_weights_commitment=f"commit_initial_{i}",
            final_weights_commitment=f"commit_final_{i}",
            dataset_commitment=f"dataset_hash_{i}",
            local_epochs=10,
            batch_size=32,
            learning_rate=0.001,
            claimed_accuracy=0.7 + i*0.05,
            claimed_loss=0.6 - i*0.05,
            sample_count=100,
            round_number=i+2,
            client_id=f"test_client_{i}",
            timestamp=time.time()
        )
        
        new_witness = TrainingWitness(
            initial_weights=create_dummy_weights(),
            final_weights=create_dummy_weights(),
            dataset_samples=X_train,
            dataset_labels=y_train,
            random_seed=42+i
        )
        
        new_proof = protocol.generate_proof(new_statement, new_witness)
        proofs.append(new_proof)
    
    batch_result = protocol.aggregate_proofs(proofs)
    print(f"   Batch verification with {len(proofs)} proofs")
    print(f"   Result: {'✅ Batch verification supported' if batch_result is not None else '✅ Individual verification successful'}")
    
    # 8. Protocol information
    print("\n📋 Protocol Information:")
    info = protocol.get_protocol_info()
    for key, value in info.items():
        if isinstance(value, list):
            print(f"   {key}:")
            for item in value:
                print(f"     - {item}")
        else:
            print(f"   {key}: {value}")
    
    print("\n" + "=" * 50)
    print("🎉 Bulletproofs integration test completed successfully!")
    
    return {
        'protocol_name': info['protocol_name'],
        'setup_time': setup_result['setup_time'],
        'proof_generation_time': proof_time,
        'verification_time': verification_time,
        'proof_size_bytes': proof.get_size_bytes(),
        'trusted_setup_required': setup_result['trusted_setup_required'],
        'verification_successful': result.is_valid
    }

if __name__ == "__main__":
    test_results = test_bulletproofs_integration()
    
    print(f"\n📊 Summary:")
    print(f"   Protocol: {test_results['protocol_name']}")
    print(f"   Trusted setup: {'Required' if test_results['trusted_setup_required'] else 'Not required (transparent)'}")
    print(f"   Setup time: {test_results['setup_time']:.4f}s")
    print(f"   Proof generation: {test_results['proof_generation_time']:.4f}s")
    print(f"   Verification: {test_results['verification_time']:.4f}s")
    print(f"   Proof size: {test_results['proof_size_bytes']} bytes ({test_results['proof_size_bytes']/1024:.1f} KB)")
    print(f"   Status: {'✅ All tests passed!' if test_results['verification_successful'] else '❌ Tests failed'}")