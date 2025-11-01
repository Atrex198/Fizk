#!/usr/bin/env python3
"""
Groth16 Simple Example
======================

Minimal working example of Groth16 protocol.

Run: python3 example_simple.py
"""

import sys
import logging
from pathlib import Path

# Add groth16 to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from groth16 import (
    Groth16Protocol,
    get_default_config,
    setup_logging
)

def main():
    """Run simple Groth16 example"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    print("\n" + "="*60)
    print("Groth16 Simple Example")
    print("="*60 + "\n")
    
    # Step 1: Configuration
    print("📋 Step 1: Configuration")
    config = get_default_config(
        num_model_params=10,  # Small model for quick demo
        num_clients=2
    )
    print(f"   Model parameters: {config['num_model_params']}")
    print(f"   Clients: {config['num_clients']}")
    print(f"   Security level: {config['security_level']} bits")
    
    # Step 2: Initialize protocol
    print("\n🔧 Step 2: Initialize Protocol")
    protocol = Groth16Protocol(config)
    info = protocol.get_protocol_info()
    print(f"   Protocol: {info['protocol_name']}")
    print(f"   Curve: {info['curve']}")
    
    # Step 3: Trusted setup
    print("\n🔑 Step 3: Trusted Setup")
    print("   ⚠️  Using DEVELOPMENT setup (insecure)")
    print("   ⚠️  Production requires secure MPC ceremony")
    setup_artifacts = protocol.setup()
    print(f"   ✅ Setup complete: {setup_artifacts['constraint_count']} constraints")
    print(f"   ✅ Setup time: {setup_artifacts['setup_time']:.2f}s")
    
    # Step 4: Generate proof
    print("\n🔐 Step 4: Generate Proof")
    
    statement = {
        'model_architecture': 'SimpleModel',
        'initial_weights_commitment': '0x1234567890abcdef',
        'final_weights_commitment': '0xfedcba0987654321',
        'training_config': {'lr': 0.01, 'epochs': 1}
    }
    
    witness = {
        'model_weights': {
            'weights': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        },
        'training_history': [{'loss': 0.5}]
    }
    
    print(f"   Generating proof for client_0...")
    proof = protocol.generate_proof(
        statement=statement,
        witness=witness,
        round_number=1,
        client_id='client_0'
    )
    
    print(f"   ✅ Proof generated in {proof.metadata.generation_time:.3f}s")
    print(f"   ✅ Proof size: {proof.metadata.proof_size_bytes} bytes")
    print(f"   ✅ Constraints: {proof.metadata.constraint_count}")
    
    # Step 5: Verify proof
    print("\n🔍 Step 5: Verify Proof")
    result = protocol.verify_proof(proof, statement)
    
    if result.is_valid:
        print(f"   ✅ Proof is VALID")
        print(f"   ✅ Verified in {result.verification_time:.3f}s")
        print(f"   ✅ Verification complexity: {result.verification_complexity}")
    else:
        print(f"   ❌ Proof is INVALID")
        print(f"   ❌ Error: {result.error_message}")
    
    # Step 6: Protocol information
    print("\n📊 Step 6: Protocol Information")
    print(f"   Protocol: {info['protocol_name']}")
    print(f"   Proof size: {info['typical_proof_size_kb']} KB")
    print(f"   Verification time: {info['typical_verification_time_ms']} ms")
    print(f"   Supports IVC: {info['supports_ivc']}")
    print(f"   Supports aggregation: {info['supports_aggregation']}")
    print(f"   Trusted setup required: {info['trusted_setup_required']}")
    print(f"   Quantum resistant: {info['quantum_resistant']}")
    
    print("\n" + "="*60)
    print("✅ Example Complete")
    print("="*60 + "\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
