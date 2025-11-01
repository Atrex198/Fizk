#!/usr/bin/env python3
"""
Simple test with minimal ML constraints to debug verification
"""

import sys
import logging
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from groth16 import (
    R1CS,
    R1CSBuilder,
    Groth16TrustedSetup,
    Groth16Prover,
    Groth16Verifier
)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_simple_multiplication():
    """Test with just a few simple multiplication constraints"""
    logger.info("\n" + "="*70)
    logger.info("TEST: Simple multiplication constraints")
    logger.info("="*70)
    
    # Build R1CS with simple constraints
    builder = R1CSBuilder()
    r1cs = builder.initialize(num_variables=20)
    
    # Add simple constraints: 2 * 3 = 6, etc.
    for i in range(5):
        a = builder.allocate_variable(f"a_{i}")
        b = builder.allocate_variable(f"b_{i}")
        c = builder.allocate_variable(f"c_{i}")
        
        r1cs.add_multiplication_constraint(a, b, c)
        
        r1cs.set_witness(a, 2)
        r1cs.set_witness(b, 3)
        r1cs.set_witness(c, 6)
    
    r1cs = builder.finalize()
    logger.info(f"✅ Built R1CS: {r1cs.num_constraints} constraints")
    
    # Verify constraints are satisfied
    assert r1cs.verify_constraint_satisfaction(), "Constraints not satisfied!"
    logger.info(f"✅ All constraints satisfied")
    
    # Trusted setup
    logger.info("⏳ Running trusted setup...")
    setup = Groth16TrustedSetup(r1cs)
    pk, vk = setup.generate_keys()
    logger.info(f"✅ Setup complete")
    
    # Generate proof
    logger.info("⏳ Generating proof...")
    prover = Groth16Prover(pk, r1cs, setup)
    witness = r1cs.get_witness_vector()
    public_inputs = []
    
    proof = prover.generate_proof(witness, public_inputs)
    logger.info(f"✅ Proof generated")
    
    # Verify proof
    logger.info("⏳ Verifying proof...")
    verifier = Groth16Verifier(vk)
    is_valid = verifier.verify_proof(proof, public_inputs)
    
    if is_valid:
        logger.info(f"✅ Proof VALID!")
        return True
    else:
        logger.error(f"❌ Proof INVALID")
        return False


if __name__ == "__main__":
    try:
        success = test_simple_multiplication()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
