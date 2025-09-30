#!/usr/bin/env python3
"""
ZK-FL Training and Verification Pipeline
Separates FL training + proof generation from verification for realistic production workflow
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import pickle
import numpy as np
import torch
import torch.nn as nn

# Import our existing modules
from metrics_collector import MetricsCollector
from zkfl_config_website import ZKFLConfigManager
from advanced_circuit_optimizer import AdvancedCircuitOptimizer

@dataclass
class TrainingResult:
    """Results from FL training round"""
    round_id: str
    timestamp: str
    hospital_id: str
    model_state: Dict[str, Any]
    training_metrics: Dict[str, float]
    data_stats: Dict[str, int]
    training_time: float

@dataclass
class ZKProof:
    """Zero-knowledge proof structure"""
    proof_id: str
    round_id: str
    hospital_id: str
    timestamp: str
    commitment: str
    witness_hash: str
    public_inputs: Dict[str, Any]
    circuit_constraints: int
    proof_size_kb: int
    generation_time: float
    groth16_proof: Dict[str, str]  # Simulated Groth16 proof components

@dataclass
class VerificationResult:
    """Proof verification result"""
    verification_id: str
    round_id: str
    timestamp: str
    aggregated_proof_id: str
    individual_proofs: List[str]
    verification_status: bool
    verification_time: float
    protogalaxy_aggregation_time: float
    error_message: Optional[str] = None

class ZKFLTrainingPipeline:
    """Handles FL training and proof generation phase"""
    
    def __init__(self, storage_root: str = "./zkfl_storage"):
        self.storage_root = Path(storage_root)
        self.config_manager = ZKFLConfigManager()
        self.circuit_optimizer = AdvancedCircuitOptimizer()
        self.metrics_collector = MetricsCollector("training_pipeline")
        
        # Ensure storage directories exist
        for subdir in ['training_rounds', 'proofs', 'models']:
            (self.storage_root / subdir).mkdir(parents=True, exist_ok=True)
            
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def run_training_round(self, round_number: int) -> Tuple[List[TrainingResult], List[ZKProof]]:
        """Execute complete FL training round with proof generation"""
        round_id = f"round_{round_number:03d}_{int(time.time())}"
        self.logger.info(f"🚀 Starting FL Training Round {round_number} (ID: {round_id})")
        
        config = self.config_manager.config
        participating_clients = int(config.num_clients * config.client_fraction)
        num_clients = max(2, participating_clients)
        
        training_results = []
        zkp_proofs = []
        
        # Phase 1: Parallel FL Training across hospitals
        self.logger.info(f"Phase 1: 🏥 {num_clients} hospitals starting FL training...")
        
        for i in range(num_clients):
            hospital_id = f"hospital_{i+1:02d}"
            
            # Simulate realistic FL training
            training_result = self._simulate_hospital_training(round_id, hospital_id, round_number)
            training_results.append(training_result)
            
            # Generate ZKP proof for this training
            zkp_proof = self._generate_zkp_proof(training_result)
            zkp_proofs.append(zkp_proof)
            
            self.logger.info(f"  ✅ {hospital_id}: Training completed, proof generated")
        
        # Phase 2: Save all training results and proofs
        self._save_training_round(round_id, training_results, zkp_proofs)
        
        self.logger.info(f"✅ Training Round {round_number} completed: {len(training_results)} models, {len(zkp_proofs)} proofs saved")
        
        return training_results, zkp_proofs
    
    def _simulate_hospital_training(self, round_id: str, hospital_id: str, round_number: int) -> TrainingResult:
        """Simulate realistic FL training at a hospital"""
        start_time = time.time()
        
        # Simulate training metrics that improve over rounds
        base_loss = 0.8 - (round_number * 0.02)
        training_loss = max(0.1, base_loss + np.random.normal(0, 0.05))
        training_accuracy = min(0.95, 0.6 + round_number * 0.008 + np.random.normal(0, 0.02))
        
        # Simulate model state (simplified)
        model_state = {
            'layer_1_weights': np.random.randn(64, 13).tolist(),
            'layer_1_bias': np.random.randn(64).tolist(),
            'layer_2_weights': np.random.randn(32, 64).tolist(),
            'layer_2_bias': np.random.randn(32).tolist(),
            'output_weights': np.random.randn(1, 32).tolist(),
            'output_bias': np.random.randn(1).tolist(),
        }
        
        # Simulate realistic training time
        training_time = 0.5 + np.random.exponential(0.3)  # 0.5-2.0 seconds typically
        time.sleep(min(training_time, 0.1))  # Don't actually wait full time in demo
        
        return TrainingResult(
            round_id=round_id,
            timestamp=datetime.now().isoformat(),
            hospital_id=hospital_id,
            model_state=model_state,
            training_metrics={
                'loss': training_loss,
                'accuracy': training_accuracy,
                'epochs': np.random.randint(3, 8),
                'learning_rate': 0.001,
                'batch_size': 32
            },
            data_stats={
                'samples': np.random.randint(800, 1200),
                'features': 13,
                'non_iid_alpha': 0.5
            },
            training_time=training_time
        )
    
    def _generate_zkp_proof(self, training_result: TrainingResult) -> ZKProof:
        """Generate ZKP proof for training result"""
        start_time = time.time()
        
        # Create deterministic proof ID
        proof_content = f"{training_result.round_id}_{training_result.hospital_id}_{training_result.timestamp}"
        proof_id = f"proof_{hashlib.sha256(proof_content.encode()).hexdigest()[:16]}"
        
        # Generate commitment (hash of model weights)
        model_hash = hashlib.sha256(str(training_result.model_state).encode()).hexdigest()
        commitment = f"groth16_{model_hash[:16]}"
        
        # Generate witness hash
        witness_data = f"{training_result.training_metrics}_{training_result.data_stats}"
        witness_hash = f"witness_{hashlib.sha256(witness_data.encode()).hexdigest()[:16]}"
        
        # Public inputs (what can be verified publicly)
        public_inputs = {
            'loss_commitment': training_result.training_metrics['loss'],
            'accuracy_commitment': training_result.training_metrics['accuracy'],
            'sample_count': training_result.data_stats['samples'],
            'model_size_hash': len(str(training_result.model_state)),
            'round_number': int(training_result.round_id.split('_')[1])
        }
        
        # Simulate circuit constraints based on model complexity
        circuit_constraints = 8000 + len(str(training_result.model_state)) * 2
        
        # Generate realistic Groth16 proof components
        groth16_proof = {
            'pi_a': f"0x{hashlib.sha256(f'{proof_id}_pi_a'.encode()).hexdigest()}",
            'pi_b': f"0x{hashlib.sha256(f'{proof_id}_pi_b'.encode()).hexdigest()}",
            'pi_c': f"0x{hashlib.sha256(f'{proof_id}_pi_c'.encode()).hexdigest()}",
            'public_signals': [str(val) for val in public_inputs.values()]
        }
        
        # Proof generation time (realistic for ZKP)
        generation_time = 0.1 + np.random.exponential(0.2)  # 0.1-0.8 seconds typically
        time.sleep(min(generation_time, 0.05))  # Brief pause for realism
        
        proof_size_kb = 45 + np.random.randint(0, 35)  # 45-80 KB typical for Groth16
        
        return ZKProof(
            proof_id=proof_id,
            round_id=training_result.round_id,
            hospital_id=training_result.hospital_id,
            timestamp=datetime.now().isoformat(),
            commitment=commitment,
            witness_hash=witness_hash,
            public_inputs=public_inputs,
            circuit_constraints=circuit_constraints,
            proof_size_kb=proof_size_kb,
            generation_time=generation_time,
            groth16_proof=groth16_proof
        )
    
    def _save_training_round(self, round_id: str, training_results: List[TrainingResult], proofs: List[ZKProof]):
        """Save training round data to organized storage"""
        round_dir = self.storage_root / "training_rounds" / round_id
        round_dir.mkdir(parents=True, exist_ok=True)
        
        # Save training results
        training_file = round_dir / "training_results.json"
        with open(training_file, 'w') as f:
            json.dump([asdict(result) for result in training_results], f, indent=2)
        
        # Save individual model states
        models_dir = self.storage_root / "models" / round_id
        models_dir.mkdir(parents=True, exist_ok=True)
        
        for result in training_results:
            model_file = models_dir / f"{result.hospital_id}_model.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(result.model_state, f)
        
        # Save proofs
        proofs_dir = self.storage_root / "proofs" / round_id
        proofs_dir.mkdir(parents=True, exist_ok=True)
        
        for proof in proofs:
            proof_file = proofs_dir / f"{proof.hospital_id}_proof.json"
            with open(proof_file, 'w') as f:
                json.dump(asdict(proof), f, indent=2)
        
        # Save round summary
        summary = {
            'round_id': round_id,
            'timestamp': datetime.now().isoformat(),
            'num_participants': len(training_results),
            'training_files': [f"{r.hospital_id}_model.pkl" for r in training_results],
            'proof_files': [f"{p.hospital_id}_proof.json" for p in proofs],
            'total_training_time': sum(r.training_time for r in training_results),
            'total_proof_generation_time': sum(p.generation_time for p in proofs),
            'average_loss': np.mean([r.training_metrics['loss'] for r in training_results]),
            'average_accuracy': np.mean([r.training_metrics['accuracy'] for r in training_results])
        }
        
        summary_file = round_dir / "round_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"💾 Saved round {round_id}: {len(training_results)} models, {len(proofs)} proofs")

class ZKFLVerificationPipeline:
    """Handles proof verification phase (separate from training)"""
    
    def __init__(self, storage_root: str = "./zkfl_storage"):
        self.storage_root = Path(storage_root)
        self.circuit_optimizer = AdvancedCircuitOptimizer()
        
        # Ensure verification results directory exists
        (self.storage_root / "verification_results").mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging"""
        self.logger = logging.getLogger(f"{__name__}_verification")
        
    def verify_round(self, round_id: str) -> VerificationResult:
        """Verify all proofs from a training round"""
        self.logger.info(f"🔍 Starting verification for round {round_id}")
        
        # Load proofs for this round
        proofs = self._load_round_proofs(round_id)
        if not proofs:
            self.logger.error(f"No proofs found for round {round_id}")
            return self._create_failed_verification(round_id, "No proofs found")
        
        # Phase 1: Protogalaxy Aggregation
        aggregation_start = time.time()
        aggregated_proof = self._protogalaxy_aggregate(proofs)
        aggregation_time = time.time() - aggregation_start
        
        # Phase 2: Verify aggregated proof
        verification_start = time.time()
        verification_success = self._verify_aggregated_proof(aggregated_proof)
        verification_time = time.time() - verification_start
        
        # Create verification result
        result = VerificationResult(
            verification_id=f"verify_{round_id}_{int(time.time())}",
            round_id=round_id,
            timestamp=datetime.now().isoformat(),
            aggregated_proof_id=aggregated_proof['proof_id'],
            individual_proofs=[p.proof_id for p in proofs],
            verification_status=verification_success,
            verification_time=verification_time,
            protogalaxy_aggregation_time=aggregation_time
        )
        
        # Save verification result
        self._save_verification_result(result)
        
        status = "✅ SUCCESS" if verification_success else "❌ FAILED"
        self.logger.info(f"🔍 Verification complete for {round_id}: {status} ({len(proofs)} proofs → 1 aggregated)")
        
        return result
    
    def _load_round_proofs(self, round_id: str) -> List[ZKProof]:
        """Load all proofs for a specific round"""
        proofs_dir = self.storage_root / "proofs" / round_id
        if not proofs_dir.exists():
            return []
        
        proofs = []
        for proof_file in proofs_dir.glob("*_proof.json"):
            try:
                with open(proof_file, 'r') as f:
                    proof_data = json.load(f)
                    proof = ZKProof(**proof_data)
                    proofs.append(proof)
            except Exception as e:
                self.logger.error(f"Failed to load proof {proof_file}: {e}")
        
        return proofs
    
    def _protogalaxy_aggregate(self, proofs: List[ZKProof]) -> Dict[str, Any]:
        """Aggregate multiple proofs using Protogalaxy protocol"""
        self.logger.info(f"🌟 Protogalaxy aggregating {len(proofs)} proofs...")
        
        # Simulate Protogalaxy aggregation work
        aggregation_complexity = len(proofs) * 0.03 + np.random.uniform(0, 0.05)
        time.sleep(min(aggregation_complexity, 0.1))  # Brief pause for realism
        
        # Create aggregated proof structure
        combined_public_inputs = {}
        for proof in proofs:
            for key, value in proof.public_inputs.items():
                if key in combined_public_inputs:
                    if isinstance(value, (int, float)):
                        combined_public_inputs[key] += value
                else:
                    combined_public_inputs[key] = value
        
        # Average some metrics
        combined_public_inputs['loss_commitment'] /= len(proofs)
        combined_public_inputs['accuracy_commitment'] /= len(proofs)
        
        aggregated_proof = {
            'proof_id': f"aggregated_{proofs[0].round_id}_{int(time.time())}",
            'type': 'protogalaxy_aggregated',
            'original_proofs': [p.proof_id for p in proofs],
            'combined_public_inputs': combined_public_inputs,
            'combined_constraints': sum(p.circuit_constraints for p in proofs),
            'aggregated_size_kb': 85,  # Protogalaxy creates compact proof regardless of input count
            'aggregation_algorithm': 'protogalaxy_fold',
            'folding_iterations': len(proofs) - 1
        }
        
        self.logger.info(f"🌟 Aggregated {len(proofs)} proofs → {aggregated_proof['aggregated_size_kb']}KB proof")
        return aggregated_proof
    
    def _verify_aggregated_proof(self, aggregated_proof: Dict[str, Any]) -> bool:
        """Verify the aggregated proof (single verification)"""
        self.logger.info(f"✅ Verifying aggregated proof {aggregated_proof['proof_id']}")
        
        # Simulate realistic verification work
        verification_complexity = 0.05 + np.random.uniform(0.02, 0.08)
        time.sleep(min(verification_complexity, 0.05))
        
        # For honest hospitals, verification should always succeed
        # In production, this would check cryptographic proof validity
        verification_success = True
        
        if verification_success:
            self.logger.info(f"✅ Aggregated proof verification: SUCCESS")
        else:
            self.logger.error(f"❌ Aggregated proof verification: FAILED")
        
        return verification_success
    
    def _create_failed_verification(self, round_id: str, error_message: str) -> VerificationResult:
        """Create a failed verification result"""
        return VerificationResult(
            verification_id=f"verify_{round_id}_{int(time.time())}_failed",
            round_id=round_id,
            timestamp=datetime.now().isoformat(),
            aggregated_proof_id="",
            individual_proofs=[],
            verification_status=False,
            verification_time=0.0,
            protogalaxy_aggregation_time=0.0,
            error_message=error_message
        )
    
    def _save_verification_result(self, result: VerificationResult):
        """Save verification result to storage"""
        results_dir = self.storage_root / "verification_results"
        result_file = results_dir / f"{result.verification_id}.json"
        
        with open(result_file, 'w') as f:
            json.dump(asdict(result), f, indent=2)
        
        self.logger.info(f"💾 Saved verification result: {result.verification_id}")
    
    def get_pending_rounds(self) -> List[str]:
        """Get list of training rounds that haven't been verified yet"""
        training_rounds_dir = self.storage_root / "training_rounds"
        verification_results_dir = self.storage_root / "verification_results"
        
        if not training_rounds_dir.exists():
            return []
        
        # Get all completed training rounds
        completed_rounds = [d.name for d in training_rounds_dir.iterdir() if d.is_dir()]
        
        # Get already verified rounds
        verified_rounds = set()
        if verification_results_dir.exists():
            for result_file in verification_results_dir.glob("*.json"):
                try:
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        if result.get('verification_status', False):
                            verified_rounds.add(result['round_id'])
                except:
                    continue
        
        # Return unverified rounds
        pending = [r for r in completed_rounds if r not in verified_rounds]
        return sorted(pending)

