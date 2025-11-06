"""Tensor data generation utilities."""

import numpy as np
from typing import Tuple, Optional
from loguru import logger


class TensorGenerator:
    """Generate random tensors for benchmarking."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize tensor generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.rng = np.random.default_rng(seed)
        logger.info(f"TensorGenerator initialized with seed={seed}")

    def generate_matrix(self, rows: int, cols: int, dtype=np.float32) -> np.ndarray:
        """Generate a random matrix.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            dtype: Data type
            
        Returns:
            Random matrix of shape (rows, cols)
        """
        return self.rng.random((rows, cols), dtype=dtype)

    def generate_tensor_3d(self, d1: int, d2: int, d3: int, dtype=np.float32) -> np.ndarray:
        """Generate a random 3D tensor.
        
        Args:
            d1, d2, d3: Dimensions
            dtype: Data type
            
        Returns:
            Random 3D tensor
        """
        return self.rng.random((d1, d2, d3), dtype=dtype)

    def generate_positive_definite_matrix(self, n: int) -> np.ndarray:
        """Generate a positive definite matrix for decomposition tests.
        
        Args:
            n: Matrix dimension
            
        Returns:
            Positive definite matrix of shape (n, n)
        """
        A = self.rng.random((n, n))
        return A @ A.T + np.eye(n) * 0.1

    def generate_convolution_input(
        self, height: int, width: int, channels: int, dtype=np.float32
    ) -> np.ndarray:
        """Generate input for convolution operations.
        
        Args:
            height: Input height
            width: Input width
            channels: Number of channels
            dtype: Data type
            
        Returns:
            Random tensor of shape (height, width, channels)
        """
        return self.rng.random((height, width, channels), dtype=dtype)

    def generate_convolution_kernel(
        self, kernel_size: int, in_channels: int, out_channels: int, dtype=np.float32
    ) -> np.ndarray:
        """Generate convolution kernel.
        
        Args:
            kernel_size: Kernel size (assumed square)
            in_channels: Input channels
            out_channels: Output channels
            dtype: Data type
            
        Returns:
            Random kernel of shape (kernel_size, kernel_size, in_channels, out_channels)
        """
        return self.rng.random(
            (kernel_size, kernel_size, in_channels, out_channels), dtype=dtype
        )

    def generate_integer_matrix(
        self, rows: int, cols: int, max_value: int = 1000
    ) -> np.ndarray:
        """Generate random integer matrix for ZKP circuits.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            max_value: Maximum integer value
            
        Returns:
            Random integer matrix
        """
        return self.rng.integers(0, max_value, size=(rows, cols))
