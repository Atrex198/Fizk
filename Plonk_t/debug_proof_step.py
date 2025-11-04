#!/usr/bin/env python3
"""
Debug proof generation step by step
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_proof_generation():
    """Debug each step of proof generation"""
    print("🔍 DEBUG PROOF GENERATION")
    print("=" * 40)
    
    try:
        from plonk_protocol import PLONKProtocol
        from circuit_builder import PLONKCircuit
        
        print("Step 1: Setup")
        config = {'trusted_setup_size': 4, 'security_level': 128, 'curve': 'bn254'}
        plonk = PLONKProtocol(config)
        plonk.setup()
        print("   ✓ Setup done")
        
        print("Step 2: Circuit")
        circuit = PLONKCircuit("debug")
        one_a = circuit.create_wire(1, "one_a")
        one_b = circuit.create_wire(1, "one_b") 
        one_c = circuit.create_wire(1, "one_c")
        circuit.add_multiplication_gate(one_a, one_b, one_c)
        print(f"   ✓ Circuit: a={circuit.a_wires}, b={circuit.b_wires}, c={circuit.c_wires}")
        
        print("Step 3: Test KZG commitment directly")
        try:
            commitment_a = plonk.kzg_commitment.commit(circuit.a_wires)
            print(f"   ✓ A commitment: {commitment_a}")
        except Exception as e:
            print(f"   ❌ A commitment failed: {e}")
            return False
            
        try:
            commitment_b = plonk.kzg_commitment.commit(circuit.b_wires)
            print(f"   ✓ B commitment: {commitment_b}")
        except Exception as e:
            print(f"   ❌ B commitment failed: {e}")
            return False
            
        try:
            commitment_c = plonk.kzg_commitment.commit(circuit.c_wires)
            print(f"   ✓ C commitment: {commitment_c}")
        except Exception as e:
            print(f"   ❌ C commitment failed: {e}")
            return False
        
        print("Step 4: Test proof generation step by step")
        statement = {"circuit_name": "debug"}
        witness = {"test": "debug"}
        
        # Try to call generate_proof with more debugging
        try:
            print("   Calling generate_proof...")
            proof = plonk.generate_proof(statement, witness, 1, "debug", circuit=circuit)
            print(f"   ✓ Proof: {proof}")
            return True
        except Exception as e:
            print(f"   ❌ generate_proof failed: {e}")
            import traceback
            print("   Traceback:")
            print(traceback.format_exc())
            return False
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    debug_proof_generation()