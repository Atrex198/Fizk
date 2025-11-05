#!/usr/bin/env python3
"""
Test script to verify that pairing verification is now enabled and working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.base import TrainingStatement, TrainingWitness
import numpy as np
import time

def test_pairing_verification_enabled():
    """Test that pairing verification is now enabled and functional"""
    
    print("🧪 Testing Pairing Verification Status...")
    print("=" * 60)
    
    try:
        # Initialize protocol
        protocol = ProductionProtostar(security_level=128)
        setup_params = protocol.setup()
        print(f"✅ Protocol initialized: {setup_params['security_level']}-bit security")
        
        # Create test statement and witness
        statement = TrainingStatement(
            model_architecture="TestNN",
            initial_weights_commitment="test_initial",
            final_weights_commitment="test_final", 
            dataset_commitment="test_dataset",
            local_epochs=1,
            batch_size=32,
            learning_rate=0.01,
            claimed_accuracy=0.85,
            claimed_loss=0.3,
            sample_count=100,
            round_number=1,
            client_id="test_client",
            timestamp=time.time()
        )
        
        witness = TrainingWitness(
            initial_weights={
                'layer1': np.random.randn(10, 5).astype(np.float32),
                'layer2': np.random.randn(5, 2).astype(np.float32)
            },
            final_weights={
                'layer1': np.random.randn(10, 5).astype(np.float32),
                'layer2': np.random.randn(5, 2).astype(np.float32)
            },
            dataset_samples=np.random.randn(100, 10).astype(np.float32),
            dataset_labels=np.random.randint(0, 2, 100)
        )
        
        print("✅ Test data created")
        
        # Generate proof
        print("🔧 Generating proof...")
        proof = protocol.generate_proof(statement, witness)
        print(f"✅ Proof generated: {proof.get_size_bytes()} bytes")
        
        # Verify proof (this should now use REAL pairing verification)
        print("🔍 Verifying proof with pairing checks...")
        result = protocol.verify_proof(statement, proof)
        
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS:")
        print("=" * 60)
        print(f"✅ Valid: {result.is_valid}")
        print(f"⏱️  Time: {result.verification_time:.4f}s")
        print(f"📝 Message: {result.message}")
        
        if result.details and 'pairing_checks' in result.details:
            pairing_details = result.details['pairing_checks']
            print(f"\n🔐 PAIRING VERIFICATION DETAILS:")
            print(f"   Status: {pairing_details.get('pairing_verification_status', 'unknown')}")
            print(f"   Operations Valid: {pairing_details.get('pairing_operations_valid', False)}")
            print(f"   Test Passed: {pairing_details.get('pairing_test_passed', False)}")
            print(f"   Method: {pairing_details.get('verification_method', 'unknown')}")
            
            if pairing_details.get('pairing_verification_status') == 'enabled_production_grade':
                print("🎉 SUCCESS: Pairing verification is ENABLED and WORKING!")
                return True
            else:
                print("❌ FAILURE: Pairing verification still disabled")
                return False
        else:
            print("❌ FAILURE: No pairing verification details found")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pairing_verification_enabled()
    sys.exit(0 if success else 1)