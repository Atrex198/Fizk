#!/usr/bin/env python3
"""
Minimal verification test with full debug
"""

import sys
import os
import time
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enable DEBUG logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

def minimal_verification_test():
    """Minimal test to isolate verification issue"""
    print("Minimal Verification Test")
    print("=" * 25)
    
    try:
        from plonk_protocol import PLONKProtocol
        from circuit_builder import PLONKCircuit
        
        # Minimal setup
        config = {'trusted_setup_size': 16, 'security_level': 128, 'curve': 'bn254'}
        plonk = PLONKProtocol(config)
        plonk.setup()
        
        # Minimal circuit: just one multiplication
        circuit = PLONKCircuit("minimal")
        a = circuit.create_wire(3, "a")
        b = circuit.create_wire(4, "b") 
        c = circuit.create_wire(12, "c")
        circuit.add_multiplication_gate(a, b, c)
        
        print("Circuit: 3 * 4 = 12")
        
        # Generate proof
        statement = {"test": "minimal"}
        witness = {"data": [3, 4, 12]}
        
        print("Generating proof...")
        proof = plonk.generate_proof(statement, witness, 1, "minimal", circuit)
        print(f"Proof generated: {proof.metadata.proof_size_bytes} bytes")
        
        print("Starting verification...")
        print("=" * 25)
        
        start_time = time.time()
        result = plonk.verify_proof(proof, statement)
        verify_time = time.time() - start_time
        
        print("=" * 25)
        print(f"Verification completed in {verify_time:.3f}s")
        print(f"Result: {'PASS' if result.is_valid else 'FAIL'}")
        
        if hasattr(result, 'error_message') and result.error_message:
            print(f"Error: {result.error_message}")
        
        return result.is_valid
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = minimal_verification_test()
    print(f"\nFinal Result: {'SUCCESS' if success else 'FAILED'}")