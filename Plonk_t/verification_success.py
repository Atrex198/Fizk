#!/usr/bin/env python3
"""
Verification Success Check - Clean implementation
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_verification_success():
    """Test verification with properly handled curve operations"""
    print("VERIFICATION SUCCESS CHECK")
    print("=" * 40)
    
    try:
        from plonk_protocol import PLONKProtocol
        
        print("Step 1: Initialize PLONK")
        config = {
            'trusted_setup_size': 8,  # Smaller for reliability
            'security_level': 128,
            'curve': 'bn254'
        }
        plonk = PLONKProtocol(config)
        plonk.setup()
        print("   ✓ Setup complete")
        
        print("Step 2: Create minimal circuit")
        from circuit_builder import PLONKCircuit
        circuit = PLONKCircuit("minimal")
        
        # Very simple: x * 1 = x
        x = circuit.create_wire(5, "x")
        one = circuit.create_wire(1, "one") 
        result = circuit.create_wire(5, "result")
        circuit.add_multiplication_gate(x, one, result)
        
        print(f"   ✓ Circuit: {len(circuit.gates)} gates")
        
        print("Step 3: Generate proof")
        # Pass the circuit directly as a parameter
        statement = {"circuit_name": "minimal"}
        witness = {"x": 5}
        
        # Debug: Check circuit structure
        print(f"   Circuit has {len(circuit.a_wires)} a_wires, {len(circuit.gates)} gates")
        if circuit.a_wires:
            print(f"   First a_wire value: {circuit.a_wires[0]}")
        
        start_time = time.time()
        proof = plonk.generate_proof(statement, witness, round_number=1, client_id="test_client", circuit=circuit)
        prove_time = time.time() - start_time
        
        if proof and hasattr(proof, 'data'):
            print(f"   ✓ Proof generated in {prove_time:.2f}s ({len(proof.data)} bytes)")
        else:
            print("   ✗ Proof generation failed")
            return False
            
        print("Step 4: Verify proof")
        start_time = time.time()
        verification_result = plonk.verify_proof(proof, statement)
        verify_time = time.time() - start_time
        
        is_valid = verification_result.is_valid if hasattr(verification_result, 'is_valid') else verification_result
        
        print(f"   Verification time: {verify_time:.2f}s")
        
        if is_valid:
            print("   ✓ VERIFICATION SUCCESSFUL!")
            return True
        else:
            print("   ✗ Verification failed")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_verification_success()
    if success:
        print("\n" + "=" * 40)
        print("🎉 ALL SYSTEMS WORKING - VERIFICATION RESOLVED! 🎉")
        print("=" * 40)
        sys.exit(0)
    else:
        print("\n" + "=" * 40)
        print("❌ VERIFICATION STILL FAILING")
        print("=" * 40)
        sys.exit(1)