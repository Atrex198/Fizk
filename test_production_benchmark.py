#!/usr/bin/env python3
"""
Test Production Multi-Protocol Benchmark
======================================

Quick test to verify the production benchmark system works
before running the full benchmark.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from real_dataset_loader import RealDatasetLoader
        print("✅ RealDatasetLoader imported")
        
        from real_ml_trainer import RealMLTrainer, TrainingConfig
        print("✅ RealMLTrainer imported")
        
        # Test dataset loading
        loader = RealDatasetLoader()
        print("✅ Dataset loader initialized")
        
        # Test trainer
        config = TrainingConfig()
        trainer = RealMLTrainer(input_features=11, config=config)
        print("✅ ML trainer initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_dataset_loading():
    """Test real dataset loading"""
    print("\n📊 Testing dataset loading...")
    
    try:
        from real_dataset_loader import RealDatasetLoader
        
        loader = RealDatasetLoader()
        
        # Check if cardio dataset exists
        cardio_file = Path("cardio_train.csv")
        if not cardio_file.exists():
            print(f"⚠️  Cardio dataset not found at {cardio_file}")
            print("   Creating synthetic test data...")
            
            # Create minimal test dataset
            import pandas as pd
            import numpy as np
            
            np.random.seed(42)
            data = {
                'id': range(1000),
                'age': np.random.randint(30, 80, 1000),
                'gender': np.random.randint(1, 3, 1000),
                'height': np.random.randint(150, 200, 1000),
                'weight': np.random.randint(50, 120, 1000),
                'ap_hi': np.random.randint(80, 180, 1000),
                'ap_lo': np.random.randint(60, 120, 1000),
                'cholesterol': np.random.randint(1, 4, 1000),
                'gluc': np.random.randint(1, 4, 1000),
                'smoke': np.random.randint(0, 2, 1000),
                'alco': np.random.randint(0, 2, 1000),
                'active': np.random.randint(0, 2, 1000),
                'cardio': np.random.randint(0, 2, 1000)
            }
            
            df = pd.DataFrame(data)
            df.to_csv('cardio_train.csv', sep=';', index=False)
            print("✅ Test dataset created")
        
        # Load dataset
        X, y = loader.load_dataset('cardio')
        print(f"✅ Dataset loaded: {X.shape} features, {y.shape} labels")
        
        # Test non-IID partitioning
        client_data = loader.create_non_iid_partition('cardio', num_clients=3)
        print(f"✅ Created partition for 3 clients")
        
        return True, X, y, client_data
        
    except Exception as e:
        print(f"❌ Dataset loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None, None

def test_ml_training():
    """Test ML training"""
    print("\n🧠 Testing ML training...")
    
    try:
        from real_ml_trainer import RealMLTrainer, TrainingConfig
        import numpy as np
        
        # Create test data
        X_test = np.random.randn(100, 11)
        y_test = np.random.randint(0, 2, 100)
        
        # Initialize trainer
        config = TrainingConfig(
            learning_rate=0.01,
            batch_size=16,
            local_epochs=2
        )
        
        trainer = RealMLTrainer(input_features=11, config=config)
        
        # Test training
        result = trainer.train_local_model(
            X_train=X_test,
            y_train=y_test,
            epochs=2
        )
        
        print(f"✅ Training completed:")
        print(f"   Final accuracy: {result.final_accuracy:.4f}")
        print(f"   Final loss: {result.final_loss:.4f}")
        print(f"   Training time: {result.training_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ ML training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_basic_benchmark():
    """Test basic benchmark functionality"""
    print("\n🏁 Testing basic benchmark...")
    
    try:
        # Import the benchmark components
        import sys
        sys.path.append('.')
        
        from production_multi_protocol_benchmark import (
            ProductionBenchmarkConfig, 
            ProductionMetricsCollector,
            ProductionBenchmarkTrainer
        )
        from real_ml_trainer import TrainingConfig
        import numpy as np
        
        # Create test configuration
        config = ProductionBenchmarkConfig(
            num_clients=2,
            num_rounds=2,
            local_epochs=1,
            zkp_security_level=128  # Reduced for testing
        )
        
        # Test metrics collector
        metrics = ProductionMetricsCollector(config)
        print("✅ Metrics collector initialized")
        
        # Test benchmark trainer wrapper
        trainer_config = TrainingConfig(
            learning_rate=0.01,
            batch_size=16,
            local_epochs=1
        )
        
        trainer = ProductionBenchmarkTrainer(input_features=11, config=trainer_config)
        print("✅ Benchmark trainer wrapper initialized")
        
        # Test training interface
        X_test = np.random.randn(50, 11)
        y_test = np.random.randint(0, 2, 50)
        
        # Test model operations
        initial_weights = trainer.get_model_weights()
        print(f"✅ Got initial weights: {len(initial_weights)} layers")
        
        # Test training
        result = trainer.train_epoch(X_test, y_test)
        print(f"✅ Training epoch completed: acc={result['accuracy']:.4f}")
        
        # Test weight update
        final_weights = trainer.get_model_weights()
        trainer.set_model_weights(final_weights)
        print("✅ Weight operations successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic benchmark test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Production Multi-Protocol Benchmark Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Imports
    if test_imports():
        tests_passed += 1
    
    # Test 2: Dataset loading
    dataset_success, X, y, client_data = test_dataset_loading()
    if dataset_success:
        tests_passed += 1
    
    # Test 3: ML training
    if test_ml_training():
        tests_passed += 1
    
    # Test 4: Basic benchmark
    if await test_basic_benchmark():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Ready for production benchmark.")
        return True
    else:
        print("❌ Some tests failed. Fix issues before running full benchmark.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)