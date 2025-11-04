#!/usr/bin/env python3
"""
Quick KZG verification test to identify hanging issue
"""

import time
import logging
from kzg_commitment import KZGCommitment
from trusted_setup import PLONKTrustedSetup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_kzg_verification_performance():
    """Test KZG verification performance"""
    
    print("🔧 Testing KZG verification performance...")
    
    # Create small setup
    setup = PLONKTrustedSetup()
    setup_data = setup.generate_setup(degree=8)  # Very small for speed
    
    # Initialize KZG
    kzg = KZGCommitment(setup_data['srs_g1'], setup_data['srs_g2'])
    
    # Test simple polynomial: p(x) = 2x + 1
    polynomial = [1, 2]  # Coefficients: 1 + 2x
    
    print("🔧 Creating commitment...")
    start = time.time()
    commitment = kzg.commit(polynomial)
    commit_time = time.time() - start
    print(f"✅ Commitment created in {commit_time:.3f}s")
    
    # Create opening proof for p(3) = 7
    evaluation_point = 3
    expected_value = 1 + 2 * 3  # = 7
    
    print("🔧 Creating opening proof...")
    start = time.time()
    proof = kzg.create_opening_proof(polynomial, evaluation_point)
    proof_time = time.time() - start
    print(f"✅ Opening proof created in {proof_time:.3f}s")
    
    # Now test verification (this is what's hanging)
    print("🔧 Starting verification...")
    print("⚠️  This might be slow due to pairing computation...")
    
    start = time.time()
    try:
        is_valid = kzg.verify_opening(commitment, evaluation_point, expected_value, proof)
        
        verify_time = time.time() - start
        print(f"{'✅' if is_valid else '❌'} Verification result: {is_valid} in {verify_time:.3f}s")
        
        if verify_time > 5.0:
            print("⚠️  Verification took longer than 5 seconds - this is the bottleneck!")
        
    except Exception as e:
        verify_time = time.time() - start
        print(f"❌ Verification failed after {verify_time:.3f}s with error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_kzg_verification_performance()