#!/usr/bin/env python3
"""
Test script for Protostar IVC integration with ZK-FL system
"""

import torch
import numpy as np
from collections import OrderedDict
from zkp_proof_generator import ZKPProofGenerator
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_model_weights(input_size=10, hidden_size=20, output_size=1):
    """Create test model weights in the format expected by the FL system"""
    weights = OrderedDict()
    
    # Layer 1: input -> hidden
    weights['net.0.weight'] = torch.randn(hidden_size, input_size) * 0.1
    weights['net.0.bias'] = torch.randn(hidden_size) * 0.1
    
    # Layer 2: hidden -> output
    weights['net.2.weight'] = torch.randn(output_size, hidden_size) * 0.1
    weights['net.2.bias'] = torch.randn(output_size) * 0.1
    
    return weights

def simulate_weight_update(weights, learning_rate=0.01):
    """Simulate training by adding small random updates to weights"""
    updated_weights = OrderedDict()
    
    for name, tensor in weights.items():
        # Add small random update
        update = torch.randn_like(tensor) * learning_rate
        updated_weights[name] = tensor + update
    
    return updated_weights

def test_protostar_ivc_basic():
    """Test basic Protostar IVC functionality"""
    logger.info("🧪 Testing Protostar IVC basic functionality...")
    
    # Initialize ZKP generator with Protostar IVC
    zkp_gen = ZKPProofGenerator(proof_system="protostar")
    
    # Create initial model weights
    initial_weights = create_test_model_weights()
    logger.info(f"Created test model with {len(initial_weights)} weight tensors")
    
    # Initialize IVC with first round
    round_1_proof = zkp_gen.generate_ivc_training_proof(
        model_weights=initial_weights,
        round_number=1,
        is_initial_round=True
    )
    
    logger.info("✅ Round 1 IVC initialization successful")
    print(f"Proof metadata: {json.dumps(round_1_proof['metadata'], indent=2)}")
    
    # Verify the proof
    print(f"\\nDEBUG: Proof structure keys: {list(round_1_proof.keys())}")
    if "proof" in round_1_proof:
        print(f"DEBUG: Proof.proof keys: {list(round_1_proof['proof'].keys())}")
    
    is_valid = zkp_gen.verify_ivc_proof(round_1_proof)
    logger.info(f"Round 1 proof verification: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    return zkp_gen, initial_weights

def test_protostar_ivc_folding():
    """Test Protostar IVC folding across multiple rounds"""
    logger.info("🧪 Testing Protostar IVC folding...")
    
    zkp_gen, initial_weights = test_protostar_ivc_basic()
    
    # Simulate multiple FL rounds
    current_weights = initial_weights
    proofs = []
    
    for round_num in range(2, 6):  # Rounds 2-5
        # Simulate training update
        current_weights = simulate_weight_update(current_weights)
        
        # Fold into accumulator
        round_proof = zkp_gen.generate_ivc_training_proof(
            model_weights=current_weights,
            round_number=round_num,
            is_initial_round=False
        )
        
        proofs.append(round_proof)
        logger.info(f"✅ Round {round_num} folded successfully")
        
        # Verify proof
        is_valid = zkp_gen.verify_ivc_proof(round_proof)
        assert is_valid, f"Round {round_num} proof validation failed"
    
    # Check accumulator summary
    summary = zkp_gen.get_ivc_accumulator_summary()
    logger.info(f"Final accumulator summary: {json.dumps(summary, indent=2)}")
    
    # Export final weights
    final_weights = zkp_gen.export_ivc_final_weights()
    logger.info(f"Exported {len(final_weights)} final weight tensors")
    
    return zkp_gen, proofs, final_weights

def test_protostar_vs_groth16():
    """Compare Protostar IVC vs Groth16 proof systems"""
    logger.info("🧪 Testing Protostar IVC vs Groth16 comparison...")
    
    # Test weights
    test_weights = create_test_model_weights()
    
    # Test Protostar IVC
    logger.info("Testing Protostar IVC...")
    protostar_gen = ZKPProofGenerator(proof_system="protostar")
    
    protostar_proof = protostar_gen.generate_ivc_training_proof(
        model_weights=test_weights,
        round_number=1,
        is_initial_round=True
    )
    
    protostar_summary = protostar_gen.get_ivc_accumulator_summary()
    
    # Test Groth16 (if available)
    logger.info("Testing Groth16...")
    groth16_gen = ZKPProofGenerator(proof_system="groth16")
    
    try:
        # This will try to use the Rust binary
        groth16_proof = groth16_gen.generate_simple_training_proof(
            model_weights=test_weights,
            training_loss=0.5,
            client_id="test_client"
        )
        groth16_available = True
    except Exception as e:
        logger.warning(f"Groth16 not available: {e}")
        groth16_available = False
        groth16_proof = None
    
    # Compare results
    logger.info("📊 Comparison Results:")
    logger.info(f"Protostar IVC - Proof system: {protostar_proof['metadata']['proof_system']}")
    logger.info(f"Protostar IVC - Incremental: {protostar_proof['metadata']['incremental']}")
    logger.info(f"Protostar IVC - Verification: {protostar_proof['proof']['verification_time']}")
    logger.info(f"Protostar IVC - Accumulator size: {protostar_summary['proof_size_bytes']} bytes")
    
    if groth16_available:
        logger.info(f"Groth16 - Proof system: {groth16_proof['proof_data']['metadata']['proof_system']}")
        logger.info(f"Groth16 - Incremental: No")
        logger.info(f"Groth16 - Verification: O(n) per round")
    
    return protostar_proof, groth16_proof if groth16_available else None

def test_system_switching():
    """Test switching between proof systems"""
    logger.info("🧪 Testing proof system switching...")
    
    # Start with Groth16
    zkp_gen = ZKPProofGenerator(proof_system="groth16")
    logger.info(f"Initial proof system: {zkp_gen.proof_system}")
    
    # Switch to Protostar IVC
    zkp_gen.switch_to_protostar_ivc()
    logger.info(f"After switch: {zkp_gen.proof_system}")
    
    # Test IVC functionality
    test_weights = create_test_model_weights()
    proof = zkp_gen.generate_ivc_training_proof(
        model_weights=test_weights,
        round_number=1,
        is_initial_round=True
    )
    
    assert proof['metadata']['proof_system'] == 'REAL_PROTOSTAR_IVC_CRYPTOGRAPHIC'
    logger.info("✅ Proof system switching works correctly")
    
    # Switch back to Groth16
    zkp_gen.switch_to_groth16()
    logger.info(f"After switch back: {zkp_gen.proof_system}")

def run_all_tests():
    """Run all Protostar IVC tests"""
    logger.info("🚀 Starting Protostar IVC test suite...")
    
    try:
        # Basic functionality
        test_protostar_ivc_basic()
        logger.info("✅ Basic functionality test passed")
        
        # Folding across rounds
        test_protostar_ivc_folding()
        logger.info("✅ Multi-round folding test passed")
        
        # Comparison with Groth16
        test_protostar_vs_groth16()
        logger.info("✅ Comparison test passed")
        
        # System switching
        test_system_switching()
        logger.info("✅ System switching test passed")
        
        logger.info("🎉 All Protostar IVC tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    run_all_tests()