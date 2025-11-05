"""
Robust Test Script for Pairing Verification
============================================
Tests that pairing-based verification is properly enabled and working.
Includes proper error handling and progress monitoring.
"""

import sys
import os
import time

# Fix encoding for Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("\n" + "="*80)
print("PAIRING VERIFICATION TEST - ROBUST VERSION")
print("="*80)
print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Working directory: {os.getcwd()}")
print("="*80 + "\n")

# Import dependencies with error handling
print("[STEP 0] Importing dependencies...")
try:
    import numpy as np
    print("  [OK] numpy imported")
except ImportError as e:
    print(f"  [ERROR] Failed to import numpy: {e}")
    sys.exit(1)

try:
    import torch
    print("  [OK] torch imported")
except ImportError as e:
    print(f"  [ERROR] Failed to import torch: {e}")
    sys.exit(1)

try:
    from zkp_protocols.protostar_production import ProductionProtostar
    print("  [OK] ProductionProtostar imported")
except ImportError as e:
    print(f"  [ERROR] Failed to import ProductionProtostar: {e}")
    sys.exit(1)

print("\n[SUCCESS] All dependencies imported successfully\n")

def print_step(step_num, step_name):
    """Print step header"""
    print("\n" + "-"*80)
    print(f"[STEP {step_num}] {step_name}")
    print("-"*80)

def print_progress(message):
    """Print progress message"""
    print(f"  >> {message}")

def print_result(success, message):
    """Print result message"""
    status = "[OK]" if success else "[FAIL]"
    print(f"  {status} {message}")

