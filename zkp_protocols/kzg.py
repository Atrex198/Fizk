"""
KZG Polynomial Commitment Scheme
================================

A mathematically correct implementation of KZG (Kate-Zaverucha-Goldberg) 
polynomial commitments using py_ecc.

KZG Overview:
- Setup: Generate SRS = ([τ^i]₁, [τ]₂) for random τ
- Commit: C = [p(τ)]₁ = Σ pᵢ[τⁱ]₁
- Open: π = [(p(τ) - p(z))/(τ - z)]₁
- Verify: e(C - [p(z)]₁, [1]₂) = e(π, [τ - z]₂)

Security: Based on hardness of discrete log in pairing-friendly groups.
"""

import secrets
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import hashlib

# Import py_ecc - REQUIRED, no fallback
from py_ecc.bn128.bn128_curve import (
    G1, G2, multiply, add, neg, Z1, Z2, 
    curve_order, FQ, FQ2, is_on_curve, b, b2
)
from py_ecc.bn128.bn128_pairing import pairing


# Type aliases for clarity
G1Point = Tuple[FQ, FQ]  # Point on G1
G2Point = Tuple[FQ2, FQ2]  # Point on G2


@dataclass
class KZGParams:
    """
    KZG Structured Reference String (SRS).
    
    Contains:
    - g1_powers: [G₁, τG₁, τ²G₁, ..., τⁿG₁]
    - g2_powers: [G₂, τG₂] (only need τG₂ for verification)
    - max_degree: Maximum polynomial degree supported
    """
    g1_powers: List[G1Point]
    g2_powers: List[G2Point]
    max_degree: int
    
    def to_dict(self) -> Dict:
        """Serialize SRS (for storage/transmission)"""
        def point_to_list(p):
            if p is None or p == Z1 or p == Z2:
                return None
            if isinstance(p[0], FQ):
                return [str(p[0].n), str(p[1].n)]
            elif isinstance(p[0], FQ2):
                return [[str(p[0].coeffs[0]), str(p[0].coeffs[1])],
                        [str(p[1].coeffs[0]), str(p[1].coeffs[1])]]
            return None
        
        return {
            'g1_powers': [point_to_list(p) for p in self.g1_powers],
            'g2_powers': [point_to_list(p) for p in self.g2_powers],
            'max_degree': self.max_degree
        }


