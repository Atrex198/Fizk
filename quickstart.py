"""Quick start script - minimal example."""

from src.zkp_techniques.stark import STARKWrapper
from src.zkp_techniques.groth16 import Groth16Wrapper
from src.tensor_ops.generator import TensorGenerator
from src.tensor_ops.operations import matrix_multiplication

print("ZKP Evaluation - Quick Start Example")
print("=" * 50)

# Generate test data
print("\n1. Generating test matrices...")
gen = TensorGenerator(seed=42)
A = gen.generate_matrix(50, 50)
B = gen.generate_matrix(50, 50)
print(f"   Matrix A: {A.shape}")
print(f"   Matrix B: {B.shape}")

# Compute result
print("\n2. Computing matrix multiplication...")
result = matrix_multiplication(A, B)
print(f"   Result shape: {result['output_shape']}")
print(f"   Total operations: {result['total_ops']:,}")

# Test STARK
print("\n3. Testing STARK...")
stark = STARKWrapper()
stark.setup(circuit_size=2500)
proof_stark = stark.generate_proof(
    public_inputs=result['output_shape'],
    private_inputs=A,
    circuit_description="matrix_mult"
)
verify_stark = stark.verify_proof(proof_stark.proof, result['output_shape'])

print(f"   Proof generation: {proof_stark.generation_time_ms:.2f} ms")
print(f"   Verification: {verify_stark.verification_time_ms:.2f} ms")
print(f"   Proof size: {proof_stark.proof_size_bytes:,} bytes")
print(f"   Memory: {proof_stark.memory_usage_mb:.2f} MB")
print(f"   Valid: {verify_stark.is_valid}")

# Test Groth16
print("\n4. Testing Groth16...")
groth16 = Groth16Wrapper()
groth16.setup(circuit_size=2500)
proof_groth = groth16.generate_proof(
    public_inputs=result['output_shape'],
    private_inputs=A,
    circuit_description="matrix_mult"
)
verify_groth = groth16.verify_proof(proof_groth.proof, result['output_shape'])

print(f"   Proof generation: {proof_groth.generation_time_ms:.2f} ms")
print(f"   Verification: {verify_groth.verification_time_ms:.2f} ms")
print(f"   Proof size: {proof_groth.proof_size_bytes:,} bytes")
print(f"   Memory: {proof_groth.memory_usage_mb:.2f} MB")
print(f"   Valid: {verify_groth.is_valid}")

# Comparison
print("\n5. Comparison:")
print(f"   STARK vs Groth16:")
print(f"   - Proof size: {proof_stark.proof_size_bytes / proof_groth.proof_size_bytes:.1f}x larger")
print(f"   - Gen time: {proof_stark.generation_time_ms / proof_groth.generation_time_ms:.1f}x slower")
print(f"   - Verify time: {verify_stark.verification_time_ms / verify_groth.verification_time_ms:.1f}x slower")

print("\n" + "=" * 50)
print("✓ Quick start complete!")
print("\nNext steps:")
print("  - Run full demo: python scripts/run_demo.py")
print("  - Open notebook: jupyter notebook notebooks/demo.ipynb")
print("  - Run benchmark: python scripts/run_full_benchmark.py")
