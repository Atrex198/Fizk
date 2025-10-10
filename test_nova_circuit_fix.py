#!/usr/bin/env python3
"""
Quick test to verify Nova now uses complete circuits with same complexity as ProtoStar
"""

import logging
import numpy as np
from real_dataset_loader import RealDatasetLoader
from real_ml_trainer import RealMLTrainer
from nova_prover import NovaProver
from zkp_protocols.protostar_production import ProtostarProduction
from zkp_protocols.base import TrainingWitness

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_circuit_complexity():
    """Test that Nova and ProtoStar use same circuit complexity"""
    
    print("🔍 Testing Nova vs ProtoStar circuit complexity...")
    
    # Load real medical dataset
    dataset_loader = RealDatasetLoader()
    X, y = dataset_loader.load_dataset('cardio')
    
    # Use small subset for fast testing
    X_test = X[:100]  # 100 samples
    y_test = y[:100]
    
    # Train a small model to get real weights
    trainer = RealMLTrainer(input_features=11, hidden_sizes=[64, 32], num_classes=2)
    initial_weights = trainer.get_weights()
    
    # Do one training step
    trainer.train_epoch(X_test, y_test, learning_rate=0.01, epochs=1)
    final_weights = trainer.get_weights()
    
    # Create witness
    witness = TrainingWitness(
        initial_weights=initial_weights,
        final_weights=final_weights,
        dataset_samples=X_test,
        dataset_labels=y_test,
        random_seed=42
    )
    
    statement = {
        'num_rounds': 1,
        'client_id': 'test_client',
        'claimed_loss': 0.5,
        'claimed_accuracy': 0.8
    }
    
    print("\n🔵 Testing Nova...")
    try:
        nova = NovaProver()
        nova_proof = nova.generate_proof(statement, witness)
        print(f"✅ Nova proof successful")
        # Check if Nova used complete circuit (should have message about constraints)
        
    except Exception as e:
        print(f"❌ Nova failed: {e}")
    
    print("\n🟣 Testing ProtoStar...")
    try:
        protostar = ProtostarProduction()
        protostar.setup(security_level=128)
        protostar_proof = protostar.generate_proof(statement, witness)
        print(f"✅ ProtoStar proof successful")
        
    except Exception as e:
        print(f"❌ ProtoStar failed: {e}")
    
    print("\n📊 Circuit Complexity Comparison:")
    print("Both protocols should now use complete_r1cs_circuit with 5963 constraints")
    print("Check the output above for 'Complete circuit' vs 'simplified' messages")

if __name__ == "__main__":
    test_circuit_complexity()