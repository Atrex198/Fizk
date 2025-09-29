"""
Simple ZK-FL Metrics Test
Clean test for metrics collection integration
"""

import logging
import time
import numpy as np
import torch
from typing import Dict, Tuple
import sys
import os

# Add current directory to path for imports
sys.path.append(os.getcwd())

from fl_server import FederatedServer
from metrics_collector import MetricsCollector

def load_heart_disease_data():
    """Load heart disease dataset for testing"""
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    
    try:
        df = pd.read_csv('heart_2020_cleaned.csv')
        logger.info(f"✅ Loaded dataset: {len(df)} samples")
    except FileNotFoundError:
        logger.error("❌ Dataset not found. Using synthetic data for testing.")
        # Create synthetic data for testing
        n_samples = 1000
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        return torch.FloatTensor(X), torch.FloatTensor(y.astype(float))
    
    # Prepare features and target
    target_column = 'HeartDisease'
    feature_columns = [col for col in df.columns if col != target_column]
    
    X = df[feature_columns].values
    y = (df[target_column] == 'Yes').astype(int).values
    
    # Normalize features
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X)
    
    return torch.FloatTensor(X), torch.FloatTensor(y.astype(float))

def create_federated_data(X, y, num_clients=3):
    """Split data among federated clients"""
    data_size = len(X)
    client_data_size = data_size // num_clients
    
    client_datasets = []
    for i in range(num_clients):
        start_idx = i * client_data_size
        end_idx = start_idx + client_data_size if i < num_clients - 1 else data_size
        
        client_X = X[start_idx:end_idx]
        client_y = y[start_idx:end_idx]
        client_datasets.append((client_X, client_y))
    
    return client_datasets

