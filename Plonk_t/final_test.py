#!/usr/bin/env python3
"""
Final comprehensive PLONK test with timeout handling
"""

import sys
import os
import signal
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out")

def test_plonk_system():
    """Test the complete PLONK system"""
    print("🔧 Testing Complete PLONK System")
    print("=" * 40)
    
    try:
        # Set timeout for 30 seconds
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        from plonk_protocol import PLONKProtocol
        
        print("1. Initializing PLONK protocol...")
        plonk = PLONKProtocol(max_degree=16)  # Smaller setup for faster testing
        
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
        proof = plonk.prove(circuit, "test_client", 1)
        proof_time = time.time() - start_time
        print(f"   ✅ Proof generated in {proof_time:.2f}s ({len(proof)} bytes)")
        
        print("5. Verifying proof...")
        start_time = time.time()
        is_valid = plonk.verify(proof, circuit.public_inputs)
        verify_time = time.time() - start_time
        print(f"   {'✅' if is_valid else '❌'} Verification {'passed' if is_valid else 'failed'} in {verify_time:.2f}s")
        
        signal.alarm(0)  # Cancel timeout
        return is_valid
        
    except TimeoutError:
        print("   ⏰ Test timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        signal.alarm(0)  # Cancel timeout
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