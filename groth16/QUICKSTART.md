# Groth16 Quick Start Guide

## Installation

### 1. Dependencies

The Groth16 implementation requires `py_ecc` for BN128 elliptic curve operations:

```bash
pip install py_ecc pyyaml
```

All other dependencies are already in your `requirements.txt`.

### 2. Verify Installation

```bash
cd groth16
python3 -c "from py_ecc.bn128 import G1, G2, pairing; print('✅ py_ecc working')"
```

Expected output:
```
✅ py_ecc working
```

---

## Quick Test

### Run Comprehensive Tests

```bash
cd groth16
python3 test_groth16.py
```

This will:
- Test R1CS constraint system
- Test FL circuit builder
- Test setup/prover/verifier
- Test protocol interface
- Collect performance metrics

**Expected runtime:** ~10-30 seconds (depending on hardware)

### Run Simple Example

```bash
cd groth16
python3 example_simple.py
```

This demonstrates:
1. Protocol initialization
2. Trusted setup
3. Proof generation
4. Proof verification
5. Protocol information

**Expected runtime:** ~5-15 seconds

---

## Integration with FL System

### Method 1: Direct Integration

Add to your FL orchestrator:

```python
from groth16 import Groth16Protocol, get_default_config

# Initialize
config = get_default_config(
    num_model_params=2914,  # Your model's parameter count
    num_clients=3
)
groth16 = Groth16Protocol(config)

# Setup (once)
setup_artifacts = groth16.setup()

# Generate proof (per client)
proof = groth16.generate_proof(
    statement=statement_dict,
    witness=witness_dict,
    round_number=1,
    client_id='client_0'
)

# Verify proof (at server)
result = groth16.verify_proof(proof, statement)
```

### Method 2: Protocol Factory

```python
class ProtocolFactory:
    """Factory for creating ZKP protocols"""
    
    @staticmethod
    def create(name: str, config: dict):
        from groth16 import Groth16Protocol
        # from plonk import PlonkProtocol  # Future
        # from bulletproofs import BulletproofsProtocol  # Future
        
        protocols = {
            'groth16': Groth16Protocol,
            # 'plonk': PlonkProtocol,
            # 'bulletproofs': BulletproofsProtocol,
        }
        
        return protocols[name](config)

# Usage
protocol = ProtocolFactory.create('groth16', config)
protocol.setup()
```

---

## Configuration

### Basic Configuration

```python
from groth16 import get_default_config

config = get_default_config(
    num_model_params=2914,
    num_clients=3
)

# Customize
config['security_level'] = 128  # 128-bit security
config['optimization_level'] = 'balanced'  # or 'fast' or 'small'
```

### From File

```python
from groth16 import load_config

config = load_config('groth16/config.yaml')
```

Edit `config.yaml` to adjust:
- Security level
- Number of clients/rounds
- Performance tuning
- Logging settings

---

## Protocol Comparison

### Run All Protocols

```python
# Initialize all protocols
protocols = {
    'protostar': ProtostarProtocol(config),
    'groth16': Groth16Protocol(config),
    # Add more as implemented
}

# Run comparison
results = {}
for name, protocol in protocols.items():
    protocol.setup()
    
    # Generate proof
    start = time.time()
    proof = protocol.generate_proof(...)
    proof_time = time.time() - start
    
    # Verify proof
    start = time.time()
    result = protocol.verify_proof(...)
    verify_time = time.time() - start
    
    results[name] = {
        'proof_time': proof_time,
        'verify_time': verify_time,
        'proof_size': len(protocol.serialize_proof(proof)),
        'is_valid': result.is_valid
    }

# Compare
print_comparison_table(results)
```

---

## Performance Tuning

### For Faster Proof Generation

```yaml
# config.yaml
performance:
  parallel_proving: true  # Enable if multiple cores available
  constraint_optimization: true
  memory_limit_gb: 16  # Increase if you have RAM
```

### For Smaller Memory Footprint

```yaml
performance:
  parallel_proving: false
  constraint_optimization: true
  memory_limit_gb: 4
  
  cache_setup: false  # Don't cache setup artifacts
```

### For Production

```yaml
trusted_setup:
  method: mpc_ceremony  # Replace with real MPC
  participants: 10  # Multiple independent parties
  verification_required: true

logging:
  level: WARNING  # Less verbose
  log_to_file: true
  log_file: /var/log/groth16.log

export:
  save_proofs: true
  proof_dir: /data/groth16_proofs
  compression: true
```

---

## Troubleshooting

### Import Error: py_ecc not found

```bash
pip install py_ecc
```

### Import Error: yaml not found

```bash
pip install pyyaml
```

### MemoryError during setup

Reduce circuit size or increase memory:

```python
config['num_model_params'] = 1000  # Smaller for testing
config['performance']['memory_limit_gb'] = 8
```

### Proof verification fails

1. Check witness satisfies constraints:
   ```python
   assert r1cs.verify_constraint_satisfaction()
   ```

2. Check public inputs match:
   ```python
   print(f"Expected: {statement_public_inputs}")
   print(f"Got: {proof.public_inputs}")
   ```

3. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Setup takes too long

The trusted setup time scales with constraint count:

- 1,000 constraints: ~1-2 seconds
- 10,000 constraints: ~10-20 seconds
- 100,000 constraints: ~1-2 minutes

For testing, use smaller circuits:
```python
config['num_model_params'] = 100  # Very small for quick tests
```

---

## Development Workflow

### 1. Test Individual Components

```python
# Test R1CS only
from groth16 import R1CS
r1cs = R1CS(10)
r1cs.add_multiplication_constraint(1, 2, 3)
# ... test logic

# Test circuit builder only
from groth16 import FLCircuitBuilder
builder = FLCircuitBuilder()
encoded = builder.encode_weight(0.5)
# ... test logic
```

### 2. Test Protocol Interface

```python
from groth16 import Groth16Protocol
protocol = Groth16Protocol(config)
protocol.setup()
# ... test with mock data
```

### 3. Integrate with FL System

```python
# Replace Protostar with Groth16
# fl_orchestrator.set_protocol(groth16)
```

### 4. Run Comparison

```python
# Compare Groth16 vs Protostar
# results = run_protocol_comparison()
```

---

## Next Steps

1. ✅ **Verify installation**: Run `test_groth16.py`
2. ✅ **Run simple example**: Run `example_simple.py`
3. ⏳ **Integrate with FL**: Add to your FL orchestrator
4. ⏳ **Test with real data**: Use actual model weights
5. ⏳ **Compare protocols**: Benchmark Groth16 vs Protostar
6. ⏳ **Implement more protocols**: PLONK, Bulletproofs, Nova

---

## Support

### Documentation

- `README.md` - Complete overview
- `INTEGRATION_SUMMARY.md` - Integration details
- `Final_Guide/GROTH16_IMPLEMENTATION.md` - Implementation guide
- `Final_Guide/FL_CIRCUIT_ENCODING_STANDARD.md` - Encoding standard

### Examples

- `example_simple.py` - Minimal example
- `test_groth16.py` - Comprehensive tests

### Configuration

- `config.yaml` - Configuration template
- `utils.py` - Configuration utilities

---

## Production Checklist

Before deploying to production:

- [ ] Replace development setup with MPC ceremony
- [ ] Verify toxic waste destruction
- [ ] Audit circuit construction
- [ ] Test with production data
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Implement proof caching
- [ ] Add error handling
- [ ] Document circuit versioning
- [ ] Set up key management

---

**Ready to go!** 🚀

Run the tests, explore the examples, and integrate Groth16 into your FL system.
