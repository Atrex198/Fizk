#!/usr/bin/env python3
"""
Groth16 Implementation Test
============================

Comprehensive test to verify all components work correctly.

Run: python3 test_groth16.py
"""

import sys
import logging
from pathlib import Path

# Add groth16 to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from groth16 import (
    R1CS,
    R1CSBuilder,
    Groth16TrustedSetup,
    Groth16Prover,
    Groth16Verifier,
    FLCircuitBuilder,
    Groth16Protocol,
    get_default_config,
    Groth16Stats
)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_r1cs():
    """Test R1CS constraint system"""
    logger.info("\n" + "="*60)
    logger.info("Test 1: R1CS Constraint System")
    logger.info("="*60)
    
    # Create R1CS
    r1cs = R1CS(num_variables=10)
    
    # Test: 2 * 3 = 6
    r1cs.set_witness(0, 1)  # constant
    r1cs.set_witness(1, 2, "a")
    r1cs.set_witness(2, 3, "b")
    r1cs.set_witness(3, 6, "c")
    
    r1cs.add_multiplication_constraint(1, 2, 3)
    
    # Verify
    assert r1cs.verify_constraint_satisfaction(), "Constraint not satisfied!"
    
    logger.info("✅ Test 1 PASSED: R1CS working correctly")
    return True


def test_fl_circuit_builder():
    """Test FL circuit builder"""
    logger.info("\n" + "="*60)
    logger.info("Test 2: FL Circuit Builder")
    logger.info("="*60)
    
    builder = FLCircuitBuilder()
    
    # Test weight encoding
    weight = 0.5
    encoded = builder.encode_weight(weight)
    decoded = builder.decode_weight(encoded)
    
    assert abs(decoded - weight) < 0.001, f"Weight encoding failed: {weight} != {decoded}"
    logger.info(f"✅ Weight encoding: {weight} -> {encoded} -> {decoded}")
    
    # Test weight commitment
    weights = {'w1': 0.1, 'w2': 0.2, 'w3': 0.3}
    commitment = builder.compute_weight_commitment(weights)
    assert len(commitment) == 64, "Commitment should be 64-char hex"
    logger.info(f"✅ Weight commitment: {commitment[:16]}...")
    
    logger.info("✅ Test 2 PASSED: FL Circuit Builder working")
    return True


def test_setup_prover_verifier():
    """Test trusted setup, prover, and verifier"""
    logger.info("\n" + "="*60)
    logger.info("Test 3: Setup + Prover + Verifier")
    logger.info("="*60)
    
    # Build simple R1CS
    builder = R1CSBuilder()
    r1cs = builder.initialize(num_variables=100)
    
    # Add some constraints
    for i in range(10):
        a = builder.allocate_variable(f"a_{i}")
        b = builder.allocate_variable(f"b_{i}")
        c = builder.allocate_variable(f"c_{i}")
        r1cs.add_multiplication_constraint(a, b, c)
        
        # Set witness
        r1cs.set_witness(a, 2)
        r1cs.set_witness(b, 3)
        r1cs.set_witness(c, 6)
    
    r1cs = builder.finalize()
    logger.info(f"✅ Built R1CS: {r1cs.num_constraints} constraints")
    
    # Trusted setup
    logger.info("⏳ Running trusted setup...")
    setup = Groth16TrustedSetup(r1cs)
    pk, vk = setup.generate_keys()
    logger.info(f"✅ Setup complete")
    
    # Generate proof
    logger.info("⏳ Generating proof...")
    prover = Groth16Prover(pk, r1cs, setup)  # Pass setup for QAP access
    witness = r1cs.get_witness_vector()
    # No public inputs in this simple test (only the constant 1 at index 0)
    public_inputs = []
    
    start = time.time()
    proof = prover.generate_proof(witness, public_inputs)
    proof_time = time.time() - start
    logger.info(f"✅ Proof generated in {proof_time:.3f}s")
    
    # Verify proof
    logger.info("⏳ Verifying proof...")
    verifier = Groth16Verifier(vk)
    
    start = time.time()
    is_valid = verifier.verify_proof(proof, public_inputs)
    verify_time = time.time() - start
    
    assert is_valid, "Proof verification failed!"
    logger.info(f"✅ Proof VALID (verified in {verify_time:.3f}s)")
    
    logger.info("✅ Test 3 PASSED: Setup/Prover/Verifier working")
    return True


