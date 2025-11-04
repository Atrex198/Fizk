#!/usr/bin/env python3
"""
Debug is_on_curve function usage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_curve_validation():
    """Debug curve validation"""
    print("🔍 DEBUGGING CURVE VALIDATION")
    print("=" * 40)
    
    try:
        from py_ecc.bn128 import G1, G2, is_on_curve, field_modulus, curve_order
        
        print(f"G1 = {G1}")
        print(f"field_modulus = {field_modulus}")
        print(f"curve_order = {curve_order}")
        
        # Try different ways to call is_on_curve
        print(f"\n🧪 Test 1: is_on_curve(G1, field_modulus)")
        try:
            result1 = is_on_curve(G1, field_modulus)
            print(f"   Result: {result1}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print(f"\n🧪 Test 2: is_on_curve(G1)")
        try:
            result2 = is_on_curve(G1)
            print(f"   Result: {result2}")
        except Exception as e:
            print(f"   Error: {e}")
            
        print(f"\n🧪 Test 3: Manual curve equation check")
        # BN254 curve: y² = x³ + 3
        x, y = G1
        print(f"   x = {x}")
        print(f"   y = {y}")
        
        # Check if y² ≡ x³ + 3 (mod field_modulus)
        y_squared = (y * y) % field_modulus
        x_cubed_plus_3 = (x * x * x + 3) % field_modulus
        
        print(f"   y² mod p = {y_squared}")
        print(f"   x³ + 3 mod p = {x_cubed_plus_3}")
        print(f"   Equal: {y_squared == x_cubed_plus_3}")
        
        # Check if coordinates are in valid range
        print(f"\n🧪 Test 4: Range validation")
        print(f"   0 <= x < field_modulus: {0 <= x < field_modulus}")
        print(f"   0 <= y < field_modulus: {0 <= y < field_modulus}")
        print(f"   0 <= x < curve_order: {0 <= x < curve_order}")
        print(f"   0 <= y < curve_order: {0 <= y < curve_order}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    debug_curve_validation()