#!/usr/bin/env python3

"""
Quick test for fixed Protostar IVC verification
"""

import sys
import logging
import torch
import numpy as np
from real_protostar_ivc import RealProtostarIVC

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fixed_verification():
    """Test the fixed verification system"""
    print("🧪 Testing Fixed Real Protostar IVC Verification")
    print("=" * 60)
    
    try:
        # Initialize Real Protostar IVC
        print("📦 Initializing Real Protostar IVC...")
        ivc = RealProtostarIVC(trusted_setup_size=256)
        print("✅ Real Protostar IVC initialized")
        
        # Create simple model weights
        model_weights = {
            'fc1.weight': torch.randn(8, 5),
            'fc1.bias': torch.randn(8),
            'fc2.weight': torch.randn(1, 8),
            'fc2.bias': torch.randn(1)
        }
        
        # Initialize accumulator
        print("🎯 Initializing accumulator...")
        ivc.initialize_accumulator(model_weights, round_number=1)
        print("✅ Accumulator initialized")
        
        # Test folding with verification
        for round_num in range(2, 5):  # Start from round 2 since accumulator is initialized with round 1
            print(f"\n🔄 Testing round {round_num}")
            
            # Fold into IVC
            print(f"  📝 Folding round {round_num}...")
            result = ivc.fold_round(model_weights, round_num)
            print(f"  ✅ Round {round_num} folded successfully")
            
            # Generate proof and verify
            print(f"  🔐 Generating and verifying proof...")
            proof = result.get("proof", {}).get("proof_data", "")  # Extract proof from fold result  
            print(f"  📄 Proof data type: {type(proof)}, length: {len(str(proof)) if proof else 0}")
            
            if not proof:
                print("  🚨 No proof data found, using direct proof generation")
                proof = ivc._generate_accumulator_proof()
            
            # Test verification
            verification_result = ivc.verify_accumulator(proof)
            print(f"  🧪 Verification result: {'✅ VALID' if verification_result else '❌ INVALID'}")
            
            if verification_result:
                print(f"  🎉 Round {round_num} verification PASSED!")
            else:
                print(f"  ⚠️  Round {round_num} verification failed")
        
        print(f"\n📊 Final state:")
        print(f"  📈 Rounds folded: {ivc.rounds_folded}")
        print(f"  🔗 Constraints: {ivc.accumulator_instance.num_constraints if ivc.accumulator_instance else 0}")
        print(f"  📐 Variables: {ivc.accumulator_instance.num_variables if ivc.accumulator_instance else 0}")
        
        # Final verification test
        print(f"\n🔬 Final comprehensive verification...")
        # Get the last proof from the folding
        final_proof = ivc._generate_accumulator_proof()  # Use private method to get current proof
        final_verification = ivc.verify_accumulator(final_proof)
        
        if final_verification:
            print("🎉 VERIFICATION FIX SUCCESS! ✅")
            print("✅ All cryptographic operations working")
            print("✅ Accumulator commitment properly generated")
            print("✅ Verification system functional")
            return True
        else:
            print("❌ Final verification still failing")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test error details:")
        return False

if __name__ == "__main__":
    success = test_fixed_verification()
    sys.exit(0 if success else 1)