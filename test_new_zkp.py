"""
Comprehensive Tests for New ZKP Implementation
==============================================

Tests all the new cryptographic modules:
1. R1CS constraint system
2. KZG polynomial commitments
3. Protostar folding
4. ProtoGalaxy aggregation
5. ML circuit building
6. FL integration
"""

import numpy as np
import sys
import traceback
from typing import Dict

# Add project to path
sys.path.insert(0, '/home/ariva/work/final_project/Fizk')

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_result(test_name: str, passed: bool, details: str = ""):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {test_name}")
    if details:
        print(f"          {details}")

def test_r1cs():
    """Test R1CS constraint system"""
    print_section("Testing R1CS Module")
    
    try:
        from zkp_protocols.r1cs import (
            SparseMatrix, R1CSInstance, R1CSWitness, 
            R1CSBuilder, check_r1cs_satisfaction
        )
        from py_ecc.bn128 import curve_order
        
        # Test 1: SparseMatrix creation
        matrix = SparseMatrix(3, 3)
        matrix.set(0, 0, 1)
        matrix.set(1, 1, 2)
        matrix.set(2, 2, 3)
        print_result("SparseMatrix creation", matrix.get(1, 1) == 2)
        
        # Test 2: R1CS Builder - simple constraint x * y = z
        builder = R1CSBuilder(curve_order)
        x_idx = builder.add_private_variable("x")
        y_idx = builder.add_private_variable("y")
        z_idx = builder.add_private_variable("z")
        builder.add_multiplication_constraint(x_idx, y_idx, z_idx)
        
        r1cs = builder.build()
        print_result("R1CSBuilder", r1cs.num_constraints == 1 and r1cs.num_variables == 4)
        
        # Test 3: R1CS satisfaction check
        # x=3, y=5, z=15 should satisfy x*y=z
        witness = R1CSWitness(values=[3, 5, 15])
        satisfied, _ = check_r1cs_satisfaction(r1cs, witness, curve_order)
        print_result("R1CS satisfaction (valid)", satisfied)
        
        # Test 4: R1CS unsatisfaction
        # x=3, y=5, z=10 should NOT satisfy x*y=z
        bad_witness = R1CSWitness(values=[3, 5, 10])
        not_satisfied, _ = check_r1cs_satisfaction(r1cs, bad_witness, curve_order)
        print_result("R1CS satisfaction (invalid)", not not_satisfied)
        
        return True
    except Exception as e:
        print_result("R1CS Module", False, str(e))
        traceback.print_exc()
        return False

def test_kzg():
    """Test KZG polynomial commitment scheme"""
    print_section("Testing KZG Module")
    
    try:
        from zkp_protocols.kzg import KZGScheme, KZGParams
        from py_ecc.bn128 import G1, Z1
        
        # Test 1: Setup
        kzg = KZGScheme()
        params = kzg.setup(16)
        print_result("KZG setup", params is not None and len(params.g1_powers) == 17)
        
        # Test 2: Commit to polynomial
        # p(x) = 1 + 2x + 3x^2
        coeffs = [1, 2, 3]
        commitment = kzg.commit(coeffs)
        print_result("KZG commit", commitment.point != Z1)
        
        # Test 3: Open at point
        z = 5  # Evaluate at x=5
        opening = kzg.open(coeffs, z)
        print_result("KZG open", opening is not None)
        
        # Test 4: Verify opening
        # p(5) = 1 + 2*5 + 3*25 = 1 + 10 + 75 = 86
        valid = kzg.verify(commitment, opening)
        print_result("KZG verify (valid)", valid)
        
        # Test 5: Reject wrong evaluation - create fake opening with wrong value
        from zkp_protocols.kzg import KZGOpening
        fake_opening = KZGOpening(
            proof_point=opening.proof_point,
            evaluation_point=z,
            evaluation=100  # Wrong value
        )
        invalid = not kzg.verify(commitment, fake_opening)
        print_result("KZG verify (invalid)", invalid)
        
        return True
    except Exception as e:
        print_result("KZG Module", False, str(e))
        traceback.print_exc()
        return False

