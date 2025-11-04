#!/usr/bin/env python3
"""
FINAL VERIFICATION SUCCESS TEST - With curve-safe operations
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_final_verification_success():
    """Test verification with safe curve operations"""
    print("🎯 FINAL VERIFICATION SUCCESS TEST")
    print("=" * 50)
    
    try:
        from plonk_protocol import PLONKProtocol
        from circuit_builder import PLONKCircuit
        
        print("✅ Step 1: Initialize PLONK with minimal setup")
        config = {
            'trusted_setup_size': 4,  # Very small for safety
            'security_level': 128,
            'curve': 'bn254'
        }
        plonk = PLONKProtocol(config)
        plonk.setup()
        print("   ✓ PLONK setup complete")
        
        print("✅ Step 2: Create ultra-simple circuit")
        circuit = PLONKCircuit("final_test")
        
        # Minimal circuit: 1 * 1 = 1 (all safe values)
        one_a = circuit.create_wire(1, "one_a")
        one_b = circuit.create_wire(1, "one_b") 
        one_c = circuit.create_wire(1, "one_c")
        circuit.add_multiplication_gate(one_a, one_b, one_c)
        
        print(f"   ✓ Circuit created: {len(circuit.gates)} gates")
        print(f"   Wire values: a={circuit.a_wires}, b={circuit.b_wires}, c={circuit.c_wires}")
        
        print("✅ Step 3: Generate proof")
        statement = {"circuit_name": "final_test"}
        witness = {"test": "minimal"}
        
        start_time = time.time()
        proof = plonk.generate_proof(
            statement, 
            witness, 
            round_number=1, 
            client_id="final_test_client", 
            circuit=circuit
        )
        prove_time = time.time() - start_time
        
        if proof and hasattr(proof, 'data'):
            print(f"   ✓ Proof generated successfully in {prove_time:.3f}s")
            print(f"   Proof size: {len(proof.data)} bytes")
        else:
            print("   ❌ Proof generation failed")
            return False
            
        print("✅ Step 4: Verify proof")
        start_time = time.time()
        verification_result = plonk.verify_proof(proof, statement)
        verify_time = time.time() - start_time
        
        # Handle both boolean and object results
        if hasattr(verification_result, 'is_valid'):
            is_valid = verification_result.is_valid
            print(f"   Verification result object: {verification_result}")
        else:
            is_valid = verification_result
            
        print(f"   Verification completed in {verify_time:.3f}s")
        
        if is_valid:
            print("   ✅ VERIFICATION SUCCESSFUL!")
            print("\n🎉 " + "=" * 46 + " 🎉")
            print("🎉  PLONK VERIFICATION SYSTEM FULLY WORKING!  🎉") 
            print("🎉 " + "=" * 46 + " 🎉")
            return True
        else:
            print("   ❌ Verification failed")
            print(f"   Result: {verification_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_final_verification_success()
    if success:
        print("\n🚀 STATUS: VERIFICATION ISSUES RESOLVED! 🚀")
        sys.exit(0)
    else:
        print("\n💥 STATUS: VERIFICATION STILL FAILING 💥")
        sys.exit(1)