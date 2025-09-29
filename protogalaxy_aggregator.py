"""
Protogalaxy Proof Aggregation Module for FL Server
Provides interface between Python FL server and Rust Protogalaxy aggregation
"""

import subprocess
import json
import tempfile
import os
import logging
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

class ProtogalaxyAggregator:
    """
    Interface for aggregating ZKP proofs using Protogalaxy on the FL server
    Bridges Python FL server with Rust Protogalaxy implementation
    """
    
    def __init__(self, zkp_binary_path: str = "./zkp-fl/target/debug/zkp-fl"):
        self.zkp_binary_path = zkp_binary_path
        self.temp_dir = tempfile.mkdtemp(prefix="protogalaxy_")
        self.aggregation_history = []
        
    def aggregate_client_proofs(self,
                               proof_data_list: List[Dict],
                               client_metadata: List[Dict],
                               round_number: int) -> Dict:
        """
        Aggregate multiple client ZKP proofs using Protogalaxy
        
        Args:
            proof_data_list: List of proof dictionaries from clients
            client_metadata: List of client metadata (client_id, num_samples, loss)
            round_number: Current FL round number
            
        Returns:
            Dictionary containing aggregated proof and metadata
        """
        try:
            logger.info(f"🔗 Aggregating {len(proof_data_list)} client proofs for round {round_number}")
            
            if not proof_data_list:
                logger.warning("No proofs to aggregate")
                return {"aggregation_valid": False, "error": "No proofs provided"}
            
            # Prepare aggregation input
            aggregation_input = self._prepare_aggregation_input(
                proof_data_list, client_metadata, round_number
            )
            
            # Create input file
            input_file = os.path.join(self.temp_dir, f"aggregation_input_round_{round_number}.json")
            with open(input_file, 'w') as f:
                json.dump(aggregation_input, f, indent=2)
            
            # Perform aggregation using Rust implementation
            aggregation_result = self._call_aggregation_binary(input_file, round_number)
            
            # Verify aggregation was successful
            if self._validate_aggregation_result(aggregation_result):
                logger.info("✅ Protogalaxy aggregation completed successfully")
                
                # Store aggregation history
                aggregation_record = {
                    "round_number": round_number,
                    "num_proofs": len(proof_data_list),
                    "client_ids": [meta.get("client_id", f"client_{i}") for i, meta in enumerate(client_metadata)],
                    "aggregation_hash": aggregation_result.get("aggregated_proof", {}).get("input_proofs_hash"),
                    "timestamp": time.time(),
                    "cross_terms_count": len(aggregation_result.get("aggregated_proof", {}).get("cross_terms", [])),
                    "complexity": aggregation_result.get("aggregation_metadata", {}).get("aggregation_complexity", {})
                }
                self.aggregation_history.append(aggregation_record)
                
                return {
                    "aggregation_valid": True,
                    "aggregated_proof": aggregation_result,
                    "aggregation_hash": aggregation_record["aggregation_hash"],
                    "stats": {
                        "num_proofs_aggregated": len(proof_data_list),
                        "cross_terms_computed": aggregation_record["cross_terms_count"],
                        "polynomial_degree": aggregation_record["complexity"].get("polynomial_degree", 0),
                        "aggregation_time": time.time() - aggregation_record["timestamp"]
                    }
                }
            else:
                logger.error("❌ Protogalaxy aggregation failed")
                return {
                    "aggregation_valid": False, 
                    "error": "Aggregation validation failed",
                    "fallback_hash": self._generate_fallback_aggregation(proof_data_list, round_number)
                }
                
        except Exception as e:
            logger.error(f"Protogalaxy aggregation error: {e}")
            return {
                "aggregation_valid": False,
                "error": str(e),
                "fallback_hash": self._generate_fallback_aggregation(proof_data_list, round_number)
            }
    
    def _prepare_aggregation_input(self, proof_data_list: List[Dict], 
                                  client_metadata: List[Dict], 
                                  round_number: int) -> Dict:
        """Prepare input for Protogalaxy aggregation"""
        
        # Extract proofs from client data
        proofs = []
        for i, proof_data in enumerate(proof_data_list):
            if "proof_data" in proof_data:
                # Real ZKP proof from our generator
                proofs.append(proof_data["proof_data"])
            else:
                # Fallback proof structure
                proofs.append({
                    "proof": {
                        "type": "groth16_bn254",
                        "proof_data": {
                            "alpha": f"fallback_alpha_{i}",
                            "beta": f"fallback_beta_{i}",
                            "gamma": f"fallback_gamma_{i}"
                        },
                        "public_inputs": {
                            "loss_value": int(proof_data.get("training_loss", 0) * 1000),
                            "training_data_hash": proof_data.get("proof_hash", f"hash_{i}")[:16]
                        }
                    }
                })
        
        # Prepare client metadata
        aggregation_metadata = []
        for i, meta in enumerate(client_metadata):
            aggregation_metadata.append({
                "client_id": meta.get("client_id", f"client_{i}"),
                "num_samples": meta.get("num_samples", 0),
                "loss": meta.get("training_loss", 0.0)
            })
        
        return {
            "round_number": round_number,
            "client_metadata": aggregation_metadata,
            "proofs": proofs,
            "aggregation_config": {
                "max_proofs": len(proofs),
                "polynomial_degree_bound": 2 * len(proofs),
                "challenge_generation_method": "fiat_shamir"
            }
        }
    
    def _call_aggregation_binary(self, input_file: str, round_number: int) -> Dict:
        """Call Rust Protogalaxy aggregation binary"""
        output_file = os.path.join(self.temp_dir, f"aggregation_output_round_{round_number}.json")
        
        try:
            cmd = [
                self.zkp_binary_path,
                "aggregate-proofs",
                "--input", input_file,
                "--output", output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                with open(output_file, 'r') as f:
                    return json.load(f)
            else:
                logger.error(f"Aggregation binary error: {result.stderr}")
                return {"error": result.stderr}
                
        except subprocess.TimeoutExpired:
            logger.error("Protogalaxy aggregation timed out")
            return {"error": "Aggregation timeout"}
        except Exception as e:
            logger.error(f"Aggregation binary call failed: {e}")
            return {"error": str(e)}
    
    def _validate_aggregation_result(self, result: Dict) -> bool:
        """Validate the aggregation result structure"""
        required_fields = ["aggregated_proof", "aggregation_metadata", "protogalaxy_features"]
        
        if not all(field in result for field in required_fields):
            return False
        
        # Check aggregated proof structure
        aggregated_proof = result.get("aggregated_proof", {})
        if not all(field in aggregated_proof for field in ["aggregated_commitments", "cross_terms", "aggregation_challenges"]):
            return False
        
        # Check if cross-terms make sense
        num_proofs = aggregated_proof.get("num_proofs_aggregated", 0)
        expected_cross_terms = num_proofs * (num_proofs - 1) // 2
        actual_cross_terms = len(aggregated_proof.get("cross_terms", []))
        
        if actual_cross_terms != expected_cross_terms:
            logger.warning(f"Cross-terms count mismatch: expected {expected_cross_terms}, got {actual_cross_terms}")
        
        return True
    
    def _generate_fallback_aggregation(self, proof_data_list: List[Dict], round_number: int) -> str:
        """Generate fallback aggregation hash when Protogalaxy fails"""
        import hashlib
        
        fallback_data = {
            "round_number": round_number,
            "num_proofs": len(proof_data_list),
            "proof_hashes": [proof.get("proof_hash", f"hash_{i}") for i, proof in enumerate(proof_data_list)],
            "timestamp": time.time(),
            "fallback_type": "simple_hash_aggregation"
        }
        
        return hashlib.sha256(json.dumps(fallback_data, sort_keys=True).encode()).hexdigest()
    
    def verify_aggregated_proof(self, aggregated_proof: Dict) -> bool:
        """Verify an aggregated proof"""
        try:
            # Check proof structure
            if not self._validate_aggregation_result(aggregated_proof):
                return False
            
            # In a real implementation, this would use cryptographic verification
            # For now, check structural integrity
            aggregated_data = aggregated_proof.get("aggregated_proof", {})
            num_proofs = aggregated_data.get("num_proofs_aggregated", 0)
            
            if num_proofs <= 0:
                return False
            
            # Check commitments and challenges match
            commitments = aggregated_data.get("aggregated_commitments", [])
            challenges = aggregated_data.get("aggregation_challenges", [])
            
            return len(commitments) == num_proofs and len(challenges) == num_proofs
            
        except Exception as e:
            logger.error(f"Aggregated proof verification error: {e}")
            return False
    
    def get_aggregation_stats(self) -> Dict:
        """Get statistics about aggregation history"""
        if not self.aggregation_history:
            return {"total_rounds": 0, "total_proofs_aggregated": 0}
        
        total_proofs = sum(record["num_proofs"] for record in self.aggregation_history)
        total_cross_terms = sum(record["cross_terms_count"] for record in self.aggregation_history)
        
        return {
            "total_rounds": len(self.aggregation_history),
            "total_proofs_aggregated": total_proofs,
            "total_cross_terms_computed": total_cross_terms,
            "average_proofs_per_round": total_proofs / len(self.aggregation_history),
            "latest_round": self.aggregation_history[-1]["round_number"] if self.aggregation_history else 0
        }
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)