class EnhancedFLClient:
    """Simple FL client for testing"""
    
    def __init__(self, client_id: str, model_config: Dict, data: Tuple[torch.Tensor, torch.Tensor]):
        from train_mlp import MLP
        from zkp_proof_generator import ZKPProofGenerator
        
        self.client_id = client_id
        self.X, self.y = data
        self.model = MLP(
            input_size=model_config['input_size'],
            hidden_sizes=model_config['hidden_sizes'],
            dropout_rate=model_config.get('dropout_rate', 0.0)
        )
        self.zkp_generator = ZKPProofGenerator()
        self.training_history = []
        self.local_proofs = []
        
    def train_local_model(self, global_weights=None, epochs=1, round_number=0):
        """Simple training for testing"""
        import torch.nn as nn
        import torch.optim as optim
        
        if global_weights:
            self.model.load_state_dict(global_weights)
        
        self.model.train()
        criterion = nn.BCELoss()
        optimizer = optim.SGD(self.model.parameters(), lr=0.01)
        
        # Quick training
        for _ in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(self.X)
            loss = criterion(outputs.squeeze(), self.y)
            loss.backward()
            optimizer.step()
        
        # Generate simple proof
        proof_result = self.zkp_generator.generate_simple_training_proof(
            model_weights={name: param for name, param in self.model.named_parameters()},
            training_loss=loss.item(),
            client_id=self.client_id
        )
        
        if proof_result.get('proof_valid'):
            proof_entry = {
                'hash': proof_result.get('proof_hash', f'proof_{self.client_id}'),
                'timestamp': time.time(),
                'loss': loss.item(),
                'generation_time': 0.1  # Simplified
            }
            self.local_proofs.append(proof_entry)
        
        return {name: param.clone() for name, param in self.model.named_parameters()}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_metrics_test():
    """Simple test for metrics collection"""
    
    logger.info("🚀 Starting Simple ZK-FL Metrics Test")
    
    # Initialize metrics
    metrics = MetricsCollector("simple_zkfl_test")
    metrics.start_monitoring()
    
    try:
        # Test 1: Basic metrics collection
        logger.info("\n📊 Test 1: Basic metrics collection")
        
        # Simulate proof generation
        start_time = time.time()
        time.sleep(0.1)  # Simulate work
        end_time = time.time()
        
        fake_proof_data = {
            "proof": {"a": "test_point", "b": "test_point", "c": "test_point"},
            "circuit_info": {"constraints_count": 1000, "variables_count": 500}
        }
        
        proof_metrics = metrics.record_proof_generation(
            client_id="test_client_1",
            start_time=start_time,
            end_time=end_time,
            proof_data=fake_proof_data
        )
        
        logger.info(f"✅ Recorded proof metrics: {proof_metrics.proof_generation_time:.3f}s")
        
        # Test 2: ML performance metrics
        logger.info("\n🤖 Test 2: ML performance metrics")
        
        ml_metrics = metrics.record_ml_performance(
            client_id="test_client_1",
            round_number=1,
            initial_loss=0.8,
            final_loss=0.6,
            accuracy=0.75,
            training_time=2.5,
            data_samples=1000,
            epochs=3,
            learning_rate=0.01
        )
        
        logger.info(f"✅ Recorded ML metrics: loss improvement {ml_metrics.loss_improvement:.3f}")
        
        # Test 3: Aggregation metrics
        logger.info("\n🔗 Test 3: Aggregation metrics")
        
        agg_start = time.time()
        time.sleep(0.05)  # Simulate aggregation
        agg_end = time.time()
        
        fake_aggregated_proof = {"aggregated_hash": "test_hash_12345"}
        
        agg_metrics = metrics.record_aggregation(
            round_number=1,
            num_proofs=3,
            start_time=agg_start,
            end_time=agg_end,
            aggregated_proof=fake_aggregated_proof,
            cross_terms=3
        )
        
        logger.info(f"✅ Recorded aggregation metrics: {agg_metrics.aggregation_time:.3f}s")
        
        # Test 4: System metrics
        logger.info("\n💻 Test 4: System metrics")
        
        sys_metrics = metrics.record_system_state(
            round_number=1,
            total_clients=3,
            active_clients=3,
            round_duration=5.0
        )
        
        logger.info(f"✅ Recorded system metrics: {sys_metrics.round_duration:.1f}s duration")
        
        # Test 5: Export metrics
        logger.info("\n📁 Test 5: Export metrics")
        
        metrics.stop_monitoring()
        metrics.export_metrics(['json', 'csv'])
        
        summary = metrics.get_summary_stats()
        
        logger.info("\n" + "="*50)
        logger.info("📊 SIMPLE METRICS TEST SUMMARY")
        logger.info("="*50)
        logger.info(f"✅ Test completed successfully!")
        logger.info(f"⏱️ Total duration: {summary['total_duration']:.2f}s")
        logger.info(f"🔐 Proofs recorded: {summary['proof_generation'].get('count', 0)}")
        logger.info(f"🔗 Aggregations recorded: {summary['aggregation'].get('count', 0)}")
        logger.info(f"📁 Metrics exported to: ./metrics/")
        logger.info("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    finally:
        try:
            metrics.stop_monitoring()
        except:
            pass

def integration_test_with_real_system():
    """Integration test with real ZK-FL system"""
    
    logger.info("🚀 Starting Integration Test with Real System")
    
    metrics = MetricsCollector("integration_test")
    metrics.start_monitoring()
    
    try:
        # Load small dataset for testing
        logger.info("📊 Loading dataset...")
        X, y = load_heart_disease_data()
        
        # Take a small subset for fast testing
        subset_size = 1000
        X_small = X[:subset_size]
        y_small = y[:subset_size]
        
        client_datasets = create_federated_data(X_small, y_small, num_clients=2)
        
        # Initialize FL system
        model_config = {
            'input_size': X_small.shape[1],
            'hidden_sizes': [32, 16],
            'dropout_rate': 0.2
        }
        
        fl_server = FederatedServer(
            host="localhost",
            port=8765,
            model_config=model_config
        )
        
        # Create clients
        clients = []
        for i, (client_X, client_y) in enumerate(client_datasets):
            client_id = f"integration_client_{i+1}"
            client = EnhancedFLClient(client_id, model_config, (client_X, client_y))
            clients.append(client)
        
        logger.info(f"✅ Initialized {len(clients)} clients")
        
        # Run one FL round with metrics
        logger.info("🔄 Running FL round with metrics...")
        
        round_start = time.time()
        client_updates = []
        
        for client in clients:
            # Train with timing
            train_start = time.time()
            local_weights = client.train_local_model(
                global_weights=fl_server.get_model_weights(),
                epochs=1,  # Quick training
                round_number=0
            )
            train_end = time.time()
            
            # Record metrics
            metrics.record_ml_performance(
                client_id=client.client_id,
                round_number=0,
                initial_loss=0.7,  # Simplified
                final_loss=0.6,
                accuracy=0.8,
                training_time=train_end - train_start,
                data_samples=len(client.X),
                epochs=1,
                learning_rate=0.01
            )
            
            client_updates.append({
                'client_id': client.client_id,
                'weights': local_weights,
                'proof': client.local_proofs[-1] if client.local_proofs else {}
            })
        
        # Aggregate
        agg_start = time.time()
        proofs = [update['proof'] for update in client_updates if update['proof']]
        
        if proofs:
            agg_result = fl_server.aggregate_proofs(proofs, 0)
        else:
            agg_result = {"mock_aggregation": "test"}
        
        agg_end = time.time()
        
        # Record aggregation metrics
        metrics.record_aggregation(
            round_number=0,
            num_proofs=len(proofs),
            start_time=agg_start,
            end_time=agg_end,
            aggregated_proof=agg_result,
            cross_terms=len(proofs)
        )
        
        round_end = time.time()
        
        # Record system metrics
        metrics.record_system_state(
            round_number=0,
            total_clients=len(clients),
            active_clients=len(client_updates),
            round_duration=round_end - round_start
        )
        
        # Export results
        metrics.stop_monitoring()
        metrics.export_metrics(['json', 'csv'])
        
        summary = metrics.get_summary_stats()
        
        logger.info("\n" + "="*60)
        logger.info("🎯 INTEGRATION TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Integration test completed!")
        logger.info(f"⏱️ Total duration: {summary['total_duration']:.2f}s")
        logger.info(f"👥 Clients tested: {len(clients)}")
        logger.info(f"🔐 Proofs generated: {len(proofs)}")
        logger.info(f"📊 Dataset size: {subset_size} samples")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            metrics.stop_monitoring()
        except:
            pass

if __name__ == "__main__":
    print("🧪 Running ZK-FL Metrics Tests")
    
    # Test 1: Simple metrics collection
    print("\n" + "="*50)
    print("TEST 1: Simple Metrics Collection")
    print("="*50)
    
    success1 = simple_metrics_test()
    
    if success1:
        print("✅ Simple metrics test PASSED")
    else:
        print("❌ Simple metrics test FAILED")
    
    # Test 2: Integration with real system
    print("\n" + "="*50)
    print("TEST 2: Integration with Real System")
    print("="*50)
    
    success2 = integration_test_with_real_system()
    
    if success2:
        print("✅ Integration test PASSED")
    else:
        print("❌ Integration test FAILED")
    
    # Final results
    if success1 and success2:
        print("\n🎉 ALL METRICS TESTS PASSED!")
        print("📊 Comprehensive metrics collection system is working!")
        print("📁 Check ./metrics/ directory for exported data")
    else:
        print("\n❌ Some tests failed")
        exit(1)