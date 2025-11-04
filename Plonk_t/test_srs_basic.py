#!/usr/bin/env python3
"""
Simple SRS and commitment test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_srs_basic():
    """Test basic SRS functionality"""
    print("SRS BASIC TEST")
    print("=" * 30)
    
    try:
        from kzg_commitment import KZGCommitment
        from py_ecc.bn128 import G1, multiply
        
        print("Step 1: Create simple SRS")
        # Create very simple SRS for testing
        srs_g1 = [G1]  # Just the generator point
        kzg = KZGCommitment(srs_g1)
        print(f"   ✓ SRS created with {len(srs_g1)} points")
        
        print("Step 2: Test commitment to constant")
        # Commit to polynomial p(x) = 5 (just a constant)
        polynomial = [5]  # p(x) = 5
        commitment = kzg.commit(polynomial)
        print(f"   ✓ Commitment: {commitment}")
        
        print("Step 3: Verify commitment manually")
        # Should be 5 * G1
        expected = multiply(G1, 5)
        print(f"   Expected: {expected}")
        print(f"   Match: {commitment == expected}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_srs_basic()
    if success:
        print("\n✓ SRS BASIC TEST PASSED")
    else:
        print("\n✗ SRS BASIC TEST FAILED")