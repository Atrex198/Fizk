#!/usr/bin/env python3
"""
Test script to verify the expanded constraint count
"""

import numpy as np
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from zkp_protocols.complete_r1cs_circuit import MLCircuitR1CS
from real_ml_trainer import RealMLTrainer, TrainingConfig
from real_dataset_loader import RealDatasetLoader

def test_constraint_count():
    """Test the constraint generation with real ML training"""
    print("🔧 Testing expanded constraint generation...")
    
    # Document the expected constraint count
    documented_constraints = 5963
    
    # Load real dataset
    print("📊 Loading cardio dataset...")
    dataset_loader = RealDatasetLoader()
    X_train, y_train = dataset_loader.load_dataset("cardio")
    
    # Take a small subset for training (faster testing)
    X_subset = X_train[:1000]  # 1000 samples
    y_subset = y_train[:1000]
    
    print(f"   Using {len(X_subset)} samples for testing")
    
    # Train a model to get real weights
    print("🔥 Training model to get real weights...")
    trainer = RealMLTrainer(
        input_features=X_subset.shape[1],
        config=TrainingConfig(
            learning_rate=0.01,
            batch_size=32,
            local_epochs=2,  # Short training for testing
            optimizer="adam"
        )
    )
    
    # Train the model
    result = trainer.train_local_model(X_subset, y_subset)
    
    print(f"   Training complete: accuracy={result.final_accuracy:.4f}, loss={result.final_loss:.4f}")
    
    # Create initial weights (simulate pre-training state)
    initial_weights = {}
    for key, value in result.model_parameters.items():
        # Create slightly different initial weights
        if hasattr(value, 'shape'):
            noise = np.random.normal(0, 0.01, value.shape)
            initial_weights[key] = value - noise
        else:
            initial_weights[key] = value - 0.01
    
    # Generate circuit with expanded constraints
    print("⚡ Generating R1CS circuit with expanded constraints...")
    
    circuit_gen = MLCircuitR1CS(curve_order=21888242871839275222246405745257275088548364400416034343698204186575808495617)
    
    # Use first sample for circuit generation
    X_sample = X_subset[0]
    y_sample = int(y_subset[0])
    
    try:
        constraints, witness = circuit_gen.generate_full_ml_circuit(
            initial_weights=initial_weights,
            final_weights=result.model_parameters,
            X_sample=X_sample,
            y_sample=y_sample,
            learning_rate=0.01,
            claimed_loss=result.final_loss
        )
        
        print(f"\n✅ SUCCESS! Generated circuit:")
        print(f"   🔢 Constraints: {len(constraints)}")
        print(f"   🔍 Witness size: {len(witness)}")
        print(f"   📊 Constraint-to-witness ratio: {len(constraints) / len(witness):.3f}")
        
        # Verify constraint satisfaction
        print(f"\n🔍 Verifying constraint satisfaction...")
        is_satisfied = circuit_gen.verify_constraint_satisfaction(constraints, witness)
        
        if is_satisfied:
            print(f"✅ All constraints satisfied!")
        else:
            print(f"❌ Constraint satisfaction failed!")
            
        # Compare to documented claim
        documented_constraints = 5963
        actual_constraints = len(constraints)
        percentage = (actual_constraints / documented_constraints) * 100
        
        print(f"\n📋 Comparison to documentation:")
        print(f"   📝 Documented: {documented_constraints} constraints")
        print(f"   ⚡ Actual: {actual_constraints} constraints")
        print(f"   📊 Achievement: {percentage:.1f}% of documented goal")
        
        if actual_constraints >= documented_constraints:
            print(f"🎉 SUCCESS: Exceeded documented constraint count!")
        elif actual_constraints >= documented_constraints * 0.8:
            print(f"✅ GOOD: Within 20% of documented constraint count")
        elif actual_constraints >= documented_constraints * 0.5:
            print(f"⚠️  FAIR: Within 50% of documented constraint count")
        else:
            print(f"❌ POOR: Significantly below documented constraint count")
            
        return actual_constraints, documented_constraints
        
    except Exception as e:
        print(f"❌ Circuit generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, documented_constraints

if __name__ == "__main__":
    test_constraint_count()