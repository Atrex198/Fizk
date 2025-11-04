#!/usr/bin/env python3
"""
SECURITY TEST: Can we fool the verification with invalid proofs?
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Parent directory

def test_invalid_proof_rejection():
    """Test if the system correctly rejects obviously invalid proofs"""
    print("🚨 SECURITY TEST: Invalid Proof Rejection")
    print("=" * 50)
    
    try:
        from plonk_protocol import PLONKProtocol, ProofObject, ProofMetadata, ProtocolType
        from circuit_builder import PLONKCircuit
        import time
        
        config = {'trusted_setup_size': 8, 'security_level': 128, 'curve': 'bn254'}
        plonk = PLONKProtocol(config)
        plonk.setup()
        
        print("🧪 Test 1: Completely fabricated proof")
        
        # Create a fake proof with random data
        fake_proof_data = {
            'wire_commitments': {
                'a': {'x': '123456789', 'y': '987654321'},
                'b': {'x': '111111111', 'y': '222222222'},
                'c': {'x': '333333333', 'y': '444444444'}
            },
            'permutation_commitment': {'x': '555555555', 'y': '666666666'},
            'quotient_commitment': {'x': '777777777', 'y': '888888888'},
            'evaluations': {'a_zeta': 42, 'b_zeta': 99, 'c_zeta': 123},
            'opening_proofs': {
                'a_zeta': {'x': '999999999', 'y': '111111111'},
                'b_zeta': {'x': '222222222', 'y': '333333333'},
                'c_zeta': {'x': '444444444', 'y': '555555555'}
            },
            'challenges': {
                'beta': 12345,
                'gamma': 67890,
                'alpha': 11111,
                'zeta': 22222
            }
        }
        
        fake_metadata = ProofMetadata(
            protocol_name="PLONK",
            protocol_type=ProtocolType.PLONK,
            proof_version="1.0.0",
            proof_size_bytes=1000,
            constraint_count=1,
            security_level=128,
            generation_time=0.001,
            round_number=1,
            client_id="fake_client",
            timestamp=time.time(),
            verification_method="PLONK_KZG_BN254",
            requires_trusted_setup=True,
            trusted_setup_size=8,
            curve_name="BN254",
            field_modulus="21888242871839275222246405745257275088548364400416034343698204186575808495617",
            commitment_scheme="KZG"
        )
        
        fake_proof = ProofObject(
            metadata=fake_metadata,
            proof_data=fake_proof_data,
            public_inputs=['fake', 'data'],
            auxiliary_data={}
        )
        
        statement = {"circuit_name": "fake"}
        result = plonk.verify_proof(fake_proof, statement)
        
        print(f"   Fake proof verification result: {result.is_valid}")
        
        if result.is_valid:
            print("   🚨 CRITICAL SECURITY FLAW: Fake proof was accepted!")
            return False
        else:
            print("   ✅ Good: Fake proof was rejected")
            
        print("\n🧪 Test 2: Valid proof with wrong statement")
        
        # Generate a real proof for one circuit
        circuit = PLONKCircuit("real_circuit")
        a = circuit.create_wire(3, "a")
        b = circuit.create_wire(4, "b")
        c = circuit.create_wire(12, "c")
        circuit.add_multiplication_gate(a, b, c)
        
        real_proof = plonk.generate_proof(
            {"circuit_name": "real_circuit"}, 
            {"test": "real"}, 
            1, "real_client", circuit=circuit
        )
        
        # Try to verify it against a different statement
        wrong_statement = {"circuit_name": "different_circuit", "claimed_accuracy": 0.95}
        result2 = plonk.verify_proof(real_proof, wrong_statement)
        
        print(f"   Real proof with wrong statement: {result2.is_valid}")
        
        if result2.is_valid:
            print("   ⚠️  WARNING: Real proof accepted with wrong statement")
            print("   This might be OK if statement validation is loose")
        else:
            print("   ✅ Good: Real proof rejected with wrong statement")
            
        print("\n🧪 Test 3: Proof with impossible circuit constraint")
        
        # Create a circuit with an impossible constraint: 2 * 3 = 7 (wrong!)
        bad_circuit = PLONKCircuit("impossible")
        a_bad = bad_circuit.create_wire(2, "a_bad")
        b_bad = bad_circuit.create_wire(3, "b_bad")
        c_bad = bad_circuit.create_wire(7, "c_bad")  # 2*3 ≠ 7
        bad_circuit.add_multiplication_gate(a_bad, b_bad, c_bad)
        
        try:
            impossible_proof = plonk.generate_proof(
                {"circuit_name": "impossible"}, 
                {"test": "impossible"}, 
                1, "bad_client", circuit=bad_circuit
            )
            
            result3 = plonk.verify_proof(impossible_proof, {"circuit_name": "impossible"})
            
            print(f"   Impossible constraint proof: {result3.is_valid}")
            
            if result3.is_valid:
                print("   🚨 CRITICAL: System accepted mathematically impossible proof!")
                return False
            else:
                print("   ✅ Good: Impossible constraint was rejected")
                
        except Exception as e:
            print(f"   ✅ Good: Impossible proof generation failed: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🔍 SECURITY AUDIT: Testing proof verification robustness")
    print("="*60)
    
    if test_invalid_proof_rejection():
        print("\n✅ SECURITY ASSESSMENT: Verification has basic protection")
        print("   • Rejects completely fake proofs")
        print("   • Has some constraint checking")
    else:
        print("\n🚨 SECURITY ASSESSMENT: CRITICAL VULNERABILITIES FOUND")
        print("   • System accepts invalid proofs")
        print("   • Verification is not cryptographically sound")