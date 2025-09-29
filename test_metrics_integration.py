"""
ZK-FL Metrics Integration Test
Tests metrics collection with the existing ZK-FL system
"""

import logging
import time
import numpy as np
import torch
from typing import Dict, List, Tuple
import json
import os

# Import existing ZK-FL components
from test_complete_system import load_heart_disease_data, create_federated_data
from fl_server import FLServer  
from zkp_proof_generator import ZKPProofGenerator
from protogalaxy_aggregator import ProtogalaxyAggregator
from metrics_collector import MetricsCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedFLClient:
    """Enhanced FL Client with integrated metrics collection"""
    
    def __init__(self, client_id: str, model_config: Dict, data: Tuple[torch.Tensor, torch.Tensor]):
        from train_mlp import MLP
        from sklearn.preprocessing import MinMaxScaler
        
        self.client_id = client_id
        self.model_config = model_config
        self.X, self.y = data
        
        # Normalize data for ZKP circuits
        self.scaler = MinMaxScaler()
        self.X = torch.FloatTensor(self.scaler.fit_transform(self.X.numpy()))
        self.y = self.y.float()
        
        # Initialize model
        self.model = MLP(
            input_size=model_config['input_size'],
            hidden_sizes=model_config['hidden_sizes'],
            dropout_rate=model_config.get('dropout_rate', 0.0)
        )
        
        # Initialize ZKP generator
        self.zkp_generator = ZKPProofGenerator()
        
        # Initialize metrics collector
        self.metrics_collector = MetricsCollector(f"enhanced_client_{client_id}")
        
        # Training history
        self.training_history = []
        self.local_proofs = []
        
        logger.info(f"✅ Enhanced FL Client {client_id} initialized with {len(self.X)} samples")
        logger.info(f"📊 Metrics collection enabled for {client_id}")\n    \n    def train_local_model(self, global_weights=None, epochs=3, learning_rate=0.01, round_number=0):
        """Train local model with comprehensive metrics collection"""
        import torch.nn as nn
        import torch.optim as optim
        
        training_start_time = time.time()
        
        # Load global weights if provided
        if global_weights:
            self.model.load_state_dict(global_weights)
        
        # Store initial weights
        initial_weights = {name: param.clone() for name, param in self.model.named_parameters()}
        
        # Setup training
        self.model.train()
        criterion = nn.BCELoss()
        optimizer = optim.SGD(self.model.parameters(), lr=learning_rate)
        
        # Calculate initial loss
        with torch.no_grad():
            self.model.eval()
            initial_outputs = self.model(self.X)
            initial_loss = criterion(initial_outputs.squeeze(), self.y).item()
            self.model.train()
        
        logger.info(f"🔄 Training {self.client_id} for {epochs} epochs (round {round_number})")
        logger.info(f"📊 Initial loss: {initial_loss:.4f}")
        
        # Training loop
        epoch_losses = []
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(self.X)
            loss = criterion(outputs.squeeze(), self.y)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())
        
        training_end_time = time.time()
        training_duration = training_end_time - training_start_time
        
        # Calculate final metrics
        with torch.no_grad():
            self.model.eval()
            final_outputs = self.model(self.X)
            final_loss = criterion(final_outputs.squeeze(), self.y).item()
            
            # Calculate accuracy
            predictions = (final_outputs.squeeze() > 0.5).float()
            accuracy = (predictions == self.y).float().mean().item()
        
        # Get final weights
        final_weights = {name: param.clone() for name, param in self.model.named_parameters()}
        
        # Record ML metrics
        self.metrics_collector.record_ml_performance(
            client_id=self.client_id,
            round_number=round_number,
            initial_loss=initial_loss,
            final_loss=final_loss,
            accuracy=accuracy,
            training_time=training_duration,
            data_samples=len(self.X),
            epochs=epochs,
            learning_rate=learning_rate
        )
        
        # Store training history
        training_record = {
            "round": round_number,
            "initial_loss": initial_loss,
            "final_loss": final_loss,
            "accuracy": accuracy,
            "epoch_losses": epoch_losses,
            "training_time": training_duration,
            "timestamp": time.time()
        }
        self.training_history.append(training_record)
        
        logger.info(f"✅ Training completed: {initial_loss:.4f} → {final_loss:.4f} (Δ={initial_loss-final_loss:.4f})")
        logger.info(f"🎯 Accuracy: {accuracy:.3f}")
        logger.info(f"⏱️ Training time: {training_duration:.3f}s")
        
        # Generate ZKP proof with metrics
        training_data = (self.X[:32], self.y[:32])  # Use subset for proof
        proof_hash = self.generate_training_proof(initial_weights, final_weights, training_data, final_loss)
        
        return final_weights\n    \n    def generate_training_proof(self, initial_weights, final_weights, training_data, training_loss):
        """Generate ZKP proof with metrics collection"""
        
        proof_start_time = time.time()
        
        try:
            # Generate proof using existing ZKP generator
            proof_result = self.zkp_generator.generate_simple_training_proof(
                model_weights=final_weights,
                training_loss=training_loss,
                client_id=self.client_id
            )
            
            proof_end_time = time.time()
            
            # Record proof generation metrics
            self.metrics_collector.record_proof_generation(
                client_id=self.client_id,
                start_time=proof_start_time,
                end_time=proof_end_time,
                proof_data=proof_result.get('proof_data', {})
            )
            
            if proof_result.get("proof_valid"):
                proof_hash = proof_result.get("proof_hash", f"proof_{self.client_id}_{int(time.time())}")
                
                # Store proof with metrics
                proof_entry = {
                    "hash": proof_hash,
                    "timestamp": time.time(),
                    "loss": training_loss,
                    "proof_data": proof_result.get("proof_data", {}),
                    "generation_time": proof_end_time - proof_start_time,
                    "client_id": self.client_id
                }
                
                self.local_proofs.append(proof_entry)
                
                logger.info(f"✅ ZKP proof generated: {proof_hash[:8]}...")
                logger.info(f"⏱️ Proof generation time: {proof_end_time - proof_start_time:.3f}s")
                
                return proof_hash
            else:
                raise Exception(f"Proof generation failed: {proof_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ Proof generation failed: {e}")
            raise\n\ndef test_metrics_integration():\n    \"\"\"Test metrics collection with existing ZK-FL system\"\"\"\n    \n    logger.info(\"🚀 Starting ZK-FL Metrics Integration Test\")\n    \n    # Initialize metrics collector\n    main_metrics = MetricsCollector(\"zkfl_metrics_integration\")\n    main_metrics.start_monitoring()\n    \n    try:\n        # Step 1: Load data\n        logger.info(\"\\n📊 Step 1: Loading heart disease dataset\")\n        X, y = load_heart_disease_data()\n        client_datasets = create_federated_data(X, y, num_clients=3)\n        \n        # Step 2: Initialize system\n        logger.info(\"\\n🔧 Step 2: Initializing FL system with metrics\")\n        \n        model_config = {\n            'input_size': X.shape[1],\n            'hidden_sizes': [64, 32],\n            'dropout_rate': 0.2\n        }\n        \n        # Initialize server\n        fl_server = FLServer(model_config)\n        \n        # Initialize enhanced clients with metrics\n        clients = []\n        for i, (client_X, client_y) in enumerate(client_datasets):\n            client_id = f\"metrics_test_client_{i+1}\"\n            client = EnhancedFLClient(client_id, model_config, (client_X, client_y))\n            clients.append(client)\n        \n        logger.info(f\"✅ Initialized {len(clients)} clients with metrics collection\")\n        \n        # Step 3: Run federated rounds with metrics\n        logger.info(\"\\n🤝 Step 3: Federated learning with metrics tracking\")\n        \n        num_rounds = 2\n        for round_num in range(num_rounds):\n            logger.info(f\"\\n🔄 FL Round {round_num + 1}/{num_rounds}\")\n            round_start_time = time.time()\n            \n            # Collect client updates\n            client_updates = []\n            for client in clients:\n                local_weights = client.train_local_model(\n                    global_weights=fl_server.get_model_weights(),\n                    epochs=2,\n                    round_number=round_num\n                )\n                \n                client_updates.append({\n                    'client_id': client.client_id,\n                    'weights': local_weights,\n                    'proof': client.local_proofs[-1] if client.local_proofs else {},\n                    'training_loss': client.training_history[-1]['final_loss']\n                })\n            \n            # Aggregate proofs\n            logger.info(f\"🔗 Aggregating {len(client_updates)} client proofs...\")\n            aggregation_start = time.time()\n            \n            proofs = [update['proof'] for update in client_updates if update['proof']]\n            if proofs:\n                aggregation_result = fl_server.aggregate_proofs(proofs, round_num)\n            else:\n                aggregation_result = {\"aggregated_hash\": f\"mock_aggregation_{round_num}\"}\n            \n            aggregation_end = time.time()\n            \n            # Record aggregation metrics\n            main_metrics.record_aggregation(\n                round_number=round_num,\n                num_proofs=len(proofs),\n                start_time=aggregation_start,\n                end_time=aggregation_end,\n                aggregated_proof=aggregation_result,\n                cross_terms=len(proofs)\n            )\n            \n            # Update global model\n            client_weights = [update['weights'] for update in client_updates]\n            global_weights = fl_server.aggregate_weights(client_weights)\n            \n            round_end_time = time.time()\n            \n            # Record system metrics\n            main_metrics.record_system_state(\n                round_number=round_num,\n                total_clients=len(clients),\n                active_clients=len(client_updates),\n                round_duration=round_end_time - round_start_time\n            )\n            \n            # Round summary\n            avg_loss = np.mean([update['training_loss'] for update in client_updates])\n            logger.info(f\"✅ Round {round_num + 1} completed - Avg loss: {avg_loss:.4f}\")\n        \n        # Step 4: Export metrics\n        logger.info(\"\\n📊 Step 4: Exporting comprehensive metrics\")\n        \n        main_metrics.stop_monitoring()\n        \n        # Export metrics for all components\n        main_metrics.export_metrics(['json', 'csv', 'plots'])\n        \n        for client in clients:\n            client.metrics_collector.export_metrics(['json', 'csv'])\n        \n        # Generate summary\n        summary = main_metrics.get_summary_stats()\n        \n        logger.info(\"\\n\" + \"=\"*60)\n        logger.info(\"📊 METRICS INTEGRATION TEST SUMMARY\")\n        logger.info(\"=\"*60)\n        logger.info(f\"✅ Test completed successfully!\")\n        logger.info(f\"⏱️ Total duration: {summary['total_duration']:.2f}s\")\n        logger.info(f\"🔐 Proofs generated: {summary['proof_generation'].get('count', 0)}\")\n        logger.info(f\"🔗 Aggregations: {summary['aggregation'].get('count', 0)}\")\n        logger.info(f\"🤖 Training rounds: {summary['ml_performance'].get('total_training_rounds', 0)}\")\n        logger.info(f\"📁 Metrics exported to: ./metrics/\")\n        logger.info(\"=\"*60)\n        \n        return {\n            'success': True,\n            'summary': summary,\n            'clients_tested': len(clients),\n            'rounds_completed': num_rounds\n        }\n        \n    except Exception as e:\n        logger.error(f\"❌ Metrics integration test failed: {e}\")\n        raise\n    finally:\n        # Cleanup\n        try:\n            main_metrics.stop_monitoring()\n        except:\n            pass\n\nif __name__ == \"__main__\":\n    try:\n        result = test_metrics_integration()\n        print(f\"\\n🎉 Metrics integration test completed successfully!\")\n        print(f\"📊 Check ./metrics/ directory for comprehensive performance data\")\n        \n    except Exception as e:\n        print(f\"❌ Test failed: {e}\")\n        import traceback\n        traceback.print_exc()\n        exit(1)\n"