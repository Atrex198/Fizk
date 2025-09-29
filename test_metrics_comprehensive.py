"""
Enhanced ZK-FL System Test with Comprehensive Metrics Collection
Tests the complete system with detailed performance, cost, and ML metrics tracking
"""

import logging
import time
import json
import numpy as np
import torch
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

# Import ZK-FL components
from fl_server import FLServer
from fl_client import EnhancedFLClient
from zkp_proof_generator import ZKPProofGenerator
from protogalaxy_aggregator import ProtogalaxyAggregator
from metrics_collector import MetricsCollector, MetricsContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_heart_disease_data() -> Tuple[torch.Tensor, torch.Tensor]:
    """Load and prepare heart disease dataset"""
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    
    # Load the dataset
    try:
        df = pd.read_csv('heart_2020_cleaned.csv')
        logger.info(f"✅ Loaded dataset: {len(df)} samples")
    except FileNotFoundError:
        logger.error("❌ Dataset not found. Please ensure heart_2020_cleaned.csv is available")
        raise
    
    # Prepare features and target
    target_column = 'HeartDisease'
    feature_columns = [col for col in df.columns if col != target_column]
    
    X = df[feature_columns].values
    y = (df[target_column] == 'Yes').astype(int).values
    
    # Normalize features
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X)
    
    # Convert to tensors
    X_tensor = torch.FloatTensor(X)
    y_tensor = torch.FloatTensor(y)
    
    logger.info(f"📊 Data types: X={X_tensor.dtype}, y={y_tensor.dtype}")
    logger.info(f"📊 Data shapes: X={X_tensor.shape}, y={y_tensor.shape}")
    
    return X_tensor, y_tensor

def create_federated_data(X: torch.Tensor, y: torch.Tensor, num_clients: int = 3) -> List[Tuple[torch.Tensor, torch.Tensor]]:
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
        
        logger.info(f"📋 Client {i+1}: {len(client_X)} samples")
    
    return client_datasets

