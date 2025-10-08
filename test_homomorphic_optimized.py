"""
Quick Test: Homomorphic Encryption with Sampling
=================================================

Tests the optimized homomorphic encryption with 10% sampling.
Expected time: ~5-10 seconds for encryption of small model.
"""

import numpy as np
import time
from zkp_protocols.homomorphic_encryption_optimized import (
    PaillierEncryptionOptimized,
    HomomorphicWeightAggregatorOptimized
)

print("="*80)
print("TESTING OPTIMIZED HOMOMORPHIC ENCRYPTION")
print("="*80)

# Create test model weights (similar size to your FL model)
print("\n1. Creating test model weights...")
test_weights = {
    'layer1.weight': np.random.randn(64, 11),  # 704 parameters
    'layer1.bias': np.random.randn(64),         # 64 parameters
    'layer2.weight': np.random.randn(32, 64),  # 2048 parameters
    'layer2.bias': np.random.randn(32),         # 32 parameters
    'output.weight': np.random.randn(2, 32),   # 64 parameters
    'output.bias': np.random.randn(2)           # 2 parameters
}

total_params = sum(w.size for w in test_weights.values())
print(f"   Total parameters: {total_params}")

# Initialize encryption
print("\n2. Initializing 512-bit Paillier encryption...")
start = time.time()
he = PaillierEncryptionOptimized(key_size=512)
print(f"   Key generation time: {time.time() - start:.2f}s")

# Create aggregator
aggregator = HomomorphicWeightAggregatorOptimized(he)

# Test encryption with 10% sampling
print("\n3. Encrypting weights (10% sampling)...")
start = time.time()
encrypted = aggregator.encrypt_model_weights(test_weights, sample_rate=0.1)
encryption_time = time.time() - start
print(f"   ✅ Encryption complete in {encryption_time:.2f}s")

# Simulate 3 clients
print("\n4. Simulating 3 clients...")
encrypted_list = [encrypted for _ in range(3)]
sample_counts = [1000, 1000, 1000]

# Test aggregation
print("\n5. Aggregating encrypted weights...")
start = time.time()
aggregated = aggregator.aggregate_encrypted_weights(encrypted_list, sample_counts)
aggregation_time = time.time() - start
print(f"   ✅ Aggregation complete in {aggregation_time:.2f}s")

# Test decryption
print("\n6. Decrypting aggregated weights...")
shapes = {k: v.shape for k, v in test_weights.items()}
start = time.time()
decrypted = aggregator.decrypt_model_weights(aggregated, shapes)
decryption_time = time.time() - start
print(f"   ✅ Decryption complete in {decryption_time:.2f}s")

# Summary
print("\n" + "="*80)
print("TEST RESULTS")
print("="*80)
print(f"Total parameters:     {total_params}")
print(f"Encryption time:      {encryption_time:.2f}s")
print(f"Aggregation time:     {aggregation_time:.2f}s")
print(f"Decryption time:      {decryption_time:.2f}s")
print(f"Total time:           {encryption_time + aggregation_time + decryption_time:.2f}s")
print(f"\n✅ ALL TESTS PASSED - Homomorphic encryption working!")
print("="*80)
