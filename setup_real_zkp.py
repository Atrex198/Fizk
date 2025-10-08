"""
Setup script for Real ZKP Implementation
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("=" * 70)
    print("Installing Real ZKP Dependencies")
    print("=" * 70)
    
    dependencies = [
        "py_ecc>=6.0.0",
        "numpy>=1.21.0",
        "torch>=1.9.0",
    ]
    
    print("\n📦 Installing dependencies...")
    for dep in dependencies:
        print(f"   Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"   ✅ {dep} installed")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {dep}: {e}")
            return False
    
    return True


def verify_installation():
    """Verify installation"""
    print("\n🔍 Verifying installation...")
    
    checks = []
    
    # Check py_ecc
    try:
        from py_ecc.bn128.bn128_curve import G1, curve_order
        print("   ✅ py_ecc (BN128 curve support)")
        checks.append(True)
    except ImportError as e:
        print(f"   ❌ py_ecc import failed: {e}")
        checks.append(False)
    
    # Check numpy
    try:
        import numpy as np
        print(f"   ✅ numpy {np.__version__}")
        checks.append(True)
    except ImportError as e:
        print(f"   ❌ numpy import failed: {e}")
        checks.append(False)
    
    # Check torch
    try:
        import torch
        print(f"   ✅ torch {torch.__version__}")
        checks.append(True)
    except ImportError as e:
        print(f"   ❌ torch import failed: {e}")
        checks.append(False)
    
    # Check our modules
    try:
        from zkp_protocols.base import IZKPProtocol
        print("   ✅ zkp_protocols.base")
        checks.append(True)
    except ImportError as e:
        print(f"   ❌ zkp_protocols.base import failed: {e}")
        checks.append(False)
    
    try:
        from zkp_protocols.protostar_real import RealProtostarProtocol
        print("   ✅ zkp_protocols.protostar_real")
        checks.append(True)
    except ImportError as e:
        print(f"   ❌ zkp_protocols.protostar_real import failed: {e}")
        checks.append(False)
    
    return all(checks)


def run_quick_test():
    """Run a quick test"""
    print("\n🧪 Running quick test...")
    
    try:
        from zkp_protocols.protostar_real import RealProtostarProtocol
        from zkp_protocols.base import TrainingStatement, TrainingWitness
        import numpy as np
        import time
        
        # Initialize protocol
        config = {
            'trusted_setup_size': 512,  # Smaller for quick test
            'curve': 'BN128',
            'enable_ivc': True,
            'max_constraints': 10000
        }
        
        print("   Initializing protocol...")
        protocol = RealProtostarProtocol(config)
        protocol.setup()
        print("   ✅ Protocol initialized")
        
        # Create test data
        print("   Creating test proof...")
        initial_weights = {
            'layer1.weight': np.random.randn(5, 3) * 0.1,
            'layer1.bias': np.random.randn(5) * 0.1,
        }
        
        final_weights = {
            'layer1.weight': initial_weights['layer1.weight'] - 0.01 * np.random.randn(5, 3),
            'layer1.bias': initial_weights['layer1.bias'] - 0.01 * np.random.randn(5),
        }
        
        statement = TrainingStatement(
            model_architecture="test",
            initial_weights_commitment="init",
            final_weights_commitment="final",
            dataset_commitment="data",
            local_epochs=5,
            batch_size=32,
            learning_rate=0.01,
            claimed_accuracy=0.85,
            claimed_loss=0.42,
            sample_count=100,
            round_number=1,
            client_id="test",
            timestamp=time.time()
        )
        
        witness = TrainingWitness(
            initial_weights=initial_weights,
            final_weights=final_weights,
            dataset_samples=np.random.randn(50, 3),
            dataset_labels=np.random.randint(0, 2, 50),
            random_seed=42
        )
        
        # Generate proof
        proof = protocol.generate_proof(statement, witness)
        print(f"   ✅ Proof generated ({proof.get_size_bytes()} bytes)")
        
        # Verify proof
        result = protocol.verify_proof(proof, statement)
        
        if result.is_valid:
            print("   ✅ Proof verified successfully")
            return True
        else:
            print(f"   ❌ Proof verification failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main setup function"""
    print("\n" + "=" * 70)
    print("🔐 Real ZKP Implementation Setup")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Install required dependencies (py_ecc, numpy, torch)")
    print("  2. Verify installation")
    print("  3. Run a quick test")
    print("\n" + "=" * 70)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed!")
        return False
    
    # Verify installation
    if not verify_installation():
        print("\n❌ Installation verification failed!")
        return False
    
    # Run quick test
    if not run_quick_test():
        print("\n❌ Quick test failed!")
        return False
    
    # Success
    print("\n" + "=" * 70)
    print("✅ SETUP COMPLETE!")
    print("=" * 70)
    print("\nYou can now:")
    print("  1. Run full test suite: python test_real_protostar.py")
    print("  2. Import in your code:")
    print("     from zkp_protocols.protostar_real import RealProtostarProtocol")
    print("  3. Read documentation: zkp_protocols/README_REAL_IMPLEMENTATION.md")
    print("\n" + "=" * 70)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