@dataclass
class KZGCommitment:
    """A polynomial commitment [p(τ)]₁"""
    point: G1Point
    degree: int  # Degree of committed polynomial
    
    def is_valid(self) -> bool:
        """Check if commitment is valid G1 point"""
        if self.point is None or self.point == Z1:
            return False
        try:
            return is_on_curve(self.point, b)
        except:
            return False
    
    def to_dict(self) -> Dict:
        """Serialize commitment"""
        if self.point is None or self.point == Z1:
            return {'point': None, 'degree': self.degree, 'valid': False}
        return {
            'point': [str(self.point[0].n), str(self.point[1].n)],
            'degree': self.degree,
            'valid': True
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KZGCommitment':
        """Deserialize commitment"""
        if data.get('point') is None:
            return cls(point=Z1, degree=data.get('degree', 0))
        coords = data['point']
        point = (FQ(int(coords[0])), FQ(int(coords[1])))
        return cls(point=point, degree=data.get('degree', 0))


@dataclass
class KZGOpening:
    """
    KZG opening proof.
    
    Proves that p(z) = v for committed polynomial p.
    π = [(p(τ) - v)/(τ - z)]₁
    """
    proof_point: G1Point  # The proof π
    evaluation_point: int  # z
    evaluation: int  # v = p(z)
    
    def is_valid(self) -> bool:
        """Check if proof point is valid"""
        if self.proof_point is None or self.proof_point == Z1:
            return False
        try:
            return is_on_curve(self.proof_point, b)
        except:
            return False
    
    def to_dict(self) -> Dict:
        """Serialize opening proof"""
        if self.proof_point is None or self.proof_point == Z1:
            return {
                'proof_point': None,
                'evaluation_point': str(self.evaluation_point),
                'evaluation': str(self.evaluation),
                'valid': False
            }
        return {
            'proof_point': [str(self.proof_point[0].n), str(self.proof_point[1].n)],
            'evaluation_point': str(self.evaluation_point),
            'evaluation': str(self.evaluation),
            'valid': True
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KZGOpening':
        """Deserialize opening proof"""
        if data.get('proof_point') is None:
            return cls(
                proof_point=Z1,
                evaluation_point=int(data['evaluation_point']),
                evaluation=int(data['evaluation'])
            )
        coords = data['proof_point']
        point = (FQ(int(coords[0])), FQ(int(coords[1])))
        return cls(
            proof_point=point,
            evaluation_point=int(data['evaluation_point']),
            evaluation=int(data['evaluation'])
        )


class KZGScheme:
    """
    KZG Polynomial Commitment Scheme.
    
    Provides:
    - setup(): Generate SRS
    - commit(polynomial): Create commitment
    - open(polynomial, point): Create opening proof
    - verify(commitment, opening): Verify opening proof
    """
    
    def __init__(self, params: Optional[KZGParams] = None):
        self.params = params
        self.field_mod = curve_order
    
    def setup(self, max_degree: int, toxic_waste: Optional[int] = None) -> KZGParams:
        """
        Generate KZG SRS.
        
        SECURITY WARNING: In production, use MPC ceremony to generate SRS.
        The toxic waste τ must be destroyed after setup!
        
        Args:
            max_degree: Maximum polynomial degree to support
            toxic_waste: τ value (if None, generates randomly)
        
        Returns:
            KZGParams containing the SRS
        """
        # Generate or use provided tau
        if toxic_waste is None:
            tau = secrets.randbelow(curve_order - 1) + 1  # τ ∈ [1, p-1]
        else:
            tau = toxic_waste % curve_order
            if tau == 0:
                tau = 1
        
        # Generate G1 powers: [G₁, τG₁, τ²G₁, ..., τⁿG₁]
        g1_powers = []
        tau_power = 1
        for i in range(max_degree + 1):
            g1_powers.append(multiply(G1, tau_power))
            tau_power = (tau_power * tau) % curve_order
        
        # Generate G2 powers: [G₂, τG₂]
        g2_powers = [G2, multiply(G2, tau)]
        
        self.params = KZGParams(
            g1_powers=g1_powers,
            g2_powers=g2_powers,
            max_degree=max_degree
        )
        
        # NOTE: In real system, tau would be destroyed here
        # We return params but tau should never be stored
        
        return self.params
    
    def commit(self, coefficients: List[int]) -> KZGCommitment:
        """
        Commit to polynomial p(x) = Σ cᵢxⁱ.
        
        Computes: C = [p(τ)]₁ = Σ cᵢ[τⁱ]₁
        
        Args:
            coefficients: [c₀, c₁, ..., cₙ] where p(x) = c₀ + c₁x + ... + cₙxⁿ
        
        Returns:
            KZGCommitment
        """
        if self.params is None:
            raise RuntimeError("Must call setup() first")
        
        if len(coefficients) > len(self.params.g1_powers):
            raise ValueError(f"Polynomial degree {len(coefficients)-1} exceeds max {self.params.max_degree}")
        
        # Compute C = Σ cᵢ[τⁱ]₁
        commitment = None
        for i, coeff in enumerate(coefficients):
            coeff_mod = coeff % curve_order
            if coeff_mod == 0:
                continue
            
            term = multiply(self.params.g1_powers[i], coeff_mod)
            
            if commitment is None:
                commitment = term
            else:
                commitment = add(commitment, term)
        
        # Handle zero polynomial
        if commitment is None:
            commitment = Z1
        
        return KZGCommitment(point=commitment, degree=len(coefficients) - 1)
    
    def evaluate(self, coefficients: List[int], point: int) -> int:
        """
        Evaluate polynomial at point: p(z).
        
        Args:
            coefficients: Polynomial coefficients
            point: Evaluation point z
        
        Returns:
            p(z) mod curve_order
        """
        result = 0
        point_power = 1
        for coeff in coefficients:
            result = (result + coeff * point_power) % curve_order
            point_power = (point_power * point) % curve_order
        return result
    
    def open(self, coefficients: List[int], point: int) -> KZGOpening:
        """
        Create opening proof for p(z) = v.
        
        Computes quotient polynomial q(x) = (p(x) - v) / (x - z)
        and returns π = [q(τ)]₁
        
        Args:
            coefficients: Polynomial coefficients
            point: Evaluation point z
        
        Returns:
            KZGOpening proof
        """
        if self.params is None:
            raise RuntimeError("Must call setup() first")
        
        # Evaluate p(z)
        evaluation = self.evaluate(coefficients, point)
        
        # Compute quotient polynomial q(x) = (p(x) - v) / (x - z)
        # Using polynomial division
        quotient_coeffs = self._compute_quotient(coefficients, point, evaluation)
        
        # Commit to quotient: π = [q(τ)]₁
        proof_commitment = self.commit(quotient_coeffs)
        
        return KZGOpening(
            proof_point=proof_commitment.point,
            evaluation_point=point,
            evaluation=evaluation
        )
    
    def _compute_quotient(self, coefficients: List[int], z: int, v: int) -> List[int]:
        """
        Compute quotient q(x) = (p(x) - v) / (x - z).
        
        Using synthetic division.
        """
        n = len(coefficients)
        if n == 0:
            return [0]
        
        # p(x) - v: subtract v from constant term
        adjusted = [coefficients[0] - v] + coefficients[1:]
        adjusted = [c % curve_order for c in adjusted]
        
        # Synthetic division by (x - z)
        # Result has degree n-1
        quotient = [0] * (n - 1) if n > 1 else [0]
        
        if n > 1:
            quotient[-1] = adjusted[-1]
            for i in range(n - 2, 0, -1):
                quotient[i - 1] = (adjusted[i] + z * quotient[i]) % curve_order
        
        return quotient
    
    def verify(self, commitment: KZGCommitment, opening: KZGOpening) -> bool:
        """
        Verify KZG opening proof using pairing equation.
        
        Verification equation:
        e(C - [v]₁, [1]₂) = e(π, [τ]₂ - [z]₂)
        
        Equivalently:
        e(C - [v]₁, [1]₂) · e(-π, [τ - z]₂) = 1
        
        Args:
            commitment: The polynomial commitment
            opening: The opening proof
        
        Returns:
            True if proof is valid
        """
        if self.params is None:
            raise RuntimeError("Must call setup() first")
        
        if not commitment.is_valid():
            return False
        
        if not opening.is_valid():
            return False
        
        try:
            # C - [v]₁
            v_G1 = multiply(G1, opening.evaluation % curve_order)
            C_minus_v = add(commitment.point, neg(v_G1))
            
            # [τ]₂ - [z]₂
            z_G2 = multiply(G2, opening.evaluation_point % curve_order)
            tau_minus_z_G2 = add(self.params.g2_powers[1], neg(z_G2))
            
            # Pairing check: e(C - v·G₁, G₂) = e(π, [τ - z]₂)
            lhs = pairing(self.params.g2_powers[0], C_minus_v)  # e(C - v·G₁, G₂)
            rhs = pairing(tau_minus_z_G2, opening.proof_point)  # e(π, [τ - z]₂)
            
            return lhs == rhs
            
        except Exception as e:
            print(f"KZG verification error: {e}")
            return False
    
    def batch_verify(
        self, 
        commitments: List[KZGCommitment], 
        openings: List[KZGOpening]
    ) -> bool:
        """
        Batch verify multiple opening proofs.
        
        Uses random linear combination for efficiency.
        """
        if len(commitments) != len(openings):
            return False
        
        if len(commitments) == 0:
            return True
        
        if len(commitments) == 1:
            return self.verify(commitments[0], openings[0])
        
        # Generate random coefficients for batching
        random_coeffs = [secrets.randbelow(curve_order) for _ in commitments]
        
        # Combine: Σ rᵢ(Cᵢ - vᵢG₁)
        combined_C_minus_v = None
        for i, (comm, opening) in enumerate(zip(commitments, openings)):
            v_G1 = multiply(G1, opening.evaluation % curve_order)
            C_minus_v = add(comm.point, neg(v_G1))
            scaled = multiply(C_minus_v, random_coeffs[i])
            
            if combined_C_minus_v is None:
                combined_C_minus_v = scaled
            else:
                combined_C_minus_v = add(combined_C_minus_v, scaled)
        
        # Combine proofs: Σ rᵢπᵢ (with appropriate scaling for different z values)
        # For simplicity, verify individually if z values differ
        z_values = set(o.evaluation_point for o in openings)
        if len(z_values) > 1:
            # Different evaluation points - verify individually
            return all(self.verify(c, o) for c, o in zip(commitments, openings))
        
        # Same z for all - can batch
        z = openings[0].evaluation_point
        z_G2 = multiply(G2, z % curve_order)
        tau_minus_z_G2 = add(self.params.g2_powers[1], neg(z_G2))
        
        combined_proof = None
        for i, opening in enumerate(openings):
            scaled_proof = multiply(opening.proof_point, random_coeffs[i])
            if combined_proof is None:
                combined_proof = scaled_proof
            else:
                combined_proof = add(combined_proof, scaled_proof)
        
        # Batch pairing check
        lhs = pairing(self.params.g2_powers[0], combined_C_minus_v)
        rhs = pairing(tau_minus_z_G2, combined_proof)
        
        return lhs == rhs


def create_kzg_scheme(max_degree: int = 1024) -> KZGScheme:
    """Factory function to create and setup KZG scheme"""
    scheme = KZGScheme()
    scheme.setup(max_degree)
    return scheme
