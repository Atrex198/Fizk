#!/usr/bin/env python3
"""
R1CS (Rank-1 Constraint System) Implementation for Groth16
===========================================================

Implements the R1CS constraint system following the FL Circuit Encoding Standard.
Based on production_zkp_fl_complete.py standards.

R1CS Constraint: (A·z) * (B·z) = (C·z)
where z = [1, public_inputs, private_witness]

Author: ZKP-FL Framework
Version: 1.0.0
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
import json
from dataclasses import dataclass, field

# Import from standard (same as Protostar)
from py_ecc.bn128.bn128_curve import curve_order

logger = logging.getLogger(__name__)

@dataclass
class R1CSConstraint:
    """Single R1CS constraint"""
    A_coeffs: Dict[int, int]  # {variable_index: coefficient}
    B_coeffs: Dict[int, int]
    C_coeffs: Dict[int, int]
    constraint_type: str  # 'neural_network_computation' or 'aggregation_verification'


class R1CS:
    """
    Rank-1 Constraint System for Groth16
    
    Each constraint: (A·z) * (B·z) = (C·z)
    where z = [1, x₁, x₂, ..., xₙ] (witness vector)
    
    Standard from FL_CIRCUIT_ENCODING_STANDARD.md Section 6.2
    """
    
    def __init__(self, num_variables: int):
        """
        Initialize R1CS
        
        Args:
            num_variables: Total number of variables (including constant 1)
        """
        self.num_variables = num_variables
        self.num_constraints = 0
        
        # Constraint matrices (sparse representation)
        self.A: List[Dict[int, int]] = []  # Left coefficients
        self.B: List[Dict[int, int]] = []  # Right coefficients
        self.C: List[Dict[int, int]] = []  # Output coefficients
        
        # Variable assignments (witness)
        self.witness: List[int] = [1]  # Start with constant 1
        
        # Public inputs (subset of variables)
        # Index 0 is always the constant 1
        self.public_input_indices: List[int] = [0]
        
        # Variable name mapping (for debugging)
        self.variable_names: Dict[int, str] = {0: "ONE"}
        
        logger.info(f"R1CS initialized: {num_variables} variables")
    
    def add_constraint(
        self,
        A_coeffs: Dict[int, int],
        B_coeffs: Dict[int, int],
        C_coeffs: Dict[int, int],
        constraint_type: str = "neural_network_computation"
    ):
        """
        Add constraint: (Σ A_i * z_i) * (Σ B_i * z_i) = (Σ C_i * z_i)
        
        Standard from FL_CIRCUIT_ENCODING_STANDARD.md Section 6.2
        """
        # Validate input types
        if not isinstance(A_coeffs, dict) or not isinstance(B_coeffs, dict) or not isinstance(C_coeffs, dict):
            raise TypeError("Coefficients must be dictionaries")
        
        # Validate indices and values
        for coeffs_name, coeffs in [('A', A_coeffs), ('B', B_coeffs), ('C', C_coeffs)]:
            for var_idx, coeff in coeffs.items():
                # Check index bounds
                if not isinstance(var_idx, int):
                    raise TypeError(f"{coeffs_name}: Variable index must be integer, got {type(var_idx)}")
                
                if var_idx < 0:
                    raise ValueError(f"{coeffs_name}: Variable index {var_idx} cannot be negative")
                
                if var_idx >= self.num_variables:
                    raise ValueError(f"{coeffs_name}: Variable index {var_idx} >= num_variables ({self.num_variables})")
                
                # Check coefficient type
                if not isinstance(coeff, int):
                    raise TypeError(f"{coeffs_name}: Coefficient must be integer, got {type(coeff)}")
        
        # Add constraint
        self.A.append(A_coeffs.copy())
        self.B.append(B_coeffs.copy())
        self.C.append(C_coeffs.copy())
        self.num_constraints += 1
    
    def add_multiplication_constraint(
        self,
        a_var: int,
        b_var: int,
        c_var: int
    ):
        """
        Multiplication gate: z[a_var] * z[b_var] = z[c_var]
        
        From GROTH16_IMPLEMENTATION.md Section 2.1
        """
        self.add_constraint(
            A_coeffs={a_var: 1},
            B_coeffs={b_var: 1},
            C_coeffs={c_var: 1},
            constraint_type="neural_network_computation"
        )
    
    def add_addition_constraint(
        self,
        a_var: int,
        b_var: int,
        c_var: int
    ):
        """
        Addition gate: z[a_var] + z[b_var] = z[c_var]
        
        Represented as: (z[a_var] + z[b_var]) * 1 = z[c_var]
        
        From GROTH16_IMPLEMENTATION.md Section 2.1
        """
        self.add_constraint(
            A_coeffs={a_var: 1, b_var: 1},
            B_coeffs={0: 1},  # Multiply by constant 1
            C_coeffs={c_var: 1},
            constraint_type="neural_network_computation"
        )
    
    def add_constant_constraint(
        self,
        var: int,
        constant: int
    ):
        """
        Constant constraint: z[var] = constant
        
        Represented as: z[var] * 1 = constant
        
        From GROTH16_IMPLEMENTATION.md Section 2.1
        """
        # Mod constant into field
        constant_mod = constant % curve_order
        
        self.add_constraint(
            A_coeffs={var: 1},
            B_coeffs={0: 1},  # Multiply by constant 1
            C_coeffs={0: constant_mod},  # Constant term
            constraint_type="neural_network_computation"
        )
    
    def add_linear_combination_constraint(
        self,
        input_vars: List[int],
        input_coeffs: List[int],
        output_var: int
    ):
        """
        Linear combination: Σ(coeffs[i] * vars[i]) = output_var
        
        Useful for weight updates and aggregations
        """
        A_coeffs = {var: coeff for var, coeff in zip(input_vars, input_coeffs)}
        
        self.add_constraint(
            A_coeffs=A_coeffs,
            B_coeffs={0: 1},  # Multiply by 1
            C_coeffs={output_var: 1},
            constraint_type="neural_network_computation"
        )
    
    def set_witness(self, variable_index: int, value: int, name: Optional[str] = None):
        """
        Assign value to witness variable
        
        Standard from FL_CIRCUIT_ENCODING_STANDARD.md Section 4.2
        """
        # Validate inputs
        if not isinstance(variable_index, int):
            raise TypeError(f"Variable index must be integer, got {type(variable_index)}")
        
        if variable_index < 0:
            raise ValueError(f"Variable index cannot be negative: {variable_index}")
        
        if variable_index >= self.num_variables:
            raise ValueError(f"Variable index {variable_index} >= num_variables ({self.num_variables})")
        
        if not isinstance(value, int):
            raise TypeError(f"Witness value must be integer, got {type(value)}")
        
        # Extend witness if needed
        while len(self.witness) <= variable_index:
            self.witness.append(0)
        
        # Mod into field (standard from encoding)
        self.witness[variable_index] = value % curve_order
        
        # Store name if provided
        if name:
            self.variable_names[variable_index] = name
    
    def set_public_input(self, variable_index: int, value: int, name: Optional[str] = None):
        """
        Set a variable as public input and assign its value
        """
        if variable_index not in self.public_input_indices:
            self.public_input_indices.append(variable_index)
        
        self.set_witness(variable_index, value, name)
    
    def verify_constraint_satisfaction(self) -> bool:
        """
        Verify all constraints are satisfied by witness
        
        Returns True if ALL constraints are satisfied
        
        From GROTH16_IMPLEMENTATION.md Section 2.1
        """
        for i in range(self.num_constraints):
            # Compute A·z
            a_val = self._evaluate_linear_combination(self.A[i])
            # Compute B·z
            b_val = self._evaluate_linear_combination(self.B[i])
            # Compute C·z
            c_val = self._evaluate_linear_combination(self.C[i])
            
            # Check: (A·z) * (B·z) = (C·z) mod p
            if (a_val * b_val) % curve_order != c_val:
                logger.error(f"❌ Constraint {i} NOT satisfied")
                logger.error(f"   A·z = {a_val}")
                logger.error(f"   B·z = {b_val}")
                logger.error(f"   C·z = {c_val}")
                logger.error(f"   (A·z)*(B·z) = {(a_val * b_val) % curve_order}")
                return False
        
        logger.info(f"✅ All {self.num_constraints} constraints satisfied")
        return True
    
    def _evaluate_linear_combination(self, coeffs: Dict[int, int]) -> int:
        """
        Evaluate Σ coeff_i * witness[i]
        
        From GROTH16_IMPLEMENTATION.md Section 2.1
        """
        result = 0
        for var_idx, coeff in coeffs.items():
            if var_idx < len(self.witness):
                result += (coeff * self.witness[var_idx])
            else:
                logger.warning(f"Variable {var_idx} not in witness (len={len(self.witness)})")
        
        return result % curve_order
    
    def get_constraint_count(self) -> int:
        """Get total number of constraints"""
        return self.num_constraints
    
    def get_witness_vector(self) -> List[int]:
        """Get complete witness vector z = [1, public, private]"""
        return self.witness.copy()
    
    def get_public_inputs(self) -> List[int]:
        """Get public input values"""
        return [self.witness[i] for i in self.public_input_indices if i < len(self.witness)]
    
    def export_for_setup(self) -> Dict[str, Any]:
        """
        Export R1CS for trusted setup
        
        From GROTH16_IMPLEMENTATION.md Section 2.1
        """
        return {
            'num_variables': self.num_variables,
            'num_constraints': self.num_constraints,
            'A_matrix': self.A,
            'B_matrix': self.B,
            'C_matrix': self.C,
            'public_input_indices': self.public_input_indices,
            'variable_names': self.variable_names
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize R1CS to dictionary"""
        return {
            'num_variables': self.num_variables,
            'num_constraints': self.num_constraints,
            'constraints': [
                {
                    'A': self.A[i],
                    'B': self.B[i],
                    'C': self.C[i]
                }
                for i in range(self.num_constraints)
            ],
            'witness': self.witness,
            'public_input_indices': self.public_input_indices,
            'variable_names': self.variable_names
        }
    
    def save(self, filepath: str):
        """Save R1CS to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"💾 R1CS saved to {filepath}")


class R1CSBuilder:
    """
    Helper class to build R1CS incrementally
    
    Provides higher-level operations for circuit construction
    """
    
    def __init__(self):
        self.next_var_idx = 1  # 0 is reserved for constant 1
        self.r1cs: Optional[R1CS] = None
        self.variable_map: Dict[str, int] = {}
    
    def initialize(self, num_variables: int) -> R1CS:
        """Initialize R1CS with estimated variable count"""
        self.r1cs = R1CS(num_variables)
        return self.r1cs
    
    def allocate_variable(self, name: str) -> int:
        """Allocate a new variable with optional name"""
        if name in self.variable_map:
            return self.variable_map[name]
        
        var_idx = self.next_var_idx
        self.next_var_idx += 1
        self.variable_map[name] = var_idx
        
        if self.r1cs:
            self.r1cs.variable_names[var_idx] = name
        
        return var_idx
    
    def get_variable(self, name: str) -> Optional[int]:
        """Get variable index by name"""
        return self.variable_map.get(name)
    
    def add_multiplication(self, a: int, b: int, c: int):
        """Add multiplication constraint: a * b = c"""
        if self.r1cs:
            self.r1cs.add_multiplication_constraint(a, b, c)
    
    def add_addition(self, a: int, b: int, c: int):
        """Add addition constraint: a + b = c"""
        if self.r1cs:
            self.r1cs.add_addition_constraint(a, b, c)
    
    def add_constant(self, var: int, constant: int):
        """Add constant constraint: var = constant"""
        if self.r1cs:
            self.r1cs.add_constant_constraint(var, constant)
    
    def set_witness_value(self, name: str, value: int):
        """Set witness value by variable name"""
        if name in self.variable_map and self.r1cs:
            var_idx = self.variable_map[name]
            self.r1cs.set_witness(var_idx, value, name)
    
    def finalize(self) -> R1CS:
        """Finalize and return R1CS"""
        if not self.r1cs:
            raise ValueError("R1CS not initialized")
        
        logger.info(f"R1CS finalized: {self.r1cs.num_constraints} constraints, "
                   f"{self.next_var_idx} variables")
        
        return self.r1cs
