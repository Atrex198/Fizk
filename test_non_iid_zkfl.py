"""
Non-IID ZK-FL System Test
Demonstrates comprehensive non-IID data partitioning with ZK-FL system
"""

import logging
import time
import json
import numpy as np
import torch
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
from pathlib import Path

# Import ZK-FL system components
from train_mlp import MLP
from zkp_proof_generator import ZKPProofGenerator
from protogalaxy_aggregator import ProtogalaxyAggregator
from metrics_collector import MetricsCollector, MetricsContext
from non_iid_data_engine import NonIIDDataEngine, create_research_scenarios

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NonIIDZKFLExperiment:
    """Comprehensive Non-IID ZK-FL Experiment Framework"""
    
    def __init__(self, experiment_name: str = "non_iid_zkfl"):
        self.experiment_name = experiment_name
        self.results = {}
        self.data_engine = NonIIDDataEngine(random_seed=42)
        
        # Create results directory
        self.results_dir = Path(f"./non_iid_experiments/{experiment_name}")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🧪 Non-IID ZK-FL Experiment initialized: {experiment_name}")
    
    def run_scenario_experiment(self, scenario_config: Dict[str, Any], 
                              num_clients: int = 4, num_rounds: int = 3) -> Dict[str, Any]:
        """Run complete ZK-FL experiment with specific non-IID scenario"""
        
        scenario_name = scenario_config['name']
        logger.info(f"\\n🚀 Running Non-IID Scenario: {scenario_name}")
        logger.info(f"📝 Description: {scenario_config['description']}")
        
        experiment_start_time = time.time()
        
        # Initialize main metrics collector
        main_metrics = MetricsCollector(f"non_iid_{scenario_name.lower().replace(' ', '_')}")
        main_metrics.start_monitoring(interval=0.1)
        
        try:
            # Step 1: Create non-IID data partition
            logger.info(f"\\n📊 Step 1: Creating Non-IID Data Partition")
            
            partition_result = self.data_engine.create_non_iid_partition(
                csv_path='heart_2020_cleaned.csv',
                num_clients=num_clients,
                **scenario_config['config']
            )
            
            client_data = partition_result['client_data']
            heterogeneity_metrics = partition_result['heterogeneity_metrics']
            
            # Step 2: Initialize ZK-FL system with non-IID data
            logger.info(f"\\n🔧 Step 2: Initializing ZK-FL System with Non-IID Data")
            
            # Model configuration based on dataset
            X_sample, _ = next(iter(client_data.values()))
            model_config = {
                'input_size': X_sample.shape[1],
                'hidden_sizes': [128, 64, 32],
                'dropout_rate': 0.2
            }
            
            # Initialize FL server
            fl_server = NonIIDFLServer(model_config, scenario_name)
            
            # Initialize FL clients with non-IID data
            clients = []
            for client_id, (X_client, y_client) in client_data.items():
                client = NonIIDFLClient(
                    client_id=f"non_iid_client_{client_id}",
                    model_config=model_config,
                    data=(X_client, y_client),
                    scenario_name=scenario_name
                )
                clients.append(client)
            
            logger.info(f"✅ Initialized {len(clients)} clients with non-IID data")
            
            # Step 3: Run federated learning rounds
            logger.info(f"\\n🤝 Step 3: Non-IID Federated Learning ({num_rounds} rounds)")
            
            round_results = []
            
            for round_num in range(num_rounds):
                logger.info(f"\\n🔄 === Non-IID FL Round {round_num + 1}/{num_rounds} ===")
                round_start_time = time.time()
                
                # Client training with non-IID data
                client_updates = []
                round_metrics = []
                
                for client in clients:
                    logger.info(f"🔄 Training {client.client_id} with non-IID data...")
                    
                    local_weights = client.train_local_model(
                        global_weights=fl_server.get_model_weights(),
                        epochs=3,
                        learning_rate=0.01,
                        round_number=round_num
                    )
                    
                    # Extract training metrics
                    training_record = client.training_history[-1]
                    proof_record = client.local_proofs[-1]
                    
                    client_updates.append({
                        'client_id': client.client_id,
                        'weights': local_weights,
                        'proof': proof_record,
                        'training_metrics': training_record
                    })
                    
                    round_metrics.append(training_record)
                
                # Server aggregation
                logger.info(f"🔗 Aggregating {len(client_updates)} non-IID client updates...")
                
                proofs_for_aggregation = [update['proof'] for update in client_updates]
                aggregation_result = fl_server.aggregate_proofs(proofs_for_aggregation, round_num)
                
                client_weights = [update['weights'] for update in client_updates]
                global_weights = fl_server.aggregate_weights(client_weights)
                
                round_end_time = time.time()
                round_duration = round_end_time - round_start_time
                
                # Calculate round statistics
                round_stats = self._calculate_round_statistics(round_metrics, round_duration, aggregation_result)
                round_results.append(round_stats)
                
                logger.info(f"✅ Non-IID Round {round_num + 1} completed:")
                logger.info(f"   📊 Avg loss: {round_stats['avg_loss']:.4f}")
                logger.info(f"   🎯 Avg accuracy: {round_stats['avg_accuracy']:.3f}")
                logger.info(f"   📈 Loss std: {round_stats['loss_std']:.4f} (heterogeneity indicator)")
                logger.info(f"   ⏱️ Round duration: {round_duration:.3f}s")
            
            experiment_end_time = time.time()
            total_duration = experiment_end_time - experiment_start_time
            
            # Step 4: Comprehensive analysis
            logger.info(f"\\n📈 Step 4: Comprehensive Non-IID Analysis")
            
            main_metrics.stop_monitoring()
            main_metrics.export_metrics(['json', 'csv'])
            
            server_summary = fl_server.cleanup()
            client_summaries = [client.cleanup() for client in clients]
            
            # Generate comprehensive results
            experiment_results = {
                'scenario': scenario_config,
                'heterogeneity_metrics': heterogeneity_metrics,
                'round_results': round_results,
                'total_duration': total_duration,
                'server_summary': server_summary,
                'client_summaries': client_summaries,
                'convergence_analysis': self._analyze_convergence(round_results),
                'heterogeneity_impact': self._analyze_heterogeneity_impact(round_results, heterogeneity_metrics)
            }
            
            # Save results
            results_file = self.results_dir / f"{scenario_name.lower().replace(' ', '_')}_results.json"
            self._save_experiment_results(experiment_results, results_file)
            
            # Generate visualizations
            self._create_experiment_visualizations(experiment_results, scenario_name)
            
            logger.info(f"\\n✅ Non-IID Scenario '{scenario_name}' completed successfully!")
            
            return experiment_results
            
        except Exception as e:
            logger.error(f"❌ Non-IID experiment failed: {e}")
            raise
        finally:
            try:
                main_metrics.stop_monitoring()
            except:
                pass
    
    def _calculate_round_statistics(self, round_metrics: List[Dict], 
                                  round_duration: float, 
                                  aggregation_result: Dict) -> Dict[str, Any]:
        """Calculate comprehensive round statistics for non-IID analysis"""
        
        losses = [m['final_loss'] for m in round_metrics]
        accuracies = [m['final_accuracy'] for m in round_metrics]
        improvements = [m['loss_improvement'] for m in round_metrics]
        
        return {
            'avg_loss': np.mean(losses),
            'loss_std': np.std(losses),
            'min_loss': np.min(losses),
            'max_loss': np.max(losses),
            'avg_accuracy': np.mean(accuracies),
            'accuracy_std': np.std(accuracies),
            'min_accuracy': np.min(accuracies),
            'max_accuracy': np.max(accuracies),
            'avg_improvement': np.mean(improvements),
            'improvement_std': np.std(improvements),
            'round_duration': round_duration,
            'aggregation_success': aggregation_result.get('success', False),
            'client_variance_loss': np.var(losses),
            'client_variance_accuracy': np.var(accuracies)
        }
    
    def _analyze_convergence(self, round_results: List[Dict]) -> Dict[str, Any]:
        """Analyze convergence patterns in non-IID settings"""
        
        avg_losses = [r['avg_loss'] for r in round_results]
        loss_stds = [r['loss_std'] for r in round_results]
        
        # Calculate convergence metrics
        total_loss_reduction = avg_losses[0] - avg_losses[-1] if len(avg_losses) > 1 else 0
        convergence_rate = total_loss_reduction / len(avg_losses) if len(avg_losses) > 1 else 0
        
        # Stability analysis (lower std deviation indicates more stable convergence)
        avg_heterogeneity = np.mean(loss_stds)
        heterogeneity_trend = np.polyfit(range(len(loss_stds)), loss_stds, 1)[0] if len(loss_stds) > 1 else 0
        
        return {
            'total_loss_reduction': total_loss_reduction,
            'convergence_rate': convergence_rate,
            'avg_client_heterogeneity': avg_heterogeneity,
            'heterogeneity_trend': heterogeneity_trend,
            'final_loss_std': loss_stds[-1] if loss_stds else 0,
            'convergence_stability': 'Stable' if heterogeneity_trend <= 0 else 'Unstable'
        }
    
    def _analyze_heterogeneity_impact(self, round_results: List[Dict], 
                                    heterogeneity_metrics: Dict) -> Dict[str, Any]:
        """Analyze the impact of data heterogeneity on FL performance"""
        
        # Calculate performance disparity
        final_round = round_results[-1] if round_results else {}
        performance_disparity = final_round.get('loss_std', 0)
        
        # Correlation between heterogeneity and performance
        js_divergence = heterogeneity_metrics.get('avg_js_divergence', 0)
        
        return {
            'performance_disparity': performance_disparity,
            'heterogeneity_severity': 'High' if js_divergence > 0.1 else 'Medium' if js_divergence > 0.05 else 'Low',
            'impact_assessment': {
                'convergence_affected': performance_disparity > 0.05,
                'stability_affected': any(r['loss_std'] > 0.1 for r in round_results),
                'fairness_affected': final_round.get('max_loss', 0) - final_round.get('min_loss', 0) > 0.1
            }
        }
    
    def _create_experiment_visualizations(self, results: Dict[str, Any], scenario_name: str):
        """Create comprehensive visualizations for non-IID experiment"""
        
        logger.info(f"📊 Creating visualizations for {scenario_name}")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'Non-IID ZK-FL Experiment: {scenario_name}', fontsize=16)
        
        round_results = results['round_results']
        rounds = list(range(1, len(round_results) + 1))
        
        # 1. Convergence with heterogeneity
        ax1 = axes[0, 0]
        avg_losses = [r['avg_loss'] for r in round_results]
        loss_stds = [r['loss_std'] for r in round_results]
        
        ax1.errorbar(rounds, avg_losses, yerr=loss_stds, marker='o', capsize=5)
        ax1.set_xlabel('Round')
        ax1.set_ylabel('Average Loss')
        ax1.set_title('Convergence with Heterogeneity')
        ax1.grid(True, alpha=0.3)
        
        # 2. Client performance disparity
        ax2 = axes[0, 1]
        ax2.plot(rounds, loss_stds, marker='s', color='red', label='Loss Std Dev')
        
        accuracy_stds = [r['accuracy_std'] for r in round_results]
        ax2_twin = ax2.twinx()
        ax2_twin.plot(rounds, accuracy_stds, marker='^', color='blue', label='Accuracy Std Dev')
        
        ax2.set_xlabel('Round')
        ax2.set_ylabel('Loss Std Dev', color='red')
        ax2_twin.set_ylabel('Accuracy Std Dev', color='blue')
        ax2.set_title('Client Performance Disparity')
        ax2.grid(True, alpha=0.3)
        
        # 3. Aggregation success rate
        ax3 = axes[0, 2]
        success_rates = [1 if r['aggregation_success'] else 0 for r in round_results]
        ax3.bar(rounds, success_rates, alpha=0.7, color='green')
        ax3.set_xlabel('Round')
        ax3.set_ylabel('Aggregation Success')
        ax3.set_title('ZKP Aggregation Success Rate')
        ax3.set_ylim(0, 1.1)
        
        # 4. Round duration analysis
        ax4 = axes[1, 0]
        durations = [r['round_duration'] for r in round_results]
        ax4.plot(rounds, durations, marker='d', color='purple')
        ax4.set_xlabel('Round')
        ax4.set_ylabel('Duration (seconds)')
        ax4.set_title('Round Duration Analysis')
        ax4.grid(True, alpha=0.3)
        
        # 5. Heterogeneity metrics summary
        ax5 = axes[1, 1]
        ax5.axis('off')
        
        heterogeneity = results['heterogeneity_metrics']
        convergence = results['convergence_analysis']
        impact = results['heterogeneity_impact']
        
        summary_text = f"""
Heterogeneity Analysis:
• JS Divergence: {heterogeneity['avg_js_divergence']:.4f}
• Sample Size CV: {heterogeneity['coefficient_variation_sizes']:.4f}
• Earth Mover's Distance: {heterogeneity['avg_earth_movers_distance']:.4f}

Convergence Analysis:
• Loss Reduction: {convergence['total_loss_reduction']:.4f}
• Convergence Rate: {convergence['convergence_rate']:.4f}
• Stability: {convergence['convergence_stability']}

Impact Assessment:
• Performance Disparity: {impact['performance_disparity']:.4f}
• Heterogeneity Level: {impact['heterogeneity_severity']}
• Convergence Affected: {impact['impact_assessment']['convergence_affected']}
        """
        
        ax5.text(0.05, 0.95, summary_text, transform=ax5.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # 6. Performance distribution
        ax6 = axes[1, 2]
        final_round = round_results[-1]
        
        # Create performance distribution visualization
        client_losses = []  # This would need to be extracted from client summaries
        if 'client_summaries' in results:
            for summary in results['client_summaries']:
                # Extract final loss from summary if available
                pass
        
        # For now, show min/max range
        min_losses = [r['min_loss'] for r in round_results]
        max_losses = [r['max_loss'] for r in round_results]
        
        ax6.fill_between(rounds, min_losses, max_losses, alpha=0.3, label='Client Range')
        ax6.plot(rounds, avg_losses, marker='o', label='Average')
        ax6.set_xlabel('Round')
        ax6.set_ylabel('Loss')
        ax6.set_title('Client Performance Distribution')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save visualization
        viz_path = self.results_dir / f"{scenario_name.lower().replace(' ', '_')}_analysis.png"
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Visualization saved: {viz_path}")
        
        plt.show()
    
    def _save_experiment_results(self, results: Dict[str, Any], file_path: Path):
        """Save experiment results with proper serialization"""
        
        # Create serializable version of results
        serializable_results = {}
        
        for key, value in results.items():
            if isinstance(value, (dict, list, str, int, float, bool)):
                serializable_results[key] = value
            elif hasattr(value, 'tolist'):  # numpy arrays
                serializable_results[key] = value.tolist()
            else:
                serializable_results[key] = str(value)
        
        with open(file_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"💾 Results saved: {file_path}")
    
    def run_comparative_study(self, num_clients: int = 4, num_rounds: int = 3) -> Dict[str, Any]:
        """Run comparative study across all research scenarios"""
        
        logger.info(f"\\n🔬 Starting Comprehensive Non-IID Comparative Study")
        
        scenarios = create_research_scenarios()
        comparative_results = {}
        
        for scenario in scenarios:
            try:
                results = self.run_scenario_experiment(scenario, num_clients, num_rounds)
                comparative_results[scenario['name']] = results
            except Exception as e:
                logger.error(f"❌ Scenario {scenario['name']} failed: {e}")
                comparative_results[scenario['name']] = {'error': str(e)}
        
        # Generate comparative analysis
        comparison = self._generate_comparative_analysis(comparative_results)
        
        # Save comparative results
        comp_file = self.results_dir / "comparative_study_results.json"
        self._save_experiment_results(comparison, comp_file)
        
        logger.info(f"\\n🏆 Comparative Study Completed!")
        logger.info(f"📁 Results saved in: {self.results_dir}")
        
        return comparison
    
    def _generate_comparative_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparative analysis across scenarios"""
        
        comparison = {
            'scenarios_compared': list(results.keys()),
            'performance_comparison': {},
            'heterogeneity_comparison': {},
            'recommendations': []
        }
        
        for scenario_name, scenario_results in results.items():
            if 'error' in scenario_results:
                continue
                
            convergence = scenario_results.get('convergence_analysis', {})
            heterogeneity = scenario_results.get('heterogeneity_metrics', {})
            
            comparison['performance_comparison'][scenario_name] = {
                'final_loss_reduction': convergence.get('total_loss_reduction', 0),
                'convergence_stability': convergence.get('convergence_stability', 'Unknown'),
                'avg_client_heterogeneity': convergence.get('avg_client_heterogeneity', 0)
            }
            
            comparison['heterogeneity_comparison'][scenario_name] = {
                'js_divergence': heterogeneity.get('avg_js_divergence', 0),
                'sample_size_cv': heterogeneity.get('coefficient_variation_sizes', 0),
                'earth_movers_distance': heterogeneity.get('avg_earth_movers_distance', 0)
            }
        
        return comparison

# Enhanced FL components for non-IID experiments
class NonIIDFLServer:
    """Enhanced FL Server for Non-IID experiments"""
    
    def __init__(self, model_config: Dict, scenario_name: str):
        self.model_config = model_config
        self.scenario_name = scenario_name
        
        self.global_model = MLP(
            in_dim=model_config['input_size'],
            hidden=tuple(model_config['hidden_sizes']),
            dropout=model_config.get('dropout_rate', 0.0)
        )
        
        self.protogalaxy_aggregator = ProtogalaxyAggregator()
        self.metrics_collector = MetricsCollector(f"non_iid_server_{scenario_name}")
        self.metrics_collector.start_monitoring(interval=0.1)
        
        self.current_round = 0
        
        logger.info(f"🔗 Non-IID FL Server initialized for scenario: {scenario_name}")
    
    def get_model_weights(self) -> Dict[str, torch.Tensor]:
        return {name: param.clone() for name, param in self.global_model.named_parameters()}
    
    def aggregate_weights(self, client_weights: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        if not client_weights:
            return self.get_model_weights()
        
        # FedAvg aggregation
        aggregated_weights = {}
        for name in client_weights[0].keys():
            aggregated_weights[name] = torch.stack([weights[name] for weights in client_weights]).mean(dim=0)
        
        self.global_model.load_state_dict(aggregated_weights)
        return aggregated_weights
    
    def aggregate_proofs(self, proofs: List[Dict], round_number: int) -> Dict[str, Any]:
        aggregation_start_time = time.time()
        
        try:
            proof_data_list = []
            client_metadata = []
            
            for i, proof in enumerate(proofs):
                proof_data_list.append({
                    'hash': proof.get('hash', f'proof_{i}'),
                    'proof_data': proof.get('proof_data', {}),
                    'timestamp': proof.get('timestamp', time.time()),
                    'round': round_number
                })
                
                client_metadata.append({
                    'client_id': proof.get('client_id', f'client_{i}'),
                    'loss': proof.get('loss', 0.5),
                    'proof_size': proof.get('proof_size', 0),
                    'generation_time': proof.get('generation_time', 0)
                })
            
            aggregation_result = self.protogalaxy_aggregator.aggregate_client_proofs(
                proof_data_list=proof_data_list,
                client_metadata=client_metadata,
                round_number=round_number
            )
            
            aggregation_end_time = time.time()
            
            if aggregation_result.get("aggregation_valid"):
                self.metrics_collector.record_aggregation(
                    round_number=round_number,
                    num_proofs=len(proofs),
                    start_time=aggregation_start_time,
                    end_time=aggregation_end_time,
                    aggregated_proof=aggregation_result,
                    cross_terms=aggregation_result.get("cross_terms_computed", len(proofs))
                )
                
                return {"success": True, **aggregation_result}
            else:
                return {"success": False, "error": aggregation_result.get('error', 'Aggregation failed')}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cleanup(self) -> Dict[str, Any]:
        self.metrics_collector.stop_monitoring()
        self.metrics_collector.export_metrics(['json', 'csv'])
        
        protogalaxy_stats = self.protogalaxy_aggregator.get_aggregation_stats()
        metrics_summary = self.metrics_collector.get_summary_stats()
        
        return {
            "protogalaxy_stats": protogalaxy_stats,
            "metrics_summary": metrics_summary
        }

class NonIIDFLClient:
    """Enhanced FL Client for Non-IID experiments"""
    
    def __init__(self, client_id: str, model_config: Dict, data: Tuple[torch.Tensor, torch.Tensor], scenario_name: str):
        self.client_id = client_id
        self.model_config = model_config
        self.scenario_name = scenario_name
        self.X, self.y = data
        
        self.model = MLP(
            in_dim=model_config['input_size'],
            hidden=tuple(model_config['hidden_sizes']),
            dropout=model_config.get('dropout_rate', 0.0)
        )
        
        self.zkp_generator = ZKPProofGenerator()
        self.metrics_collector = MetricsCollector(f"{client_id}_{scenario_name}")
        self.metrics_collector.start_monitoring(interval=0.1)
        
        self.training_history = []
        self.local_proofs = []
        
        # Log client-specific data statistics
        pos_ratio = (self.y == 1).float().mean().item()
        logger.info(f"✅ Non-IID Client {client_id}: {len(self.X)} samples, {pos_ratio:.1%} positive")
    
    def train_local_model(self, global_weights: Optional[Dict[str, torch.Tensor]] = None, 
                         epochs: int = 3, learning_rate: float = 0.01, round_number: int = 0) -> Dict[str, torch.Tensor]:
        import torch.nn as nn
        import torch.optim as optim
        
        training_start_time = time.time()
        
        if global_weights:
            self.model.load_state_dict(global_weights)
        
        initial_weights = {name: param.clone() for name, param in self.model.named_parameters()}
        
        self.model.train()
        criterion = nn.BCELoss()
        optimizer = optim.SGD(self.model.parameters(), lr=learning_rate)
        
        # Calculate initial metrics
        with torch.no_grad():
            self.model.eval()
            initial_outputs = self.model(self.X)
            initial_loss = criterion(initial_outputs.squeeze(), self.y).item()
            initial_predictions = (initial_outputs.squeeze() > 0.5).float()
            initial_accuracy = (initial_predictions == self.y).float().mean().item()
            self.model.train()
        
        # Training loop
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(self.X)
            loss = criterion(outputs.squeeze(), self.y)
            loss.backward()
            optimizer.step()
        
        training_end_time = time.time()
        training_duration = training_end_time - training_start_time
        
        # Calculate final metrics
        with torch.no_grad():
            self.model.eval()
            final_outputs = self.model(self.X)
            final_loss = criterion(final_outputs.squeeze(), self.y).item()
            final_predictions = (final_outputs.squeeze() > 0.5).float()
            final_accuracy = (final_predictions == self.y).float().mean().item()
        
        final_weights = {name: param.clone() for name, param in self.model.named_parameters()}
        
        # Record comprehensive metrics
        self.metrics_collector.record_ml_performance(
            client_id=self.client_id,
            round_number=round_number,
            initial_loss=initial_loss,
            final_loss=final_loss,
            accuracy=final_accuracy,
            training_time=training_duration,
            data_samples=len(self.X),
            epochs=epochs,
            learning_rate=learning_rate
        )
        
        training_record = {
            "round": round_number,
            "initial_loss": initial_loss,
            "final_loss": final_loss,
            "initial_accuracy": initial_accuracy,
            "final_accuracy": final_accuracy,
            "loss_improvement": initial_loss - final_loss,
            "accuracy_improvement": final_accuracy - initial_accuracy,
            "training_time": training_duration,
            "convergence_rate": (initial_loss - final_loss) / training_duration if training_duration > 0 else 0,
            "timestamp": time.time()
        }
        self.training_history.append(training_record)
        
        # Generate ZKP proof
        training_data = (self.X[:32], self.y[:32])
        proof_hash = self.generate_training_proof(initial_weights, final_weights, training_data, final_loss, round_number)
        
        return final_weights
    
    def generate_training_proof(self, initial_weights: Dict[str, torch.Tensor], 
                               final_weights: Dict[str, torch.Tensor],
                               training_data: Tuple[torch.Tensor, torch.Tensor],
                               training_loss: float,
                               round_number: int) -> str:
        proof_start_time = time.time()
        
        try:
            proof_result = self.zkp_generator.generate_simple_training_proof(
                model_weights=final_weights,
                training_loss=training_loss,
                client_id=self.client_id
            )
            
            proof_end_time = time.time()
            proof_generation_time = proof_end_time - proof_start_time
            
            proof_data = proof_result.get('proof_data', {})
            self.metrics_collector.record_proof_generation(
                client_id=self.client_id,
                start_time=proof_start_time,
                end_time=proof_end_time,
                proof_data=proof_data
            )
            
            if proof_result.get("proof_valid"):
                proof_hash = proof_result.get("proof_hash", f"proof_{self.client_id}_{round_number}_{int(time.time())}")
                
                proof_size = len(json.dumps(proof_result).encode())
                weights_size = sum(param.numel() * 4 for param in final_weights.values())
                
                self.metrics_collector.record_communication(
                    round_number=round_number,
                    client_id=self.client_id,
                    weights_size=weights_size,
                    proof_size=proof_size,
                    upload_time=proof_generation_time * 0.1,
                    download_time=0.05
                )
                
                proof_entry = {
                    "hash": proof_hash,
                    "timestamp": time.time(),
                    "round": round_number,
                    "loss": training_loss,
                    "proof_data": proof_data,
                    "generation_time": proof_generation_time,
                    "proof_size": proof_size,
                    "weights_size": weights_size,
                    "client_id": self.client_id,
                    "circuit_config": proof_result.get("circuit_config", {})
                }
                
                self.local_proofs.append(proof_entry)
                return proof_hash
            else:
                raise Exception(f"Real ZKP proof generation failed: {proof_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            raise Exception(f"Real ZKP proof generation failed: {e}")
    
    def cleanup(self) -> Dict[str, Any]:
        self.metrics_collector.stop_monitoring()
        self.metrics_collector.export_metrics(['json', 'csv'])
        
        return self.metrics_collector.get_summary_stats()

if __name__ == "__main__":
    # Run comprehensive non-IID experiment
    experiment = NonIIDZKFLExperiment("comprehensive_non_iid_study")
    
    # Run comparative study across all scenarios
    results = experiment.run_comparative_study(num_clients=4, num_rounds=3)
    
    print("\\n🎉 COMPREHENSIVE NON-IID ZK-FL STUDY COMPLETED!")
    print("📁 Check ./non_iid_experiments/ for detailed results and visualizations")