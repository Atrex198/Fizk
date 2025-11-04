#!/usr/bin/env python3
"""
Quick verification test to isolate the issue
"""

import sys
import os
import time
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_verification_only():
    """Test just the verification step"""
    print("🔧 Testing PLONK Verification")
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
        plonk.setup()
        
        print("2. Creating test circuit...")
        from circuit_builder import PLONKCircuit
        circuit = PLONKCircuit("verification_test")
        
        # Simple arithmetic: 5 * 5 = 25
        a = circuit.create_wire(5, "a")
        b = circuit.create_wire(5, "b") 
        c = circuit.create_wire(25, "c")
        circuit.add_multiplication_gate(a, b, c)
        
        print(f"   ✅ Circuit created: {len(circuit.gates)} gates, {len(circuit.wires)} wires")
        
        print("3. Generating proof...")
        statement = {"circuit_name": "verification_test"}
        witness = {"client_data": [5, 5], "model_weights": [1.0], "target_loss": 0.1}
        
        start_time = time.time()
        proof = plonk.generate_proof(
            statement=statement,
            witness=witness,
            round_number=1,
            client_id="test_client",
            circuit=circuit
        )
        proof_time = time.time() - start_time
        print(f"   ✅ Proof generated in {proof_time:.2f}s ({proof.metadata.proof_size_bytes} bytes)")
        
        print("4. Starting verification with timeout...")
        start_time = time.time()
        max_time = 5  # 5 second timeout
        
        # Start verification
        verification_result = None
        try:
            logger.info("🔍 Starting verification process...")
            verification_result = plonk.verify_proof(proof, statement)
            verify_time = time.time() - start_time
            
            if verify_time > max_time:
                print(f"   ⏰ Verification took too long: {verify_time:.2f}s")
                return False
            
            logger.info(f"🏁 Verification completed in {verify_time:.2f}s")
            is_valid = verification_result.is_valid
            print(f"   {'✅' if is_valid else '❌'} Verification {'passed' if is_valid else 'failed'} in {verify_time:.2f}s")
            
            # Print verification details
            if hasattr(verification_result, 'error_message') and verification_result.error_message:
                print(f"   Error: {verification_result.error_message}")
            
            return is_valid
            
        except KeyboardInterrupt:
            verify_time = time.time() - start_time
            print(f"   ⏹️ Verification interrupted after {verify_time:.2f}s")
            return False
        except Exception as e:
            verify_time = time.time() - start_time
            print(f"   ❌ Verification error after {verify_time:.2f}s: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_verification_only()
    print("\n" + "=" * 40)
    if success:
        print("🎉 Verification test passed!")
    else:
        print("❌ Verification test failed")