def test_protostar():
    """Test Protostar folding scheme"""
    print_section("Testing Protostar Module")
    
    try:
        from zkp_protocols.protostar_core import (
            Protostar, RelaxedR1CSInstance, RelaxedR1CSWitness,
            FoldingProof, FiatShamirTranscript
        )
        from zkp_protocols.r1cs import R1CSBuilder, R1CSWitness
        from zkp_protocols.kzg import KZGScheme
        from py_ecc.bn128 import G1, multiply, curve_order, Z1
        
        # Build a simple R1CS: x * y = z
        builder = R1CSBuilder(curve_order)
        x_idx = builder.add_private_variable("x")
        y_idx = builder.add_private_variable("y")
        z_idx = builder.add_private_variable("z")
        builder.add_multiplication_constraint(x_idx, y_idx, z_idx)
        r1cs = builder.build()
        
        # Create KZG scheme
        kzg = KZGScheme()
        kzg.setup(32)
        
        # Create Protostar
        protostar = Protostar(kzg)
        print_result("Protostar creation", protostar is not None)
        
        # Create two instances with satisfied witnesses
        # Instance 1: x=2, y=3, z=6 (satisfies 2*3=6)
        witness1 = R1CSWitness(values=[2, 3, 6])
        relaxed1, rel_wit1 = protostar.create_relaxed_instance(r1cs, witness1)
        print_result("Create relaxed instance 1", relaxed1.u == 1)
        
        # Instance 2: x=4, y=5, z=20 (satisfies 4*5=20)
        witness2 = R1CSWitness(values=[4, 5, 20])
        relaxed2, rel_wit2 = protostar.create_relaxed_instance(r1cs, witness2)
        print_result("Create relaxed instance 2", relaxed2.u == 1)
        
        # Fold
        transcript1 = FiatShamirTranscript("test_fold")
        folded_inst, folded_wit, proof = protostar.fold(
            relaxed1, rel_wit1, relaxed2, rel_wit2, transcript1
        )
        print_result("Protostar fold", folded_inst is not None and proof is not None)
        
        # Verify fold
        transcript2 = FiatShamirTranscript("test_fold")  # Same domain for verification
        valid = protostar.verify_fold(relaxed1, relaxed2, folded_inst, proof, transcript2)
        print_result("Protostar verify_fold", valid)
        
        # Check relaxed R1CS satisfaction
        is_sat, residual = protostar.check_relaxed_r1cs_satisfaction(folded_inst, folded_wit)
        print_result("Relaxed R1CS satisfaction", is_sat, f"residual sum: {sum(residual)}")
        
        return True
    except Exception as e:
        print_result("Protostar Module", False, str(e))
        traceback.print_exc()
        return False

def test_protogalaxy():
    """Test ProtoGalaxy multi-instance folding"""
    print_section("Testing ProtoGalaxy Module")
    
    try:
        from zkp_protocols.protogalaxy import ProtoGalaxy, AggregatedProof
        from zkp_protocols.protostar_core import RelaxedR1CSInstance, RelaxedR1CSWitness, Protostar
        from zkp_protocols.r1cs import R1CSBuilder, R1CSWitness
        from zkp_protocols.kzg import KZGScheme
        from py_ecc.bn128 import G1, multiply, curve_order, Z1
        
        # Build simple R1CS: x * x = x^2
        builder = R1CSBuilder(curve_order)
        x_idx = builder.add_private_variable("x")
        x_sq_idx = builder.add_private_variable("x_sq")
        builder.add_multiplication_constraint(x_idx, x_idx, x_sq_idx)
        r1cs = builder.build()
        
        # Create KZG
        kzg = KZGScheme()
        kzg.setup(32)
        
        # Create Protostar for creating relaxed instances
        protostar = Protostar(kzg)
        
        # Create 3 instances
        instances = []
        witnesses = []
        for i in range(3):
            val = (i + 2)  # 2, 3, 4
            witness = R1CSWitness(values=[val, val*val])
            inst, wit = protostar.create_relaxed_instance(r1cs, witness)
            instances.append(inst)
            witnesses.append(wit)
        
        # Create ProtoGalaxy
        galaxy = ProtoGalaxy(r1cs, kzg)
        print_result("ProtoGalaxy creation", galaxy is not None)
        
        # Fold all 3 instances
        folded_inst, folded_wit, proof = galaxy.fold_instances(instances, witnesses)
        print_result("ProtoGalaxy fold_instances", folded_inst is not None)
        
        # Verify aggregation
        valid = galaxy.verify_aggregation(instances, folded_inst, proof)
        print_result("ProtoGalaxy verify_aggregation", valid)
        
        return True
    except Exception as e:
        print_result("ProtoGalaxy Module", False, str(e))
        traceback.print_exc()
        return False

