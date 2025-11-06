"""
Commitment Utilities for ZKP Protocols

This module provides standardized functions for creating cryptographic commitments
from ML model weights and other data structures. It ensures consistent serialization
across proof generation and verification to prevent hash mismatches.

CRITICAL: All code that generates commitments for weights MUST use these functions
to ensure identical hash values across different code paths.
"""

import hashlib
import json
import torch
import numpy as np
from typing import Dict, Any, Union


def create_weight_commitment(weights: Dict[str, Any]) -> str:
    """
    Create a cryptographic commitment (hash) from model weights.
    
    This function ensures consistent tensor->hash conversion by:
    1. Converting all tensors to CPU
    2. Detaching from computation graph
    3. Converting to numpy
    4. Converting to Python lists
    5. JSON serialization with sorted keys
    6. SHA-256 hashing
    
    Args:
        weights: Dictionary mapping layer names to weight tensors/arrays
        
    Returns:
        Hexadecimal string hash of the weights
        
    Example:
        >>> weights = {'layer1.weight': torch.randn(10, 5)}
        >>> hash1 = create_weight_commitment(weights)
        >>> hash2 = create_weight_commitment(weights)
        >>> assert hash1 == hash2  # Same weights produce same hash
    """
    serializable_weights = {}
    
    for key, value in weights.items():
        # Handle PyTorch tensors
        if isinstance(value, torch.Tensor):
            # CRITICAL: Must detach, move to CPU, convert to numpy, then to list
            # This exact sequence ensures consistent floating point representation
            serializable_weights[key] = value.cpu().detach().numpy().tolist()
        
        # Handle numpy arrays
        elif isinstance(value, np.ndarray):
            serializable_weights[key] = value.tolist()
        
        # Handle already-serializable types (lists, floats, ints)
        elif isinstance(value, (list, float, int)):
            serializable_weights[key] = value
        
        else:
            raise TypeError(
                f"Unsupported weight type for key '{key}': {type(value)}. "
                f"Expected torch.Tensor, np.ndarray, list, float, or int."
            )
    
    # Sort keys to ensure deterministic JSON serialization
    json_str = json.dumps(serializable_weights, sort_keys=True)
    
    # Create SHA-256 hash
    return hashlib.sha256(json_str.encode()).hexdigest()


def create_data_commitment(data: Union[np.ndarray, torch.Tensor]) -> str:
    """
    Create a cryptographic commitment from dataset samples.
    
    Args:
        data: Dataset as numpy array or torch tensor
        
    Returns:
        Hexadecimal string hash of the data
    """
    if isinstance(data, torch.Tensor):
        # Convert tensor to bytes via numpy
        data_bytes = data.cpu().detach().numpy().tobytes()
    elif isinstance(data, np.ndarray):
        data_bytes = data.tobytes()
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")
    
    return hashlib.sha256(data_bytes).hexdigest()


def verify_commitment(data: Any, claimed_commitment: str, commitment_type: str = "weight") -> bool:
    """
    Verify that data matches a claimed commitment.
    
    Args:
        data: The data to verify (weights dict or dataset array)
        claimed_commitment: The claimed hash value
        commitment_type: Either "weight" or "data"
        
    Returns:
        True if commitment matches, False otherwise
    """
    if commitment_type == "weight":
        actual_commitment = create_weight_commitment(data)
    elif commitment_type == "data":
        actual_commitment = create_data_commitment(data)
    else:
        raise ValueError(f"Unknown commitment type: {commitment_type}")
    
    return actual_commitment == claimed_commitment
