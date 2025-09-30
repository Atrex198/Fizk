#!/usr/bin/env python3
"""
Test script for Protogalaxy aggregation with real ZKP proofs
"""

import torch
import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from zkp_proof_generator import ZKPProofGenerator

def test_protogalaxy_aggregation():
    print("🔄 Testing Protogalaxy aggregation with real ZKP proofs...")
    
    # Create ZKP generator
    zkp_generator = ZKPProofGenerator()
    
    # Generate multiple real proofs
    proofs = []
    client_metadata = []
    
    try:
        for i in range(3):  # Test with 3 clients
            print(f"🔐 Generating proof for client_{i+1}...")
            
            # Create different model weights for each client
            model_weights = {
                'net.0.weight': torch.randn(2, 3) + i * 0.1,
                'net.0.bias': torch.randn(2) + i * 0.05,
                'net.1.weight': torch.randn(1, 2) + i * 0.1,
                'net.1.bias': torch.randn(1) + i * 0.05
            }
            
            proof_result = zkp_generator.generate_simple_training_proof(
                model_weights=model_weights,
                training_loss=0.5 - i * 0.1,  # Different losses
                client_id=f"client_{i+1}"
            )
            
            if not proof_result.get('proof_valid', False):
                print(f"❌ Failed to generate valid proof for client_{i+1}")
                return False
                
            proofs.append(proof_result.get('proof_data', {}))
            client_metadata.append({
                "client_id": f"client_{i+1}",
                "training_loss": 0.5 - i * 0.1,
                "proof_hash": proof_result.get('proof_hash', 'unknown')
            })
            
            print(f"✅ Client_{i+1} proof: {proof_result.get('proof_hash', 'unknown')[:16]}...")
        
        # Create aggregation input
        aggregation_input = {
            "proofs": proofs,
            "client_metadata": client_metadata,
            "round_number": 1
        }
        
        # Save to file for Rust aggregation
        with open('test_aggregation_input.json', 'w') as f:
            json.dump(aggregation_input, f, indent=2)
        
        print("🔗 Calling Protogalaxy aggregation...")
        
        # Call Rust binary for aggregation
        import subprocess
        result = subprocess.run([
            './zkp-fl/target/debug/zkp-fl',
            'aggregate-proofs',
            '--input', 'test_aggregation_input.json',
            '--output', 'test_aggregation_output.json'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Protogalaxy aggregation completed successfully!")
            
            # Read and verify aggregated proof
            with open('test_aggregation_output.json', 'r') as f:
                aggregated_proof = json.load(f)
            
            aggregation_info = aggregated_proof.get('aggregated_proof', {})
            metadata = aggregated_proof.get('aggregation_metadata', {})
            
            print(f"🔗 Aggregated {metadata.get('total_proofs', 0)} proofs")
            print(f"📊 Cross-terms: {aggregation_info.get('cross_terms', [])[:2]}...")
            print(f"🔒 Aggregation method: {aggregation_info.get('aggregation_method', 'unknown')}")
            
            return True
        else:
            print(f"❌ Protogalaxy aggregation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Protogalaxy aggregation test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_protogalaxy_aggregation()
    if success:
        print("\n🎉 Protogalaxy aggregation test PASSED!")
        exit(0)
    else:
        print("\n💥 Protogalaxy aggregation test FAILED!")
        exit(1)