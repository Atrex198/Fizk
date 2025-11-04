#!/usr/bin/env python3
"""
Quick success test for PLONK
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def quick_success_test():
    """Quick test to verify PLONK is working"""
    try:
        from plonk_protocol import PLONKProtocol
        from circuit_builder import PLONKCircuit
        
        # Quick setup
        config = {'trusted_setup_size': 16, 'security_level': 128, 'curve': 'bn254'}
        plonk = PLONKProtocol(config)
        plonk.setup()
        
        # Simple circuit
        circuit = PLONKCircuit("success_test")
        a = circuit.create_wire(2, "a")
        b = circuit.create_wire(3, "b") 
        c = circuit.create_wire(6, "c")
        circuit.add_multiplication_gate(a, b, c)
        
        # Test proof generation
        statement = {"test": "success"}
        witness = {"data": [2, 3, 6]}
        
        start_time = time.time()
        proof = plonk.generate_proof(statement, witness, 1, "success", circuit)
        proof_time = time.time() - start_time
        
        # Test verification with timeout
        start_time = time.time()
        result = plonk.verify_proof(proof, statement)
        verify_time = time.time() - start_time
        
        print(f"PLONK SYSTEM STATUS:")
        print(f"  Proof Generation: {'SUCCESS' if proof else 'FAILED'} ({proof_time:.3f}s)")
        print(f"  Proof Size: {proof.metadata.proof_size_bytes} bytes")
        print(f"  Verification: {'SUCCESS' if result.is_valid else 'FAILED'} ({verify_time:.3f}s)")
        
        return result.is_valid
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = quick_success_test()
    print(f"\nFINAL RESULT: {'✅ ALL SYSTEMS WORKING' if success else '❌ SYSTEM FAILED'}")