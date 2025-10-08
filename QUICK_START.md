# Quick Start Guide - Real Protostar ZKP

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
py setup_real_zkp.py
```

✅ Installs: `py_ecc`, `numpy`, `torch`  
✅ Verifies: All modules working  
✅ Tests: Quick proof generation

---

### Step 2: Import and Initialize
```python
from zkp_protocols.protostar_real import RealProtostarProtocol
from zkp_protocols.base import TrainingStatement, TrainingWitness
import numpy as np
import time

# Configure protocol
config = {
    'trusted_setup_size': 2048,  # Number of SRS elements
    'curve': 'BN128',            # Elliptic curve
    'enable_ivc': True,          # Enable IVC accumulation
    'max_constraints': 100000    # Max constraints per proof
}

# Initialize
protocol = RealProtostarProtocol(config)
protocol.setup()
print("✅ Protocol ready!")
```

---

### Step 3: Prepare Training Data
```python
# Your model weights
initial_weights = {
    'layer1.weight': np.random.randn(64, 32) * 0.1,
    'layer1.bias': np.random.randn(64) * 0.1,
    'layer2.weight': np.random.randn(10, 64) * 0.1,
    'layer2.bias': np.random.randn(10) * 0.1,
}

# After training
final_weights = {
    'layer1.weight': initial_weights['layer1.weight'] - 0.01 * np.random.randn(64, 32),
    'layer1.bias': initial_weights['layer1.bias'] - 0.01 * np.random.randn(64),
    'layer2.weight': initial_weights['layer2.weight'] - 0.01 * np.random.randn(10, 64),
    'layer2.bias': initial_weights['layer2.bias'] - 0.01 * np.random.randn(10),
}
```

---

### Step 4: Create Statement and Witness
```python
# Public statement
statement = TrainingStatement(
    model_architecture="feedforward_nn",
    initial_weights_commitment="sha256_hash_of_initial",
    final_weights_commitment="sha256_hash_of_final",
    dataset_commitment="sha256_hash_of_dataset",
    local_epochs=10,
    batch_size=64,
    learning_rate=0.01,
    claimed_accuracy=0.87,
    claimed_loss=0.35,
    sample_count=5000,
    round_number=1,
    client_id="client_001",
    timestamp=time.time()
)

# Private witness
witness = TrainingWitness(
    initial_weights=initial_weights,
    final_weights=final_weights,
    dataset_samples=X_train,  # Your training data
    dataset_labels=y_train,   # Your labels
    random_seed=42
)
```

---

### Step 5: Generate Proof
```python
print("🔐 Generating proof...")
proof = protocol.generate_proof(statement, witness)

print(f"✅ Proof generated!")
print(f"   Size: {proof.get_size_bytes()} bytes")
print(f"   Constraints: {proof.proof_data['r1cs_system']['num_constraints']}")
print(f"   Security: {proof.metadata['security_level']} bits")
```

---

### Step 6: Verify Proof
```python
print("🔍 Verifying proof...")
result = protocol.verify_proof(proof, statement)

if result.is_valid:
    print(f"✅ PROOF VALID!")
    print(f"   Verification time: {result.verification_time:.4f}s")
    print(f"   Checks passed:")
    for check, status in result.detailed_checks.items():
        print(f"      {check}: {'✓' if status else '✗'}")
else:
    print(f"❌ PROOF INVALID: {result.error_message}")
```

---

## 🔄 Multi-Round IVC Example

```python
# Initialize protocol once
protocol = RealProtostarProtocol(config)
protocol.setup()

# Generate proofs for multiple rounds
for round_num in range(1, 6):
    print(f"\n=== Round {round_num} ===")
    
    # Update statement for this round
    statement.round_number = round_num
    statement.claimed_accuracy = 0.80 + round_num * 0.02
    
    # Generate proof (IVC automatically accumulates)
    proof = protocol.generate_proof(statement, witness)
    
    # Check IVC status
    ivc_data = proof.proof_data['ivc_data']
    print(f"Cross-terms: {len(ivc_data['cross_terms'])}")
    print(f"Accumulated rounds: {ivc_data['accumulated_rounds']}")
    
    # Verify
    result = protocol.verify_proof(proof, statement)
    print(f"Valid: {result.is_valid}")
```

---

## 🔗 Multi-Client Aggregation Example

```python
# Generate proofs from multiple clients
client_proofs = []

for client_id in range(5):
    # Each client creates their statement and witness
    client_statement = TrainingStatement(
        model_architecture="mlp",
        initial_weights_commitment=f"client_{client_id}_init",
        final_weights_commitment=f"client_{client_id}_final",
        dataset_commitment="shared_dataset",
        local_epochs=10,
        batch_size=64,
        learning_rate=0.01,
        claimed_accuracy=0.80 + client_id * 0.02,
        claimed_loss=0.45,
        sample_count=1000,
        round_number=1,
        client_id=f"client_{client_id:03d}",
        timestamp=time.time()
    )
    
    # Generate proof
    proof = protocol.generate_proof(client_statement, client_witness)
    client_proofs.append(proof)
    print(f"Client {client_id}: {proof.get_size_bytes()} bytes")

