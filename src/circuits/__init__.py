"""Circuit representations for ZKP systems.

This module provides abstractions for different circuit types used in ZKP systems:
- R1CS (Rank-1 Constraint System) for SNARKs
- AIR (Algebraic Intermediate Representation) for STARKs  
- Arithmetic Circuits for various proof systems
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
import numpy as np
from dataclasses import dataclass, field


@dataclass
class Variable:
    """A variable in a circuit."""
    name: str
    value: Any = None
    is_public: bool = False


@dataclass
class Constraint:
    """A constraint in the circuit."""
    a_vars: List[Tuple[int, Any]]  # (variable_index, coefficient)
    b_vars: List[Tuple[int, Any]]
    c_vars: List[Tuple[int, Any]]
    
    def evaluate(self, assignments: List[Any]) -> bool:
        """Check if constraint is satisfied."""
        a = sum(coeff * assignments[idx] for idx, coeff in self.a_vars)
        b = sum(coeff * assignments[idx] for idx, coeff in self.b_vars)
        c = sum(coeff * assignments[idx] for idx, coeff in self.c_vars)
        return a * b == c


class Circuit(ABC):
    """Abstract base class for circuits."""
    
    def __init__(self):
        self.variables: List[Variable] = []
        self.constraints: List[Constraint] = []
        self.public_inputs: List[int] = []
        self.private_inputs: List[int] = []
    
    @abstractmethod
    def compile(self) -> Any:
        """Compile circuit to backend-specific format."""
        pass
    
    @abstractmethod
    def generate_witness(self, inputs: Dict[str, Any]) -> List[Any]:
        """Generate witness (variable assignments) from inputs."""
        pass
    
    def add_variable(self, name: str, is_public: bool = False) -> int:
        """Add a variable and return its index."""
        idx = len(self.variables)
        self.variables.append(Variable(name, is_public=is_public))
        if is_public:
            self.public_inputs.append(idx)
        else:
            self.private_inputs.append(idx)
        return idx
    
    def add_constraint(self, a_vars, b_vars, c_vars):
        """Add a constraint: (sum a) * (sum b) = (sum c)."""
        self.constraints.append(Constraint(a_vars, b_vars, c_vars))


class R1CS(Circuit):
    """R1CS (Rank-1 Constraint System) for SNARKs.
    
    R1CS represents circuits as a system of constraints of the form:
    (A · z) * (B · z) = (C · z)
    
    where z is the witness vector.
    """
    
    def __init__(self, field_size: int = None):
        super().__init__()
        # Use a large prime for the field (BN254 curve order)
        self.field_size = field_size or 21888242871839275222246405745257275088548364400416034343698204186575808495617
    
    def compile(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compile to constraint matrices A, B, C."""
        n_vars = len(self.variables)
        n_constraints = len(self.constraints)
        
        A = np.zeros((n_constraints, n_vars), dtype=object)
        B = np.zeros((n_constraints, n_vars), dtype=object)
        C = np.zeros((n_constraints, n_vars), dtype=object)
        
        for i, constraint in enumerate(self.constraints):
            for var_idx, coeff in constraint.a_vars:
                A[i, var_idx] = coeff
            for var_idx, coeff in constraint.b_vars:
                B[i, var_idx] = coeff
            for var_idx, coeff in constraint.c_vars:
                C[i, var_idx] = coeff
        
        return A, B, C
    
    def generate_witness(self, inputs: Dict[str, Any]) -> List[int]:
        """Generate witness from inputs."""
        witness = [0] * len(self.variables)
        
        # Always add constant 1 at index 0
        witness[0] = 1
        
        # Fill in known values
        for var in self.variables:
            if var.name in inputs:
                idx = self.variables.index(var)
                witness[idx] = int(inputs[var.name]) % self.field_size
        
        return witness
    
    @staticmethod
    def from_matrix_multiplication(a_matrix: np.ndarray, b_matrix: np.ndarray) -> 'R1CS':
        """Create R1CS for matrix multiplication.
        
        For C = A * B, we need to prove that for each element c[i,j]:
        c[i,j] = sum_k(a[i,k] * b[k,j])
        """
        circuit = R1CS()
        
        # Add constant one
        circuit.add_variable("one", is_public=True)
        
        rows_a, cols_a = a_matrix.shape
        rows_b, cols_b = b_matrix.shape
        
        if cols_a != rows_b:
            raise ValueError("Incompatible matrix dimensions")
        
        # Add variables for all matrix elements
        a_vars = []
        for i in range(rows_a):
            row = []
            for j in range(cols_a):
                var_idx = circuit.add_variable(f"a_{i}_{j}", is_public=False)
                row.append(var_idx)
            a_vars.append(row)
        
        b_vars = []
        for i in range(rows_b):
            row = []
            for j in range(cols_b):
                var_idx = circuit.add_variable(f"b_{i}_{j}", is_public=False)
                row.append(var_idx)
            b_vars.append(row)
        
        c_vars = []
        for i in range(rows_a):
            row = []
            for j in range(cols_b):
                var_idx = circuit.add_variable(f"c_{i}_{j}", is_public=True)
                row.append(var_idx)
            c_vars.append(row)
        
        # Add constraints for each output element
        for i in range(rows_a):
            for j in range(cols_b):
                # c[i,j] = sum_k(a[i,k] * b[k,j])
                # We need multiple constraints for the sum
                # For simplicity, we'll add constraints for each multiplication
                for k in range(cols_a):
                    # Intermediate variable for a[i,k] * b[k,j]
                    temp_var = circuit.add_variable(f"temp_{i}_{j}_{k}", is_public=False)
                    
                    # Constraint: a[i,k] * b[k,j] = temp
                    circuit.add_constraint(
                        [(a_vars[i][k], 1)],  # a coefficient
                        [(b_vars[k][j], 1)],  # b coefficient
                        [(temp_var, 1)]       # c coefficient
                    )
        
        return circuit


