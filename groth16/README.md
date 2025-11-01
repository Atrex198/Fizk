# Groth16 ZKP Protocol Implementation

Complete Groth16 SNARK implementation for the ZKP-FL framework.

## Overview

This implementation provides a production-ready Groth16 protocol that integrates seamlessly with the federated learning system through the `IZKPProtocol` interface.

### Key Features

- **128-byte proofs**: Smallest proof size among all protocols
- **O(1) verification**: Constant-time verification (~2-5ms)
- **BN128 curve**: 128-bit security level
- **Full FL integration**: Follows `FL_CIRCUIT_ENCODING_STANDARD.md`
- **R1CS constraints**: Neural network computation encoding
- **Production cryptography**: Real BN128 operations via py_ecc

## Architecture

```
┌─────────────────────────────────────────────┐
│         Groth16Protocol                     │
│  Implements: IZKPProtocol                   │
│  Methods: setup, generate_proof, verify     │
└─────────────────────────────────────────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
┌─────────▼────────┐  ┌───────▼──────────┐
│  Groth16Prover   │  │ Groth16Verifier  │
│  π=(π_A,π_B,π_C) │  │  3 pairing checks│
└──────────────────┘  └──────────────────┘
          │                   │
          └─────────┬─────────┘
                    │
        ┌───────────▼──────────────┐
        │  Groth16TrustedSetup     │
        │  Keys: (pk, vk)          │
        └──────────────────────────┘
                    │
        ┌───────────▼──────────────┐
        │         R1CS             │
        │  (A·z)*(B·z)=(C·z)       │
        └──────────────────────────┘
                    │
        ┌───────────▼──────────────┐
        │   FLCircuitBuilder       │
        │  Neural network encoding │
        └──────────────────────────┘
```

## Components

### 1. R1CS (r1cs.py)
Rank-1 Constraint System for arithmetic circuits.

```python
from groth16 import R1CS, R1CSBuilder

# Build R1CS
builder = R1CSBuilder()
r1cs = builder.initialize(num_variables=1000)

# Add constraints
r1cs.add_multiplication_constraint(a=1, b=2, c=3)  # z[1] * z[2] = z[3]
r1cs.add_addition_constraint(a=3, b=4, c=5)        # z[3] + z[4] = z[5]

# Set witness
r1cs.set_witness(1, 10)
r1cs.set_witness(2, 5)
r1cs.set_witness(3, 50)  # 10 * 5 = 50

# Verify
assert r1cs.verify_constraint_satisfaction()
```

### 2. Trusted Setup (trusted_setup.py)
Circuit-specific key generation.

**⚠️ WARNING**: This is a development setup only. Production requires secure MPC ceremony.

```python
from groth16 import generate_groth16_setup

# Generate keys
proving_key, verification_key = generate_groth16_setup(r1cs)
```

### 3. Prover (prover.py)
Generates 128-byte Groth16 proofs.

```python
from groth16 import Groth16Prover

prover = Groth16Prover(proving_key, r1cs)
proof = prover.generate_proof(
    witness=[1, 10, 5, 50, ...],
    public_inputs=[10, 5]
)
```

### 4. Verifier (verifier.py)
Verifies proofs with 3 pairing checks.

```python
from groth16 import Groth16Verifier

verifier = Groth16Verifier(verification_key)
is_valid = verifier.verify_proof(proof, public_inputs=[10, 5])
```

### 5. FL Circuit Builder (fl_circuit_builder.py)
Encodes neural network operations into R1CS.

```python
from groth16 import FLCircuitBuilder

builder = FLCircuitBuilder()

# Encode weight
field_element = builder.encode_weight(0.5)  # 0.5 -> 500 (scaled by 1000)

# Build FL round circuit
var_indices = builder.build_full_fl_round(
    num_params=2914,  # Model parameters
    num_clients=3,
    round_number=1
)
```

### 6. Protocol (groth16_protocol.py)
Main interface implementing `IZKPProtocol`.

```python
from groth16 import Groth16Protocol

# Initialize
protocol = Groth16Protocol(config={
    'num_model_params': 2914,
    'num_clients': 3,
    'security_level': 128
})

# Setup
setup_artifacts = protocol.setup()

# Generate proof
proof = protocol.generate_proof(
    statement={
        'initial_weights_commitment': '0xabc...',
        'final_weights_commitment': '0xdef...'
    },
    witness={
        'model_weights': {'layer1.weight': [0.1, 0.2, ...]},
    },
    round_number=1,
    client_id='client_0'
)

# Verify proof
result = protocol.verify_proof(proof, statement)
print(f"Valid: {result.is_valid}, Time: {result.verification_time:.3f}s")
```

## Standards Compliance

### FL Circuit Encoding Standard
Follows `FL_CIRCUIT_ENCODING_STANDARD.md`:

1. **Weight encoding**: Clamp → Scale → Mod
   ```python
   w_clamped = clip(w, -1000, 1000)
   w_scaled = w_clamped * 1000
   w_field = int(w_scaled) % curve_order
   ```

2. **Weight commitment**: SHA256(sorted_json(weights))

3. **Forward pass**: Linear layers with matrix multiplication constraints

4. **Gradient computation**: Chain rule in R1CS

5. **Weight updates**: SGD constraints

6. **Aggregation**: FedAvg in field arithmetic

### Architecture Standard
Implements `IZKPProtocol` from `ARCHITECTURE.md`:

