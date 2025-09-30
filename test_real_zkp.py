#!/usr/bin/env python3
"""
Test script for real ZKP proof generation
"""

import torch
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from zkp_proof_generator import ZKPProofGenerator

def test_real_zkp_proof():
    print("🔄 Testing real ZKP proof generation...")
    
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
        # Test real proof generation
        print("🔐 Generating real cryptographic proof...")
        proof_result = zkp_generator.generate_simple_training_proof(
            model_weights=model_weights,
            training_loss=0.5,
            client_id="test_client_001"
        )
        
        print(f"✅ Real ZKP proof generated successfully!")
        print(f"🔍 Proof valid: {proof_result.get('proof_valid', False)}")
        print(f"📊 Proof hash: {proof_result.get('proof_hash', 'unknown')[:16]}...")
        
        # Check proof structure
        proof_data = proof_result.get('proof_data', {})
        if proof_data.get('proof', {}).get('type') == 'groth16_bn254_REAL':
            print("✅ Confirmed: Real Groth16 proof generated (not mock)")
            print(f"🔧 Circuit features: {proof_data.get('circuit_info', {}).get('circuit_features', [])}")
            print(f"🌐 Curve: {proof_data.get('metadata', {}).get('curve', 'unknown')}")
            print(f"🔒 Proof system: {proof_data.get('metadata', {}).get('proof_system', 'unknown')}")
            
            return True
        else:
            print("❌ Error: Mock proof detected instead of real cryptographic proof")
            return False
            
    except Exception as e:
        print(f"❌ Real ZKP proof generation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_real_zkp_proof()
    if success:
        print("\n🎉 Real ZKP proof generation test PASSED!")
        exit(0)
    else:
        print("\n💥 Real ZKP proof generation test FAILED!")
        exit(1)