#!/usr/bin/env python3

"""
Test real KZG polynomial commitments with BN128
"""

import sys
import logging
from real_protostar_ivc import RealProtostarIVC, KZGCommitment, CURVE_ORDER, G1_GENERATOR, G2_GENERATOR, bn128

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_kzg():
    """Test real KZG polynomial commitments"""
    print("🔒 Testing Real KZG Polynomial Commitments")
    print("=" * 60)
    
    try:
        # Create small trusted setup
        print("📦 Generating trusted setup...")
        ivc = RealProtostarIVC(trusted_setup_size=10)
        srs = ivc.srs
        print(f"✅ SRS generated: {len(srs['tau_powers_g1'])} G1 points")
        
        # Test polynomial: p(x) = 5 + 3x + 2x²
        coeffs = [5, 3, 2]  # [a₀, a₁, a₂]
        print(f"📈 Testing polynomial: {coeffs[0]} + {coeffs[1]}x + {coeffs[2]}x²")
        
        # Create KZG commitment
        print("🔐 Creating KZG commitment...")
        commitment = KZGCommitment(coeffs, srs["tau_powers_g1"])
        print(f"✅ Commitment created: {commitment.commitment}")
        print(f"   Degree: {commitment.degree}")
        
        # Test evaluation and opening
        eval_point = 7
        print(f"🧮 Creating opening proof at x = {eval_point}...")
        
        evaluation, proof = commitment.create_opening(eval_point, srs["tau_powers_g1"], srs["tau_powers_g2"])
        
        # Verify expected evaluation: p(7) = 5 + 3*7 + 2*49 = 5 + 21 + 98 = 124
        expected = (5 + 3*7 + 2*7*7) % CURVE_ORDER
        print(f"📊 Evaluation at x={eval_point}: {evaluation}")
        print(f"📊 Expected: {expected}")
        print(f"✅ Evaluation correct: {evaluation == expected}")
        
        # Verify opening proof
        print("🔍 Verifying KZG opening proof...")
        verification_result = KZGCommitment.verify_opening(
            commitment.commitment, eval_point, evaluation, proof, srs["tau_powers_g2"]
        )
        
        print(f"🧪 Verification result: {'✅ VALID' if verification_result else '❌ INVALID'}")
        
        if verification_result:
            print("🎉 REAL KZG SUCCESS!")
            print("✅ Cryptographic polynomial commitment working")
            print("✅ BN128 elliptic curve operations functional")
            print("✅ Pairing-based verification successful")
            return True
        else:
            print("❌ KZG verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test error details:")
        return False

if __name__ == "__main__":
    success = test_real_kzg()
    sys.exit(0 if success else 1)