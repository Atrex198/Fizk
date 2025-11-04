#!/usr/bin/env python3
"""
Investigation Script: Find the 19-constraint fallback mechanism

This script will help us identify where the system is falling back to a simple
19-constraint circuit instead of using the full 8,281-constraint circuit.
"""

import os
import sys
import json
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_constraint_count_discrepancy():
    """Test the major discrepancy between claimed and actual constraints"""
    print('=== CONSTRAINT COUNT DISCREPANCY ANALYSIS ===')
    print()
    
    # Check README claims vs actual proof data
    with open('../README.md', 'r') as f:
        readme = f.read()
        if '5963 constraints' in readme:
            print('README claims: 5963 constraints')
        else:
            print('README claims: No specific constraint count found')
    
    # Check actual proof data
    proof_path = '../production_zkp_fl_results_real/run_20251009_075239_clients3_rounds3/proofs/client_0/round_1_proof.json'
    if os.path.exists(proof_path):
        with open(proof_path) as f:
            proof = json.load(f)
        constraints = proof['proof_data'].get('constraints', {})
        actual_count = constraints.get('count', 'MISSING')
        actual_witness = constraints.get('witness_size', 'MISSING')
        
        print(f'Actual proof: {actual_count} constraints, {actual_witness} witness')
        if actual_count != 'MISSING':
            discrepancy = 5963 / int(actual_count)
            print(f'Discrepancy: 5963 vs {actual_count} = {discrepancy:.1f}x overstatement')
        else:
            print('Discrepancy: Cannot calculate - missing constraint count')
    
    print()

def test_complete_circuit_generation():
    """Test what the complete R1CS circuit actually produces"""
    print('=== COMPLETE CIRCUIT GENERATION TEST ===')
    print()
    
    try:
        from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS
        from py_ecc.bn128.bn128_curve import curve_order
        
        print('✓ Successfully imported MLCircuitR1CS')
        
        # Create test instance
        circuit_gen = MLCircuitR1CS(curve_order)
        
        # Create realistic test data
        fake_weights = {
            'network.0.weight': np.random.randn(64, 11),
            'network.0.bias': np.random.randn(64),
            'network.4.weight': np.random.randn(32, 64), 
            'network.4.bias': np.random.randn(32),
            'network.8.weight': np.random.randn(2, 32),
            'network.8.bias': np.random.randn(2)
        }
        
        X_sample = np.random.randn(11)
        y_sample = 0
        
        print('✓ Created test data')
        
        # Generate the complete circuit
        constraints, witness_values = circuit_gen.generate_full_ml_circuit(
            initial_weights=fake_weights,
            final_weights=fake_weights,
            X_sample=X_sample,
            y_sample=y_sample,
            learning_rate=0.01,
            claimed_loss=0.5
        )
        
        print(f'🎯 COMPLETE CIRCUIT PRODUCES: {len(constraints)} constraints')
        print(f'🎯 COMPLETE CIRCUIT WITNESS: {len(witness_values)} variables')
        print(f'🎯 This is what SHOULD be in the proofs!')
        
        return len(constraints), len(witness_values)
        
    except Exception as e:
        print(f'❌ Complete circuit generation failed: {e}')
        import traceback
        traceback.print_exc()
        return None, None

