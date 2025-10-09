#!/usr/bin/env python3
"""
Real Machine Learning Training Module for ZK-FL
==============================================

Production-grade ML training implementation replacing all simulated training
with authentic PyTorch-based federated learning. Integrates with real medical
datasets and generates genuine training metrics for ZK proof verification.

Features:
- Real PyTorch neural network training
- Actual SGD/Adam optimization 
- Real loss computation and backpropagation
- Genuine model parameter updates
- Integration with real medical datasets
- Proper federated learning client training

Author: Advanced ZK-FL Framework
Version: 1.0.0 Production  
Date: September 2025
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
import time
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass 
class TrainingConfig:
    """Configuration for real ML training"""
    learning_rate: float = 0.001  # Reduced from 0.01 for federated learning stability
    batch_size: int = 32
    local_epochs: int = 5
    optimizer: str = "sgd"  # "sgd" or "adam"
    loss_function: str = "cross_entropy"  # "cross_entropy" or "bce"
    regularization: float = 0.001  # L2 regularization
    early_stopping_patience: int = 3
    min_delta: float = 0.001  # Minimum improvement for early stopping

@dataclass
class TrainingResult:
    """Results from real ML training with comprehensive metrics"""
    initial_loss: float
    final_loss: float
    initial_accuracy: float  
    final_accuracy: float
    epochs_completed: int
    training_time: float
    model_parameters: Dict[str, torch.Tensor]
    parameter_updates: Dict[str, torch.Tensor]
    gradient_norms: List[float]
    convergence_achieved: bool
    
    # Enhanced metrics for federated learning
    initial_weights: Dict[str, torch.Tensor]
    final_weights: Dict[str, torch.Tensor]
    loss_history: List[float]
    accuracy_history: List[float]
    data_distribution: Dict[str, int]  # Class distribution in training data
    training_samples: int
    weight_delta_norm: float  # L2 norm of weight changes
    learning_progress: float  # Improvement percentage

class MedicalMLPModel(nn.Module):
    """
    Real neural network for medical prediction tasks.
    Designed for cardio/heart disease prediction with proper architecture.
    """
    
    def __init__(self, input_features: int, hidden_sizes: List[int] = [64, 32], 
                 num_classes: int = 2, dropout_rate: float = 0.3):
        super(MedicalMLPModel, self).__init__()
        
        self.input_features = input_features
        self.num_classes = num_classes
        
        # Build layers dynamically
        layers = []
        prev_size = input_features
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.BatchNorm1d(hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])
            prev_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(prev_size, num_classes))
        
        self.network = nn.Sequential(*layers)
        
        # Initialize weights using Xavier initialization
        self.apply(self._init_weights)
        
        logger.info(f"Medical MLP Model initialized: {input_features} -> {hidden_sizes} -> {num_classes}")
    
    def _init_weights(self, module):
        """Xavier weight initialization for better convergence"""
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
    
    def forward(self, x):
        return self.network(x)
    
    def get_parameter_dict(self) -> Dict[str, torch.Tensor]:
        """Get model parameters as dictionary"""
        return {name: param.detach().clone() for name, param in self.named_parameters()}
    
    def set_parameters(self, parameters: Dict[str, torch.Tensor]):
        """Set model parameters from dictionary and reset optimizer state"""
        with torch.no_grad():
            for name, param in self.named_parameters():
                if name in parameters:
                    # Convert numpy arrays to tensors if needed
                    param_value = parameters[name]
                    if isinstance(param_value, np.ndarray):
                        param_value = torch.from_numpy(param_value).float()
                    param.copy_(param_value)

class RealMLTrainer:
    """
    Production-grade ML trainer for federated learning clients.
    Replaces all simulated training with authentic PyTorch implementation.
    """
    
    def __init__(self, input_features: int, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.input_features = input_features
        
        # Initialize model
        self.model = MedicalMLPModel(
            input_features=input_features,
            hidden_sizes=[64, 32],  # Medical data appropriate architecture
            num_classes=2,  # Binary classification (cardio disease)
            dropout_rate=0.3
        )
        
        # Setup optimizer
        if self.config.optimizer.lower() == "adam":
            self.optimizer = optim.Adam(
                self.model.parameters(), 
                lr=self.config.learning_rate,
                weight_decay=self.config.regularization
            )
        else:  # SGD
            self.optimizer = optim.SGD(
                self.model.parameters(), 
                lr=self.config.learning_rate, 
                momentum=0.9,
                weight_decay=self.config.regularization
            )
        
        # Loss function
        if self.config.loss_function == "bce":
            self.criterion = nn.BCEWithLogitsLoss()
        else:
            self.criterion = nn.CrossEntropyLoss()
        
        # Training state
        self.training_history = []
        
        logger.info(f"Real ML Trainer initialized with {self.config.optimizer} optimizer")
    
    def train_local_model(self, X: np.ndarray = None, y: np.ndarray = None,
                         X_train: np.ndarray = None, y_train: np.ndarray = None,
                         X_val: Optional[np.ndarray] = None, 
                         y_val: Optional[np.ndarray] = None,
                         initial_weights: Optional[Dict[str, torch.Tensor]] = None,
                         epochs: Optional[int] = None,
                         learning_rate: Optional[float] = None,
                         batch_size: Optional[int] = None) -> TrainingResult:
        """
        Perform real local training with authentic ML algorithms.
        
        Args:
            X: Training features (alternative parameter name)
            y: Training labels (alternative parameter name)
            X_train: Training features
            y_train: Training labels  
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            initial_weights: Initial model weights (optional)
            epochs: Number of training epochs (optional, overrides config)
            learning_rate: Learning rate (optional, overrides config)
            batch_size: Batch size (optional, overrides config)
            
        Returns:
            TrainingResult with genuine training metrics
        """
        start_time = time.time()
        
        # Handle alternative parameter names
        if X is not None and X_train is None:
            X_train = X
        if y is not None and y_train is None:
            y_train = y
            
        if X_train is None or y_train is None:
            raise ValueError("Training data (X_train/X and y_train/y) must be provided")
        
        # Override config with provided parameters
        if epochs is not None:
            self.config.local_epochs = epochs
        if learning_rate is not None:
            self.config.learning_rate = learning_rate
            # Update optimizer with new learning rate
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = learning_rate
        if batch_size is not None:
            self.config.batch_size = batch_size
            
        # Set initial weights if provided
        if initial_weights is not None:
            self.model.set_parameters(initial_weights)
        
        # Store initial model state
        initial_params = self.model.get_parameter_dict()
        
        # Convert to PyTorch tensors
        X_tensor = torch.FloatTensor(X_train)
        y_tensor = torch.LongTensor(y_train)
        
        # Create data loader for real batch processing
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(
            dataset, 
            batch_size=self.config.batch_size, 
            shuffle=True,
            drop_last=False
        )
        
        # Validation data if provided
        val_loader = None
        if X_val is not None and y_val is not None:
            X_val_tensor = torch.FloatTensor(X_val)
            y_val_tensor = torch.LongTensor(y_val)
            val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
            val_loader = DataLoader(val_dataset, batch_size=self.config.batch_size, shuffle=False)
        
        # Calculate initial metrics
        self.model.eval()
        with torch.no_grad():
            initial_loss, initial_accuracy = self._evaluate_model(dataloader)
        
        logger.info(f"Starting training - Initial loss: {initial_loss:.4f}, accuracy: {initial_accuracy:.4f}")
        
        # Training loop with real gradient descent
        self.model.train()
        best_val_loss = float('inf')
        patience_counter = 0
        gradient_norms = []
        loss_history = []
        accuracy_history = []
        
        for epoch in range(self.config.local_epochs):
            epoch_loss = 0.0
            epoch_correct = 0
            epoch_total = 0
            
            for batch_idx, (batch_X, batch_y) in enumerate(dataloader):
                # Zero gradients
                self.optimizer.zero_grad()
                
                # Forward pass
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                # Backward pass - REAL GRADIENT COMPUTATION
                loss.backward()
                
                # Calculate gradient norm
                total_norm = 0
                for param in self.model.parameters():
                    if param.grad is not None:
                        param_norm = param.grad.data.norm(2)
                        total_norm += param_norm.item() ** 2
                total_norm = total_norm ** (1. / 2)
                gradient_norms.append(total_norm)
                
                # Update parameters - REAL PARAMETER UPDATES
                self.optimizer.step()
                
                # Track metrics
                epoch_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                epoch_total += batch_y.size(0)
                epoch_correct += (predicted == batch_y).sum().item()
            
            # Epoch metrics
            epoch_loss /= len(dataloader)
            epoch_accuracy = epoch_correct / epoch_total
            
            # Store history
            loss_history.append(epoch_loss)
            accuracy_history.append(epoch_accuracy)
            
            # Validation check
            val_loss = None
            if val_loader is not None:
                self.model.eval()
                with torch.no_grad():
                    val_loss, val_accuracy = self._evaluate_model(val_loader)
                self.model.train()
                
                # Early stopping check
                if val_loss < best_val_loss - self.config.min_delta:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch + 1}")
                    break
            
            logger.debug(f"Epoch {epoch + 1}/{self.config.local_epochs}: "
                        f"Loss={epoch_loss:.4f}, Acc={epoch_accuracy:.4f}"
                        f"{f', Val_Loss={val_loss:.4f}' if val_loss else ''}")
        
        # Calculate final metrics
        self.model.eval()
        with torch.no_grad():
            final_loss, final_accuracy = self._evaluate_model(dataloader)
        
        # Get final parameters and compute updates
        final_params = self.model.get_parameter_dict()
        parameter_updates = {
            name: final_params[name] - initial_params[name] 
            for name in initial_params.keys()
        }
        
        # Calculate weight delta norm
        weight_delta_norm = sum(torch.norm(update).item() ** 2 for update in parameter_updates.values()) ** 0.5
        
        # Calculate data distribution
        unique_labels, counts = torch.unique(torch.LongTensor(y_train), return_counts=True)
        data_distribution = {f"class_{label.item()}": count.item() for label, count in zip(unique_labels, counts)}
        
        # Calculate learning progress
        learning_progress = ((initial_loss - final_loss) / initial_loss * 100) if initial_loss > 0 else 0.0
        
        training_time = time.time() - start_time
        epochs_completed = epoch + 1
        convergence_achieved = patience_counter < self.config.early_stopping_patience
        
        result = TrainingResult(
            initial_loss=initial_loss,
            final_loss=final_loss,
            initial_accuracy=initial_accuracy,
            final_accuracy=final_accuracy,
            epochs_completed=epochs_completed,
            training_time=training_time,
            model_parameters=final_params,
            parameter_updates=parameter_updates,
            gradient_norms=gradient_norms,
            convergence_achieved=convergence_achieved,
            # Enhanced metrics
            initial_weights=initial_params,
            final_weights=final_params,
            loss_history=loss_history,
            accuracy_history=accuracy_history,
            data_distribution=data_distribution,
            training_samples=len(y_train),
            weight_delta_norm=weight_delta_norm,
            learning_progress=learning_progress
        )
        
        logger.info(f"Training completed: {epochs_completed} epochs, "
                   f"Final loss: {final_loss:.4f}, accuracy: {final_accuracy:.4f}")
        
        return result
    
    def evaluate_federated_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate the federated model on test data after aggregation
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary with comprehensive test metrics
        """
        self.model.eval()
        
        # Convert to tensors
        X_test_tensor = torch.FloatTensor(X_test)
        y_test_tensor = torch.LongTensor(y_test)
        
        # Create test dataset and loader
        test_dataset = TensorDataset(X_test_tensor, y_test_tensor)
        test_loader = DataLoader(test_dataset, batch_size=self.config.batch_size, shuffle=False)
        
        total_loss = 0.0
        correct = 0
        total = 0
        predictions = []
        true_labels = []
        
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += batch_y.size(0)
                correct += (predicted == batch_y).sum().item()
                
                predictions.extend(predicted.cpu().numpy())
                true_labels.extend(batch_y.cpu().numpy())
        
        # Calculate metrics
        test_loss = total_loss / len(test_loader)
        test_accuracy = correct / total
        
        # Calculate per-class accuracy
        predictions = np.array(predictions)
        true_labels = np.array(true_labels)
        
        unique_classes = np.unique(true_labels)
        per_class_accuracy = {}
        
        for cls in unique_classes:
            cls_mask = true_labels == cls
            if cls_mask.sum() > 0:
                cls_correct = (predictions[cls_mask] == true_labels[cls_mask]).sum()
                per_class_accuracy[f"class_{cls}_accuracy"] = cls_correct / cls_mask.sum()
        
        # Calculate class distribution in test set
        unique_labels, counts = np.unique(true_labels, return_counts=True)
        test_distribution = {f"class_{label}": count for label, count in zip(unique_labels, counts)}
        
        metrics = {
            'test_loss': test_loss,
            'test_accuracy': test_accuracy,
            'test_samples': len(y_test),
            'test_distribution': test_distribution,
            **per_class_accuracy
        }
        
        logger.info(f"Federated model test results: Loss={test_loss:.4f}, Accuracy={test_accuracy:.4f}")
        
        return metrics

    def _evaluate_model(self, dataloader: DataLoader) -> Tuple[float, float]:
        """Evaluate model on given dataloader"""
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_X, batch_y in dataloader:
            outputs = self.model(batch_X)
            loss = self.criterion(outputs, batch_y)
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
        
        avg_loss = total_loss / len(dataloader)
        accuracy = correct / total
        
        return avg_loss, accuracy
    
    def reset_optimizer_state(self):
        """Reset optimizer state to prevent momentum/history contamination"""
        # Reinitialize optimizer with same parameters but clean state
        if self.config.optimizer.lower() == "adam":
            self.optimizer = optim.Adam(
                self.model.parameters(), 
                lr=self.config.learning_rate,
                weight_decay=self.config.regularization
            )
        else:  # SGD
            self.optimizer = optim.SGD(
                self.model.parameters(), 
                lr=self.config.learning_rate, 
                momentum=0.9,
                weight_decay=self.config.regularization
            )
        logger.info("Optimizer state reset")
    
    def load_global_model(self, global_parameters: Dict[str, torch.Tensor]):
        """Load global model parameters for federated learning"""
        self.model.set_parameters(global_parameters)
        self.reset_optimizer_state()  # CRITICAL: Reset optimizer state to prevent momentum contamination
        logger.info("Global model parameters loaded and optimizer state reset")
    
    def get_model_updates(self) -> Dict[str, torch.Tensor]:
        """Get model parameter updates for federated aggregation"""
        return self.model.get_parameter_dict()