# Aggregate all proofs using ProtoGalaxy
print("\n🔗 Aggregating proofs...")
aggregated = protocol.aggregate_proofs(client_proofs)

print(f"✅ Aggregation complete!")
print(f"   Original proofs: {aggregated.proof_data['num_original_proofs']}")
print(f"   Aggregation depth: {aggregated.proof_data['aggregation_depth']}")
print(f"   Cross-terms: {len(aggregated.proof_data['protogalaxy_cross_terms'])}")
print(f"   Verification complexity: {aggregated.proof_data['verification_complexity']}")

# Size comparison
total_original = sum(p.get_size_bytes() for p in client_proofs)
aggregated_size = aggregated.get_size_bytes()
print(f"   Compression: {(1 - aggregated_size/total_original)*100:.1f}%")
```

---

## 📊 Get Protocol Info

```python
info = protocol.get_protocol_info()

print(f"Protocol: {info['name']}")
print(f"Version: {info['version']}")
print(f"Type: {info['type']}")
print(f"Curve: {info['curve']}")
print(f"Security: {info['parameters']['security_level_bits']} bits")

print("\nFeatures:")
for feature, value in info['features'].items():
    print(f"  {feature}: {value}")

print("\nComplexity:")
for operation, complexity in info['complexity'].items():
    print(f"  {operation}: {complexity}")
```

---

## 🧪 Run Tests

```bash
# Full test suite
py test_real_protostar.py
```

Tests include:
1. Single proof generation & verification
2. IVC accumulation across rounds
3. ProtoGalaxy aggregation
4. Security properties (soundness)

---

## 📁 File Structure

```
your_project/
├── zkp_protocols/
│   ├── __init__.py              # Package
│   ├── base.py                  # Interfaces
│   ├── protostar_real.py        # Implementation
│   └── README_REAL_IMPLEMENTATION.md
│
├── test_real_protostar.py       # Tests
├── setup_real_zkp.py            # Setup script
├── IMPLEMENTATION_SUMMARY.md    # Summary
└── COMPARISON_OLD_VS_NEW.md     # Comparison
```

---

## ⚡ Quick Tips

### 1. Adjust Trusted Setup Size
```python
config = {
    'trusted_setup_size': 512,   # Smaller = faster, less constraints
    'trusted_setup_size': 1024,  # Balanced
    'trusted_setup_size': 2048,  # Larger = more constraints
}
```

### 2. Disable IVC if Not Needed
```python
config = {
    'enable_ivc': False,  # Single-round only
    'enable_ivc': True,   # Multi-round accumulation
}
```

### 3. Check Proof Size
```python
proof_size_bytes = proof.get_size_bytes()
proof_size_kb = proof_size_bytes / 1024
print(f"Proof size: {proof_size_kb:.2f} KB")
```

### 4. Serialize/Deserialize Proofs
```python
# Serialize
proof_bytes = protocol.serialize_proof(proof)

# Save to file
with open('proof.bin', 'wb') as f:
    f.write(proof_bytes)

# Load from file
with open('proof.bin', 'rb') as f:
    proof_bytes = f.read()

# Deserialize
proof = protocol.deserialize_proof(proof_bytes)
```

### 5. Error Handling
```python
try:
    proof = protocol.generate_proof(statement, witness)
except ValueError as e:
    print(f"Proof generation failed: {e}")

try:
    result = protocol.verify_proof(proof, statement)
    if not result.is_valid:
        print(f"Verification failed: {result.error_message}")
except Exception as e:
    print(f"Verification error: {e}")
```

---

## 🆘 Troubleshooting

### Issue: "py_ecc not found"
```bash
pip install py_ecc>=6.0.0
```

### Issue: "Witness does not satisfy constraints"
- Check that witness weights are reasonable values
- Ensure no NaN or Inf values in weights
- Verify data types (should be numpy arrays)

### Issue: "Proof too large"
- Reduce `trusted_setup_size`
- Simplify model (fewer parameters)
- Use smaller batches

### Issue: "Verification failed"
- Ensure statement matches the one used for proof generation
- Check that proof wasn't tampered with
- Verify all fields in statement are correct

---

## 📚 Learn More

- **Full Documentation**: `zkp_protocols/README_REAL_IMPLEMENTATION.md`
- **Implementation Details**: `zkp_protocols/protostar_real.py`
- **Comparison**: `COMPARISON_OLD_VS_NEW.md`
- **Summary**: `IMPLEMENTATION_SUMMARY.md`

---

## ✅ Checklist

Before using in production:

- [ ] Run `py setup_real_zkp.py` successfully
- [ ] Run `py test_real_protostar.py` - all tests pass
- [ ] Understand statement vs witness (public vs private)
- [ ] Configure appropriate trusted setup size
- [ ] Test with your actual model architecture
- [ ] Verify proof sizes are reasonable
- [ ] Test verification with tampered proofs
- [ ] Benchmark performance for your use case
- [ ] Read full documentation
- [ ] Implement error handling

---

**Status**: ✅ Ready to Use  
**Security**: 🔐 128-bit  
**Support**: See documentation files

---

*Simple. Secure. Real Cryptography.*
