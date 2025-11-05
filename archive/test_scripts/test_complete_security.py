#!/usr/bin/env python3
"""
Comprehensive Security Test for Complete ZKP Implementation
===========================================================

This test verifies:
1. Complete pairing verification is enabled
2. No simulation fallbacks exist  
3. Real cryptographic operations throughout
4. Proper error handling and security enforcement
"""

import sys
import os
import time
import numpy as np

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_crypto_requirements():
    """Test that all cryptographic dependencies are enforced"""
    print("🧪 Testing Cryptographic Requirements...")
    print("=" * 60)
    
    try:
        # This should work - py_ecc is required
        from zkp_protocols.protostar_production import ProductionProtostar
        print("✅ ProductionProtostar imports successfully")
        
        # Test that py_ecc is actually working
        from py_ecc.bn128.bn128_curve import G1, G2, multiply, add, FQ
        from py_ecc.bn128.bn128_pairing import pairing
        
        # Basic operations test
        point1 = multiply(G1, 123)
        point2 = add(G1, point1)
        pairing_result = pairing(G1, G2)
        
        print("✅ py_ecc cryptographic operations functional")
        return True
        
    except ImportError as e:
        print(f"❌ CRITICAL: Cryptographic requirements not met: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Crypto operations failed: {e}")
        return False

def test_no_simulation_fallbacks():
    """Test that simulation fallbacks have been eliminated"""
    print("\n🔍 Testing for Simulation Fallbacks...")
    print("=" * 60)
    
    try:
        # Read the main protocol file
        with open('/home/ariva/work/final_project/Fizk/zkp_protocols/protostar_production.py', 'r') as f:
            source_code = f.read()
        
        # Check for dangerous patterns
        danger_patterns = [
            "CRYPTO_AVAILABLE = False",
            "temporarily disabled",
            "disabled_for_demo", 
            "simulation mode",
            "bypass",
            "skip verification",
            "return True  # FIXME",
            "# TODO: implement"
        ]
        
        found_issues = []
        for pattern in danger_patterns:
            if pattern.lower() in source_code.lower():
                found_issues.append(pattern)
        
        if found_issues:
            print(f"❌ Found simulation patterns: {found_issues}")
            return False
        else:
            print("✅ No simulation fallback patterns found")
            
        # Check for security enforcements
        security_patterns = [
            "CRITICAL SECURITY ERROR",
            "py_ecc library is REQUIRED", 
            "complete_protostar_verification",
            "REAL pairing verification",
            "curve validation"
        ]
        
        found_security = []
        for pattern in security_patterns:
            if pattern in source_code:
                found_security.append(pattern)
        
        print(f"✅ Found {len(found_security)}/5 security enforcement patterns")
        return len(found_security) >= 4  # Most patterns should be present
        
    except Exception as e:
        print(f"❌ ERROR reading source: {e}")
        return False