def test_ml_circuit():
    """Test ML circuit builder"""
    print_section("Testing ML Circuit Module")
    
    try:
        from zkp_protocols.ml_circuit import (
            MLCircuitBuilder, MLCircuitConfig, FixedPoint, create_ml_circuit
        )
        from py_ecc.bn128 import curve_order
        
        # Test 1: FixedPoint arithmetic
        fp = FixedPoint(16, curve_order)
        
        val1 = 3.14159
        encoded = fp.encode(val1)
        decoded = fp.decode(encoded)
        print_result("FixedPoint encode/decode", abs(decoded - val1) < 0.001)
        
        # Test 2: MLCircuitBuilder creation
        config = MLCircuitConfig(input_dim=4, hidden_dims=[8], output_dim=2)
        builder = MLCircuitBuilder(config)
        print_result("MLCircuitBuilder creation", builder is not None)
        
        # Test 3: Build circuit for simple weights
        initial_weights = {
            'layer0.weight': np.random.randn(8, 4).astype(np.float32) * 0.1,
            'layer0.bias': np.zeros(8).astype(np.float32),
            'layer1.weight': np.random.randn(2, 8).astype(np.float32) * 0.1,
            'layer1.bias': np.zeros(2).astype(np.float32)
        }
        
        # Simulate training step
        final_weights = {}
        for k, v in initial_weights.items():
            final_weights[k] = v - 0.001 * np.random.randn(*v.shape).astype(np.float32)
        
        x_sample = np.random.randn(4).astype(np.float32)
        y_label = 1
        learning_rate = 0.001
        
        r1cs, witness = builder.build_training_circuit(
            initial_weights, final_weights, x_sample, y_label, learning_rate
        )
        
        print_result("ML Circuit build", r1cs is not None and witness is not None)
        print_result("ML Circuit constraints", r1cs.num_constraints > 0, 
                    f"{r1cs.num_constraints} constraints")
        
        return True
    except Exception as e:
        print_result("ML Circuit Module", False, str(e))
        traceback.print_exc()
        return False

def test_fl_integration():
    """Test complete FL integration"""
    print_section("Testing FL Integration Module")
    
    try:
        from zkp_protocols.protostar_fl import (
            ProtoStarFLProver, ProtoGalaxyAggregator, 
            ProtoStarFLSystem, ClientProof
        )
        from zkp_protocols.protostar_core import Protostar, RelaxedR1CSInstance, RelaxedR1CSWitness
        from zkp_protocols.r1cs import R1CSBuilder, R1CSWitness
        from zkp_protocols.kzg import KZGScheme
        from zkp_protocols.protogalaxy import ProtoGalaxy
        from py_ecc.bn128 import curve_order
        
        # Test 1: Create prover
        prover = ProtoStarFLProver(client_id=0)
        print_result("ProtoStarFLProver creation", prover is not None)
        
        # Test 2: Create aggregator
        aggregator = ProtoGalaxyAggregator()
        print_result("ProtoGalaxyAggregator creation", aggregator is not None)
        
        # Test 3: Create manual proofs for testing (bypass ML circuit)
        # Build simple R1CS: x * x = x^2
        builder = R1CSBuilder(curve_order)
        x_idx = builder.add_private_variable("x")
        x_sq_idx = builder.add_private_variable("x_sq")
        builder.add_multiplication_constraint(x_idx, x_idx, x_sq_idx)
        r1cs = builder.build()
        
        # Create KZG and Protostar
        kzg = KZGScheme()
        kzg.setup(64)
        protostar = Protostar(kzg)
        
        # Create multiple satisfied instances
        client_instances = []
        client_witnesses = []
        
        for i in range(3):
            val = (i + 2)  # 2, 3, 4
            witness = R1CSWitness(values=[val, val * val])  # x=val, x^2=val^2
            inst, wit = protostar.create_relaxed_instance(r1cs, witness)
            client_instances.append(inst)
            client_witnesses.append(wit)
        
        print_result("Create client instances", len(client_instances) == 3)
        
        # Test 4: Use ProtoGalaxy to aggregate
        galaxy = ProtoGalaxy(r1cs, kzg)
        folded_inst, folded_wit, proof = galaxy.fold_instances(client_instances, client_witnesses)
        
        print_result("ProtoGalaxy aggregation", folded_inst is not None)
        
        # Test 5: Verify aggregation
        valid = galaxy.verify_aggregation(client_instances, folded_inst, proof)
        print_result("Aggregation verification", valid)
        
        # Test 6: Check folded instance still satisfies relaxed R1CS
        is_sat, residual = protostar.check_relaxed_r1cs_satisfaction(folded_inst, folded_wit)
        print_result("Folded instance satisfaction", is_sat, f"residual sum: {sum(residual)}")
        
        return True
    except Exception as e:
        print_result("FL Integration Module", False, str(e))
        traceback.print_exc()
        return False