def test_protocol_interface():
    """Test Groth16Protocol (IZKPProtocol interface)"""
    logger.info("\n" + "="*60)
    logger.info("Test 4: Protocol Interface")
    logger.info("="*60)
    
    # Initialize protocol
    config = get_default_config(num_model_params=10, num_clients=2)
    protocol = Groth16Protocol(config)
    
    # Get protocol info
    info = protocol.get_protocol_info()
    logger.info(f"✅ Protocol: {info['protocol_name']}")
    logger.info(f"   Proof size: {info['typical_proof_size_kb']} KB")
    logger.info(f"   Verification: {info['typical_verification_time_ms']} ms")
    
    # Setup
    logger.info("⏳ Running protocol setup...")
    setup_result = protocol.setup()
    logger.info(f"✅ Setup: {setup_result['constraint_count']} constraints")
    
    # Generate proof
    logger.info("⏳ Generating proof via protocol interface...")
    # Note: Not including commitments since FL circuit doesn't allocate public inputs yet
    statement = {
        'model_architecture': 'TestModel',
        'training_config': {}
    }
    
    witness = {
        'model_weights': {
            'layer1': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        }
    }
    
    proof_obj = protocol.generate_proof(
        statement=statement,
        witness=witness,
        round_number=1,
        client_id='test_client'
    )
    
    logger.info(f"✅ Proof generated: {proof_obj.metadata.proof_size_bytes} bytes")
    
    # Verify proof
    logger.info("⏳ Verifying proof via protocol interface...")
    result = protocol.verify_proof(proof_obj, statement)
    
    assert result.is_valid, "Protocol verification failed!"
    logger.info(f"✅ Proof VALID (protocol interface)")
    
    # Test serialization
    proof_bytes = protocol.serialize_proof(proof_obj)
    logger.info(f"✅ Serialized: {len(proof_bytes)} bytes")
    
    # Test aggregation (should return None)
    agg_result = protocol.aggregate_proofs([proof_obj])
    assert agg_result is None, "Groth16 should not support aggregation"
    logger.info(f"✅ Aggregation correctly returns None")
    
    logger.info("✅ Test 4 PASSED: Protocol interface working")
    return True


def test_performance():
    """Test performance metrics"""
    logger.info("\n" + "="*60)
    logger.info("Test 5: Performance Metrics")
    logger.info("="*60)
    
    stats = Groth16Stats()
    
    # Initialize small protocol
    config = get_default_config(num_model_params=20, num_clients=2)
    protocol = Groth16Protocol(config)
    protocol.setup()
    
    # Generate multiple proofs
    num_proofs = 3
    logger.info(f"⏳ Generating {num_proofs} proofs...")
    
    # Note: Not including commitments since FL circuit doesn't allocate public inputs yet
    statement = {
        'model_architecture': 'PerfTest',
        'training_config': {}
    }
    
    witness = {
        'model_weights': {
            'weights': [0.1] * 20
        }
    }
    
    for i in range(num_proofs):
        start = time.time()
        proof = protocol.generate_proof(
            statement=statement,
            witness=witness,
            round_number=i+1,
            client_id=f'client_{i}'
        )
        elapsed = time.time() - start
        stats.record_proof(elapsed, proof.metadata.constraint_count)
        
        # Verify
        start = time.time()
        result = protocol.verify_proof(proof, statement)
        elapsed = time.time() - start
        stats.record_verification(elapsed)
        
        assert result.is_valid
    
    # Print summary
    stats.print_summary()
    
    logger.info("✅ Test 5 PASSED: Performance metrics collected")
    return True


def run_all_tests():
    """Run all tests"""
    logger.info("\n" + "="*70)
    logger.info("GROTH16 IMPLEMENTATION TEST SUITE")
    logger.info("="*70)
    
    tests = [
        ("R1CS Constraint System", test_r1cs),
        ("FL Circuit Builder", test_fl_circuit_builder),
        ("Setup/Prover/Verifier", test_setup_prover_verifier),
        ("Protocol Interface", test_protocol_interface),
        ("Performance Metrics", test_performance)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"\n❌ Test '{name}' FAILED with error:")
            logger.error(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{status}: {name}")
    
    logger.info("="*70)
    logger.info(f"Result: {passed}/{total} tests passed")
    logger.info("="*70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
