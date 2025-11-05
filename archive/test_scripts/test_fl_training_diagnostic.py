#!/usr/bin/env python3
"""
FL Training Diagnostic Test
============================
Checks if federated learning is actually improving the model
"""

import sys
sys.path.append('.')

import numpy as np
import torch
from real_ml_trainer import RealMLTrainer, TrainingConfig
from real_dataset_loader import RealDatasetLoader

print("="*80)
print("FL TRAINING DIAGNOSTIC TEST")
print("="*80)

# Load real dataset
print("\n📊 Loading cardio dataset...")
loader = RealDatasetLoader()
X_train, y_train = loader.load_dataset('cardio')
print(f"   Dataset: {X_train.shape[0]} samples, {X_train.shape[1]} features")

# Split into 3 clients
samples_per_client = len(X_train) // 3
clients_data = []

for i in range(3):
    start = i * samples_per_client
    end = start + samples_per_client if i < 2 else len(X_train)
    clients_data.append({
        'X': X_train[start:end],
        'y': y_train[start:end]
    })
    print(f"   Client {i}: {len(clients_data[i]['X'])} samples")

# Initialize clients
config = TrainingConfig(
    learning_rate=0.01,
    batch_size=64,
    local_epochs=5,
    optimizer="adam"
)

clients = []
for i in range(3):
    trainer = RealMLTrainer(input_features=X_train.shape[1], config=config)
    clients.append({
        'trainer': trainer,
        'X': clients_data[i]['X'],
        'y': clients_data[i]['y']
    })

print("\n" + "="*80)
print("SIMULATING FL TRAINING (3 rounds)")
print("="*80)

global_weights = None

for round_num in range(1, 4):
    print(f"\n{'='*80}")
    print(f"ROUND {round_num}")
    print(f"{'='*80}")
    
    round_updates = []
    
    for client_id, client in enumerate(clients):
        trainer = client['trainer']
        X_data = client['X']
        y_data = client['y']
        
        # Load global weights if available
        if global_weights is not None:
            print(f"\n[Client {client_id}] Loading global weights...")
            # Check weight statistics before loading
            for k, v in list(global_weights.items())[:2]:
                if isinstance(v, torch.Tensor):
                    print(f"   {k}: mean={v.mean():.6f}, std={v.std():.6f}")
            
            trainer.load_global_model(global_weights)
            
            # Get weights AFTER loading
            loaded_weights = trainer.model.get_parameter_dict()
            print(f"   After loading:")
            for k, v in list(loaded_weights.items())[:2]:
                print(f"   {k}: mean={v.mean():.6f}, std={v.std():.6f}")
        
        # Get initial weights
        initial_weights = trainer.model.get_parameter_dict()
        
        print(f"\n[Client {client_id}] Training...")
        result = trainer.train_local_model(X_data, y_data)
        
        final_weights = result.model_parameters
        
        # Calculate weight change
        weight_change = 0
        for k in initial_weights.keys():
            if k in final_weights:
                diff = (final_weights[k] - initial_weights[k]).abs().mean().item()
                weight_change += diff
        
        print(f"   Initial Acc: {result.initial_accuracy:.4f}")
        print(f"   Final Acc:   {result.final_accuracy:.4f}")
        print(f"   Improvement: {result.final_accuracy - result.initial_accuracy:.4f}")
        print(f"   Total weight change: {weight_change:.6f}")
        
        round_updates.append({
            'weights': final_weights,
            'samples': len(X_data),
            'accuracy': result.final_accuracy
        })
    
    # FedAvg aggregation
    print(f"\n[Server] Aggregating weights...")
    total_samples = sum(u['samples'] for u in round_updates)
    
    aggregated = {}
    for update in round_updates:
        weight_factor = update['samples'] / total_samples
        for key, value in update['weights'].items():
            if key not in aggregated:
                aggregated[key] = torch.zeros_like(value)
            aggregated[key] = aggregated[key] + weight_factor * value
    
    global_weights = aggregated
    
    # Check aggregated weights
    print(f"   Aggregated weights (sample):")
    for k, v in list(global_weights.items())[:2]:
        print(f"   {k}: mean={v.mean():.6f}, std={v.std():.6f}")
    
    avg_acc = np.mean([u['accuracy'] for u in round_updates])
    print(f"\n   Round {round_num} Average Accuracy: {avg_acc:.4f}")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
print("\nIf accuracies improved across rounds, FL training is working!")
print("If weights are changing significantly, training is happening!")
