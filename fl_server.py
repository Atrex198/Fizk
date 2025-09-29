"""
Federated Learning Server for FL+MLP with ZKP verification
Coordinates training across multiple clients and handles proof aggregation
"""

import asyncio
import json
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import websockets
import threading
import time

# Import our MLP model
from train_mlp import MLP

# Import Protogalaxy aggregation
from protogalaxy_aggregator import ProtogalaxyAggregator

# Import metrics collection
from metrics_collector import MetricsCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClientUpdate:
    """Structure for client model updates"""
    client_id: str
    model_weights: Dict[str, torch.Tensor]
    loss: float
    num_samples: int
    proof_hash: Optional[str] = None  # ZKP proof hash
    timestamp: float = 0.0

@dataclass
class FLRound:
    """Structure for FL training round"""
    round_num: int
    global_model_weights: Dict[str, torch.Tensor]
    client_updates: List[ClientUpdate]
    aggregated_loss: float
    participation_rate: float
    proof_aggregation_hash: Optional[str] = None

class FederatedServer:
    """
    Federated Learning Server with comprehensive metrics collection
    Coordinates multiple clients and performs ZKP proof aggregation
    """
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 8765,
                 model_config: Dict = None,
                 min_clients: int = 2,
                 max_rounds: int = 10):
        self.host = host
        self.port = port
        self.model_config = model_config or {"input_size": 37, "hidden_sizes": [64, 32]}
        self.min_clients = min_clients
        self.max_rounds = max_rounds
        
        # Initialize global model
        self.global_model = MLP(
            input_size=self.model_config["input_size"],
            hidden_sizes=self.model_config["hidden_sizes"],
            dropout_rate=self.model_config.get("dropout_rate", 0.0)
        )
        
        # Initialize Protogalaxy aggregator
        self.protogalaxy_aggregator = ProtogalaxyAggregator()
        logger.info("🔗 Protogalaxy aggregator initialized")
        
        # Initialize comprehensive metrics collection
        self.metrics_collector = MetricsCollector("fl_server_comprehensive")
        self.metrics_collector.start_monitoring(interval=0.1)  # High frequency monitoring
        logger.info("📊 Comprehensive server metrics collection enabled")
        
        # Server state
        self.connected_clients = {}
        self.current_round = 0
        self.round_results = []
        self.is_training = False
        
        logger.info(f"FL Server initialized with {self.model_config}")
    
    def get_global_weights(self) -> Dict[str, torch.Tensor]:
        """Get current global model weights"""
        return {name: param.clone() for name, param in self.global_model.named_parameters()}
    
    def set_global_weights(self, weights: Dict[str, torch.Tensor]):
        """Update global model with new weights"""
        with torch.no_grad():
            for name, param in self.global_model.named_parameters():
                if name in weights:
                    param.copy_(weights[name])
    
    def federated_averaging(self, client_updates: List[ClientUpdate]) -> Dict[str, torch.Tensor]:
        """
        Perform federated averaging of client updates
        Weighted by number of samples each client trained on
        """
        if not client_updates:
            return self.get_global_weights()
        
        total_samples = sum(update.num_samples for update in client_updates)
        if total_samples == 0:
            logger.warning("No samples in client updates, returning current weights")
            return self.get_global_weights()
        
        # Initialize aggregated weights
        aggregated_weights = {}
        for name, param in self.global_model.named_parameters():
            aggregated_weights[name] = torch.zeros_like(param)
        
        # Weighted averaging
        for update in client_updates:
            weight = update.num_samples / total_samples
            for name, param_tensor in update.model_weights.items():
                if name in aggregated_weights:
                    aggregated_weights[name] += weight * param_tensor
        
        return aggregated_weights
    
    async def handle_client_connection(self, websocket, path):
        """Handle individual client connections"""
        client_id = f"client_{len(self.connected_clients)}"
        self.connected_clients[client_id] = {
            'websocket': websocket,
            'status': 'connected',
            'last_seen': time.time()
        }
        
        logger.info(f"Client {client_id} connected from {websocket.remote_address}")
        
        try:
            # Send initial model weights
            initial_message = {
                'type': 'model_weights',
                'round': self.current_round,
                'weights': self._serialize_weights(self.get_global_weights()),
                'client_id': client_id
            }
            await websocket.send(json.dumps(initial_message))
            
            # Listen for client messages
            async for message in websocket:
                await self.process_client_message(client_id, json.loads(message))
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
    
    async def process_client_message(self, client_id: str, message: dict):
        """Process incoming messages from clients"""
        msg_type = message.get('type')
        
        if msg_type == 'model_update':
            # Receive model update from client
            update = ClientUpdate(
                client_id=client_id,
                model_weights=self._deserialize_weights(message['weights']),
                loss=message['loss'],
                num_samples=message['num_samples'],
                proof_hash=message.get('proof_hash'),
                timestamp=time.time()
            )
            
            await self.receive_client_update(update)
            
        elif msg_type == 'training_complete':
            # Client finished local training
            self.connected_clients[client_id]['status'] = 'ready'
            logger.info(f"Client {client_id} completed training")
            
        elif msg_type == 'heartbeat':
            # Keep-alive message
            self.connected_clients[client_id]['last_seen'] = time.time()
    
    async def receive_client_update(self, update: ClientUpdate):
        """Handle received client model update"""
        logger.info(f"Received update from {update.client_id}: loss={update.loss:.4f}, samples={update.num_samples}")
        
        # Store update for current round
        if not hasattr(self, 'pending_updates'):
            self.pending_updates = []
        
        self.pending_updates.append(update)
        
        # Check if we have enough updates to proceed
        if len(self.pending_updates) >= self.min_clients:
            await self.aggregate_and_update()
    
    async def aggregate_and_update(self):
        """Aggregate client updates and update global model"""
        if not hasattr(self, 'pending_updates') or not self.pending_updates:
            return
        
        logger.info(f"Aggregating {len(self.pending_updates)} client updates for round {self.current_round}")
        
        # Perform federated averaging
        new_weights = self.federated_averaging(self.pending_updates)
        
        # Update global model
        self.set_global_weights(new_weights)
        
        # Calculate aggregated metrics
        total_samples = sum(update.num_samples for update in self.pending_updates)
        weighted_loss = sum(update.loss * update.num_samples for update in self.pending_updates) / total_samples
        
        # Create FL round record
        fl_round = FLRound(
            round_num=self.current_round,
            global_model_weights=new_weights,
            client_updates=self.pending_updates.copy(),
            aggregated_loss=weighted_loss,
            participation_rate=len(self.pending_updates) / len(self.connected_clients) if self.connected_clients else 0,
            proof_aggregation_hash=await self.aggregate_proofs([u.proof_hash for u in self.pending_updates if u.proof_hash])
        )
        
        self.fl_history.append(fl_round)
        
        # Broadcast updated model to all clients
        await self.broadcast_model_update()
        
        # Prepare for next round
        self.current_round += 1
        self.pending_updates = []
        
        logger.info(f"Round {fl_round.round_num} complete: loss={weighted_loss:.4f}, participation={fl_round.participation_rate:.2%}")
    
    async def aggregate_proofs(self, proof_hashes: List[str]) -> Optional[str]:
        """
        Aggregate ZKP proofs using Protogalaxy aggregation
        Now uses real Protogalaxy implementation for client proof aggregation
        """
        if not proof_hashes:
            logger.info("No proofs to aggregate")
            return None
        
        logger.info(f"🔗 Starting Protogalaxy aggregation for {len(proof_hashes)} proofs")
        
        try:
            # Prepare proof data for aggregation
            proof_data_list = []
            client_metadata = []
            
            # Extract proof data from pending updates
            for i, update in enumerate(self.pending_updates):
                if update.proof_hash:
                    # Check if we have stored proof data for this hash
                    stored_proof = self.round_proofs.get(update.proof_hash)
                    
                    if stored_proof:
                        proof_data_list.append(stored_proof)
                    else:
                        # Create fallback proof structure
                        proof_data_list.append({
                            "training_loss": update.loss,
                            "proof_hash": update.proof_hash,
                            "client_weights_hash": self._hash_weights(update.model_weights)
                        })
                    
                    # Prepare client metadata
                    client_metadata.append({
                        "client_id": update.client_id,
                        "num_samples": update.num_samples,
                        "training_loss": update.loss
                    })
            
            # Use Protogalaxy aggregator
            aggregation_result = self.protogalaxy_aggregator.aggregate_client_proofs(
                proof_data_list=proof_data_list,
                client_metadata=client_metadata,
                round_number=self.current_round
            )
            
            if aggregation_result.get("aggregation_valid", False):
                logger.info("✅ Protogalaxy aggregation successful")
                
                # Store aggregation result for this round
                self.round_proofs[f"aggregated_round_{self.current_round}"] = aggregation_result
                
                return aggregation_result.get("aggregation_hash", f"protogalaxy_round_{self.current_round}")
            else:
                logger.warning("⚠️ Protogalaxy aggregation failed, using fallback")
                return aggregation_result.get("fallback_hash", f"fallback_round_{self.current_round}")
                
        except Exception as e:
            logger.error(f"Error in Protogalaxy aggregation: {e}")
            # Fallback to simple hash aggregation
            combined = "".join(sorted(proof_hashes))
            return f"fallback_aggregated_{hash(combined):08x}"
    
    def _hash_weights(self, weights: Dict[str, torch.Tensor]) -> str:
        """Generate hash of model weights for proof verification"""
        import hashlib
        
        # Convert weights to string representation
        weight_str = ""
        for name, tensor in sorted(weights.items()):
            weight_str += f"{name}:{tensor.flatten()[:10].tolist()}"  # Sample first 10 values
        
        return hashlib.md5(weight_str.encode()).hexdigest()[:16]
    
    async def broadcast_model_update(self):
        """Broadcast updated global model to all connected clients"""
        if not self.connected_clients:
            return
        
        message = {
            'type': 'model_weights',
            'round': self.current_round,
            'weights': self._serialize_weights(self.get_global_weights())
        }
        
        disconnected_clients = []
        for client_id, client_info in self.connected_clients.items():
            try:
                await client_info['websocket'].send(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send update to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            del self.connected_clients[client_id]
    
    def _serialize_weights(self, weights: Dict[str, torch.Tensor]) -> Dict[str, List]:
        """Convert tensor weights to serializable format"""
        return {name: tensor.detach().cpu().numpy().tolist() for name, tensor in weights.items()}
    
    def _deserialize_weights(self, weights_dict: Dict[str, List]) -> Dict[str, torch.Tensor]:
        """Convert serialized weights back to tensors"""
        return {name: torch.tensor(weight_list, dtype=torch.float32) for name, weight_list in weights_dict.items()}
    
    async def start_server(self):
        """Start the federated learning server"""
        logger.info(f"Starting FL server on {self.host}:{self.port}")
        
        # Start WebSocket server
        start_server = websockets.serve(self.handle_client_connection, self.host, self.port)
        
        logger.info(f"FL Server running on ws://{self.host}:{self.port}")
        logger.info(f"Waiting for at least {self.min_clients} clients to connect...")
        
        await start_server
        
        # Keep server running
        await asyncio.Future()  # Run forever
    
    def get_training_stats(self) -> Dict:
        """Get training statistics"""
        if not self.fl_history:
            return {'rounds': 0, 'avg_loss': 0.0, 'latest_loss': 0.0}
        
        latest_round = self.fl_history[-1]
        avg_loss = np.mean([r.aggregated_loss for r in self.fl_history])
        
        return {
            'rounds': len(self.fl_history),
            'avg_loss': avg_loss,
            'latest_loss': latest_round.aggregated_loss,
            'participation_rate': latest_round.participation_rate,
            'connected_clients': len(self.connected_clients)
        }
    
    def save_model(self, path: str):
        """Save the current global model"""
        torch.save(self.global_model.state_dict(), path)
        logger.info(f"Global model saved to {path}")
    
    def load_model(self, path: str):
        """Load a saved global model"""
        self.global_model.load_state_dict(torch.load(path))
        logger.info(f"Global model loaded from {path}")
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        logger.info("🧹 Cleaning up FL server resources...")
        
        # Clean up Protogalaxy aggregator
        if hasattr(self, 'protogalaxy_aggregator'):
            self.protogalaxy_aggregator.cleanup()
            
        # Get final aggregation stats
        if hasattr(self, 'protogalaxy_aggregator'):
            agg_stats = self.protogalaxy_aggregator.get_aggregation_stats()
            logger.info(f"📊 Final Protogalaxy stats: {agg_stats}")
        
        logger.info("✅ FL server cleanup completed")

# Main server execution
async def main():
    """Main server execution"""
    # Model configuration (matching our trained MLP)
    model_config = {
        'input_size': 18,  # Heart disease dataset features
        'hidden_sizes': [128, 64, 32],
        'dropout_rate': 0.3
    }
    
    # Create and start FL server
    server = FederatedServer(
        model_config=model_config,
        host="localhost",
        port=8765,
        min_clients=2,
        rounds_per_epoch=10
    )
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.cleanup()
        print(f"\nFinal training stats: {server.get_training_stats()}")

if __name__ == "__main__":
    asyncio.run(main())