#!/usr/bin/env python3
"""
Debug the SRS point generation and validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_srs_points():
    """Debug SRS point generation"""
    print("🔍 DEBUGGING SRS POINT GENERATION")
    print("=" * 50)
    
    try:
        from py_ecc.bn128 import G1, G2, multiply, curve_order
        from kzg_commitment import KZGCommitment
        
        print("🧪 Test 1: Check basic curve points")
        print(f"   G1 = {G1}")
        print(f"   G1 type = {type(G1)}")
        
        # Test our validation function directly
        kzg = KZGCommitment([G1])  # Minimal SRS for testing
        
        print(f"\n🧪 Test 2: Validate G1 point directly")
        is_g1_valid = kzg._validate_curve_point(G1)
        print(f"   G1 valid according to our validator: {is_g1_valid}")
        
        print(f"\n🧪 Test 3: Test point multiplication")
        try:
            point_2 = multiply(G1, 2)
            print(f"   2 * G1 = {point_2}")
            print(f"   2 * G1 type = {type(point_2)}")
            
            is_2g1_valid = kzg._validate_curve_point(point_2)
            print(f"   2 * G1 valid: {is_2g1_valid}")
            
        except Exception as e:
            print(f"   Point multiplication failed: {e}")
        
        print(f"\n🧪 Test 4: Test curve validation function")
        try:
            from py_ecc.bn128 import is_on_curve, field_modulus
            print(f"   py_ecc.is_on_curve available: {hasattr(is_on_curve, '__call__')}")
            
            # Test with G1
            try:
                result = is_on_curve(G1, field_modulus)
                print(f"   is_on_curve(G1): {result}")
            except Exception as curve_e:
                print(f"   is_on_curve(G1) failed: {curve_e}")
                
        except ImportError as import_e:
            print(f"   is_on_curve not available: {import_e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    debug_srs_points()