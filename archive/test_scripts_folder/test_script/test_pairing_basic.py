#!/usr/bin/env python3
"""
Simple Pairing Test
==================

Test basic pairing operations to isolate the FQ2 error.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py_ecc.bn128 import G1, G2, pairing, multiply, add, curve_order
from py_ecc.fields import bn128_FQ2 as FQ2

def test_basic_pairing():
    """Test basic pairing operations"""
    print("🧪 Testing Basic Pairing Operations")
    print("=" * 40)
    
    # Test 1: Basic pairing
    print("1. Basic pairing e(G1, G2)...")
    try:
        p1 = pairing(G1, G2)
        print("   ✅ Basic pairing successful")
    except Exception as e:
        print(f"   ❌ Basic pairing failed: {e}")
        return False
    
    # Test 2: Pairing with scalar multiplication
    print("2. Pairing with scalar multiplication...")
    try:
        scalar = 123456
        g1_scaled = multiply(G1, scalar)
        g2_scaled = multiply(G2, scalar)
        p2 = pairing(g1_scaled, G2)
        p3 = pairing(G1, g2_scaled)
        print("   ✅ Scalar multiplication pairings successful")
    except Exception as e:
        print(f"   ❌ Scalar multiplication pairing failed: {e}")
        return False
    
    # Test 3: SRS-style operations
    print("3. SRS-style operations...")
    try:
        tau = 98765
        tau_g1 = multiply(G1, tau)
        tau_g2 = multiply(G2, tau)
        
        # Test pairing with SRS elements
        p4 = pairing(tau_g1, G2)
        p5 = pairing(G1, tau_g2)
        print("   ✅ SRS-style operations successful")
        
        # Check types
        print(f"   📊 tau_g2 type: {type(tau_g2)}")
        if hasattr(tau_g2, '__len__'):
            print(f"   📊 tau_g2 length: {len(tau_g2)}")
            if len(tau_g2) == 2:
                print(f"   📊 tau_g2[0] type: {type(tau_g2[0])}")
                print(f"   📊 tau_g2[1] type: {type(tau_g2[1])}")
        
    except Exception as e:
        print(f"   ❌ SRS-style operations failed: {e}")
        return False
    
    # Test 4: Point addition
    print("4. Point addition operations...")
    try:
        point1 = multiply(G1, 111)
        point2 = multiply(G1, 222)
        added = add(point1, point2)
        p6 = pairing(added, G2)
        print("   ✅ Point addition successful")
    except Exception as e:
        print(f"   ❌ Point addition failed: {e}")
        return False
    
    print("🎉 All basic pairing tests passed!")
    return True

if __name__ == "__main__":
    success = test_basic_pairing()
    if success:
        print("\n✅ Basic pairing operations work correctly")
    else:
        print("\n❌ Basic pairing operations have issues")
    sys.exit(0 if success else 1)