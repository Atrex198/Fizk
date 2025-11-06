"""Tensor operations for benchmarking."""

import numpy as np
from typing import Tuple, Dict, Any
from loguru import logger


def matrix_multiplication(A: np.ndarray, B: np.ndarray) -> Dict[str, Any]:
    """Perform matrix multiplication and return result with metadata.
    
    Args:
        A: First matrix
        B: Second matrix
        
    Returns:
        Dictionary with result and operation metadata
    """
    if A.shape[1] != B.shape[0]:
        raise ValueError(f"Incompatible shapes: {A.shape} and {B.shape}")
    
    C = A @ B
    
    return {
        "result": C,
        "operation": "matrix_multiplication",
        "input_shapes": [A.shape, B.shape],
        "output_shape": C.shape,
        "total_ops": A.shape[0] * A.shape[1] * B.shape[1] * 2,  # multiply-add
    }


def tensor_contraction(
    tensor_a: np.ndarray, tensor_b: np.ndarray, axes: Tuple[int, int]
) -> Dict[str, Any]:
    """Perform Einstein summation (tensor contraction).
    
    Args:
        tensor_a: First tensor
        tensor_b: Second tensor
        axes: Axes to contract
        
    Returns:
        Dictionary with result and metadata
    """
    result = np.tensordot(tensor_a, tensor_b, axes=axes)
    
    return {
        "result": result,
        "operation": "tensor_contraction",
        "input_shapes": [tensor_a.shape, tensor_b.shape],
        "output_shape": result.shape,
        "contraction_axes": axes,
    }


def element_wise_ops(
    tensor_a: np.ndarray, tensor_b: np.ndarray, operation: str = "multiply"
) -> Dict[str, Any]:
    """Perform element-wise operations.
    
    Args:
        tensor_a: First tensor
        tensor_b: Second tensor
        operation: Operation type ('add', 'multiply', 'relu', etc.)
        
    Returns:
        Dictionary with result and metadata
    """
    if tensor_a.shape != tensor_b.shape:
        raise ValueError(f"Incompatible shapes: {tensor_a.shape} and {tensor_b.shape}")
    
    if operation == "add":
        result = tensor_a + tensor_b
    elif operation == "multiply":
        result = tensor_a * tensor_b
    elif operation == "relu":
        result = np.maximum(0, tensor_a + tensor_b)
    elif operation == "sigmoid":
        result = 1 / (1 + np.exp(-(tensor_a + tensor_b)))
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    return {
        "result": result,
        "operation": f"element_wise_{operation}",
        "input_shapes": [tensor_a.shape, tensor_b.shape],
        "output_shape": result.shape,
        "total_ops": tensor_a.size,
    }


def tensor_decomposition(matrix: np.ndarray, method: str = "svd") -> Dict[str, Any]:
    """Perform tensor decomposition.
    
    Args:
        matrix: Input matrix
        method: Decomposition method ('svd', 'eig', 'qr')
        
    Returns:
        Dictionary with decomposition results and metadata
    """
    if method == "svd":
        U, S, Vt = np.linalg.svd(matrix, full_matrices=False)
        result = {"U": U, "S": S, "Vt": Vt}
        # Verify: A ≈ U @ diag(S) @ Vt
        reconstruction = U @ np.diag(S) @ Vt
        error = np.linalg.norm(matrix - reconstruction)
        
    elif method == "eig":
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        result = {"eigenvalues": eigenvalues, "eigenvectors": eigenvectors}
        # Verify: A @ v = λ @ v
        error = 0
        for i in range(len(eigenvalues)):
            v = eigenvectors[:, i]
            error += np.linalg.norm(matrix @ v - eigenvalues[i] * v)
        error /= len(eigenvalues)
        
    elif method == "qr":
        Q, R = np.linalg.qr(matrix)
        result = {"Q": Q, "R": R}
        # Verify: A = Q @ R
        reconstruction = Q @ R
        error = np.linalg.norm(matrix - reconstruction)
        
    else:
        raise ValueError(f"Unknown decomposition method: {method}")
    
    return {
        "result": result,
        "operation": f"decomposition_{method}",
        "input_shape": matrix.shape,
        "reconstruction_error": error,
    }


def convolution_2d(
    input_tensor: np.ndarray,
    kernel: np.ndarray,
    stride: int = 1,
    padding: int = 0,
) -> Dict[str, Any]:
    """Perform 2D convolution.
    
    Args:
        input_tensor: Input tensor (H, W, C_in)
        kernel: Convolution kernel (K, K, C_in, C_out)
        stride: Stride for convolution
        padding: Padding size
        
    Returns:
        Dictionary with convolution result and metadata
    """
    H, W, C_in = input_tensor.shape
    K, _, _, C_out = kernel.shape
    
    # Add padding
    if padding > 0:
        input_padded = np.pad(
            input_tensor,
            ((padding, padding), (padding, padding), (0, 0)),
            mode='constant'
        )
    else:
        input_padded = input_tensor
    
    H_padded, W_padded, _ = input_padded.shape
    
    # Calculate output dimensions
    H_out = (H_padded - K) // stride + 1
    W_out = (W_padded - K) // stride + 1
    
    # Initialize output
    output = np.zeros((H_out, W_out, C_out))
    
    # Perform convolution
    for i in range(H_out):
        for j in range(W_out):
            h_start = i * stride
            w_start = j * stride
            
            # Extract patch
            patch = input_padded[h_start:h_start+K, w_start:w_start+K, :]
            
            # Apply kernel
            for c in range(C_out):
                output[i, j, c] = np.sum(patch * kernel[:, :, :, c])
    
    total_ops = H_out * W_out * C_out * K * K * C_in * 2  # multiply-add
    
    return {
        "result": output,
        "operation": "convolution_2d",
        "input_shape": input_tensor.shape,
        "kernel_shape": kernel.shape,
        "output_shape": output.shape,
        "stride": stride,
        "padding": padding,
        "total_ops": total_ops,
    }
