#!/usr/bin/env python3
"""
Final comprehensive PLONK test - Windows compatible
"""

import sys
import os
import time
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def test_plonk_system():
    """Test the complete PLONK system"""
    print("🔧 Testing Complete PLONK System")
    print("=" * 40)
    
    try:
        from plonk_protocol import PLONKProtocol
        
        print("1. Initializing PLONK protocol...")
        config = {
            'trusted_setup_size': 16,
            'security_level': 128,
            'curve': 'bn254'
        }
        plonk = PLONKProtocol(config)
        
        print("2. Generating trusted setup...")
        start_time = time.time()
        plonk.setup()
        setup_time = time.time() - start_time
        print(f"   ✅ Setup complete in {setup_time:.2f}s")
        
        print("3. Creating test circuit...")
        from circuit_builder import PLONKCircuit
        circuit = PLONKCircuit("final_test")
        
        # Simple arithmetic: 10 * 20 = 200
        a = circuit.create_wire(10, "a")
        b = circuit.create_wire(20, "b") 
        c = circuit.create_wire(200, "c")
        circuit.add_multiplication_gate(a, b, c)
        
        # Addition: 200 + 50 = 250
        d = circuit.create_wire(50, "d")
        e = circuit.create_wire(250, "e")
        circuit.add_addition_gate(c, d, e)
        
        print(f"   ✅ Circuit created: {len(circuit.gates)} gates, {len(circuit.wires)} wires")
        
        print("4. Generating proof...")
        start_time = time.time()
        
        # Create statement and witness
        statement = {"circuit_name": "final_test"}
        witness = {
            "client_data": [10, 20, 50],  # Simple test data
            "model_weights": [1.0, 2.0],
            "target_loss": 0.5
        }
        
        proof = plonk.generate_proof(
            statement=statement,
            witness=witness,
            round_number=1,
            client_id="test_client",
            circuit=circuit
        )
        proof_time = time.time() - start_time
        print(f"   ✅ Proof generated in {proof_time:.2f}s ({proof.metadata.proof_size_bytes} bytes)")
        
        print("5. Verifying proof...")
        start_time = time.time()
        verification_result = plonk.verify_proof(proof, statement)
        verify_time = time.time() - start_time
        is_valid = verification_result.is_valid
        print(f"   {'✅' if is_valid else '❌'} Verification {'passed' if is_valid else 'failed'} in {verify_time:.2f}s")
        
        return is_valid
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_plonk_system()
    print("\n" + "=" * 40)
    if success:
        print("🎉 PLONK Implementation: ALL TESTS PASSED!")
        print("✅ Critical fixes successfully implemented:")
        print("   • Polynomial division algorithm")
        print("   • KZG opening verification") 
        print("   • Quotient polynomial computation")
        print("   • Full PLONK constraint verification")
        print("   • Wire value preservation")
    else:
        print("❌ Some tests failed - further investigation needed")