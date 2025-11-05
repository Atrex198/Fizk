#!/usr/bin/env python3
"""
Deep Dive Script: Find the exact fallback location

This script will trace through the proof generation process step by step
to find exactly where the system falls back to 19 constraints.
"""

import os
import sys
import json
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def trace_proof_generation_step_by_step():
    """Trace proof generation with detailed logging"""
    print('=== STEP-BY-STEP PROOF GENERATION TRACE ===')
    print()
    
    try:
        from zkp_protocols.protostar_production import ProductionProtostar
        from zkp_protocols.base import TrainingStatement, TrainingWitness
        
        # Monkey patch to add logging
        original_build_circuit = ProductionProtostar._build_ml_circuit
        
        def logged_build_circuit(self, statement, witness):
            print(f'🔍 _build_ml_circuit called with:')
            print(f'   Statement: {statement.model_architecture}')
            print(f'   Witness weights: {list(witness.initial_weights.keys())}')
            print(f'   Witness samples: {witness.dataset_samples.shape}')
            
            try:
                result = original_build_circuit(self, statement, witness)
                print(f'✅ _build_ml_circuit succeeded: {len(result[0])} constraints, {len(result[1])} witness')
                return result
            except Exception as e:
                print(f'❌ _build_ml_circuit FAILED: {e}')
                print(f'🔍 Exception type: {type(e).__name__}')
                import traceback
                traceback.print_exc()
                raise
        
        # Apply monkey patch
        ProductionProtostar._build_ml_circuit = logged_build_circuit
        
        print('✅ Applied logging monkey patch')
        
        # Create test instance
        protostar = ProductionProtostar(security_level=128)
        
        print('🔧 Setting up protostar...')
        setup_params = protostar.setup()
        print(f'✅ Setup complete: {setup_params["srs_size"]} SRS elements')
        
        # Create test data
        print('🔧 Creating test data...')
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
        
        print('✅ Test data created')
        
        # Generate proof with detailed tracing
        print('🔧 Generating proof...')
        proof = protostar.generate_proof(statement, witness)
        
        # Extract final constraint count from proof
        proof_data = proof.proof_data
        constraints_info = proof_data.get('constraints', {})
        final_count = constraints_info.get('count', 'MISSING')
        final_witness = constraints_info.get('witness_size', 'MISSING')
        
        print(f'🎯 FINAL PROOF: {final_count} constraints, {final_witness} witness')
        
        return proof, final_count, final_witness
        
    except Exception as e:
        print(f'❌ Detailed trace failed: {e}')
        import traceback
        traceback.print_exc()
        return None, None, None

