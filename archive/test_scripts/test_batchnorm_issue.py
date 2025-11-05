#!/usr/bin/env python3
"""
BatchNorm Investigation
========================
Check if BatchNorm is causing FL training issues
"""

import sys
sys.path.append('.')

import torch
import torch.nn as nn

print("="*80)
print("BATCHNORM INVESTIGATION")
print("="*80)

# Simulate what happens during FL with BatchNorm

# Client 1's model
model1 = nn.Sequential(
    nn.Linear(10, 64),
    nn.BatchNorm1d(64),
    nn.ReLU()
)

# Client 2's model  
model2 = nn.Sequential(
    nn.Linear(10, 64),
    nn.BatchNorm1d(64),
    nn.ReLU()
)

print("\n1. Initial BatchNorm running stats:")
print(f"   Model 1 running_mean: {model1[1].running_mean[:5]}")
print(f"   Model 2 running_mean: {model2[1].running_mean[:5]}")

# Simulate training on different data
X1 = torch.randn(100, 10) + 1.0  # Different distribution
X2 = torch.randn(100, 10) - 1.0  # Different distribution

model1.train()
model2.train()

with torch.no_grad():
    out1 = model1(X1)
    out2 = model2(X2)

print("\n2. After training on different data:")
print(f"   Model 1 running_mean: {model1[1].running_mean[:5]}")
print(f"   Model 2 running_mean: {model2[1].running_mean[:5]}")

# Now simulate FedAvg - average the weights
print("\n3. Averaging weights (FedAvg):")
avg_weight = (model1[0].weight + model2[0].weight) / 2
avg_bias = (model1[0].bias + model2[0].bias) / 2

# BatchNorm parameters - weight and bias
avg_bn_weight = (model1[1].weight + model2[1].weight) / 2
avg_bn_bias = (model1[1].bias + model2[1].bias) / 2

# The PROBLEM: running_mean and running_var are NOT averaged!
print(f"   Averaged linear weight mean: {avg_weight.mean().item():.6f}")
print(f"   Averaged BN weight mean: {avg_bn_weight.mean().item():.6f}")

# Create global model with averaged weights
global_model = nn.Sequential(
    nn.Linear(10, 64),
    nn.BatchNorm1d(64),
    nn.ReLU()
)

global_model[0].weight.data = avg_weight
global_model[0].bias.data = avg_bias
global_model[1].weight.data = avg_bn_weight
global_model[1].bias.data = avg_bn_bias

# BUT: running_mean and running_var are NOT in state_dict by default!
print("\n4. What gets saved in state_dict:")
state_dict = global_model.state_dict()
for key in state_dict.keys():
    print(f"   {key}: {state_dict[key].shape if hasattr(state_dict[key], 'shape') else type(state_dict[key])}")

# The issue: running_mean and running_var might not be properly aggregated
print("\n5. Checking if running stats are aggregated:")
if '1.running_mean' in state_dict:
    print(f"   ✅ running_mean IS in state_dict")
else:
    print(f"   ❌ running_mean NOT in state_dict (THIS IS THE PROBLEM!)")

print("\n" + "="*80)
print("DIAGNOSIS:")
print("="*80)
print("""
The problem is likely:
1. BatchNorm has running_mean and running_var that track statistics
2. These are NOT aggregated during FedAvg (only weight/bias are)
3. When client loads global model, it gets incompatible running stats
4. This causes poor performance initially (until BN re-adapts)

SOLUTION OPTIONS:
A) Remove BatchNorm from model
B) Properly aggregate BN running stats
C) Use GroupNorm or LayerNorm instead
D) Reset BN stats after loading global model
""")