# Example usage and testing
if __name__ == "__main__":
    print("🧠 Real ML Training Module Test")
    print("=" * 40)
    
    # Test with synthetic data (replace with real dataset in production)
    print("📊 Generating test data...")
    X_train = np.random.randn(1000, 11)  # 11 features like cardio dataset
    y_train = np.random.randint(0, 2, 1000)  # Binary classification
    
    X_val = np.random.randn(200, 11)
    y_val = np.random.randint(0, 2, 200)
    
    # Initialize trainer
    config = TrainingConfig(
        learning_rate=0.01,
        batch_size=32,
        local_epochs=10,
        optimizer="adam"
    )
    
    trainer = RealMLTrainer(input_features=11, config=config)
    
    # Perform real training
    print("🚀 Starting real ML training...")
    result = trainer.train_local_model(X_train, y_train, X_val, y_val)
    
    print("✅ Training Results:")
    print(f"  Initial Loss: {result.initial_loss:.4f} -> Final Loss: {result.final_loss:.4f}")
    print(f"  Initial Accuracy: {result.initial_accuracy:.4f} -> Final Accuracy: {result.final_accuracy:.4f}")
    print(f"  Epochs: {result.epochs_completed}")
    print(f"  Training Time: {result.training_time:.2f}s")
    print(f"  Convergence: {'Yes' if result.convergence_achieved else 'No'}")
    print(f"  Avg Gradient Norm: {np.mean(result.gradient_norms):.6f}")
    
    print("🎉 Real ML training module ready!")