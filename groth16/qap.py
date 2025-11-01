#!/usr/bin/env python3
"""
QAP (Quadratic Arithmetic Program) Implementation
==================================================

Transforms R1CS constraints into QAP polynomials for Groth16.

From Groth16 paper: "On the Size of Pairing-based Non-interactive Arguments" (2016)

Author: ZKP-FL Framework
Version: 1.0.0
"""

import logging
from typing import List, Dict, Tuple
from py_ecc.bn128.bn128_curve import curve_order

logger = logging.getLogger(__name__)


class QAP:
    """
    Quadratic Arithmetic Program
    
    Transforms R1CS (Rank-1 Constraint System) into polynomial form:
    - R1CS: (A·z) * (B·z) = (C·z)
    - QAP: (Σ a_i·u_i(x)) · (Σ a_i·v_i(x)) = (Σ a_i·w_i(x)) + h(x)·t(x)
    
    Where:
    - u_i(x), v_i(x), w_i(x) are QAP polynomials for variable i
    - h(x) is the quotient polynomial
    - t(x) is the target polynomial
    """
    
    def __init__(self, r1cs_A: List[Dict[int, int]], 
                 r1cs_B: List[Dict[int, int]],
                 r1cs_C: List[Dict[int, int]],
                 num_variables: int):
        """
        Initialize QAP from R1CS matrices
        
        Args:
            r1cs_A: A matrix (list of sparse dicts)
            r1cs_B: B matrix (list of sparse dicts)
            r1cs_C: C matrix (list of sparse dicts)
            num_variables: Total number of variables
        """
        self.A = r1cs_A
        self.B = r1cs_B
        self.C = r1cs_C
        self.num_variables = num_variables
        self.num_constraints = len(r1cs_A)
        
        # QAP polynomials (evaluated at points)
        self.u_polys = None  # List of polynomials for A
        self.v_polys = None  # List of polynomials for B
        self.w_polys = None  # List of polynomials for C
        self.t_poly = None   # Target polynomial
        
        logger.info(f"QAP initialized: {self.num_constraints} constraints, {self.num_variables} variables")
    
    def construct_polynomials(self):
        """
        Construct QAP polynomials from R1CS using Lagrange interpolation
        
        For each variable i, we create polynomials u_i(x), v_i(x), w_i(x) that:
        - u_i(r_j) = A[j][i] (coefficient of variable i in constraint j)
        - v_i(r_j) = B[j][i]
        - w_i(r_j) = C[j][i]
        
        Where r_j are evaluation points (typically r_j = j+1)
        """
        logger.info("Constructing QAP polynomials via Lagrange interpolation...")
        
        # Define evaluation points: r_j = j+1 for j in [0, m-1]
        # This gives us points [1, 2, 3, ..., m]
        self.eval_points = list(range(1, self.num_constraints + 1))
        
        # For each variable, construct its polynomials
        self.u_polys = []
        self.v_polys = []
        self.w_polys = []
        
        for var_idx in range(self.num_variables):
            # Extract column var_idx from each matrix
            a_column = [self.A[j].get(var_idx, 0) for j in range(self.num_constraints)]
            b_column = [self.B[j].get(var_idx, 0) for j in range(self.num_constraints)]
            c_column = [self.C[j].get(var_idx, 0) for j in range(self.num_constraints)]
            
            # Create Lagrange interpolating polynomials
            # Store as coefficient list [a_0, a_1, a_2, ...] for a_0 + a_1*x + a_2*x^2 + ...
            u_poly = self._lagrange_interpolation(self.eval_points, a_column)
            v_poly = self._lagrange_interpolation(self.eval_points, b_column)
            w_poly = self._lagrange_interpolation(self.eval_points, c_column)
            
            self.u_polys.append(u_poly)
            self.v_polys.append(v_poly)
            self.w_polys.append(w_poly)
        
        # Construct target polynomial t(x) = (x-r_1)(x-r_2)...(x-r_m)
        self.t_poly = self._construct_target_polynomial()
        
        logger.info(f"✅ QAP polynomials constructed")
        logger.info(f"   Polynomial degree: {len(self.u_polys[0]) - 1}")
        logger.info(f"   Target polynomial degree: {len(self.t_poly) - 1}")
    
    def _lagrange_interpolation(self, points: List[int], values: List[int]) -> List[int]:
        """
        Lagrange polynomial interpolation in finite field
        
        Given points x_0, x_1, ..., x_n and values y_0, y_1, ..., y_n,
        construct polynomial P(x) such that P(x_i) = y_i
        
        Returns polynomial as coefficient list [a_0, a_1, ..., a_d]
        """
        n = len(points)
        if n == 0:
            return [0]
        
        # Initialize result polynomial (starts as zero)
        result = [0] * n
        
        # For each point, compute its Lagrange basis polynomial
        for i in range(n):
            if values[i] == 0:
                continue  # Skip if value is zero
            
            # Compute L_i(x) = Π_{j≠i} (x - x_j) / (x_i - x_j)
            basis = [1]  # Start with polynomial "1"
            
            denominator = 1
            for j in range(n):
                if i == j:
                    continue
                
                # Multiply basis by (x - x_j)
                basis = self._poly_multiply(basis, [-points[j], 1])
                
                # Accumulate denominator: (x_i - x_j)
                denominator = (denominator * (points[i] - points[j])) % curve_order
            
            # Compute 1/denominator in finite field
            denom_inv = pow(denominator, -1, curve_order)
            
            # Scale basis by y_i / denominator
            scale = (values[i] * denom_inv) % curve_order
            basis = [((coeff * scale) % curve_order) for coeff in basis]
            
            # Add to result
            result = self._poly_add(result, basis)
        
        return result
    
    def _poly_add(self, p1: List[int], p2: List[int]) -> List[int]:
        """Add two polynomials in finite field"""
        max_len = max(len(p1), len(p2))
        result = [0] * max_len
        
        for i in range(len(p1)):
            result[i] = (result[i] + p1[i]) % curve_order
        
        for i in range(len(p2)):
            result[i] = (result[i] + p2[i]) % curve_order
        
        # Remove leading zeros
        while len(result) > 1 and result[-1] == 0:
            result.pop()
        
        return result
    
    def _poly_multiply(self, p1: List[int], p2: List[int]) -> List[int]:
        """Multiply two polynomials in finite field"""
        if not p1 or not p2:
            return [0]
        
        result = [0] * (len(p1) + len(p2) - 1)
        
        for i in range(len(p1)):
            for j in range(len(p2)):
                result[i + j] = (result[i + j] + p1[i] * p2[j]) % curve_order
        
        return result
    
    def _construct_target_polynomial(self) -> List[int]:
        """
        Construct target polynomial t(x) = (x-r_1)(x-r_2)...(x-r_m)
        
        This polynomial has roots at all evaluation points
        """
        result = [1]  # Start with constant polynomial "1"
        
        for point in self.eval_points:
            # Multiply by (x - point)
            result = self._poly_multiply(result, [-point, 1])
        
        return result
    
    def evaluate_polynomial(self, poly: List[int], x: int) -> int:
        """
        Evaluate polynomial at point x in finite field
        
        P(x) = a_0 + a_1*x + a_2*x^2 + ... + a_n*x^n
        """
        result = 0
        x_power = 1
        
        for coeff in poly:
            result = (result + coeff * x_power) % curve_order
            x_power = (x_power * x) % curve_order
        
        return result
    
    def evaluate_at_tau(self, tau: int) -> Tuple[List[int], List[int], List[int]]:
        """
        Evaluate all QAP polynomials at secret point τ
        
        Returns: (u_at_tau, v_at_tau, w_at_tau)
        where each is a list of evaluations for all variables
        """
        if not self.u_polys:
            raise ValueError("QAP polynomials not constructed. Call construct_polynomials() first.")
        
        u_at_tau = [self.evaluate_polynomial(poly, tau) for poly in self.u_polys]
        v_at_tau = [self.evaluate_polynomial(poly, tau) for poly in self.v_polys]
        w_at_tau = [self.evaluate_polynomial(poly, tau) for poly in self.w_polys]
        
        return u_at_tau, v_at_tau, w_at_tau
    
    def compute_quotient_polynomial(self, witness: List[int]) -> List[int]:
        """
        Compute quotient polynomial h(x) such that:
        (Σ a_i·u_i(x)) · (Σ a_i·v_i(x)) - (Σ a_i·w_i(x)) = h(x)·t(x)
        
        Args:
            witness: Variable assignments [a_0, a_1, ..., a_n]
        
        Returns:
            h(x) as coefficient list
        """
        if not self.u_polys:
            raise ValueError("QAP polynomials not constructed")
        
        # Compute A(x) = Σ a_i·u_i(x)
        A_poly = [0]
        for i, a_i in enumerate(witness):
            if i < len(self.u_polys) and a_i != 0:
                scaled = [(coeff * a_i) % curve_order for coeff in self.u_polys[i]]
                A_poly = self._poly_add(A_poly, scaled)
        
        # Compute B(x) = Σ a_i·v_i(x)
        B_poly = [0]
        for i, a_i in enumerate(witness):
            if i < len(self.v_polys) and a_i != 0:
                scaled = [(coeff * a_i) % curve_order for coeff in self.v_polys[i]]
                B_poly = self._poly_add(B_poly, scaled)
        
        # Compute C(x) = Σ a_i·w_i(x)
        C_poly = [0]
        for i, a_i in enumerate(witness):
            if i < len(self.w_polys) and a_i != 0:
                scaled = [(coeff * a_i) % curve_order for coeff in self.w_polys[i]]
                C_poly = self._poly_add(C_poly, scaled)
        
        # Compute P(x) = A(x)·B(x) - C(x)
        AB_poly = self._poly_multiply(A_poly, B_poly)
        P_poly = self._poly_add(AB_poly, [(-c % curve_order) for c in C_poly])
        
        # Compute h(x) = P(x) / t(x)
        h_poly = self._poly_divide(P_poly, self.t_poly)
        
        return h_poly
    
    def _poly_divide(self, dividend: List[int], divisor: List[int]) -> List[int]:
        """
        Polynomial division in finite field
        
        Returns quotient q(x) such that dividend = q(x)·divisor + remainder
        """
        # Validate inputs
        if not divisor or all(c == 0 for c in divisor):
            raise ValueError("Division by zero polynomial")
        
        if not dividend:
            return [0]
        
        # Make copies
        remainder = dividend[:]
        divisor_cleaned = divisor[:]
        
        # Remove leading zeros from divisor
        while len(divisor_cleaned) > 1 and divisor_cleaned[-1] == 0:
            divisor_cleaned.pop()
        
        # Check if divisor is constant zero after cleaning
        if len(divisor_cleaned) == 1 and divisor_cleaned[0] == 0:
            raise ValueError("Division by zero polynomial")
        
        # Remove leading zeros from dividend
        while len(remainder) > 1 and remainder[-1] == 0:
            remainder.pop()
        
        # If dividend degree < divisor degree, quotient is 0
        if len(remainder) < len(divisor_cleaned):
            return [0]
        
        divisor_lead = divisor_cleaned[-1]
        
        # Check if leading coefficient is invertible
        if divisor_lead == 0:
            raise ValueError("Leading coefficient of divisor is zero")
        
        try:
            divisor_lead_inv = pow(divisor_lead, -1, curve_order)
        except ValueError as e:
            raise ValueError(f"Cannot invert leading coefficient {divisor_lead}: {e}")
        
        quotient = []
        
        while len(remainder) >= len(divisor_cleaned) and any(c != 0 for c in remainder):
            # Compute leading coefficient of quotient
            lead_coeff = remainder[-1]
            q_coeff = (lead_coeff * divisor_lead_inv) % curve_order
            
            quotient.append(q_coeff)
            
            # Subtract q_coeff * divisor from remainder
            for i in range(len(divisor_cleaned)):
                idx = len(remainder) - len(divisor_cleaned) + i
                remainder[idx] = (remainder[idx] - q_coeff * divisor_cleaned[i]) % curve_order
            
            # Remove leading term
            remainder.pop()
        
        quotient.reverse()
        return quotient if quotient else [0]