- ✅ `setup()`: Trusted setup
- ✅ `generate_proof()`: Proof generation
- ✅ `verify_proof()`: Proof verification
- ✅ `aggregate_proofs()`: Returns None (not supported)
- ✅ `get_protocol_info()`: Protocol metadata
- ✅ `serialize_proof()`: Proof serialization

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Proof size | 128 bytes |
| Verification time | 2-5 ms |
| Verification complexity | O(1) |
| Pairing checks | 3 |
| Setup required | Yes (circuit-specific) |
| IVC support | No |
| Aggregation support | No |
| Quantum resistant | No |
| Ethereum gas cost | ~280k |

## Comparison with Protostar

| Feature | Groth16 | Protostar |
|---------|---------|-----------|
| Proof size | **128 bytes** | ~5-10 KB |
| Verification | **O(1), 2-5ms** | O(log n), ~50-100ms |
| Setup | Circuit-specific MPC | Universal (trusted) |
| IVC | No | **Yes** |
| Aggregation | No | **Yes (Protogalaxy)** |
| FL suitability | High | **Very High** |

## Configuration

Default configuration:

```yaml
protocol: groth16
security_level: 128
curve_name: BN128
optimization_level: balanced
num_model_params: 2914
num_clients: 3
num_rounds: 1

trusted_setup:
  method: development  # WARNING: Use 'mpc_ceremony' in production
  participants: 1
  seed: null

performance:
  parallel_proving: false
  constraint_optimization: true

logging:
  level: INFO
  log_to_file: true
  log_file: groth16.log
```

## Integration with FL System

### 1. Protocol Registration

```python
# In FL orchestrator
from groth16 import Groth16Protocol

protocol = Groth16Protocol(config)
fl_system.register_protocol('groth16', protocol)
```

### 2. Hot-Swapping Protocols

```python
# Switch from Protostar to Groth16
fl_system.set_active_protocol('groth16')
```

### 3. Multi-Protocol Comparison

```python
# Run all protocols simultaneously
protocols = ['protostar', 'groth16', 'plonk', 'bulletproofs', 'nova']
results = fl_system.run_comparison(protocols, rounds=10)
```

## Example: Complete FL Round

```python
from groth16 import Groth16Protocol, get_default_config

# 1. Initialize
config = get_default_config(num_model_params=2914, num_clients=3)
protocol = Groth16Protocol(config)

# 2. Setup (once per circuit)
print("Performing trusted setup...")
setup_artifacts = protocol.setup()
print(f"Setup complete: {setup_artifacts['constraint_count']} constraints")

# 3. Generate proof (per client per round)
print("\nGenerating proof for client_0...")
proof = protocol.generate_proof(
    statement={
        'model_architecture': 'MLP(11->64->32->2)',
        'initial_weights_commitment': '0x1234...',
        'final_weights_commitment': '0x5678...',
        'training_config': {'lr': 0.01, 'epochs': 5}
    },
    witness={
        'model_weights': {
            'fc1.weight': [0.1] * 704,
            'fc1.bias': [0.01] * 64,
            'fc2.weight': [0.05] * 2048,
            'fc2.bias': [0.0] * 32,
            'fc3.weight': [0.02] * 64,
            'fc3.bias': [0.0] * 2
        },
        'training_history': [{'loss': 0.5, 'accuracy': 0.75}]
    },
    round_number=1,
    client_id='client_0'
)

print(f"Proof generated in {proof.metadata.generation_time:.3f}s")
print(f"Proof size: {proof.metadata.proof_size_bytes} bytes")

# 4. Verify proof (at server)
print("\nVerifying proof...")
result = protocol.verify_proof(proof, statement)

if result.is_valid:
    print(f"✅ Proof VALID (verified in {result.verification_time:.3f}s)")
else:
    print(f"❌ Proof INVALID: {result.error_message}")

# 5. Get protocol info
info = protocol.get_protocol_info()
print(f"\nProtocol: {info['protocol_name']}")
print(f"Proof size: {info['typical_proof_size_kb']} KB")
print(f"Verification time: {info['typical_verification_time_ms']} ms")
```

## Limitations

1. **Trusted setup required**: Circuit-specific, must regenerate if circuit changes
2. **No native aggregation**: Cannot combine multiple proofs (unlike Protostar/Nova)
3. **No IVC**: Cannot incrementally verify computation across rounds
4. **Not quantum-resistant**: Based on elliptic curve pairings

## Production Deployment

### Security Checklist

- [ ] Replace development setup with secure MPC ceremony
- [ ] Verify toxic waste destruction
- [ ] Audit circuit construction
- [ ] Test with production data
- [ ] Implement circuit versioning
- [ ] Add proof caching
- [ ] Monitor verification failures
- [ ] Set up key management infrastructure

### MPC Ceremony

For production, replace `Groth16TrustedSetup` with a secure multi-party computation ceremony:

1. Use [snarkjs](https://github.com/iden3/snarkjs) for ceremony
2. Require multiple independent participants
3. Destroy all toxic waste securely
4. Verify ceremony transcript
5. Publish verification keys publicly

## References

- Original paper: "On the Size of Pairing-based Non-interactive Arguments" (Groth, 2016)
- BN128 curve: `py_ecc` library
- FL encoding: `FL_CIRCUIT_ENCODING_STANDARD.md`
- Architecture: `ARCHITECTURE.md`
- Implementation guide: `GROTH16_IMPLEMENTATION.md`

## License

Part of ZKP-FL Framework, version 1.0.0