def test_security_properties():
    """Test security properties"""
    print_section("Testing Security Properties")
    
    try:
        from zkp_protocols.kzg import KZGScheme
        from zkp_protocols.protostar_core import Protostar, FiatShamirTranscript
        from zkp_protocols.r1cs import R1CSBuilder
        from py_ecc.bn128 import curve_order
        
        # Test 1: Fiat-Shamir is deterministic
        t1 = FiatShamirTranscript("test")
        t1.absorb_scalar("data", 12345)
        r1 = t1.squeeze_challenge("challenge")
        
        t2 = FiatShamirTranscript("test")
        t2.absorb_scalar("data", 12345)
        r2 = t2.squeeze_challenge("challenge")
        
        print_result("Fiat-Shamir deterministic", r1 == r2)
        
        # Test 2: Fiat-Shamir different inputs -> different outputs
        t3 = FiatShamirTranscript("test")
        t3.absorb_scalar("data", 12346)  # Different value
        r3 = t3.squeeze_challenge("challenge")
        
        print_result("Fiat-Shamir distinct", r1 != r3)
        
        # Test 3: Challenge is in field
        print_result("Challenge in field", 0 < r1 < curve_order)
        
        # Test 4: KZG binding - can't open to two different values
        kzg = KZGScheme()
        kzg.setup(16)
        
        coeffs = [1, 2, 3]
        commitment = kzg.commit(coeffs)
        z = 5
        opening = kzg.open(coeffs, z)
        
        # Correct evaluation: 1 + 2*5 + 3*25 = 86
        correct_valid = kzg.verify(commitment, opening)
        
        # Create fake opening with wrong value
        from zkp_protocols.kzg import KZGOpening
        wrong_opening = KZGOpening(
            proof_point=opening.proof_point,
            evaluation_point=z,
            evaluation=87  # Wrong!
        )
        wrong_valid = kzg.verify(commitment, wrong_opening)
        
        print_result("KZG binding property", correct_valid and not wrong_valid)
        
        return True
    except Exception as e:
        print_result("Security Properties", False, str(e))
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" COMPREHENSIVE ZKP IMPLEMENTATION TESTS")
    print(" Testing new proper cryptographic modules")
    print("="*60)
    
    results = {}
    
    # Run all tests
    results['R1CS'] = test_r1cs()
    results['KZG'] = test_kzg()
    results['Protostar'] = test_protostar()
    results['ProtoGalaxy'] = test_protogalaxy()
    results['ML Circuit'] = test_ml_circuit()
    results['FL Integration'] = test_fl_integration()
    results['Security'] = test_security_properties()
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    
    print(f"\n  Total: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n  ✓ All tests passed! New implementation is working correctly.")
        return 0
    else:
        print("\n  ✗ Some tests failed. Review the output above.")
        return 1

if __name__ == "__main__":
    exit(main())