def search_for_fallback_mechanism():
    """Search for the fallback mechanism that creates 19-constraint circuits"""
    print('=== SEARCHING FOR FALLBACK MECHANISM ===')
    print()
    
    # Search for hardcoded simple circuits
    fallback_patterns = [
        '19', 'simple', 'toy', 'demo', 'fallback', 'simplified'
    ]
    
    for root, dirs, files in os.walk('../zkp_protocols'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Look for suspicious patterns
                    for pattern in fallback_patterns:
                        if pattern in content.lower() and 'constraint' in content.lower():
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if pattern in line.lower() and 'constraint' in line.lower():
                                    print(f'Suspicious pattern "{pattern}" in: {filepath}')
                                    print(f'  Line {i+1}: {line.strip()}')
                                    break
                except:
                    pass

def test_protostar_circuit_integration():
    """Test how protostar integrates with the circuit generator"""
    print('=== PROTOSTAR CIRCUIT INTEGRATION TEST ===')
    print()
    
    try:
        from zkp_protocols.protostar_production import ProductionProtostar
        from zkp_protocols.base import TrainingStatement, TrainingWitness
        
        print('✓ Imports successful')
        
        # Create minimal test
        protostar = ProductionProtostar(security_level=128)
        protostar.setup()  # Initialize SRS
        
        # Create test data
        statement = TrainingStatement(
            model_architecture='FederatedNN',
            initial_weights_commitment='test_initial',
            final_weights_commitment='test_final', 
            dataset_commitment='test_dataset',
            local_epochs=5,
            batch_size=64,
            learning_rate=0.01,
            claimed_accuracy=0.7,
            claimed_loss=0.5,
            sample_count=1000,
            round_number=1,
            client_id='test_client',
            timestamp=1234567890
        )
        
        fake_weights = {
            'network.0.weight': np.random.randn(64, 11),
            'network.0.bias': np.random.randn(64),
            'network.4.weight': np.random.randn(32, 64), 
            'network.4.bias': np.random.randn(32),
            'network.8.weight': np.random.randn(2, 32),
            'network.8.bias': np.random.randn(2)
        }
        
        witness = TrainingWitness(
            initial_weights=fake_weights,
            final_weights=fake_weights,
            dataset_samples=np.random.randn(10, 11),
            dataset_labels=np.random.randint(0, 2, 10)
        )
        
        print('✓ Created test statement and witness')
        
        # Test circuit building through protostar
        print('\nTesting protostar._build_ml_circuit:')
        constraints, witness_vals = protostar._build_ml_circuit(statement, witness)
        print(f'Protostar circuit generation: {len(constraints)} constraints, {len(witness_vals)} witness')
        
        # Test full proof generation
        print('\nTesting full proof generation:')
        proof = protostar.generate_proof(statement, witness)
        proof_constraints = proof.proof_data.get('constraints', {})
        proof_count = proof_constraints.get('count', 'MISSING')
        proof_witness = proof_constraints.get('witness_size', 'MISSING')
        
        print(f'Generated proof: {proof_count} constraints, {proof_witness} witness')
        
        return constraints, witness_vals, proof_count, proof_witness
        
    except Exception as e:
        print(f'❌ Protostar integration test failed: {e}')
        import traceback
        traceback.print_exc()
        return None, None, None, None

def main():
    """Main investigation function"""
    print('🔍 INVESTIGATING ZKP-FL FALLBACK MECHANISM')
    print('=' * 60)
    print()
    
    # Test 1: Constraint count discrepancy
    test_constraint_count_discrepancy()
    
    # Test 2: Complete circuit generation
    complete_constraints, complete_witness = test_complete_circuit_generation()
    
    # Test 3: Search for fallback mechanism
    search_for_fallback_mechanism()
    
    # Test 4: Protostar integration
    proto_constraints, proto_witness, proof_constraints, proof_witness = test_protostar_circuit_integration()
    
    # Summary
    print('\n' + '=' * 60)
    print('🎯 INVESTIGATION SUMMARY')
    print('=' * 60)
    
    if complete_constraints:
        print(f'Complete circuit produces: {complete_constraints} constraints')
    
    if proto_constraints:
        print(f'Protostar circuit produces: {len(proto_constraints)} constraints')
    
    if proof_constraints:
        print(f'Final proof contains: {proof_constraints} constraints')
    
    if complete_constraints and proof_constraints and proof_constraints != 'MISSING':
        if complete_constraints != int(proof_constraints):
            print(f'🚨 MISMATCH DETECTED: {complete_constraints} vs {proof_constraints}')
            print('🚨 The system is NOT using the complete circuit in proofs!')
        else:
            print('✅ Circuit and proof constraint counts match')

if __name__ == '__main__':
    main()