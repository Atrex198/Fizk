#!/usr/bin/env python3
"""
Test script for real ZKP proof verification
"""

import torch
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from zkp_proof_generator import ZKPProofGenerator

def test_proof_verification():
    print("🔄 Testing real ZKP proof verification...")
    
    # Create sample model weights
    model_weights = {
        'net.0.weight': torch.randn(2, 3),
        'net.0.bias': torch.randn(2),
        'net.1.weight': torch.randn(1, 2),
        'net.1.bias': torch.randn(1)
    }
    
    # Create ZKP generator
    zkp_generator = ZKPProofGenerator()
    
    try:
        # Generate proof
        print("🔐 Generating proof...")
        proof_result = zkp_generator.generate_simple_training_proof(
            model_weights=model_weights,
            training_loss=0.5,
            client_id="test_client_verification"
        )
        
        if not proof_result.get('proof_valid', False):
            print("❌ Failed to generate valid proof")
            return False
            
        proof_data = proof_result.get('proof_data', {})
        print(f"✅ Proof generated with hash: {proof_result.get('proof_hash', 'unknown')[:16]}...")
        
        # Test verification
        print("🔍 Verifying proof...")
        verification_result = zkp_generator.verify_proof(proof_data)
        
        if verification_result:
            print("✅ Proof verification PASSED!")
            return True
        else:
            print("❌ Proof verification FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Proof verification test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_proof_verification()
    if success:
        print("\n🎉 Real ZKP proof verification test PASSED!")
        exit(0)
    else:
        print("\n💥 Real ZKP proof verification test FAILED!")
        exit(1)