"""
Quick test to debug homomorphic aggregation issue
"""
import numpy as np
from zkp_protocols.homomorphic_encryption_optimized import HomomorphicWeightAggregatorOptimized, PaillierEncryptionOptimized

# Create simple test weights
test_weights = {
    'layer1': np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32),
    'layer2': np.array([0.5, 0.6, 0.7], dtype=np.float32)
}

print("Original weights:")
for k, v in test_weights.items():
    print(f"  {k}: shape={v.shape}, values={v.flatten()}")

# Initialize Paillier encryption (generates keys automatically)
paillier = PaillierEncryptionOptimized(key_size=512)

# Create aggregator
aggregator = HomomorphicWeightAggregatorOptimized(paillier)

# Simulate 3 clients with slightly different weights
client_weights = []
for i in range(3):
    weights_copy = {k: v + np.random.randn(*v.shape) * 0.01 for k, v in test_weights.items()}
    client_weights.append(weights_copy)

print("\nClient weights (before encryption):")
for i, cw in enumerate(client_weights):
    print(f"  Client {i}: layer1 mean={cw['layer1'].mean():.6f}, layer2 mean={cw['layer2'].mean():.6f}")

# Encrypt each client's weights
encrypted_weights_list = []
shapes = {}
for i, weights in enumerate(client_weights):
    print(f"\nEncrypting client {i} weights...")
    encrypted = aggregator.encrypt_model_weights(weights, sample_rate=0.5)  # 50% sampling
    encrypted_weights_list.append(encrypted)
    if i == 0:
        shapes = {k: v.shape for k, v in weights.items()}

# Aggregate
print("\nAggregating encrypted weights...")
sample_counts = [1000, 1000, 1000]  # Equal weight
aggregated = aggregator.aggregate_encrypted_weights(encrypted_weights_list, sample_counts)

print("Aggregated encrypted weights structure:")
for k, v in aggregated.items():
    print(f"  {k}: {len(v)} elements")
    # Check placeholders
    placeholder_count = sum(1 for item in v if item.get('is_placeholder', False))
    encrypted_count = len(v) - placeholder_count
    print(f"    Encrypted: {encrypted_count}, Placeholders: {placeholder_count}")
    if placeholder_count > 0:
        # Check first placeholder
        first_placeholder = next(item for item in v if item.get('is_placeholder', False))
        print(f"    First placeholder original_value: {first_placeholder.get('original_value', 'MISSING')}")

# Decrypt
print("\nDecrypting aggregated weights...")
decrypted = aggregator.decrypt_model_weights(aggregated, shapes)

print("\nDecrypted weights:")
for k, v in decrypted.items():
    print(f"  {k}: shape={v.shape}")
    print(f"    values={v.flatten()}")
    print(f"    min={v.min():.6f}, max={v.max():.6f}, mean={v.mean():.6f}")
    if np.isnan(v).any():
        print(f"    ❌ CONTAINS NaN!")
    if np.isinf(v).any():
        print(f"    ❌ CONTAINS Inf!")

# Compare with expected (simple average)
print("\nExpected (simple average):")
expected = {}
for k in test_weights.keys():
    expected[k] = np.mean([cw[k] for cw in client_weights], axis=0)
    print(f"  {k}: mean={expected[k].mean():.6f}")

print("\nDifference (decrypted - expected):")
for k in test_weights.keys():
    diff = decrypted[k] - expected[k]
    print(f"  {k}: max_abs_diff={np.abs(diff).max():.6f}")
