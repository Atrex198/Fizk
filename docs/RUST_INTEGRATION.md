# Rust Integration Guide for ZKP Libraries

## Overview

Several ZKP systems (PLONK, Bulletproofs, Halo2, Nova) are implemented in Rust and require compilation to use from Python. This guide explains how to build and integrate them.

## Prerequisites

### 1. Install Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### 2. Install maturin (Rust-Python bridge)
```bash
pip install maturin
```

### 3. Install build dependencies
```bash
# On Ubuntu/Debian
sudo apt-get install build-essential libssl-dev pkg-config

# On macOS
brew install openssl pkg-config
```

## Building the Rust ZKP Bindings

### Step 1: Navigate to Rust project
```bash
cd rust_zkp
```

### Step 2: Build in development mode
```bash
maturin develop --release
```

This will:
- Compile the Rust code
- Create a Python wheel
- Install it in your Python environment

### Step 3: Verify installation
```python
python -c "import zkp_bindings; print('✓ Rust bindings installed')"
```

## Available Rust-Based ZKP Systems

### 1. PLONK (via Halo2)
- **Library**: `halo2_proofs`
- **Features**: Custom gates, lookup tables, universal setup
- **Use case**: Complex circuits with table lookups

### 2. Bulletproofs
- **Library**: `bulletproofs`
- **Features**: Range proofs, R1CS, no trusted setup
- **Use case**: Privacy-preserving transactions

### 3. Nova
- **Library**: `nova-snark`
- **Features**: Recursive SNARKs, folding schemes
- **Use case**: Incremental verifiable computation

### 4. Halo2 (full implementation)
- **Library**: `halo2_gadgets`
- **Features**: Polynomial commitments via IPA
- **Use case**: Recursive composition

## Full Implementation Steps

### For PLONK (Halo2):

1. **Define the Circuit**:
```rust
// In rust_zkp/src/plonk.rs

use halo2_proofs::{
    circuit::{Layouter, SimpleFloorPlanner, Value},
    plonk::{Circuit, ConstraintSystem, Error},
};

#[derive(Clone)]
struct MatrixMultCircuit<F: Field> {
    a: Vec<Vec<Value<F>>>,
    b: Vec<Vec<Value<F>>>,
    c: Vec<Vec<Value<F>>>,
}

impl<F: Field> Circuit<F> for MatrixMultCircuit<F> {
    type Config = MatrixConfig;
    type FloorPlanner = SimpleFloorPlanner;

    fn without_witnesses(&self) -> Self {
        Self::default()
    }

    fn configure(meta: &mut ConstraintSystem<F>) -> Self::Config {
        // Define columns and constraints
        let a = meta.advice_column();
        let b = meta.advice_column();
        let c = meta.advice_column();
        
        // Create custom gate for multiplication
        meta.create_gate("mul", |meta| {
            let a = meta.query_advice(a, Rotation::cur());
            let b = meta.query_advice(b, Rotation::cur());
            let c = meta.query_advice(c, Rotation::cur());
            
            vec![a * b - c]
        });
        
        MatrixConfig { a, b, c }
    }

    fn synthesize(&self, config: Self::Config, mut layouter: impl Layouter<F>) -> Result<(), Error> {
        // Assign witnesses and constraints
        layouter.assign_region(|| "matrix multiply", |mut region| {
            // ... assign values
        })
    }
}
```

2. **Expose to Python**:
```rust
#[pymethods]
impl PlonkProver {
    pub fn prove(&self, witness: Vec<i64>) -> PyResult<Vec<u8>> {
        let circuit = MatrixMultCircuit::new(witness);
        let proof = create_proof(&self.params, &self.pk, circuit)?;
        Ok(proof.to_bytes())
    }
}
```

### For Bulletproofs:

```rust
use bulletproofs::{BulletproofGens, PedersenGens, RangeProof};
use curve25519_dalek::scalar::Scalar;

#[pymethods]
impl BulletproofsProver {
    pub fn prove_range(&self, value: u64) -> PyResult<Vec<u8>> {
        let pc_gens = PedersenGens::default();
        let bp_gens = BulletproofGens::new(64, 1);
        
        let blinding = Scalar::random(&mut thread_rng());
        let mut transcript = Transcript::new(b"range_proof");
        
        let (proof, commitment) = RangeProof::prove_single(
            &bp_gens,
            &pc_gens,
            &mut transcript,
            value,
            &blinding,
            64,
        )?;
        
        Ok(proof.to_bytes())
    }
}
```

## Development Workflow

### 1. Make changes to Rust code
Edit files in `rust_zkp/src/`

### 2. Rebuild
```bash
cd rust_zkp
maturin develop --release
```

### 3. Test in Python
```python
from zkp_bindings import PlonkProver

prover = PlonkProver(100)
keys = prover.setup()
proof = prover.prove([1, 2, 3], [4])
```

## Troubleshooting

### Issue: Compilation fails
- Ensure Rust is up to date: `rustup update`
- Check dependencies: `cargo check`

### Issue: Import error in Python
- Verify installation: `pip list | grep zkp-bindings`
- Rebuild: `maturin develop --release`

### Issue: Slow compilation
- Use `--release` flag for optimizations
- Enable incremental compilation: `export CARGO_INCREMENTAL=1`

## Alternative Approaches

If Rust compilation is problematic, consider:

### 1. Use Pre-built Wheels
```bash
pip install zkp-bindings --pre
```

### 2. Use Docker
```bash
docker build -t zkp-eval -f Dockerfile .
docker run zkp-eval python scripts/run_benchmark.py
```

### 3. Use Subprocess with CLI Tools
Some ZKP libraries provide CLI tools. Example:
```python
import subprocess

def groth16_prove(witness_file):
    result = subprocess.run(
        ['groth16-prover', '--witness', witness_file],
        capture_output=True
    )
    return result.stdout
```

## Performance Optimization

### 1. Release Builds
Always use `--release` for benchmarking:
```bash
maturin build --release
```

### 2. CPU Features
Enable native CPU optimizations:
```bash
RUSTFLAGS="-C target-cpu=native" maturin develop --release
```

### 3. Parallel Compilation
```bash
cargo build -j $(nproc)
```

## Testing

### Unit Tests (Rust)
```bash
cd rust_zkp
cargo test
```

### Integration Tests (Python)
```bash
pytest tests/test_zkp_techniques.py -v
```

## Production Deployment

### 1. Build Wheel
```bash
maturin build --release --out dist/
```

### 2. Install Wheel
```bash
pip install dist/zkp_bindings-*.whl
```

### 3. Verify
```python
import zkp_bindings
print(zkp_bindings.__version__)
```

## Resources

- **Halo2 Book**: https://zcash.github.io/halo2/
- **Bulletproofs Paper**: https://eprint.iacr.org/2017/1066
- **Nova**: https://github.com/microsoft/Nova
- **PyO3 Guide**: https://pyo3.rs/
- **Maturin Docs**: https://www.maturin.rs/

## Support

For issues with Rust integration:
1. Check `rust_zkp/Cargo.toml` dependencies
2. Review build errors in `rust_zkp/target/`
3. Consult library-specific documentation
4. File issues with detailed error logs
