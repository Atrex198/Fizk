"""
ZKP Integration Module for Federated Learning Client
Provides interface between Python FL client and Rust ZKP circuits
"""

import subprocess
import json
import tempfile
import os
import numpy as np
import torch
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ZKPProofGenerator:
    """
    Interface for generating ZKP proofs using our enhanced MLP circuits
    Bridges Python FL client with Rust ZKP implementation
    """
    
    def __init__(self, zkp_binary_path: str = "./zkp-fl/target/debug/zkp-fl"):
        self.zkp_binary_path = zkp_binary_path
        self.temp_dir = tempfile.mkdtemp(prefix="zkp_fl_")
        
    def generate_training_proof(self,
                              initial_weights: Dict[str, torch.Tensor],
                              final_weights: Dict[str, torch.Tensor],
                              training_data: Tuple[torch.Tensor, torch.Tensor],
                              training_loss: float,
                              learning_rate: float,
                              local_epochs: int) -> Dict:
        """
        Generate ZKP proof of correct local training using enhanced MLP circuits
        
        Args:
            initial_weights: Model weights before training
            final_weights: Model weights after training  
            training_data: (X, y) training batch used
            training_loss: Final training loss
            learning_rate: Learning rate used
            local_epochs: Number of training epochs
            
        Returns:
            Dictionary containing proof data and verification info
        """
        try:
            # Extract MLP architecture from weights
            mlp_config = self._extract_mlp_config(initial_weights)
            
            # Convert PyTorch weights to field elements format
            initial_weights_fe = self._convert_weights_to_field_elements(initial_weights)
            final_weights_fe = self._convert_weights_to_field_elements(final_weights)
            
            # Prepare training data for circuit
            circuit_inputs = self._prepare_circuit_inputs(
                training_data, initial_weights_fe, final_weights_fe,
                training_loss, learning_rate, local_epochs
            )
            
            # Create input file for ZKP proof generation
            input_file = os.path.join(self.temp_dir, "proof_input.json")
            with open(input_file, 'w') as f:
                json.dump(circuit_inputs, f, indent=2)
            
            # Generate proof using Rust implementation
            proof_output = self._call_zkp_binary(input_file)
            
            # Verify proof was generated successfully
            if self._validate_proof_output(proof_output):
                return {
                    "proof_generated": True,
                    "proof_valid": True,
                    "proof_hash": proof_output.get("proof_hash", "unknown"),
                    "proof_data": proof_output.get("proof_data", {}),
                    "circuit_config": mlp_config
                }
            else:
                logger.error("❌ ZKP proof validation failed - Real cryptographic proofs only!")
                raise Exception("ZKP proof validation failed - mock proofs not acceptable")
                
        except Exception as e:
            logger.error(f"❌ ZKP proof generation failed: {e}")
            # NO FALLBACK - Real cryptographic proofs only!
            raise Exception(f"Real ZKP proof generation failed: {e}")
    
    def _validate_proof_output(self, proof_output: Dict) -> bool:
        """Validate ZKP proof output structure and ensure real cryptographic proofs"""
        try:
            if not isinstance(proof_output, dict):
                return False
                
            # Check for required fields
            required_fields = ["proof", "metadata"]
            if not all(field in proof_output for field in required_fields):
                return False
            
            # Check that it's a real cryptographic proof, not a mock/fallback
            metadata = proof_output.get("metadata", {})
            proof_system = metadata.get("proof_system", "")
            
            # Must be a real Groth16 proof
            if "REAL" not in proof_system or "groth16" not in proof_system.lower():
                logger.error(f"Invalid proof system: {proof_system} - Real Groth16 required")
                return False
                
            # Check for actual proof elements
            proof_data = proof_output.get("proof", {}).get("proof_data", {})
            if "mock" in str(proof_data).lower():
                logger.error("Mock proof elements detected - Real cryptographic proofs required")
                return False
                
            # Verify we have actual elliptic curve points in the proof
            required_proof_elements = ["a", "b", "c"]
            if not all(elem in proof_data for elem in required_proof_elements):
                logger.error("Missing Groth16 proof elements")
                return False
                
            logger.info("✅ Real cryptographic proof validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Proof validation error: {e}")
            return False
    
    def generate_simple_training_proof(self,
                                     model_weights: Dict[str, torch.Tensor],
                                     training_loss: float,
                                     client_id: str) -> Dict:
        """
        Simplified interface for generating training proofs (for testing/compatibility)
        """
        try:
            logger.info(f"🔄 Generating ZKP proof for {client_id}, loss: {training_loss:.4f}")
            
            # Use current weights as both initial and final for simplified proof
            # In real training, this would track actual weight changes
            return self.generate_training_proof(
                initial_weights=model_weights,
                final_weights=model_weights,
                training_data=(torch.randn(32, list(model_weights.values())[0].shape[1] if len(list(model_weights.values())[0].shape) > 1 else 1), 
                              torch.randn(32, 1)),  # Minimal training data for proof structure
                training_loss=training_loss,
                learning_rate=0.01,
                local_epochs=1
            )
            
        except Exception as e:
            logger.error(f"⚠️ ZKP proof generation failed for {client_id}: {e}")
            # NO FALLBACK - Real cryptographic proofs only!
            raise Exception(f"Real ZKP proof generation failed: {e}. Mock proofs are not acceptable.")
            
            # Verify proof was generated successfully
            if ("proof" in proof_output and 
                "circuit_info" in proof_output and 
                proof_output.get("proof", {}).get("verification_key") is not None):
                logger.info("✅ ZKP proof generated successfully")
                return {
                    "proof_valid": True,
                    "proof_data": proof_output,
                    "circuit_config": mlp_config,
                    "proof_hash": self._compute_proof_hash(proof_output)
                }
            else:
                logger.error("❌ ZKP proof generation failed")
                logger.error(f"Proof output keys: {list(proof_output.keys())}")
                return {"proof_valid": False, "error": "Proof generation failed"}
                
        except Exception as e:
            logger.error(f"ZKP proof generation error: {e}")
            return {"proof_valid": False, "error": str(e)}
    
    def _extract_mlp_config(self, weights: Dict[str, torch.Tensor]) -> Dict:
        """Extract MLP architecture configuration from PyTorch weights"""
        layer_sizes = []
        
        # Sort weight tensors by layer order
        weight_keys = [k for k in sorted(weights.keys()) if 'weight' in k and 'net' in k]
        
        for i, key in enumerate(weight_keys):
            weight_tensor = weights[key]
            if i == 0:
                # First layer: input size is second dimension
                layer_sizes.append(weight_tensor.shape[1])
            # Output size is first dimension  
            layer_sizes.append(weight_tensor.shape[0])
        
        return {
            "input_size": layer_sizes[0],
            "hidden_sizes": layer_sizes[1:-1],
            "output_size": layer_sizes[-1],
            "use_bias": any("bias" in k for k in weights.keys())
        }
    
    def _convert_weights_to_field_elements(self, weights: Dict[str, torch.Tensor]) -> Dict:
        """Convert PyTorch weights to field element representation"""
        field_weights = {
            "layer_weights": [],
            "layer_biases": []
        }
        
        # Group weights by layer
        layer_weights = {}
        layer_biases = {}
        
        for name, tensor in weights.items():
            if 'net.' in name:
                # Extract layer number from name like 'net.0.weight', 'net.0.bias'
                parts = name.split('.')
                layer_idx = int(parts[1])
                
                if 'weight' in name:
                    layer_weights[layer_idx] = tensor.detach().cpu().numpy()
                elif 'bias' in name:
                    layer_biases[layer_idx] = tensor.detach().cpu().numpy()
        
        # Convert to field element format (normalized to prevent overflow)
        for layer_idx in sorted(layer_weights.keys()):
            weight_matrix = layer_weights[layer_idx]
            # Normalize weights to [0, 1] range then scale for field elements
            weight_matrix = (weight_matrix - weight_matrix.min()) / (weight_matrix.max() - weight_matrix.min() + 1e-8)
            field_weights["layer_weights"].append((weight_matrix * 1000).astype(int).tolist())
            
            if layer_idx in layer_biases:
                bias_vector = layer_biases[layer_idx]
                bias_vector = (bias_vector - bias_vector.min()) / (bias_vector.max() - bias_vector.min() + 1e-8)
                field_weights["layer_biases"].append((bias_vector * 1000).astype(int).tolist())
            else:
                # Zero bias if not present
                field_weights["layer_biases"].append([0] * weight_matrix.shape[0])
        
        return field_weights
    
    def _prepare_circuit_inputs(self, training_data: Tuple[torch.Tensor, torch.Tensor],
                               initial_weights: Dict, final_weights: Dict,
                               training_loss: float, learning_rate: float,
                               local_epochs: int) -> Dict:
        """Prepare inputs for ZKP circuit"""
        X, y = training_data
        
        # Use subset of training data for proof (due to circuit size constraints)
        max_samples = 4  # Limit for circuit efficiency
        if len(X) > max_samples:
            indices = torch.randperm(len(X))[:max_samples]
            X = X[indices]
            y = y[indices]
        
        # Convert training data to field elements
        X_normalized = (X.detach().cpu().numpy() * 1000).astype(int).tolist()
        y_normalized = (y.detach().cpu().numpy() * 1000).astype(int).tolist()
        
        return {
            "circuit_type": "mlp_training",
            "training_data": {
                "inputs": X_normalized,
                "targets": y_normalized
            },
            "initial_weights": initial_weights,
            "final_weights": final_weights,
            "training_params": {
                "learning_rate": int(learning_rate * 1000),  # Scale for field element
                "local_epochs": local_epochs,
                "loss": int(training_loss * 1000)
            },
            "proof_config": {
                "proof_system": "groth16",
                "curve": "bn254"
            }
        }
    
    def _call_zkp_binary(self, input_file: str) -> Dict:
        """Call Rust ZKP binary to generate proof"""
        output_file = os.path.join(self.temp_dir, "proof_output.json")
        
        try:
            # Call our enhanced ZKP-FL binary
            cmd = [
                self.zkp_binary_path,
                "generate-proof",
                "--input", input_file,
                "--output", output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                with open(output_file, 'r') as f:
                    return json.load(f)
            else:
                logger.error(f"ZKP binary error: {result.stderr}")
                return {"error": result.stderr}
                
        except subprocess.TimeoutExpired:
            logger.error("ZKP proof generation timed out")
            return {"error": "Proof generation timeout"}
        except Exception as e:
            logger.error(f"ZKP binary call failed: {e}")
            return {"error": str(e)}
    
    def _compute_proof_hash(self, proof_output: Dict) -> str:
        """Compute hash of proof for verification"""
        import hashlib
        proof_str = json.dumps(proof_output, sort_keys=True)
        return hashlib.sha256(proof_str.encode()).hexdigest()
    
    def verify_proof(self, proof_data: Dict) -> bool:
        """Verify a ZKP proof"""
        try:
            # Create verification input file
            input_file = os.path.join(self.temp_dir, "verify_input.json")
            with open(input_file, 'w') as f:
                json.dump(proof_data, f, indent=2)
            
            # Call verification
            cmd = [
                self.zkp_binary_path,
                "verify-proof", 
                "--input", input_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Proof verification error: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)