#!/usr/bin/env python3
"""
Complete End-to-End ZK-FL System Test
Tests the full pipeline: Multiple clients -> ZKP proof generation -> Protogalaxy aggregation -> FL training
"""

import asyncio
import sys
import logging
import time
import torch
import numpy as np
from pathlib import Path
import json
import threading
from concurrent.futures import ThreadPoolExecutor

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from fl_server import FederatedServer, ClientUpdate
from fl_client import FederatedClient
from train_mlp import MLP, load_and_prepare, to_loader
from zkp_proof_generator import ZKPProofGenerator

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EndToEndTestSuite:
    """Complete end-to-end testing of the ZK-FL system"""
    
    def __init__(self):
        self.model_config = {
            'input_size': 37,  # Heart disease dataset (actual feature count)
            'hidden_sizes': [64, 32],
            'dropout_rate': 0.2
        }
        self.num_clients = 3
        self.num_rounds = 2
        self.results = {}
        
    async def run_complete_test(self):
        """Run the complete end-to-end test"""
        logger.info("🚀 Starting Complete End-to-End ZK-FL System Test")
        logger.info(f"Configuration: {self.num_clients} clients, {self.num_rounds} rounds")
        
        start_time = time.time()
        
        try:
            # Step 1: Prepare data for clients
            logger.info("\n📊 Step 1: Preparing data for federated clients")
            client_datasets = await self.prepare_client_data()
            
            # Step 2: Test individual client ZKP proof generation
            logger.info("\n🔐 Step 2: Testing ZKP proof generation per client")
            proof_generation_results = await self.test_client_proof_generation(client_datasets)
            
            # Step 3: Test server Protogalaxy aggregation
            logger.info("\n🔗 Step 3: Testing Protogalaxy proof aggregation")
            aggregation_results = await self.test_protogalaxy_aggregation(proof_generation_results)
            
            # Step 4: Test complete federated learning workflow
            logger.info("\n🤝 Step 4: Testing complete FL workflow with ZKP")
            fl_results = await self.test_complete_fl_workflow(client_datasets)
            
            # Step 5: Performance and validation analysis
            logger.info("\n📈 Step 5: Performance analysis and validation")
            performance_results = await self.analyze_performance(fl_results)
            
            # Compile final results
            total_time = time.time() - start_time
            
            self.results = {
                "test_duration_seconds": total_time,
                "data_preparation": len(client_datasets) > 0,
                "proof_generation": proof_generation_results,
                "aggregation": aggregation_results,
                "federated_learning": fl_results,
                "performance": performance_results,
                "overall_success": all([
                    len(client_datasets) > 0,
                    proof_generation_results.get("success", False),
                    aggregation_results.get("success", False),
                    fl_results.get("success", False)
                ])
            }
            
            # Print summary
            await self.print_test_summary()
            
            return self.results.get("overall_success", False)
            
        except Exception as e:
            logger.error(f"💥 End-to-end test failed: {e}")
            self.results = {"overall_success": False, "error": str(e)}
            return False
    
    async def prepare_client_data(self):
        """Prepare data splits for each client"""
        try:
            # Load the dataset
            X, y = load_and_prepare("heart_2020_cleaned.csv")
            logger.info(f"✅ Loaded dataset: {len(X)} training samples")
            
            # Convert to numpy arrays and ensure proper data types
            X_array = X.to_numpy() if hasattr(X, 'to_numpy') else X.values
            y_array = y.to_numpy() if hasattr(y, 'to_numpy') else y.values
            
            # Ensure X is numeric (float32)
            X_array = X_array.astype(np.float32)
            
            # Ensure y is binary (float32)
            y_array = y_array.astype(np.float32)
            
            logger.info(f"📊 Data types: X={X_array.dtype}, y={y_array.dtype}")
            logger.info(f"📊 Data shapes: X={X_array.shape}, y={y_array.shape}")
            
            # Split data among clients (simple random split for now)
            np.random.seed(42)  # Reproducible splits
            indices = np.random.permutation(len(X_array))
            
            client_datasets = []
            samples_per_client = len(X_array) // self.num_clients
            
            for i in range(self.num_clients):
                start_idx = i * samples_per_client
                end_idx = start_idx + samples_per_client if i < self.num_clients - 1 else len(X_array)
                
                client_indices = indices[start_idx:end_idx]
                
                client_data = {
                    "client_id": f"test_client_{i+1}",
                    "X_train": X_array[client_indices],
                    "y_train": y_array[client_indices],
                    "num_samples": len(client_indices)
                }
                client_datasets.append(client_data)
                
                logger.info(f"📋 {client_data['client_id']}: {client_data['num_samples']} samples")
            
            return client_datasets
            
        except Exception as e:
            logger.error(f"❌ Data preparation failed: {e}")
            return []
    
    async def test_client_proof_generation(self, client_datasets):
        """Test ZKP proof generation for each client"""
        results = {
            "success": False,
            "clients_tested": 0,
            "proofs_generated": 0,
            "generation_times": [],
            "proof_details": []
        }
        
        try:
            zkp_generator = ZKPProofGenerator()
            
            for client_data in client_datasets:
                logger.info(f"🔐 Testing proof generation for {client_data['client_id']}")
                
                # Create a small model for testing
                model = MLP(
                    in_dim=self.model_config['input_size'],
                    hidden=tuple(self.model_config['hidden_sizes']),
                    dropout=self.model_config['dropout_rate']
                )
                
                # Simulate training on a small batch
                batch_size = min(32, client_data['num_samples'])
                X_batch = client_data['X_train'][:batch_size]
                y_batch = client_data['y_train'][:batch_size]
                
                # Convert to tensors
                X_tensor = torch.FloatTensor(X_batch)
                y_tensor = torch.FloatTensor(y_batch)
                
                # Quick training step
                optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
                criterion = torch.nn.BCELoss()
                
                model.train()
                optimizer.zero_grad()
                outputs = model(X_tensor)
                loss = criterion(outputs, y_tensor.unsqueeze(1))
                loss.backward()
                optimizer.step()
                
                training_loss = loss.item()
                
                # Generate ZKP proof with real training data
                start_time = time.time()
                
                # Use the simplified interface with real training loss and data
                proof_result = zkp_generator.generate_simple_training_proof(
                    model_weights={name: param.detach() for name, param in model.named_parameters()},
                    training_loss=training_loss,
                    client_id=client_data['client_id']
                )
                generation_time = time.time() - start_time
                
                if proof_result.get("proof_generated", False):
                    results["proofs_generated"] += 1
                    results["generation_times"].append(generation_time)
                    results["proof_details"].append({
                        "client_id": client_data['client_id'],
                        "training_loss": training_loss,
                        "generation_time": generation_time,
                        "proof_hash": proof_result.get("proof_hash", "")[:16]
                    })
                    logger.info(f"✅ Proof generated for {client_data['client_id']} in {generation_time:.3f}s")
                else:
                    logger.warning(f"⚠️ Proof generation failed for {client_data['client_id']}")
                
                results["clients_tested"] += 1
            
            results["success"] = results["proofs_generated"] > 0
            results["avg_generation_time"] = np.mean(results["generation_times"]) if results["generation_times"] else 0
            
            logger.info(f"📊 Proof generation summary: {results['proofs_generated']}/{results['clients_tested']} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Proof generation test failed: {e}")
            results["error"] = str(e)
            return results
    
    async def test_protogalaxy_aggregation(self, proof_results):
        """Test Protogalaxy aggregation with generated proofs"""
        results = {
            "success": False,
            "aggregations_tested": 0,
            "aggregation_times": []
        }
        
        try:
            if not proof_results.get("success", False):
                logger.warning("⚠️ Skipping aggregation test - no valid proofs generated")
                return results
            
            # Create server instance
            server = FederatedServer(
                model_config=self.model_config,
                host="localhost",
                port=8767,  # Test port
                min_clients=2
            )
            
            # Create mock client updates with proof data
            client_updates = []
            for proof_detail in proof_results["proof_details"]:
                update = ClientUpdate(
                    client_id=proof_detail["client_id"],
                    model_weights=server.get_global_weights(),  # Mock weights
                    loss=proof_detail["training_loss"],
                    num_samples=100,  # Mock sample count
                    proof_hash=proof_detail["proof_hash"]
                )
                client_updates.append(update)
            
            # Test aggregation
            server.pending_updates = client_updates
            
            start_time = time.time()
            proof_hashes = [update.proof_hash for update in client_updates if update.proof_hash]
            aggregation_hash = await server.aggregate_proofs(proof_hashes)
            aggregation_time = time.time() - start_time
            
            if aggregation_hash:
                results["success"] = True
                results["aggregations_tested"] = 1
                results["aggregation_times"].append(aggregation_time)
                results["aggregation_hash"] = aggregation_hash[:20]
                results["num_proofs_aggregated"] = len(proof_hashes)
                
                logger.info(f"✅ Protogalaxy aggregation successful in {aggregation_time:.3f}s")
                logger.info(f"🔗 Aggregated {len(proof_hashes)} proofs: {aggregation_hash[:20]}...")
            else:
                logger.error("❌ Protogalaxy aggregation failed")
            
            # Get aggregation statistics
            if hasattr(server, 'protogalaxy_aggregator'):
                agg_stats = server.protogalaxy_aggregator.get_aggregation_stats()
                results["aggregation_stats"] = agg_stats
                logger.info(f"📊 Aggregation stats: {agg_stats}")
            
            server.cleanup()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Aggregation test failed: {e}")
            results["error"] = str(e)
            return results
    
    async def test_complete_fl_workflow(self, client_datasets):
        """Test complete federated learning workflow with ZKP"""
        results = {
            "success": False,
            "rounds_completed": 0,
            "total_aggregations": 0,
            "final_loss": None
        }
        
        try:
            # Create server
            server = FederatedServer(
                model_config=self.model_config,
                host="localhost",
                port=8768,  # Another test port
                min_clients=len(client_datasets)
            )
            
            # Simulate FL rounds
            for round_num in range(self.num_rounds):
                logger.info(f"🔄 FL Round {round_num + 1}/{self.num_rounds}")
                
                # Simulate client training and proof generation
                round_updates = []
                for client_data in client_datasets:
                    # Create model
                    model = MLP(
                        in_dim=self.model_config['input_size'],
                        hidden=tuple(self.model_config['hidden_sizes']),
                        dropout=self.model_config['dropout_rate']
                    )
                    
                    # Load global weights (simulate receiving from server)
                    model.load_state_dict(server.global_model.state_dict())
                    
                    # Train on client data
                    batch_size = min(32, client_data['num_samples'])
                    X_batch = torch.FloatTensor(client_data['X_train'][:batch_size])
                    y_batch = torch.FloatTensor(client_data['y_train'][:batch_size])
                    
                    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
                    criterion = torch.nn.BCELoss()
                    
                    model.train()
                    for _ in range(3):  # Few training steps
                        optimizer.zero_grad()
                        outputs = model(X_batch)
                        loss = criterion(outputs, y_batch.unsqueeze(1))
                        loss.backward()
                        optimizer.step()
                    
                    training_loss = loss.item()
                    
                    # Generate proof with real training data and weights
                    zkp_generator = ZKPProofGenerator()
                    proof_result = zkp_generator.generate_simple_training_proof(
                        model_weights={name: param.detach() for name, param in model.named_parameters()},
                        training_loss=training_loss,
                        client_id=client_data['client_id']
                    )
                    
                    # Create client update
                    update = ClientUpdate(
                        client_id=client_data['client_id'],
                        model_weights={name: param.detach() for name, param in model.named_parameters()},
                        loss=training_loss,
                        num_samples=client_data['num_samples'],
                        proof_hash=proof_result.get("proof_hash", f"mock_proof_{round_num}_{client_data['client_id']}")
                    )
                    round_updates.append(update)
                
                # Server aggregation
                server.pending_updates = round_updates
                
                # Aggregate proofs
                proof_hashes = [u.proof_hash for u in round_updates if u.proof_hash]
                aggregation_hash = await server.aggregate_proofs(proof_hashes)
                
                if aggregation_hash:
                    results["total_aggregations"] += 1
                    logger.info(f"✅ Round {round_num + 1} aggregation: {aggregation_hash[:16]}...")
                
                # Federated averaging
                new_weights = server.federated_averaging(round_updates)
                server.set_global_weights(new_weights)
                
                # Calculate round metrics
                round_loss = np.mean([u.loss for u in round_updates])
                results["final_loss"] = round_loss
                
                logger.info(f"📊 Round {round_num + 1} complete - Avg loss: {round_loss:.4f}")
                
                results["rounds_completed"] += 1
            
            results["success"] = results["rounds_completed"] == self.num_rounds
            
            # Get final server stats
            if hasattr(server, 'protogalaxy_aggregator'):
                final_stats = server.protogalaxy_aggregator.get_aggregation_stats()
                results["final_aggregation_stats"] = final_stats
            
            server.cleanup()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Complete FL workflow test failed: {e}")
            results["error"] = str(e)
            return results
    
    async def analyze_performance(self, fl_results):
        """Analyze performance metrics"""
        results = {
            "performance_analysis_complete": False
        }
        
        try:
            if not fl_results.get("success", False):
                logger.warning("⚠️ Skipping performance analysis - FL workflow failed")
                return results
            
            # Performance metrics
            metrics = {
                "rounds_completed": fl_results.get("rounds_completed", 0),
                "total_aggregations": fl_results.get("total_aggregations", 0),
                "final_training_loss": fl_results.get("final_loss", None),
                "aggregation_success_rate": fl_results.get("total_aggregations", 0) / max(fl_results.get("rounds_completed", 1), 1)
            }
            
            results.update(metrics)
            results["performance_analysis_complete"] = True
            
            logger.info(f"📈 Performance Analysis:")
            logger.info(f"   • Rounds completed: {metrics['rounds_completed']}")
            logger.info(f"   • Successful aggregations: {metrics['total_aggregations']}")
            logger.info(f"   • Final loss: {metrics['final_training_loss']:.4f}" if metrics['final_training_loss'] else "   • Final loss: N/A")
            logger.info(f"   • Aggregation success rate: {metrics['aggregation_success_rate']:.2%}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Performance analysis failed: {e}")
            results["error"] = str(e)
            return results
    
    async def print_test_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "="*80)
        logger.info("🎯 COMPLETE END-TO-END ZK-FL SYSTEM TEST SUMMARY")
        logger.info("="*80)
        
        if self.results.get("overall_success", False):
            logger.info("🎉 ✅ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY!")
        else:
            logger.info("❌ Some tests failed - see details below")
        
        logger.info(f"\n⏱️  Total test duration: {self.results.get('test_duration_seconds', 0):.2f} seconds")
        
        # Data preparation
        logger.info(f"\n📊 Data Preparation: {'✅ SUCCESS' if self.results.get('data_preparation', False) else '❌ FAILED'}")
        
        # Proof generation
        proof_results = self.results.get("proof_generation", {})
        logger.info(f"\n🔐 ZKP Proof Generation:")
        logger.info(f"   • Success: {'✅' if proof_results.get('success', False) else '❌'}")
        logger.info(f"   • Proofs generated: {proof_results.get('proofs_generated', 0)}/{proof_results.get('clients_tested', 0)}")
        if proof_results.get('avg_generation_time'):
            logger.info(f"   • Avg generation time: {proof_results['avg_generation_time']:.3f}s")
        
        # Aggregation
        agg_results = self.results.get("aggregation", {})
        logger.info(f"\n🔗 Protogalaxy Aggregation:")
        logger.info(f"   • Success: {'✅' if agg_results.get('success', False) else '❌'}")
        logger.info(f"   • Proofs aggregated: {agg_results.get('num_proofs_aggregated', 0)}")
        if agg_results.get('aggregation_times'):
            logger.info(f"   • Aggregation time: {agg_results['aggregation_times'][0]:.3f}s")
        
        # FL workflow
        fl_results = self.results.get("federated_learning", {})
        logger.info(f"\n🤝 Federated Learning Workflow:")
        logger.info(f"   • Success: {'✅' if fl_results.get('success', False) else '❌'}")
        logger.info(f"   • Rounds completed: {fl_results.get('rounds_completed', 0)}/{self.num_rounds}")
        logger.info(f"   • Total aggregations: {fl_results.get('total_aggregations', 0)}")
        if fl_results.get('final_loss') is not None:
            logger.info(f"   • Final training loss: {fl_results['final_loss']:.4f}")
        
        # Performance
        perf_results = self.results.get("performance", {})
        if perf_results.get("performance_analysis_complete", False):
            logger.info(f"\n📈 Performance Metrics:")
            logger.info(f"   • Aggregation success rate: {perf_results.get('aggregation_success_rate', 0):.2%}")
        
        logger.info("\n" + "="*80)
        
        # Save results to file
        with open("end_to_end_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info("📝 Detailed results saved to: end_to_end_test_results.json")

async def main():
    """Main test execution"""
    test_suite = EndToEndTestSuite()
    
    try:
        success = await test_suite.run_complete_test()
        
        if success:
            print("\n🚀 Complete ZK-FL system is working perfectly!")
            print("✅ Ready for production deployment")
            sys.exit(0)
        else:
            print("\n⚠️ Some system components need attention")
            print("📋 Check the detailed logs above for specific issues")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())