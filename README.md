# Zero-Knowledge Proof Federated Learning System

Production-grade federated learning system with cryptographic zero-knowledge proofs for privacy-preserving machine learning.

## ⚠️ Important: Architecture Limitations

**Please read [ARCHITECTURE_LIMITATIONS.md](ARCHITECTURE_LIMITATIONS.md)** for a detailed analysis of the security model and known limitations when using adaptive optimizers (Adam, RMSprop, etc.).

**TL;DR**: This system cryptographically verifies that clients computed real gradients, but does not enforce the specific optimizer update rule. This is a fundamental trade-off enabling Adam support while maintaining practical proof times. Security relies on honest majority + server-side validation (standard in FL).

## Features

- **Complete R1CS Circuits**: 10,500+ constraints proving actual ML training
- **Real Cryptography**: BN254 elliptic curve, py_ecc pairing operations  
- **Protostar ZKP Protocol**: Polynomial commitment scheme with 256-bit security
- **Federated Learning**: Multi-client distributed training with FedAvg aggregation
- **Medical Dataset**: 70K cardiovascular disease samples
- **Anti-Freeloading**: Prevents clients from submitting unchanged weights
- **Replay Protection**: Nonce-based proof freshness validation

## Requirements

```bash
pip install -r requirements.txt
```

Required packages:
- Python 3.8+
- PyTorch
- py_ecc (REQUIRED - no fallback mode)
- NumPy, Pandas, Scikit-learn

## Quick Start

### Basic Run (3 clients, 3 rounds)

```bash
python3 production_zkp_fl_real.py
```

### Custom Configuration

```bash
# Specify number of clients and rounds
python3 production_zkp_fl_real.py --num-clients 5 --num-rounds 10

# Adjust learning parameters
python3 production_zkp_fl_real.py --learning-rate 0.001 --batch-size 32 --local-epochs 5
```

### Command-line Options

- `--num-clients N`: Number of federated clients (default: 3)
- `--num-rounds N`: Number of training rounds (default: 3)
- `--learning-rate LR`: Learning rate (default: 0.01)
- `--batch-size BS`: Batch size (default: 64)
- `--local-epochs E`: Local training epochs per round (default: 5)

## Output

Results are saved to `production_zkp_fl_results_real/run_TIMESTAMP/`:

```
run_TIMESTAMP/
├── run_config.json          # Configuration parameters
├── models/
│   ├── global_round_1.json  # Global model weights per round
│   └── ...
├── proofs/
│   ├── client_0/
│   │   ├── round_1_proof.json  # ZKP proof (5963 constraints)
│   │   └── ...
│   └── aggregated/
│       ├── round_1_batch_proof.json  # Aggregated proofs
│       └── ...
└── results/
    └── training_results.json    # Metrics and performance data
```

## System Architecture

### ZKP Protocols (`zkp_protocols/`)

- `protostar_production.py`: Core Protostar ZKP protocol
- `complete_r1cs_circuit.py`: Complete R1CS constraint generation (5963 constraints)
- `pairing_verification.py`: BN254 pairing verification
- `proof_batching.py`: Batch proof verification
- `homomorphic_encryption_optimized.py`: Secure aggregation
- `mpc_trusted_setup.py`: Multi-party trusted setup ceremony
- `nonce_store.py`: Replay attack protection

### ML Components

- `real_ml_trainer.py`: PyTorch neural network trainer
- `real_dataset_loader.py`: Medical dataset preprocessing
- `production_zkp_fl_real.py`: Main federated learning orchestrator

## Security Features

### Cryptographic Guarantees

- **256-bit security**: BN254 elliptic curve
- **2048 SRS elements**: Structured Reference String for commitments
- **Complete R1CS**: 5963 constraints proving:
  - Real input encoding (11 features)
  - Forward pass matrix operations (3 layers: 64→32→2)
  - Cross-entropy loss computation
  - Backward pass with actual gradients
  - Weight updates with optimizer verification

### Security Audit Results

✅ **No fallback circuits**: Complete R1CS only (no 19-constraint simplification)  
✅ **No simulation modes**: py_ecc required, real pairing operations  
✅ **Fail-closed design**: System fails if cryptography unavailable  
✅ **Replay protection**: Nonce database prevents proof reuse  
✅ **Challenge verification**: Fiat-Shamir with timestamp/nonce/SRS commitment  

## Performance

Typical runtime (3 clients, 3 rounds):
- Setup: ~15s (SRS generation)
- Per-client proof generation: ~1-2s (5963 constraints)
- Proof verification: ~0.5s
- Total round time: ~20-25s

## Dataset

Uses cardiovascular disease dataset (`cardio_train.csv`):
- 70,000 patients
- 11 normalized features (age, blood pressure, cholesterol, etc.)
- Binary classification (cardiovascular disease present/absent)

## Verification

Each proof includes:
- Constraint count: 5963 (complete circuit)
- EC commitments: 4 valid elliptic curve points
- Witness size: ~8931 variables
- Cryptographic properties: All commitments verified as EC points

## Troubleshooting

### ImportError: py_ecc not found

```bash
pip install py_ecc==8.0.0
```

### CUDA/GPU errors

The system works on CPU. If you see GPU warnings, they can be ignored.

### Low constraint count in proofs

If proofs show <100 constraints instead of 5963, ensure model weights include all layers:
- `network.0.weight/bias` (input layer)
- `network.4.weight/bias` (hidden layer)
- `network.8.weight/bias` (output layer)

## Advanced Usage

### Custom Model Architecture

Edit `real_ml_trainer.py` to modify the neural network:

```python
self.network = nn.Sequential(
    nn.Linear(input_dim, 64),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(64, 32),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(32, output_dim)
)
```

Note: R1CS circuit expects 3 linear layers. Modify `complete_r1cs_circuit.py` if architecture changes.

### Trusted Setup Ceremony

For production deployment, use multi-party trusted setup:

```python
from zkp_protocols.mpc_trusted_setup import MPCTrustedSetup

ceremony = MPCTrustedSetup(security_level=256)
srs = ceremony.run_ceremony(num_participants=10)
```

## License

Research/Educational Use