class ArithmeticCircuit(Circuit):
    """Arithmetic circuit for PLONK and similar systems.
    
    Uses custom gates with addition and multiplication operations.
    """
    
    def __init__(self):
        super().__init__()
        self.gates: List[Dict[str, Any]] = []
    
    def add_mul_gate(self, a_idx: int, b_idx: int, c_idx: int):
        """Add multiplication gate: c = a * b."""
        self.gates.append({
            'type': 'mul',
            'inputs': [a_idx, b_idx],
            'output': c_idx
        })
    
    def add_add_gate(self, a_idx: int, b_idx: int, c_idx: int):
        """Add addition gate: c = a + b."""
        self.gates.append({
            'type': 'add',
            'inputs': [a_idx, b_idx],
            'output': c_idx
        })
    
    def compile(self) -> List[Dict[str, Any]]:
        """Return gate list."""
        return self.gates
    
    def generate_witness(self, inputs: Dict[str, Any]) -> List[Any]:
        """Generate witness by evaluating gates."""
        witness = [None] * len(self.variables)
        
        # Set input values
        for var in self.variables:
            if var.name in inputs:
                idx = self.variables.index(var)
                witness[idx] = inputs[var.name]
        
        # Evaluate gates
        for gate in self.gates:
            a_idx, b_idx = gate['inputs']
            c_idx = gate['output']
            
            if gate['type'] == 'mul':
                witness[c_idx] = witness[a_idx] * witness[b_idx]
            elif gate['type'] == 'add':
                witness[c_idx] = witness[a_idx] + witness[b_idx]
        
        return witness


class AIRCircuit:
    """Algebraic Intermediate Representation for STARKs.
    
    AIR represents computation as state transitions with polynomial constraints.
    """
    
    def __init__(self, trace_length: int, num_registers: int):
        self.trace_length = trace_length
        self.num_registers = num_registers
        self.transition_constraints = []
        self.boundary_constraints = []
    
    def add_transition_constraint(self, constraint_fn):
        """Add a constraint on state transitions.
        
        Args:
            constraint_fn: Function that takes (current_state, next_state) and returns constraint polynomial
        """
        self.transition_constraints.append(constraint_fn)
    
    def add_boundary_constraint(self, register: int, step: int, value: Any):
        """Add constraint on specific register value at specific step."""
        self.boundary_constraints.append({
            'register': register,
            'step': step,
            'value': value
        })
    
    def generate_trace(self, initial_state: List[Any], computation_fn) -> np.ndarray:
        """Generate execution trace.
        
        Args:
            initial_state: Initial register values
            computation_fn: Function that computes next state from current state
            
        Returns:
            Trace matrix of shape (trace_length, num_registers)
        """
        trace = np.zeros((self.trace_length, self.num_registers), dtype=object)
        trace[0] = initial_state
        
        for i in range(self.trace_length - 1):
            trace[i + 1] = computation_fn(trace[i])
        
        return trace
    
    @staticmethod
    def from_matrix_multiplication(a_matrix: np.ndarray, b_matrix: np.ndarray) -> 'AIRCircuit':
        """Create AIR circuit for matrix multiplication."""
        rows_a, cols_a = a_matrix.shape
        rows_b, cols_b = b_matrix.shape
        
        # Trace length = number of steps to compute all elements
        trace_length = rows_a * cols_b * cols_a + 1
        
        # Registers: accumulator, indices, intermediate values
        num_registers = 10
        
        circuit = AIRCircuit(trace_length, num_registers)
        
        # Add transition constraints for computation steps
        def transition(current, next_state):
            # Polynomial constraint: next = current + delta
            return next_state - current
        
        circuit.add_transition_constraint(transition)
        
        return circuit