# Main execution functions
def run_training_session(num_rounds: int = 5):
    """Run a complete FL training session"""
    pipeline = ZKFLTrainingPipeline()
    
    print(f"🚀 Starting FL Training Session: {num_rounds} rounds")
    print("=" * 60)
    
    for round_num in range(1, num_rounds + 1):
        print(f"\n📍 Round {round_num}/{num_rounds}")
        training_results, proofs = pipeline.run_training_round(round_num)
        
        print(f"  ✅ Training: {len(training_results)} hospitals")
        print(f"  ✅ Proofs: {len(proofs)} generated")
        print(f"  💾 Saved to: zkfl_storage/")
        
        time.sleep(1)  # Brief pause between rounds
    
    print(f"\n🎉 Training Session Complete!")
    print(f"📁 All data saved in: ./zkfl_storage/")

def run_verification_session():
    """Run verification for all pending training rounds"""
    pipeline = ZKFLVerificationPipeline()
    
    pending_rounds = pipeline.get_pending_rounds()
    if not pending_rounds:
        print("✅ No pending rounds to verify")
        return
    
    print(f"🔍 Starting Verification Session: {len(pending_rounds)} rounds")
    print("=" * 60)
    
    for round_id in pending_rounds:
        print(f"\n🔍 Verifying: {round_id}")
        result = pipeline.verify_round(round_id)
        
        status = "✅ SUCCESS" if result.verification_status else "❌ FAILED"
        print(f"  {status}")
        print(f"  🌟 Aggregation: {result.protogalaxy_aggregation_time:.3f}s")
        print(f"  ✅ Verification: {result.verification_time:.3f}s")
        print(f"  💾 Saved: {result.verification_id}")
        
        time.sleep(0.5)  # Brief pause between verifications
    
    print(f"\n🎉 Verification Session Complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ZK-FL Training and Verification Pipeline")
    parser.add_argument("--mode", choices=['train', 'verify', 'both'], default='both',
                        help="Run training, verification, or both")
    parser.add_argument("--rounds", type=int, default=3,
                        help="Number of training rounds (for training mode)")
    
    args = parser.parse_args()
    
    if args.mode in ['train', 'both']:
        run_training_session(args.rounds)
    
    if args.mode in ['verify', 'both']:
        print("\n" + "="*60)
        run_verification_session()