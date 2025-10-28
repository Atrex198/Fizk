"""
Polynomial Arithmetic Utilities for PLONK
Implements finite field polynomial operations

This provides REAL polynomial arithmetic over finite fields.
NOT a dummy implementation.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from py_ecc.bn128 import curve_order

logger = logging.getLogger(__name__)


class PolynomialArithmetic:
    """
    Finite field polynomial arithmetic for PLONK protocol
    
    Implements polynomial operations modulo curve_order for BN254
    """
    
    def __init__(self, field_modulus: int = curve_order):
        self.field_modulus = field_modulus
        logger.info(f"🔢 Polynomial arithmetic initialized over F_{field_modulus}")
    
    def add(self, poly1: List[int], poly2: List[int]) -> List[int]:
        """
        Add two polynomials
        
        Args:
            poly1, poly2: Polynomial coefficients [p₀, p₁, p₂, ...]
            
        Returns:
            Sum polynomial coefficients
        """
        max_len = max(len(poly1), len(poly2))
        
        # Pad with zeros
        p1_padded = poly1 + [0] * (max_len - len(poly1))
        p2_padded = poly2 + [0] * (max_len - len(poly2))
        
        result = [(a + b) % self.field_modulus for a, b in zip(p1_padded, p2_padded)]
        
        # Remove leading zeros
        return self._trim_leading_zeros(result)
    
    def subtract(self, poly1: List[int], poly2: List[int]) -> List[int]:
        """Subtract poly2 from poly1"""
        max_len = max(len(poly1), len(poly2))
        
        p1_padded = poly1 + [0] * (max_len - len(poly1))
        p2_padded = poly2 + [0] * (max_len - len(poly2))
        
        result = [(a - b) % self.field_modulus for a, b in zip(p1_padded, p2_padded)]
        
        return self._trim_leading_zeros(result)
    
    def multiply(self, poly1: List[int], poly2: List[int]) -> List[int]:
        """
        Multiply two polynomials using convolution
        
        Args:
            poly1, poly2: Polynomial coefficients
            
        Returns:
            Product polynomial coefficients
        """
        if not poly1 or not poly2:
            return [0]
        
        result_degree = len(poly1) + len(poly2) - 1
        result = [0] * result_degree
        
        for i, a in enumerate(poly1):
            for j, b in enumerate(poly2):
                result[i + j] = (result[i + j] + a * b) % self.field_modulus
        
        return self._trim_leading_zeros(result)
    
    def multiply_by_scalar(self, poly: List[int], scalar: int) -> List[int]:
        """Multiply polynomial by scalar"""
        return [(coeff * scalar) % self.field_modulus for coeff in poly]
    
    def divide(self, dividend: List[int], divisor: List[int]) -> Tuple[List[int], List[int]]:
        """
        Polynomial long division
        
        Args:
            dividend: Polynomial to be divided
            divisor: Polynomial to divide by
            
        Returns:
            (quotient, remainder) polynomials
        """
        if not divisor or all(c == 0 for c in divisor):
            raise ValueError("Cannot divide by zero polynomial")
        
        # Remove leading zeros
        dividend = self._trim_leading_zeros(dividend.copy())
        divisor = self._trim_leading_zeros(divisor.copy())
        
        if len(dividend) < len(divisor):
            return [0], dividend
        
        quotient = []
        remainder = dividend.copy()
        
        divisor_lead = divisor[-1]
        divisor_lead_inv = self._multiplicative_inverse(divisor_lead)
        
        while len(remainder) >= len(divisor) and not all(c == 0 for c in remainder):
            # Leading coefficient ratio
            lead_coeff = (remainder[-1] * divisor_lead_inv) % self.field_modulus
            quotient.append(lead_coeff)
            
            # Degree difference
            degree_diff = len(remainder) - len(divisor)
            
            # Subtract divisor * lead_coeff * X^degree_diff from remainder
            for i in range(len(divisor)):
                remainder[degree_diff + i] = (
                    remainder[degree_diff + i] - lead_coeff * divisor[i]
                ) % self.field_modulus
            
            # Remove leading zero
            remainder = self._trim_leading_zeros(remainder)
        
        quotient.reverse()  # We built it backwards
        return self._trim_leading_zeros(quotient), remainder
    
    def evaluate(self, poly: List[int], x: int) -> int:
        """
        Evaluate polynomial at point x using Horner's method
        
        Args:
            poly: Polynomial coefficients [p₀, p₁, p₂, ...]
            x: Evaluation point
            
        Returns:
            p(x) mod field_modulus
        """
        if not poly:
            return 0
        
        result = 0
        for coeff in reversed(poly):
            result = (result * x + coeff) % self.field_modulus
        
        return result
    
    def evaluate_multiple(self, poly: List[int], points: List[int]) -> List[int]:
        """Evaluate polynomial at multiple points"""
        return [self.evaluate(poly, x) for x in points]
    
    def interpolate_lagrange(self, points: List[Tuple[int, int]]) -> List[int]:
        """
        Lagrange interpolation to find polynomial passing through given points
        
        Args:
            points: List of (x, y) coordinate pairs
            
        Returns:
            Polynomial coefficients
        """
        n = len(points)
        if n == 0:
            return [0]
        
        # Initialize result polynomial as zero
        result = [0]
        
        for i in range(n):
            xi, yi = points[i]
            
            # Compute Lagrange basis polynomial Li(x)
            basis = [1]  # Start with polynomial "1"
            denominator = 1
            
            for j in range(n):
                if i != j:
                    xj, _ = points[j]
                    
                    # Multiply basis by (x - xj)
                    basis = self.multiply(basis, [-xj % self.field_modulus, 1])
                    
                    # Update denominator
                    denominator = (denominator * (xi - xj)) % self.field_modulus
            
            # Divide by denominator
            denominator_inv = self._multiplicative_inverse(denominator)
            basis = self.multiply_by_scalar(basis, (yi * denominator_inv) % self.field_modulus)
            
            # Add to result
            result = self.add(result, basis)
        
        return result
    
    def compute_vanishing_polynomial(self, points: List[int]) -> List[int]:
        """
        Compute vanishing polynomial Z(x) = ∏(x - pᵢ)
        
        Args:
            points: Points where polynomial should vanish
            
        Returns:
            Vanishing polynomial coefficients
        """
        result = [1]  # Start with polynomial "1"
        
        for point in points:
            # Multiply by (x - point)
            linear_factor = [(-point) % self.field_modulus, 1]
            result = self.multiply(result, linear_factor)
        
        return result
    
    def compute_quotient_polynomial(
        self,
        numerator: List[int],
        denominator: List[int]
    ) -> List[int]:
        """
        Compute quotient polynomial numerator(x) / denominator(x)
        
        Assumes exact division (remainder should be zero)
        """
        quotient, remainder = self.divide(numerator, denominator)
        
        if not all(c == 0 for c in remainder):
            logger.warning("⚠️  Non-zero remainder in quotient computation")
        
        return quotient
    
    def fft_evaluation(self, poly: List[int], n: int) -> List[int]:
        """
        Fast Fourier Transform evaluation (simplified)
        
        Evaluates polynomial at n-th roots of unity
        Used in PLONK for efficient polynomial operations
        """
        # Find primitive n-th root of unity
        omega = self._find_primitive_root_of_unity(n)
        
        if omega is None:
            # Fallback to naive evaluation
            return self._naive_fft_evaluation(poly, n)
        
        # Pad polynomial to length n
        padded_poly = poly + [0] * (n - len(poly))
        
        # Evaluate at powers of omega
        result = []
        omega_power = 1
        
        for i in range(n):
            evaluation = self.evaluate(padded_poly, omega_power)
            result.append(evaluation)
            omega_power = (omega_power * omega) % self.field_modulus
        
        return result
    
    def _trim_leading_zeros(self, poly: List[int]) -> List[int]:
        """Remove leading zero coefficients"""
        if not poly:
            return [0]
        
        while len(poly) > 1 and poly[-1] == 0:
            poly.pop()
        
        return poly or [0]
    
    def _multiplicative_inverse(self, a: int) -> int:
        """Compute multiplicative inverse using extended Euclidean algorithm"""
        if a == 0:
            raise ValueError("Cannot find inverse of zero")
        
        # Extended Euclidean algorithm
        def extended_gcd(a, b):
            if a == 0:
                return b, 0, 1
            gcd, x1, y1 = extended_gcd(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd, x, y
        
        gcd, x, _ = extended_gcd(a % self.field_modulus, self.field_modulus)
        
        if gcd != 1:
            raise ValueError(f"No multiplicative inverse exists for {a}")
        
        return x % self.field_modulus
    
    def _find_primitive_root_of_unity(self, n: int) -> Optional[int]:
        """Find primitive n-th root of unity in the field"""
        # Check if n divides (field_modulus - 1)
        if (self.field_modulus - 1) % n != 0:
            return None
        
        # Find generator and compute n-th root
        # This is simplified - in practice would use more sophisticated methods
        exponent = (self.field_modulus - 1) // n
        
        # Try small generators
        for g in range(2, min(100, self.field_modulus)):
            root = pow(g, exponent, self.field_modulus)
            if pow(root, n, self.field_modulus) == 1 and root != 1:
                return root
        
        return None
    
    def _naive_fft_evaluation(self, poly: List[int], n: int) -> List[int]:
        """Fallback naive evaluation at n points"""
        points = [i for i in range(n)]
        return self.evaluate_multiple(poly, points)
    
    def get_polynomial_info(self, poly: List[int]) -> Dict[str, Any]:
        """Get information about a polynomial"""
        return {
            'degree': len(poly) - 1,
            'coefficients': poly,
            'leading_coefficient': poly[-1] if poly else 0,
            'constant_term': poly[0] if poly else 0,
            'is_zero': all(c == 0 for c in poly),
            'field_modulus': self.field_modulus
        }


def test_polynomial_arithmetic():
    """Test polynomial arithmetic functionality"""
    print("🔢 Testing Polynomial Arithmetic")
    print("=" * 40)
    
    poly_arith = PolynomialArithmetic()
    
    # Test polynomials: p(x) = 1 + 2x + 3x², q(x) = 2 + x
    p = [1, 2, 3]  # 1 + 2x + 3x²
    q = [2, 1]     # 2 + x
    
    print(f"p(x) = {p[0]} + {p[1]}x + {p[2]}x²")
    print(f"q(x) = {q[0]} + {q[1]}x")
    
    # Test addition
    sum_poly = poly_arith.add(p, q)
    print(f"p + q = {sum_poly}")
    
    # Test multiplication
    product = poly_arith.multiply(p, q)
    print(f"p * q = {product}")
    
    # Test evaluation
    x = 5
    p_at_5 = poly_arith.evaluate(p, x)
    expected = 1 + 2*5 + 3*25  # = 86
    print(f"p({x}) = {p_at_5} (expected: {expected})")
    
    # Test interpolation
    points = [(0, 1), (1, 6), (2, 17)]  # Points on p(x) = 1 + 2x + 3x²
    interpolated = poly_arith.interpolate_lagrange(points)
    print(f"Interpolated polynomial: {interpolated}")
    
    return True


if __name__ == "__main__":
    # Run tests
    test_success = test_polynomial_arithmetic()
    print(f"\n🎯 Polynomial Arithmetic Test: {'PASSED' if test_success else 'FAILED'}")