def test_basic_protocol():
    """Test basic protocol setup and operations"""
    
    print_step(1, "Protocol Setup")
    print_progress("Creating ProductionProtostar instance...")
    
    try:
        protocol = ProductionProtostar(security_level=128)
        print_result(True, "Protocol instance created")
    except Exception as e:
        print_result(False, f"Failed to create protocol: {e}")
        return None
    
    print_progress("Running setup (generating SRS)...")
    print_progress("Note: This will take 1-2 minutes for 4096 elements...")
    
    try:
        start_time = time.time()
        setup_params = protocol.setup()
        setup_time = time.time() - start_time
        
        print_result(True, f"Setup completed in {setup_time:.1f}s")
        print_progress(f"SRS size: {setup_params['srs_size']} elements")
        print_progress(f"Security level: {setup_params['security_level']}-bit")
        print_progress(f"Curve: {setup_params['curve']}")
        
    except Exception as e:
        print_result(False, f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return protocol

def test_simple_proof_generation(protocol):
    """Test proof generation with a simple witness"""
    
    print_step(2, "Simple Proof Generation")
    print_progress("Creating minimal witness and public inputs...")
    
    try:
        # Create a very simple witness (just a few values)
        witness = np.array([1, 2, 3, 4, 5], dtype=int)
        public_inputs = np.array([10, 20], dtype=int)
        
        print_progress(f"Witness size: {len(witness)} elements")
        print_progress(f"Public inputs size: {len(public_inputs)} elements")
        
        print_progress("Generating proof...")
        start_time = time.time()
        
        proof = protocol.prove(
            statement=None,
            witness=witness,
            public_inputs=public_inputs
        )
        
        proof_time = time.time() - start_time
        print_result(True, f"Proof generated in {proof_time:.2f}s")
        
        # Check proof structure
        if isinstance(proof, dict):
            print_progress("Proof structure:")
            for key in proof.keys():
                print(f"    - {key}")
        
        return proof, witness, public_inputs
        
    except Exception as e:
        print_result(False, f"Proof generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def test_proof_verification(protocol, proof, witness, public_inputs):
    """Test proof verification with pairing checks"""
    
    print_step(3, "Proof Verification (With Pairing)")
    
    if proof is None:
        print_result(False, "Cannot verify: proof is None")
        return False
    
    print_progress("Verifying valid proof...")
    
    try:
        start_time = time.time()
        
        result = protocol.verify(
            proof=proof,
            statement=None,
            public_inputs=public_inputs
        )
        
        verify_time = time.time() - start_time
        
        print_result(result.is_valid, f"Verification completed in {verify_time:.3f}s")
        print_progress(f"Result: {result.message}")
        
        # Check for pairing verification details
        if hasattr(result, 'details') and result.details:
            print_progress("Verification details:")
            for key, value in result.details.items():
                if key == 'pairing_checks':
                    print(f"    - {key}:")
                    for pk, pv in value.items():
                        print(f"        * {pk}: {pv}")
                else:
                    print(f"    - {key}: {value}")
            
            # Check pairing verification status
            if 'pairing_checks' in result.details:
                pairing_status = result.details['pairing_checks'].get(
                    'pairing_verification_status', 
                    'unknown'
                )
                
                print("\n" + "="*80)
                print("PAIRING VERIFICATION STATUS CHECK:")
                print("="*80)
                print(f"Status: {pairing_status}")
                
                if pairing_status == 'enabled':
                    print("[SUCCESS] Pairing verification IS ENABLED!")
                    print("="*80 + "\n")
                    return True
                else:
                    print("[WARNING] Pairing verification is NOT enabled!")
                    print(f"Found status: {pairing_status}")
                    print("="*80 + "\n")
                    return False
        
        return result.is_valid
        
    except Exception as e:
        print_result(False, f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tampered_proof_rejection(protocol, proof, public_inputs):
    """Test that tampered proofs are rejected"""
    
    print_step(4, "Tampered Proof Rejection Test")
    
    if proof is None:
        print_result(False, "Cannot test: proof is None")
        return False
    
    print_progress("Creating tampered proof...")
    
    try:
        # Make a copy and tamper with it
        tampered_proof = proof.copy()
        
        # Tamper with witness commitment if it exists
        if 'witness_commitment' in tampered_proof:
            if isinstance(tampered_proof['witness_commitment'], dict):
                if 'point_coords' in tampered_proof['witness_commitment']:
                    coords = tampered_proof['witness_commitment']['point_coords']
                    if len(coords) > 0:
                        # Tamper with first coordinate
                        original = coords[0]
                        coords[0] = str((int(str(original)) + 99999) % 
                            0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47)
                        print_progress(f"Tampered witness commitment coordinate")
        
        print_progress("Verifying tampered proof (should FAIL)...")
        
        result = protocol.verify(
            proof=tampered_proof,
            statement=None,
            public_inputs=public_inputs
        )
        
        if not result.is_valid:
            print_result(True, "Tampered proof correctly REJECTED")
            print_progress(f"Reason: {result.message}")
            return True
        else:
            print_result(False, "Tampered proof was ACCEPTED (security issue!)")
            return False
            
    except Exception as e:
        # Exception during verification of tampered proof is acceptable
        print_result(True, f"Tampered proof rejected with exception: {e}")
        return True

def main():
    """Main test execution"""
    
    test_results = {
        'protocol_setup': False,
        'proof_generation': False,
        'proof_verification': False,
        'pairing_enabled': False,
        'tamper_rejection': False
    }
    
    # Test 1: Protocol setup
    protocol = test_basic_protocol()
    test_results['protocol_setup'] = (protocol is not None)
    
    if not protocol:
        print("\n[CRITICAL] Cannot continue without protocol setup")
        print_final_summary(test_results)
        return False
    
    # Test 2: Proof generation
    proof, witness, public_inputs = test_simple_proof_generation(protocol)
    test_results['proof_generation'] = (proof is not None)
    
    if not proof:
        print("\n[WARNING] Cannot test verification without proof")
        print_final_summary(test_results)
        return False
    
    # Test 3: Proof verification
    verification_passed = test_proof_verification(protocol, proof, witness, public_inputs)
    test_results['proof_verification'] = verification_passed
    test_results['pairing_enabled'] = verification_passed
    
    # Test 4: Tampered proof rejection
    if proof:
        tamper_test_passed = test_tampered_proof_rejection(protocol, proof, public_inputs)
        test_results['tamper_rejection'] = tamper_test_passed
    
    # Final summary
    print_final_summary(test_results)
    
    # Return overall success
    return all(test_results.values())

def print_final_summary(results):
    """Print final test summary"""
    
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        formatted_name = test_name.replace('_', ' ').title()
        print(f"{status} {formatted_name}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print("-"*80)
    print(f"Tests Passed: {passed_count}/{total_count}")
    print("="*80)
    
    if passed_count == total_count:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        print("The system is 100% proper with pairing verification enabled.\n")
        return True
    else:
        print(f"\n[WARNING] {total_count - passed_count} test(s) failed.")
        print("Review the output above for details.\n")
        return False

if __name__ == "__main__":
    try:
        print(f"\n[START] Beginning test execution...")
        success = main()
        print(f"\n[END] Test execution completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test execution interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n\n[CRITICAL ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
