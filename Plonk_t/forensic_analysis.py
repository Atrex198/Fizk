#!/usr/bin/env python3
"""
FORENSIC ANALYSIS: Test if commitments vary with different inputs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_commitment_variance():
    """Test if KZG commitments actually vary with different polynomial inputs"""
    print("🔍 FORENSIC ANALYSIS: KZG Commitment Variance Test")
    print("=" * 60)
    
    try:
        from plonk_protocol import PLONKProtocol
        from circuit_builder import PLONKCircuit
        
        # Setup PLONK
        config = {'trusted_setup_size': 8, 'security_level': 128, 'curve': 'bn254'}
        plonk = PLONKProtocol(config)
        plonk.setup()
        
        print("🧪 Test 1: Different polynomial inputs should give different commitments")
        
        # Test with polynomial [1] (constant 1)
        commitment_1 = plonk.kzg_commitment.commit([1])
        print(f"   commit([1]) = {commitment_1}")
        
        # Test with polynomial [2] (constant 2)  
        commitment_2 = plonk.kzg_commitment.commit([2])
        print(f"   commit([2]) = {commitment_2}")
        
        # Test with polynomial [5] (constant 5)
        commitment_5 = plonk.kzg_commitment.commit([5])
        print(f"   commit([5]) = {commitment_5}")
        
        # Test with polynomial [1, 1] (1 + x)
        commitment_1x = plonk.kzg_commitment.commit([1, 1])
        print(f"   commit([1,1]) = {commitment_1x}")
        
        print("\n🔬 Analysis:")
        if commitment_1 == commitment_2 == commitment_5:
            print("   ❌ SUSPICIOUS: All commitments are identical!")
            print("   🚨 This suggests the KZG commitment is not working properly")
            return False
        else:
            print("   ✅ Different inputs produce different commitments")
            
        # Check if we're always getting the identity point
        identity_point = (1, 2)  # BN254 G1 generator point
        if commitment_1 == identity_point and commitment_2 == identity_point:
            print("   ❌ SUSPICIOUS: All commitments return identity point (1,2)")
            print("   🚨 This suggests fallback to G1 generator")
            return False
        else:
            print("   ✅ Commitments are not just returning identity point")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_circuit_variance():
    """Test if different circuits produce different proofs"""
    print("\n🧪 Test 2: Different circuits should give different proof data")
    print("=" * 50)
    
    try:
        from plonk_protocol import PLONKProtocol
        from circuit_builder import PLONKCircuit
        
        config = {'trusted_setup_size': 8, 'security_level': 128, 'curve': 'bn254'}
        plonk = PLONKProtocol(config)
        plonk.setup()
        
        # Circuit 1: 2 * 3 = 6
        circuit1 = PLONKCircuit("test1")
        a1 = circuit1.create_wire(2, "a1")
        b1 = circuit1.create_wire(3, "b1")
        c1 = circuit1.create_wire(6, "c1")
        circuit1.add_multiplication_gate(a1, b1, c1)
        
        proof1 = plonk.generate_proof(
            {"circuit_name": "test1"}, 
            {"test": "1"}, 
            1, "client1", circuit=circuit1
        )
        
        # Circuit 2: 4 * 5 = 20  
        circuit2 = PLONKCircuit("test2")
        a2 = circuit2.create_wire(4, "a2")
        b2 = circuit2.create_wire(5, "b2")
        c2 = circuit2.create_wire(20, "c2")
        circuit2.add_multiplication_gate(a2, b2, c2)
        
        proof2 = plonk.generate_proof(
            {"circuit_name": "test2"}, 
            {"test": "2"}, 
            1, "client2", circuit=circuit2
        )
        
        print(f"   Proof 1 challenges: {proof1.proof_data['challenges']}")
        print(f"   Proof 2 challenges: {proof2.proof_data['challenges']}")
        
        # Check if challenges are the same (they should be different)
        if proof1.proof_data['challenges'] == proof2.proof_data['challenges']:
            print("   ❌ SUSPICIOUS: Same challenges for different circuits!")
            print("   🚨 This suggests challenges are not properly randomized")
            return False
        else:
            print("   ✅ Different circuits produce different challenges")
            
        # Check wire commitments
        if (proof1.proof_data['wire_commitments'] == 
            proof2.proof_data['wire_commitments']):
            print("   ❌ SUSPICIOUS: Same wire commitments for different circuits!")
            return False
        else:
            print("   ✅ Different circuits produce different wire commitments")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🕵️ FORENSIC INVESTIGATION: Is the PLONK system legitimate?")
    print("="*70)
    
    test1_result = test_commitment_variance()
    test2_result = test_circuit_variance()
    
    if test1_result and test2_result:
        print("\n✅ INVESTIGATION RESULT: System appears to be LEGITIMATE")
        print("   • Commitments vary with different inputs")
        print("   • Challenges are properly randomized") 
        print("   • Different circuits produce different proofs")
    else:
        print("\n🚨 INVESTIGATION RESULT: System has SUSPICIOUS behavior")
        print("   • May be using fallback/dummy values")
        print("   • Cryptographic operations may not be working properly")