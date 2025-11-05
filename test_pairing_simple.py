"""
Simple test script to verify pairing verification is properly enabled
"""
import sys
import numpy as np
import torch

# Fix encoding for Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from zkp_protocols.protostar_production import ProductionProtostar
from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS
from real_ml_trainer import MedicalMLPModel

def test_pairing_verification():
    """Test that pairing verification is working"""
    print("="*70)
    print("PAIRING VERIFICATION TEST")
    print("="*70)
    
    # 1. Setup protocol
    print("\n1. Setting up Protostar protocol...")
    protocol = ProductionProtostar(security_level=128)
    setup_params = protocol.setup()
    print(f"[OK] Setup complete: {setup_params['srs_size']} SRS elements")
    
    # 2. Generate small circuit
    print("\n2. Generating R1CS circuit...")
    model = MedicalMLPModel(input_features=4, hidden_sizes=[2], num_classes=1)
    circuit_gen = MLCircuitR1CS(model)
    
    # Create mini batch
    X = torch.randn(2, 4)
    y = torch.randn(2, 1)
    circuit = circuit_gen.generate_full_ml_circuit(X, y, learning_rate=0.01)
    print(f"[OK] Circuit generated: {circuit.num_constraints} constraints")
    
    # 3. Generate proof
    print("\n3. Generating proof...")
    witness = circuit.witness
    public_inputs = circuit.public_inputs
    proof = protocol.prove(statement=None, witness=witness, public_inputs=public_inputs)
    print(f"[OK] Proof generated")
    
    # 4. Verify proof (should pass with pairing checks)
    print("\n4. Verifying proof with pairing verification...")
    result = protocol.verify(proof=proof, statement=None, public_inputs=public_inputs)
    
    print("\n" + "="*70)
    print("VERIFICATION RESULT:")
    print("="*70)
    print(f"Valid: {result.is_valid}")
    print(f"Message: {result.message}")
    print(f"Time: {result.verification_time:.3f}s")
    
    if result.details:
        print("\nDetails:")
        for key, value in result.details.items():
            if key == 'pairing_checks':
                print(f"  {key}:")
                for pk, pv in value.items():
                    print(f"    {pk}: {pv}")
            else:
                print(f"  {key}: {value}")
    
    # 5. Test tampered proof (should fail)
    print("\n" + "="*70)
    print("5. Testing tampered proof (should FAIL)...")
    print("="*70)
    
    # Tamper with proof by modifying witness commitment
    tampered_proof = proof.copy()
    tampered_proof['witness_commitment']['point_coords'][0] = str(
        (int(tampered_proof['witness_commitment']['point_coords'][0]) + 12345) % 
        0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47
    )
    
    result_tampered = protocol.verify(
        proof=tampered_proof, 
        statement=None, 
        public_inputs=public_inputs
    )
    
    print(f"\nTampered Proof Result:")
    print(f"Valid: {result_tampered.is_valid}")
    print(f"Message: {result_tampered.message}")
    
    # 6. Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    tests_passed = 0
    tests_total = 2
    
    if result.is_valid:
        print("[PASS] Test 1: Valid proof accepted")
        tests_passed += 1
    else:
        print("[FAIL] Test 1: Valid proof REJECTED (should pass)")
    
    if not result_tampered.is_valid:
        print("[PASS] Test 2: Tampered proof rejected")
        tests_passed += 1
    else:
        print("[FAIL] Test 2: Tampered proof ACCEPTED (should fail)")
    
    print(f"\nTests passed: {tests_passed}/{tests_total}")
    
    # Check pairing status
    if result.details and 'pairing_checks' in result.details:
        pairing_status = result.details['pairing_checks'].get('pairing_verification_status', 'unknown')
        print(f"\nPairing Verification Status: {pairing_status}")
        
        if pairing_status == 'enabled':
            print("[SUCCESS] PAIRING VERIFICATION IS ENABLED!")
        else:
            print("[ERROR] PAIRING VERIFICATION IS NOT ENABLED!")
    
    return tests_passed == tests_total


if __name__ == "__main__":
    try:
        success = test_pairing_verification()
        if success:
            print("\n" + "="*70)
            print("ALL TESTS PASSED - PAIRING VERIFICATION WORKING!")
            print("="*70)
        else:
            print("\n" + "="*70)
            print("SOME TESTS FAILED - CHECK OUTPUT ABOVE")
            print("="*70)
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