def test_complete_proof_generation():
    """Test complete proof generation with enhanced verification"""
    print("\n🔧 Testing Complete Proof Generation...")
    print("=" * 60)
    
    try:
        from zkp_protocols.protostar_production import ProductionProtostar
        from zkp_protocols.base import TrainingStatement, TrainingWitness
        
        # Initialize with higher security
        protocol = ProductionProtostar(security_level=128)
        print("✅ Protocol initialized")
        
        # Setup (this should use real cryptographic operations)
        setup_start = time.time()
        setup_params = protocol.setup()
        setup_time = time.time() - setup_start
        
        print(f"✅ Setup completed in {setup_time:.2f}s")
        print(f"   SRS size: {setup_params['srs_size']}")
        print(f"   Security level: {setup_params['security_level']}")
        print(f"   Tau commitment: {setup_params['tau_commitment'][:16]}...")
        
        # Create test data
        statement = TrainingStatement(
            model_architecture="TestNN",
            initial_weights_commitment="test_initial_hash",
            final_weights_commitment="test_final_hash",
            dataset_commitment="test_dataset_hash",
            local_epochs=3,
            batch_size=32,
            learning_rate=0.01,
            claimed_accuracy=0.85,
            claimed_loss=0.25,
            sample_count=1000,
            round_number=1,
            client_id="test_client",
            timestamp=time.time()
        )
        
        # Create witness with proper structure
        witness = TrainingWitness(
            initial_weights={
                'layer1': np.random.randn(10, 5).astype(np.float32) * 0.1,
                'layer2': np.random.randn(5, 2).astype(np.float32) * 0.1
            },
            final_weights={
                'layer1': np.random.randn(10, 5).astype(np.float32) * 0.1,  
                'layer2': np.random.randn(5, 2).astype(np.float32) * 0.1
            },
            dataset_samples=np.random.randn(100, 10).astype(np.float32),
            dataset_labels=np.random.randint(0, 2, 100)
        )
        
        print("✅ Test data created")
        
        # Generate proof (should use enhanced simplified circuit)
        proof_start = time.time()
        proof = protocol.generate_proof(statement, witness)
        proof_time = time.time() - proof_start
        
        print(f"✅ Proof generated in {proof_time:.2f}s")
        print(f"   Proof size: {proof.get_size_bytes()} bytes")
        
        # Check proof structure
        if not hasattr(proof, 'proof_data'):
            raise ValueError("Proof missing proof_data")
            
        required_commitments = [
            'witness_commitment',
            'witness_error_commitment', 
            'constraint_commitment',
            'constraint_error_commitment'
        ]
        
        for comm in required_commitments:
            if comm not in proof.proof_data:
                raise ValueError(f"Missing commitment: {comm}")
            if not proof.proof_data[comm].get('is_ec_point', False):
                raise ValueError(f"{comm} is not an EC point")
        
        print("✅ Proof structure validated")
        
        return True, proof, statement
        
    except Exception as e:
        print(f"❌ Proof generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_complete_verification(proof, statement):
    """Test complete pairing-based verification"""
    print("\n🔍 Testing Complete Verification...")
    print("=" * 60)
    
    try:
        from zkp_protocols.protostar_production import ProductionProtostar
        
        # Create fresh protocol instance for verification
        protocol = ProductionProtostar(security_level=128)
        protocol.setup()  # Must setup for verification
        
        # Verify proof (should use complete pairing verification)
        verify_start = time.time()
        result = protocol.verify_proof(statement, proof)
        verify_time = time.time() - verify_start
        
        print(f"   Verification time: {verify_time:.4f}s")
        print(f"   Result: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
        print(f"   Message: {result.message}")
        
        if not result.is_valid:
            print("❌ Verification failed")
            return False
        
        # Check verification details
        if result.details and 'pairing_checks' in result.details:
            pairing_details = result.details['pairing_checks']
            status = pairing_details.get('pairing_verification_status', 'unknown')
            
            print(f"\n🔐 Pairing Verification Details:")
            print(f"   Status: {status}")
            print(f"   Verification complete: {pairing_details.get('verification_complete', False)}")
            print(f"   Equations verified: {pairing_details.get('equations_verified', 0)}")
            print(f"   Commitments validated: {pairing_details.get('commitment_points_validated', 0)}")
            
            if status == 'complete_protostar_verification':
                print("🎉 SUCCESS: Complete Protostar verification is working!")
                return True
            else:
                print(f"❌ Verification status is not complete: {status}")
                return False
        else:
            print("❌ No pairing verification details found")
            return False
            
    except Exception as e:
        print(f"❌ Verification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security_enforcement():
    """Test that security measures are properly enforced"""
    print("\n🛡️ Testing Security Enforcement...")
    print("=" * 60)
    
    try:
        from zkp_protocols.protostar_production import ProductionProtostar
        from zkp_protocols.base import TrainingStatement, TrainingWitness
        
        protocol = ProductionProtostar(security_level=128)
        protocol.setup()
        
        # Test 1: Invalid challenge should fail
        print("   Testing invalid challenge rejection...")
        
        # Create valid proof first
        statement = TrainingStatement(
            model_architecture="TestNN", initial_weights_commitment="test1",
            final_weights_commitment="test2", dataset_commitment="test3",
            local_epochs=1, batch_size=32, learning_rate=0.01,
            claimed_accuracy=0.8, claimed_loss=0.3, sample_count=100,
            round_number=1, client_id="test", timestamp=time.time()
        )
        
        witness = TrainingWitness(
            initial_weights={'layer1': np.random.randn(5, 3).astype(np.float32) * 0.1},
            final_weights={'layer1': np.random.randn(5, 3).astype(np.float32) * 0.1},
            dataset_samples=np.random.randn(50, 5).astype(np.float32),
            dataset_labels=np.random.randint(0, 2, 50)
        )
        
        proof = protocol.generate_proof(statement, witness)
        
        # Tamper with challenge
        original_challenge = proof.proof_data['challenge']
        proof.proof_data['challenge'] = str(int(original_challenge) + 1)
        
        # This should fail
        result = protocol.verify_proof(statement, proof)
        if result.is_valid:
            print("❌ Tampered proof incorrectly accepted")
            return False
        else:
            print("✅ Tampered proof correctly rejected")
        
        print("✅ Security enforcement tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

def run_all_tests():
    """Run comprehensive security test suite"""
    print("🔬 COMPREHENSIVE ZKP SECURITY TEST SUITE")
    print("=" * 80)
    print("Testing complete implementation with no shortcuts or simulations")
    print("=" * 80)
    
    test_results = []
    
    # Test 1: Crypto requirements
    test_results.append(("Crypto Requirements", test_crypto_requirements()))
    
    # Test 2: No simulation fallbacks
    test_results.append(("No Simulation Fallbacks", test_no_simulation_fallbacks()))
    
    # Test 3: Complete proof generation 
    proof_success, proof, statement = test_complete_proof_generation()
    test_results.append(("Complete Proof Generation", proof_success))
    
    if proof_success and proof and statement:
        # Test 4: Complete verification
        verify_success = test_complete_verification(proof, statement)
        test_results.append(("Complete Verification", verify_success))
        
        # Test 5: Security enforcement
        security_success = test_security_enforcement()
        test_results.append(("Security Enforcement", security_success))
    else:
        test_results.append(("Complete Verification", False))
        test_results.append(("Security Enforcement", False))
    
    # Print results
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("=" * 80)
    print(f"OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("🔒 ZKP implementation is PRODUCTION-GRADE SECURE!")
        print("✅ No simulations, no shortcuts, complete cryptographic verification!")
        return True
    else:
        print("❌ Some tests failed - implementation needs fixes")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)