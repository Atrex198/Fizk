#!/usr/bin/env python3
"""
Debug verification with timeout
"""

import sys
import os
import time
import signal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Verification timed out")

def test_verification_debug():
    """Test verification with timeout and detailed error handling"""
    print("Debug PLONK Verification")
    print("=" * 30)
    
    try:
        from plonk_protocol import PLONKProtocol
        from circuit_builder import PLONKCircuit
        
        # Create simple test
        print("1. Setting up...")
        config = {'trusted_setup_size': 16, 'security_level': 128, 'curve': 'bn254'}
        plonk = PLONKProtocol(config)
        plonk.setup()
        
        circuit = PLONKCircuit("debug_test")
        a = circuit.create_wire(5, "a")
        b = circuit.create_wire(5, "b") 
        c = circuit.create_wire(25, "c")
        circuit.add_multiplication_gate(a, b, c)
        
        print("2. Generating proof...")
        statement = {"test": "debug"}
        witness = {"data": [5, 5, 25]}
        
        proof = plonk.generate_proof(statement, witness, 1, "debug", circuit)
        print(f"   Proof: {proof.metadata.proof_size_bytes} bytes")
        
        print("3. Verification with 10s timeout...")
        start_time = time.time()
        
        try:
            # Set 10 second timeout
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(10)
            
            result = plonk.verify_proof(proof, statement)
            
            if hasattr(signal, 'alarm'):
                signal.alarm(0)  # Cancel timeout
            
            verify_time = time.time() - start_time
            print(f"   Result: {'PASS' if result.is_valid else 'FAIL'}")
            print(f"   Time: {verify_time:.2f}s")
            
            if hasattr(result, 'error_message') and result.error_message:
                print(f"   Error: {result.error_message}")
            
            return result.is_valid
            
        except TimeoutException:
            print("   TIMEOUT: Verification took > 10s")
            return False
        except Exception as e:
            verify_time = time.time() - start_time
            print(f"   ERROR after {verify_time:.2f}s: {e}")
            return False
            
    except Exception as e:
        print(f"Setup error: {e}")
        return False

if __name__ == "__main__":
    success = test_verification_debug()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")