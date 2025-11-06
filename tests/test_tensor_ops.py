"""Unit tests for tensor operations."""

import numpy as np
import pytest
from src.tensor_ops.generator import TensorGenerator
from src.tensor_ops.operations import (
    matrix_multiplication,
    tensor_contraction,
    element_wise_ops,
    tensor_decomposition,
    convolution_2d,
)


class TestTensorGenerator:
    """Test tensor generation."""
    
    def test_generate_matrix(self):
        gen = TensorGenerator(seed=42)
        matrix = gen.generate_matrix(10, 20)
        assert matrix.shape == (10, 20)
        assert matrix.dtype == np.float32
    
    def test_generate_tensor_3d(self):
        gen = TensorGenerator(seed=42)
        tensor = gen.generate_tensor_3d(5, 6, 7)
        assert tensor.shape == (5, 6, 7)
    
    def test_reproducibility(self):
        gen1 = TensorGenerator(seed=42)
        gen2 = TensorGenerator(seed=42)
        
        m1 = gen1.generate_matrix(5, 5)
        m2 = gen2.generate_matrix(5, 5)
        
        np.testing.assert_array_equal(m1, m2)


class TestMatrixMultiplication:
    """Test matrix multiplication."""
    
    def test_basic_multiplication(self):
        A = np.array([[1, 2], [3, 4]], dtype=np.float32)
        B = np.array([[5, 6], [7, 8]], dtype=np.float32)
        
        result = matrix_multiplication(A, B)
        
        assert 'result' in result
        assert result['result'].shape == (2, 2)
        expected = np.array([[19, 22], [43, 50]], dtype=np.float32)
        np.testing.assert_array_almost_equal(result['result'], expected)
    
    def test_incompatible_shapes(self):
        A = np.array([[1, 2, 3]])
        B = np.array([[1, 2]])
        
        with pytest.raises(ValueError):
            matrix_multiplication(A, B)


class TestTensorDecomposition:
    """Test tensor decomposition."""
    
    def test_svd_decomposition(self):
        A = np.random.rand(5, 5).astype(np.float32)
        result = tensor_decomposition(A, method='svd')
        
        assert 'result' in result
        assert 'U' in result['result']
        assert 'S' in result['result']
        assert 'Vt' in result['result']
        
        # Check reconstruction error is small
        assert result['reconstruction_error'] < 1e-5
    
    def test_qr_decomposition(self):
        A = np.random.rand(5, 5).astype(np.float32)
        result = tensor_decomposition(A, method='qr')
        
        assert 'Q' in result['result']
        assert 'R' in result['result']
        assert result['reconstruction_error'] < 1e-5


class TestConvolution:
    """Test convolution operations."""
    
    def test_basic_convolution(self):
        input_tensor = np.ones((10, 10, 3), dtype=np.float32)
        kernel = np.ones((3, 3, 3, 1), dtype=np.float32)
        
        result = convolution_2d(input_tensor, kernel, stride=1, padding=0)
        
        assert 'result' in result
        assert result['output_shape'] == (8, 8, 1)