def find_alternative_circuit_generators():
    """Search for alternative circuit generators that might be used as fallbacks"""
    print('=== SEARCHING FOR ALTERNATIVE CIRCUIT GENERATORS ===')
    print()
    
    # Look for other circuit generation methods
    circuit_generators = []
    
    for root, dirs, files in os.walk('../zkp_protocols'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Look for circuit generation patterns
                    if 'def ' in content and 'circuit' in content.lower():
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'def ' in line and 'circuit' in line.lower():
                                circuit_generators.append((filepath, i+1, line.strip()))
                except:
                    pass
    
    print('Found circuit generation methods:')
    for filepath, line_num, line_content in circuit_generators:
        print(f'  {filepath}:{line_num} - {line_content}')
    
    return circuit_generators

def analyze_proof_structure():
    """Analyze the structure of generated proofs to understand the constraint count"""
    print('=== ANALYZING EXISTING PROOF STRUCTURE ===')
    print()
    
    # Look at an existing proof in detail
    proof_path = '../production_zkp_fl_results_real/run_20251009_075239_clients3_rounds3/proofs/client_0/round_1_proof.json'
    
    if os.path.exists(proof_path):
        with open(proof_path) as f:
            proof = json.load(f)
        
        print('Proof structure analysis:')
        print(f'  Protocol: {proof["proof_data"]["protocol"]}')
        print(f'  Version: {proof["proof_data"]["version"]}')
        
        # Check constraints section
        constraints = proof['proof_data'].get('constraints', {})
        print(f'  Constraint count: {constraints.get("count", "MISSING")}')
        print(f'  Witness size: {constraints.get("witness_size", "MISSING")}')
        
        # Check cryptographic properties
        crypto_props = proof['proof_data'].get('cryptographic_properties', {})
        print('  Cryptographic properties:')
        for prop, value in crypto_props.items():
            print(f'    {prop}: {value}')
        
        # Check if this looks like a real complex proof or a simple one
        witness_size = constraints.get('witness_size', 0)
        constraint_count = constraints.get('count', 0)
        
        if isinstance(witness_size, int) and isinstance(constraint_count, int):
            if constraint_count < 100:
                print(f'  🚨 SUSPICIOUS: Only {constraint_count} constraints (should be thousands)')
                print(f'  🚨 This looks like a TOY CIRCUIT, not a real ML circuit')
            else:
                print(f'  ✅ Reasonable constraint count: {constraint_count}')
        
        return proof
    else:
        print('No existing proof found for analysis')
        return None

def test_circuit_generation_isolation():
    """Test circuit generation in isolation to see what it really produces"""
    print('=== ISOLATED CIRCUIT GENERATION TEST ===')
    print()
    
    try:
        # Test the complete R1CS circuit directly
        from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS
        from py_ecc.bn128.bn128_curve import curve_order
        
        circuit_gen = MLCircuitR1CS(curve_order)
        
        # Create test weights
        test_weights = {
            'network.0.weight': np.random.randn(64, 11),
            'network.0.bias': np.random.randn(64),
            'network.4.weight': np.random.randn(32, 64), 
            'network.4.bias': np.random.randn(32),
            'network.8.weight': np.random.randn(2, 32),
            'network.8.bias': np.random.randn(2)
        }
        
        X_sample = np.random.randn(11)
        y_sample = 0
        
        print('Testing complete circuit generation...')
        constraints, witness_values = circuit_gen.generate_full_ml_circuit(
            initial_weights=test_weights,
            final_weights=test_weights,
            X_sample=X_sample,
            y_sample=y_sample,
            learning_rate=0.01,
            claimed_loss=0.5
        )
        
        print(f'✅ Isolated circuit generation: {len(constraints)} constraints')
        print(f'✅ Isolated witness generation: {len(witness_values)} variables')
        
        # Verify constraint satisfaction
        is_satisfied = circuit_gen.verify_constraint_satisfaction(constraints, witness_values)
        print(f'✅ Constraint satisfaction: {is_satisfied}')
        
        return len(constraints), len(witness_values), is_satisfied
        
    except Exception as e:
        print(f'❌ Isolated circuit test failed: {e}')
        import traceback
        traceback.print_exc()
        return None, None, None

def main():
    """Main deep dive function"""
    print('🔬 DEEP DIVE: FINDING THE EXACT FALLBACK LOCATION')
    print('=' * 60)
    print()
    
    # Test 1: Analyze existing proof structure
    existing_proof = analyze_proof_structure()
    
    # Test 2: Test isolated circuit generation
    iso_constraints, iso_witness, iso_satisfied = test_circuit_generation_isolation()
    
    # Test 3: Find alternative circuit generators
    alt_generators = find_alternative_circuit_generators()
    
    # Test 4: Trace step-by-step proof generation
    traced_proof, traced_constraints, traced_witness = trace_proof_generation_step_by_step()
    
    # Summary and conclusions
    print('\n' + '=' * 60)
    print('🎯 DEEP DIVE CONCLUSIONS')
    print('=' * 60)
    
    if iso_constraints:
        print(f'Isolated complete circuit: {iso_constraints} constraints')
    
    if traced_constraints and traced_constraints != 'MISSING':
        print(f'Traced proof generation: {traced_constraints} constraints')
        
        if iso_constraints and iso_constraints != int(traced_constraints):
            print(f'🚨 SMOKING GUN: Isolated circuit produces {iso_constraints} constraints')
            print(f'🚨 But traced proof only has {traced_constraints} constraints')
            print(f'🚨 There is a FALLBACK mechanism between circuit generation and proof!')
        else:
            print(f'✅ Constraint counts match - no fallback detected')
    
    print(f'\nAlternative circuit generators found: {len(alt_generators)}')
    for generator in alt_generators:
        print(f'  - {generator[0]}:{generator[1]}')

if __name__ == '__main__':
    main()