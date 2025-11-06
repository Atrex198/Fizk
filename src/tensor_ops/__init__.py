"""Tensor operation generators and utilities."""

from .generator import TensorGenerator
from .operations import (
    matrix_multiplication,
    tensor_contraction,
    element_wise_ops,
    tensor_decomposition,
    convolution_2d,
)

__all__ = [
    "TensorGenerator",
    "matrix_multiplication",
    "tensor_contraction",
    "element_wise_ops",
    "tensor_decomposition",
    "convolution_2d",
]
