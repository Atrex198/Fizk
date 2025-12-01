"""
R1CS (Rank-1 Constraint System) Implementation
==============================================

A mathematically correct R1CS implementation for ZKP systems.

R1CS Definition:
- A constraint system where each constraint has form: (A·z) * (B·z) = (C·z)
- z = (1, x, w) where x are public inputs and w is the witness

This module provides:
1. Sparse matrix representation for A, B, C
2. Witness assignment and validation
3. Constraint satisfaction checking
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import hashlib


@dataclass
class SparseMatrix:
    """
    Sparse matrix representation using coordinate format.
    
    For R1CS, matrices are typically very sparse, so this is efficient.
    Format: rows[i] = {col_idx: coefficient}
    """
    num_rows: int
    num_cols: int
    rows: Dict[int, Dict[int, int]] = field(default_factory=dict)
    
    def set(self, row: int, col: int, val: int):
        """Set matrix entry M[row, col] = val"""
        if row not in self.rows:
            self.rows[row] = {}
        if val != 0:
            self.rows[row][col] = val
        elif col in self.rows[row]:
            del self.rows[row][col]
    
    def get(self, row: int, col: int) -> int:
        """Get matrix entry M[row, col]"""
        if row in self.rows and col in self.rows[row]:
            return self.rows[row][col]
        return 0
    
    def dot(self, vec: List[int], field_mod: int) -> List[int]:
        """Compute M · vec mod field_mod"""
        result = [0] * self.num_rows
        for row_idx in range(self.num_rows):
            if row_idx in self.rows:
                for col_idx, coeff in self.rows[row_idx].items():
                    if col_idx < len(vec):
                        result[row_idx] = (result[row_idx] + coeff * vec[col_idx]) % field_mod
        return result
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            'num_rows': self.num_rows,
            'num_cols': self.num_cols,
            'rows': {str(k): {str(kk): vv for kk, vv in v.items()} for k, v in self.rows.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SparseMatrix':
        """Deserialize from dictionary"""
        m = cls(data['num_rows'], data['num_cols'])
        m.rows = {int(k): {int(kk): vv for kk, vv in v.items()} for k, v in data['rows'].items()}
        return m


@dataclass
class R1CSInstance:
    """
    An R1CS instance (public part).
    
    Contains:
    - Constraint matrices A, B, C
    - Number of public inputs
    - Public input values x
    
    Satisfiability: ∃w such that (A·z)∘(B·z) = C·z where z = (1, x, w)
    """
    A: SparseMatrix
    B: SparseMatrix
    C: SparseMatrix
    num_public_inputs: int
    num_constraints: int
    num_variables: int  # Total = 1 + num_public + num_private
    public_inputs: List[int] = field(default_factory=list)
    
    def get_constraint_hash(self) -> str:
        """Get hash of constraint structure (for caching setup)"""
        data = f"{self.A.to_dict()}{self.B.to_dict()}{self.C.to_dict()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


@dataclass
class R1CSWitness:
    """
    An R1CS witness (private part).
    
    Contains the private witness values w.
    Combined with public inputs x: z = (1, x, w)
    """
    values: List[int]
    
    def get_full_assignment(self, public_inputs: List[int]) -> List[int]:
        """Get full assignment z = (1, x, w)"""
        return [1] + public_inputs + self.values


class R1CSBuilder:
    """
    Builder for R1CS constraint systems.
    
    Provides methods to add variables and constraints programmatically.
    """
    
    def __init__(self, field_mod: int):
        self.field_mod = field_mod
        self.num_public = 0
        self.num_private = 0
        self.constraints: List[Tuple[Dict[int, int], Dict[int, int], Dict[int, int]]] = []
        self.var_names: Dict[str, int] = {'ONE': 0}  # Variable 0 is always 1
        
    def add_public_input(self, name: str) -> int:
        """Add a public input variable, returns its index"""
        self.num_public += 1
        idx = self.num_public  # Public inputs start at index 1
        self.var_names[name] = idx
        return idx
    
    def add_private_variable(self, name: str) -> int:
        """Add a private witness variable, returns its index"""
        self.num_private += 1
        idx = self.num_public + self.num_private  # Private vars after public
        self.var_names[name] = idx
        return idx
    
    def get_var(self, name: str) -> int:
        """Get variable index by name"""
        return self.var_names[name]
    
    def add_constraint(self, a_terms: Dict[int, int], b_terms: Dict[int, int], c_terms: Dict[int, int]):
        """
        Add constraint: (Σ a_i * z_i) * (Σ b_j * z_j) = (Σ c_k * z_k)
        
        Args:
            a_terms: {var_idx: coefficient} for A row
            b_terms: {var_idx: coefficient} for B row
            c_terms: {var_idx: coefficient} for C row
        """
        self.constraints.append((a_terms, b_terms, c_terms))
    
    def add_multiplication_constraint(self, a_idx: int, b_idx: int, c_idx: int):
        """Add constraint: z[a] * z[b] = z[c]"""
        self.add_constraint({a_idx: 1}, {b_idx: 1}, {c_idx: 1})
    
    def add_addition_constraint(self, a_idx: int, b_idx: int, sum_idx: int):
        """Add constraint: z[a] + z[b] = z[sum] (encoded as (a+b)*1 = sum)"""
        self.add_constraint({a_idx: 1, b_idx: 1}, {0: 1}, {sum_idx: 1})  # 0 is ONE
    
    def add_constant_constraint(self, var_idx: int, constant: int):
        """Add constraint: z[var] = constant"""
        self.add_constraint({var_idx: 1}, {0: 1}, {0: constant})
    
    def add_linear_combination_constraint(
        self, 
        terms: List[Tuple[int, int]],  # [(var_idx, coeff), ...]
        result_idx: int
    ):
        """Add constraint: Σ coeff_i * z[var_i] = z[result]"""
        a_terms = {var_idx: coeff for var_idx, coeff in terms}
        self.add_constraint(a_terms, {0: 1}, {result_idx: 1})
    
    def build(self) -> R1CSInstance:
        """Build the R1CS instance"""
        num_vars = 1 + self.num_public + self.num_private
        num_constraints = len(self.constraints)
        
        A = SparseMatrix(num_constraints, num_vars)
        B = SparseMatrix(num_constraints, num_vars)
        C = SparseMatrix(num_constraints, num_vars)
        
        for row_idx, (a_terms, b_terms, c_terms) in enumerate(self.constraints):
            for col_idx, coeff in a_terms.items():
                A.set(row_idx, col_idx, coeff % self.field_mod)
            for col_idx, coeff in b_terms.items():
                B.set(row_idx, col_idx, coeff % self.field_mod)
            for col_idx, coeff in c_terms.items():
                C.set(row_idx, col_idx, coeff % self.field_mod)
        
        return R1CSInstance(
            A=A, B=B, C=C,
            num_public_inputs=self.num_public,
            num_constraints=num_constraints,
            num_variables=num_vars
        )


def check_r1cs_satisfaction(
    instance: R1CSInstance,
    witness: R1CSWitness,
    field_mod: int
) -> Tuple[bool, List[int]]:
    """
    Check if witness satisfies R1CS instance.
    
    Computes: (A·z) ∘ (B·z) - C·z for each constraint
    Returns (is_satisfied, error_vector)
    
    If is_satisfied is True, error_vector is all zeros.
    """
    z = witness.get_full_assignment(instance.public_inputs)
    
    # Compute A·z, B·z, C·z
    Az = instance.A.dot(z, field_mod)
    Bz = instance.B.dot(z, field_mod)
    Cz = instance.C.dot(z, field_mod)
    
    # Check (A·z) ∘ (B·z) = C·z for each constraint
    error_vector = []
    is_satisfied = True
    
    for i in range(instance.num_constraints):
        lhs = (Az[i] * Bz[i]) % field_mod
        rhs = Cz[i]
        error = (lhs - rhs) % field_mod
        error_vector.append(error)
        if error != 0:
            is_satisfied = False
    
    return is_satisfied, error_vector


def compute_hadamard_product(a: List[int], b: List[int], field_mod: int) -> List[int]:
    """Compute element-wise product a ∘ b"""
    return [(a[i] * b[i]) % field_mod for i in range(len(a))]


def compute_linear_combination(vectors: List[List[int]], coeffs: List[int], field_mod: int) -> List[int]:
    """Compute Σ coeffs[i] * vectors[i]"""
    if not vectors:
        return []
    result = [0] * len(vectors[0])
    for vec, coeff in zip(vectors, coeffs):
        for i in range(len(vec)):
            result[i] = (result[i] + coeff * vec[i]) % field_mod
    return result
