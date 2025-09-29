"""
Federated Learning Client for FL+MLP with ZKP verification
Performs local training and generates ZKP proofs of computation correctness
"""

import asyncio
import json
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import websockets
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import time
import hashlib

# Import our MLP model and data loading
from train_mlp import MLP, load_and_prepare

# Import ZKP proof generation
from zkp_proof_generator import ZKPProofGenerator

# Import metrics collection
from metrics_collector import MetricsCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FederatedClient:
    """
    Federated Learning Client that performs local training and ZKP proof generation
    """
    
    def __init__(self, 
                 client_id: str,
                 server_host: str = "localhost",
                 server_port: int = 8765,
                 local_epochs: int = 5,
                 batch_size: int = 32,
                 learning_rate: float = 0.001):
        
        self.client_id = client_id
        self.server_host = server_host
        self.server_port = server_port
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        
        # Model and training state
        self.model = None
        self.optimizer = None
        self.criterion = nn.BCEWithLogitsLoss()
        self.scaler = StandardScaler()
        
        # Local data
        self.X_train = None
        self.y_train = None
        self.X_val = None
        self.y_val = None
        
        # Training history
        self.training_history = []
        self.current_round = 0
        
        # ZKP state
        self.local_proofs = []
        self.zkp_generator = ZKPProofGenerator()
        
        logger.info(f"FL Client {client_id} initialized with ZKP proof generation")
    
    def load_local_data(self, data_fraction: float = 0.1, random_seed: Optional[int] = None):
        """
        Load a fraction of the heart disease dataset for local training
        Simulates data being distributed across clients
        """
        try:
            # Load full dataset
            X_full, y_full = load_and_prepare('heart_2020_cleaned.csv')
            
            # Take a random fraction for this client
            if random_seed is not None:
                np.random.seed(random_seed + hash(self.client_id) % 1000)
            
            n_samples = int(len(X_full) * data_fraction)
            indices = np.random.choice(len(X_full), n_samples, replace=False)
            
            X_client = X_full.iloc[indices]
            y_client = y_full.iloc[indices]
            
            # Split into train/validation
            X_train, X_val, y_train, y_val = train_test_split(
                X_client, y_client, test_size=0.2, random_state=42, stratify=y_client
            )
            
            # Fit scaler on local training data
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            
            # Convert to tensors
            self.X_train = torch.FloatTensor(X_train_scaled)
            self.y_train = torch.FloatTensor(y_train.values).unsqueeze(1)
            self.X_val = torch.FloatTensor(X_val_scaled)
            self.y_val = torch.FloatTensor(y_val.values).unsqueeze(1)
            
            logger.info(f"Client {self.client_id} loaded {len(self.X_train)} training samples, {len(self.X_val)} validation samples")
            
        except Exception as e:
            logger.error(f"Error loading local data: {e}")
            raise
    
    def initialize_model(self, model_config: dict):
        """Initialize the local model with given configuration"""
        self.model = MLP(
            in_dim=model_config['input_size'],
            hidden=tuple(model_config['hidden_sizes']),
            dropout=model_config['dropout_rate']
        )
        
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Move to GPU if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.X_train = self.X_train.to(self.device)
        self.y_train = self.y_train.to(self.device)
        self.X_val = self.X_val.to(self.device)
        self.y_val = self.y_val.to(self.device)
        
        logger.info(f"Model initialized on {self.device}")
    
    def set_model_weights(self, weights: Dict[str, List]):
        """Update local model with weights from server"""
        if self.model is None:
            logger.error("Model not initialized")
            return
        
        with torch.no_grad():
            for name, param in self.model.named_parameters():
                if name in weights:
                    param.copy_(torch.tensor(weights[name], dtype=torch.float32).to(self.device))
        
        logger.debug(f"Updated model weights from server")
    
    def get_model_weights(self) -> Dict[str, torch.Tensor]:
        """Get current local model weights"""
        return {name: param.cpu().clone() for name, param in self.model.named_parameters()}
    
    def generate_training_proof(self, 
                               initial_weights: Dict[str, torch.Tensor],
                               final_weights: Dict[str, torch.Tensor],
                               training_data: Tuple[torch.Tensor, torch.Tensor],
                               training_loss: float) -> str:
        """
        Generate ZKP proof of correct local training using enhanced MLP circuits
        """
        try:
            logger.info("🔄 Generating ZKP proof of training correctness...")
            
            # Generate ZKP proof using our enhanced circuits
            proof_result = self.zkp_generator.generate_training_proof(
                initial_weights=initial_weights,
                final_weights=final_weights,
                training_data=training_data,
                training_loss=training_loss,
                learning_rate=self.learning_rate,
                local_epochs=self.local_epochs
            )
            
            if proof_result.get("proof_valid", False):
                proof_hash = proof_result["proof_hash"]
                
                # Store proof with metadata
                proof_data = {
                    'client_id': self.client_id,
                    'round': self.current_round,
                    'proof_hash': proof_hash,
                    'proof_data': proof_result["proof_data"],
                    'circuit_config': proof_result["circuit_config"],
                    'training_loss': training_loss,
                    'num_samples': len(self.X_train),
                    'local_epochs': self.local_epochs,
                    'timestamp': time.time()
                }
                
                self.local_proofs.append(proof_data)
                
                logger.info(f"✅ ZKP proof generated successfully: {proof_hash[:8]}...")
                return proof_hash
            else:
                error_msg = proof_result.get("error", "Unknown error")
                logger.error(f"❌ ZKP proof generation failed: {error_msg}")
                
                # Fallback to hash-based proof for now
                fallback_proof = self._generate_fallback_proof(initial_weights, final_weights, training_loss)
                logger.warning(f"⚠️  Using fallback proof: {fallback_proof[:8]}...")
                return fallback_proof
                
        except Exception as e:
            logger.error(f"ZKP proof generation error: {e}")
            # Fallback to hash-based proof
            fallback_proof = self._generate_fallback_proof(initial_weights, final_weights, training_loss)
            logger.warning(f"⚠️  Using fallback proof due to error: {fallback_proof[:8]}...")
            return fallback_proof
    
    def _generate_fallback_proof(self, initial_weights: Dict[str, torch.Tensor],
                                final_weights: Dict[str, torch.Tensor],
                                training_loss: float) -> str:
        """Generate fallback hash-based proof when ZKP generation fails"""
        proof_data = {
            'client_id': self.client_id,
            'round': self.current_round,
            'initial_weights_hash': self._hash_weights(initial_weights),
            'final_weights_hash': self._hash_weights(final_weights),
            'training_loss': training_loss,
            'num_samples': len(self.X_train),
            'local_epochs': self.local_epochs,
            'timestamp': time.time(),
            'proof_type': 'fallback_hash'
        }
        
        proof_hash = hashlib.sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()
        
        self.local_proofs.append({
            'proof_hash': proof_hash,
            'proof_data': proof_data,
            'proof_type': 'fallback'
        })
        
        return proof_hash
    
    def _hash_weights(self, weights: Dict[str, torch.Tensor]) -> str:
        """Create a hash of model weights"""
        weight_str = ""
        for name in sorted(weights.keys()):
            weight_str += f"{name}:{weights[name].detach().cpu().numpy().tobytes().hex()}"
        return hashlib.sha256(weight_str.encode()).hexdigest()[:16]
    
    def local_training(self) -> Tuple[float, int]:
        """
        Perform local training for specified number of epochs
        Returns (loss, num_samples)
        """
        if self.model is None or self.X_train is None:
            logger.error("Model or data not initialized")
            return 0.0, 0
        
        # Store initial weights for proof generation
        initial_weights = self.get_model_weights()
        
        self.model.train()
        epoch_losses = []
        
        logger.info(f"Starting local training for {self.local_epochs} epochs")
        
        for epoch in range(self.local_epochs):
            # Create data batches
            n_samples = len(self.X_train)
            indices = torch.randperm(n_samples)
            batch_losses = []
            
            for i in range(0, n_samples, self.batch_size):
                batch_indices = indices[i:i + self.batch_size]
                X_batch = self.X_train[batch_indices]
                y_batch = self.y_train[batch_indices]
                
                # Forward pass
                self.optimizer.zero_grad()
                outputs = self.model(X_batch)
                loss = self.criterion(outputs, y_batch)
                
                # Backward pass
                loss.backward()
                self.optimizer.step()
                
                batch_losses.append(loss.item())
            
            epoch_loss = np.mean(batch_losses)
            epoch_losses.append(epoch_loss)
            
            if epoch % 2 == 0:
                logger.debug(f"Epoch {epoch + 1}/{self.local_epochs}, Loss: {epoch_loss:.4f}")
        
        final_loss = np.mean(epoch_losses)
        final_weights = self.get_model_weights()
        
        # Prepare sample training data for ZKP proof (use small subset for circuit efficiency)
        sample_size = min(4, len(self.X_train))  # Limit for circuit constraints
        sample_indices = torch.randperm(len(self.X_train))[:sample_size]
        sample_X = self.X_train[sample_indices]
        sample_y = self.y_train[sample_indices]
        training_data = (sample_X, sample_y)
        
        # Generate ZKP proof of training correctness
        proof_hash = self.generate_training_proof(initial_weights, final_weights, training_data, final_loss)
        
        logger.info(f"Local training complete. Final loss: {final_loss:.4f}, Proof: {proof_hash[:8]}...")
        
        return final_loss, len(self.X_train)
    
    def evaluate_model(self) -> Dict[str, float]:
        """Evaluate current model on local validation data"""
        if self.model is None or self.X_val is None:
            return {'val_loss': 0.0, 'val_accuracy': 0.0}
        
        self.model.eval()
        with torch.no_grad():
            val_outputs = self.model(self.X_val)
            val_loss = self.criterion(val_outputs, self.y_val).item()
            
            # Calculate accuracy
            predictions = (torch.sigmoid(val_outputs) > 0.5).float()
            val_accuracy = (predictions == self.y_val).float().mean().item()
        
        return {'val_loss': val_loss, 'val_accuracy': val_accuracy}
    
    async def connect_to_server(self):
        """Connect to the federated learning server"""
        uri = f"ws://{self.server_host}:{self.server_port}"
        logger.info(f"Connecting to FL server at {uri}")
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to FL server")
                
                # Listen for server messages
                async for message in websocket:
                    await self.process_server_message(websocket, json.loads(message))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection to server closed")
        except Exception as e:
            logger.error(f"Connection error: {e}")
    
    async def process_server_message(self, websocket, message: dict):
        """Process incoming messages from server"""
        msg_type = message.get('type')
        
        if msg_type == 'model_weights':
            # Received updated global model weights
            self.current_round = message['round']
            
            # Initialize model if this is the first message
            if self.model is None:
                model_config = {
                    'input_size': 18,  # Heart disease dataset
                    'hidden_sizes': [128, 64, 32],
                    'dropout_rate': 0.3
                }
                self.initialize_model(model_config)
            
            # Update model weights
            self.set_model_weights(message['weights'])
            
            # Perform local training
            training_loss, num_samples = self.local_training()
            
            # Evaluate on local validation set
            val_metrics = self.evaluate_model()
            
            # Send update back to server
            response = {
                'type': 'model_update',
                'client_id': self.client_id,
                'round': self.current_round,
                'weights': self._serialize_weights(self.get_model_weights()),
                'loss': training_loss,
                'num_samples': num_samples,
                'val_metrics': val_metrics,
                'proof_hash': self.local_proofs[-1]['proof_hash'] if self.local_proofs else None
            }
            
            await websocket.send(json.dumps(response))
            logger.info(f"Sent update to server: loss={training_loss:.4f}, val_acc={val_metrics['val_accuracy']:.4f}")
    
    def _serialize_weights(self, weights: Dict[str, torch.Tensor]) -> Dict[str, List]:
        """Convert tensor weights to serializable format"""
        return {name: tensor.detach().cpu().numpy().tolist() for name, tensor in weights.items()}
    
    async def start_client(self, data_fraction: float = 0.1):
        """Start the federated learning client"""
        # Load local data
        client_seed = hash(self.client_id) % 10000
        self.load_local_data(data_fraction=data_fraction, random_seed=client_seed)
        
        # Connect to server and participate in FL
        await self.connect_to_server()

# Main client execution
async def main():
    """Main client execution"""
    import sys
    
    # Get client ID from command line or use default
    client_id = sys.argv[1] if len(sys.argv) > 1 else "client_default"
    data_fraction = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    
    # Create and start FL client
    client = FederatedClient(
        client_id=client_id,
        server_host="localhost",
        server_port=8765,
        local_epochs=5,
        batch_size=32,
        learning_rate=0.001
    )
    
    try:
        await client.start_client(data_fraction=data_fraction)
    except KeyboardInterrupt:
        logger.info(f"Client {client_id} shutting down...")
        print(f"Generated {len(client.local_proofs)} training proofs")

if __name__ == "__main__":
    asyncio.run(main())