def run_comprehensive_metrics_test():
    """Run comprehensive ZK-FL system test with full metrics collection"""
    
    logger.info("🚀 Starting Comprehensive ZK-FL Metrics Test")
    
    # Initialize main metrics collector
    main_metrics = MetricsCollector("comprehensive_zkfl_test", "./metrics")
    main_metrics.start_monitoring(interval=0.5)
    
    try:
        # Step 1: Data preparation
        logger.info("\\n📊 Step 1: Loading and preparing data")
        X, y = load_heart_disease_data()
        client_datasets = create_federated_data(X, y, num_clients=5)  # Test with 5 clients
        
        # Step 2: Initialize FL components
        logger.info("\\n🔧 Step 2: Initializing FL system components")
        
        model_config = {
            'input_size': X.shape[1],
            'hidden_sizes': [64, 32],
            'dropout_rate': 0.2
        }
        
        # Initialize FL server with metrics
        fl_server = FLServer(model_config)
        server_metrics = MetricsCollector(\"fl_server\", \"./metrics\")\n        \n        # Initialize FL clients with metrics\n        clients = []\n        client_metrics = []\n        for i, (client_X, client_y) in enumerate(client_datasets):\n            client_id = f\"metrics_client_{i+1}\"\n            client = EnhancedFLClient(client_id, model_config, (client_X, client_y))\n            clients.append(client)\n            \n            # Each client gets its own metrics collector\n            client_metric = MetricsCollector(f\"client_{client_id}\", \"./metrics\")\n            client_metric.start_monitoring()\n            client_metrics.append(client_metric)\n        \n        logger.info(f\"✅ Initialized {len(clients)} clients with metrics collection\")\n        \n        # Step 3: Run federated training rounds with comprehensive metrics\n        logger.info(\"\\n🤝 Step 3: Federated training with metrics collection\")\n        \n        num_rounds = 3\n        all_round_metrics = []\n        \n        for round_num in range(num_rounds):\n            logger.info(f\"\\n🔄 === FL Round {round_num + 1}/{num_rounds} ===\")\n            round_start_time = time.time()\n            \n            # Collect client updates with detailed metrics\n            client_updates = []\n            round_proof_metrics = []\n            \n            for i, (client, client_metric) in enumerate(zip(clients, client_metrics)):\n                logger.info(f\"🔄 Training {client.client_id}...\")\n                \n                # Training with metrics\n                training_start = time.time()\n                local_weights = client.train_local_model(\n                    global_weights=fl_server.get_model_weights(),\n                    epochs=2,  # Reduced for faster testing\n                    learning_rate=0.01,\n                    round_number=round_num\n                )\n                training_end = time.time()\n                \n                # Record training metrics\n                client_metric.record_ml_performance(\n                    client_id=client.client_id,\n                    round_number=round_num,\n                    initial_loss=client.training_history[-1]['initial_loss'],\n                    final_loss=client.training_history[-1]['final_loss'],\n                    accuracy=client.training_history[-1].get('accuracy', 0.0),\n                    training_time=training_end - training_start,\n                    data_samples=len(client.X),\n                    epochs=2,\n                    learning_rate=0.01\n                )\n                \n                # Simulate communication metrics\n                weights_size = sum(param.numel() * 4 for param in local_weights.values())  # 4 bytes per float32\n                proof_size = len(json.dumps(client.local_proofs[-1]).encode())\n                \n                client_metric.record_communication(\n                    round_number=round_num,\n                    client_id=client.client_id,\n                    weights_size=weights_size,\n                    proof_size=proof_size,\n                    upload_time=0.1,  # Simulated\n                    download_time=0.05  # Simulated\n                )\n                \n                client_updates.append({\n                    'client_id': client.client_id,\n                    'weights': local_weights,\n                    'proof': client.local_proofs[-1],\n                    'training_loss': client.training_history[-1]['final_loss']\n                })\n                \n                round_proof_metrics.append({\n                    'client_id': client.client_id,\n                    'generation_time': client.local_proofs[-1].get('generation_time', 0),\n                    'proof_size': proof_size\n                })\n            \n            # Aggregate with metrics\n            logger.info(f\"🔗 Aggregating {len(client_updates)} client updates...\")\n            \n            aggregation_start = time.time()\n            \n            # Collect proofs for aggregation\n            proofs_for_aggregation = [update['proof'] for update in client_updates]\n            \n            # Perform Protogalaxy aggregation\n            aggregation_result = fl_server.aggregate_proofs(proofs_for_aggregation, round_num)\n            \n            # Update global model\n            client_weights = [update['weights'] for update in client_updates]\n            global_weights = fl_server.aggregate_weights(client_weights)\n            \n            aggregation_end = time.time()\n            \n            # Record aggregation metrics\n            server_metrics.record_aggregation(\n                round_number=round_num,\n                num_proofs=len(proofs_for_aggregation),\n                start_time=aggregation_start,\n                end_time=aggregation_end,\n                aggregated_proof=aggregation_result,\n                cross_terms=len(proofs_for_aggregation) * (len(proofs_for_aggregation) - 1) // 2\n            )\n            \n            round_end_time = time.time()\n            round_duration = round_end_time - round_start_time\n            \n            # Record system metrics\n            main_metrics.record_system_state(\n                round_number=round_num,\n                total_clients=len(clients),\n                active_clients=len(client_updates),\n                round_duration=round_duration\n            )\n            \n            # Calculate round statistics\n            avg_loss = np.mean([update['training_loss'] for update in client_updates])\n            avg_proof_time = np.mean([pm['generation_time'] for pm in round_proof_metrics])\n            total_proof_size = sum([pm['proof_size'] for pm in round_proof_metrics])\n            \n            round_metrics = {\n                'round': round_num + 1,\n                'duration': round_duration,\n                'avg_loss': avg_loss,\n                'avg_proof_time': avg_proof_time,\n                'total_proof_size': total_proof_size,\n                'aggregation_time': aggregation_end - aggregation_start,\n                'active_clients': len(client_updates)\n            }\n            all_round_metrics.append(round_metrics)\n            \n            logger.info(f\"✅ Round {round_num + 1} completed:\")\n            logger.info(f\"   📊 Avg loss: {avg_loss:.4f}\")\n            logger.info(f\"   ⏱️  Round duration: {round_duration:.3f}s\")\n            logger.info(f\"   🔐 Avg proof time: {avg_proof_time:.3f}s\")\n            logger.info(f\"   🔗 Aggregation time: {aggregation_end - aggregation_start:.3f}s\")\n        \n        # Step 4: Generate comprehensive metrics reports\n        logger.info(\"\\n📈 Step 4: Generating comprehensive metrics reports\")\n        \n        # Stop all monitoring\n        main_metrics.stop_monitoring()\n        server_metrics.stop_monitoring() if hasattr(server_metrics, 'stop_monitoring') else None\n        for client_metric in client_metrics:\n            client_metric.stop_monitoring()\n        \n        # Export all metrics\n        main_metrics.export_metrics(['json', 'csv', 'plots'])\n        server_metrics.export_metrics(['json', 'csv'])\n        for i, client_metric in enumerate(client_metrics):\n            client_metric.export_metrics(['json', 'csv'])\n        \n        # Generate summary report\n        summary_stats = main_metrics.get_summary_stats()\n        \n        # Step 5: Performance analysis\n        logger.info(\"\\n📊 Step 5: Performance Analysis\")\n        \n        total_experiment_time = time.time() - main_metrics.start_time\n        \n        logger.info(\"\\n\" + \"=\"*80)\n        logger.info(\"🎯 COMPREHENSIVE ZK-FL METRICS TEST SUMMARY\")\n        logger.info(\"=\"*80)\n        \n        logger.info(f\"\\n⏱️  Total experiment duration: {total_experiment_time:.2f} seconds\")\n        logger.info(f\"\\n📊 System Configuration:\")\n        logger.info(f\"   • Clients: {len(clients)}\")\n        logger.info(f\"   • Rounds: {num_rounds}\")\n        logger.info(f\"   • Data samples: {len(X):,}\")\n        logger.info(f\"   • Features: {X.shape[1]}\")\n        \n        logger.info(f\"\\n🔐 ZKP Performance:\")\n        if main_metrics.proof_metrics:\n            proof_times = [m.proof_generation_time for m in main_metrics.proof_metrics]\n            logger.info(f\"   • Total proofs generated: {len(proof_times)}\")\n            logger.info(f\"   • Avg proof generation time: {np.mean(proof_times):.3f}s\")\n            logger.info(f\"   • Min/Max proof time: {np.min(proof_times):.3f}s / {np.max(proof_times):.3f}s\")\n        \n        logger.info(f\"\\n🔗 Aggregation Performance:\")\n        if main_metrics.aggregation_metrics:\n            agg_times = [m.aggregation_time for m in main_metrics.aggregation_metrics]\n            logger.info(f\"   • Total aggregations: {len(agg_times)}\")\n            logger.info(f\"   • Avg aggregation time: {np.mean(agg_times):.3f}s\")\n            logger.info(f\"   • Total proofs aggregated: {sum(m.num_proofs for m in main_metrics.aggregation_metrics)}\")\n        \n        logger.info(f\"\\n🤖 ML Performance:\")\n        if all_round_metrics:\n            initial_loss = all_round_metrics[0]['avg_loss']\n            final_loss = all_round_metrics[-1]['avg_loss']\n            logger.info(f\"   • Initial avg loss: {initial_loss:.4f}\")\n            logger.info(f\"   • Final avg loss: {final_loss:.4f}\")\n            logger.info(f\"   • Total improvement: {initial_loss - final_loss:.4f}\")\n            logger.info(f\"   • Convergence rate: {(initial_loss - final_loss) / total_experiment_time:.6f} loss/sec\")\n        \n        logger.info(f\"\\n💾 Metrics Export:\")\n        logger.info(f\"   • JSON reports: ./metrics/*_metrics.json\")\n        logger.info(f\"   • CSV datasets: ./metrics/*_metrics.csv\")\n        logger.info(f\"   • Performance plots: ./metrics/*_performance.png\")\n        \n        logger.info(\"\\n\" + \"=\"*80)\n        logger.info(\"✅ COMPREHENSIVE METRICS COLLECTION SUCCESSFUL!\")\n        logger.info(\"📊 Ready for performance analysis and benchmarking\")\n        logger.info(\"=\"*80)\n        \n        # Return summary for further analysis\n        return {\n            'success': True,\n            'total_time': total_experiment_time,\n            'rounds_completed': num_rounds,\n            'clients_tested': len(clients),\n            'proofs_generated': len(main_metrics.proof_metrics) if main_metrics.proof_metrics else 0,\n            'aggregations_completed': len(main_metrics.aggregation_metrics) if main_metrics.aggregation_metrics else 0,\n            'summary_stats': summary_stats,\n            'round_metrics': all_round_metrics\n        }\n        \n    except Exception as e:\n        logger.error(f\"❌ Comprehensive metrics test failed: {e}\")\n        raise\n    finally:\n        # Cleanup\n        try:\n            main_metrics.stop_monitoring()\n            if 'server_metrics' in locals():\n                server_metrics.stop_monitoring() if hasattr(server_metrics, 'stop_monitoring') else None\n            if 'client_metrics' in locals():\n                for client_metric in client_metrics:\n                    client_metric.stop_monitoring()\n        except:\n            pass\n\nif __name__ == \"__main__\":\n    try:\n        result = run_comprehensive_metrics_test()\n        print(f\"\\n🎉 Test completed successfully!\")\n        print(f\"📊 Performance summary: {result['total_time']:.2f}s total, \"\n              f\"{result['proofs_generated']} proofs, {result['aggregations_completed']} aggregations\")\n              \n    except Exception as e:\n        print(f\"❌ Test failed: {e}\")\n        exit(1)\n"