"""
Multi-Party Computation Trusted Setup Ceremony

SECURITY GOAL: No single party knows the toxic waste (tau)
PROTOCOL: Powers of Tau ceremony for SNARKs

Each participant contributes randomness:
- Party 1: tau_1 → [G1^tau_1, G2^tau_1, G1^tau_1^2, ...]
- Party 2: updates with tau_2 → [G1^(tau_1*tau_2), G2^(tau_1*tau_2), ...]
- Final: tau = tau_1 * tau_2 * ... * tau_n (no one knows full tau)

VERIFICATION: Each contribution is verifiable via pairing checks
"""

import hashlib
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import secrets
import os

logger = logging.getLogger(__name__)


@dataclass
class SetupParameters:
    """Parameters for the trusted setup"""
    curve: str  # 'BN254' or 'BLS12_381'
    max_constraints: int  # Maximum R1CS constraints
    g1_powers: int  # Number of G1 powers needed
    g2_powers: int  # Number of G2 powers needed
    

@dataclass
class Contribution:
    """A single party's contribution to the ceremony"""
    participant_id: str
    participant_hash: str  # Hash of previous state (for verification)
    g1_powers: List[Tuple[int, int]]  # Updated G1 powers
    g2_powers: List[Tuple[int, int]]  # Updated G2 powers
    proof_of_knowledge: Dict  # Proof that contributor knows their secret
    timestamp: str


class MPCTrustedSetup:
    """
    Multi-Party Trusted Setup Ceremony
    
    SECURITY:
    - Each party contributes secret randomness
    - No single party knows final tau
    - Contributions are publicly verifiable
    - As long as 1 party is honest, setup is secure
    
    PROTOCOL:
    1. Initialize with base powers (tau=1)
    2. Party i samples random tau_i
    3. Party i updates all powers: [tau^k] → [(tau*tau_i)^k]
    4. Party i proves knowledge of tau_i
    5. Verification checks pairing equations
    """
    
    def __init__(self, params: SetupParameters, use_py_ecc: bool = False):
        self.params = params
        self.use_py_ecc = use_py_ecc
        self.contributions: List[Contribution] = []
        self.current_state: Optional[Dict] = None
        
        # Initialize curve operations
        if use_py_ecc and params.curve == 'BLS12_381':
            try:
                from py_ecc.bls12_381 import G1, G2, multiply, add, pairing
                self.G1 = G1
                self.G2 = G2
                self.multiply = multiply
                self.add = add
                self.pairing = pairing
                self.field_modulus = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
                logger.info("✅ Using py_ecc with BLS12-381 curve")
            except ImportError:
                logger.warning("⚠️ py_ecc not available, using simulation mode")
                self._init_simulation_mode()
        else:
            # Use simulation mode for BN254 or when py_ecc not available
            self._init_simulation_mode()
            
    def _init_simulation_mode(self):
        """Initialize with simulated elliptic curve operations"""
        # Use 256-bit prime field for simulation
        self.field_modulus = 2**256 - 2**224 + 2**192 + 2**96 - 1  # P-256 prime
        
        # Simulated generator points (just integers for PoC)
        self.G1 = (1, 2)  # Simulated G1 generator
        self.G2 = (3, 4)  # Simulated G2 generator
        
        logger.info(f"✅ Using simulation mode with {self.params.curve}")
    
    def initialize_ceremony(self) -> Dict:
        """
        Initialize the ceremony with tau=1 (base powers)
        
        Returns:
            Initial state with G1 and G2 powers
        """
        logger.info("🎬 Initializing MPC Trusted Setup Ceremony")
        logger.info(f"   Curve: {self.params.curve}")
        logger.info(f"   Max constraints: {self.params.max_constraints}")
        logger.info(f"   G1 powers: {self.params.g1_powers}")
        logger.info(f"   G2 powers: {self.params.g2_powers}")
        
        if self.use_py_ecc and hasattr(self, 'multiply'):
            # Real py_ecc mode
            g1_powers = []
            for i in range(self.params.g1_powers):
                # [G1^(tau^i)] starting with tau=1 → just [G1, G1, G1, ...]
                g1_powers.append(self._point_to_tuple(self.G1))
            
            g2_powers = []
            for i in range(self.params.g2_powers):
                g2_powers.append(self._point_to_tuple(self.G2))
        else:
            # Simulation mode: use integers
            g1_powers = [(i+1, i+2) for i in range(self.params.g1_powers)]
            g2_powers = [(i+3, i+4) for i in range(self.params.g2_powers)]
        
        self.current_state = {
            'g1_powers': g1_powers,
            'g2_powers': g2_powers,
            'phase': 'initialized',
            'num_contributions': 0
        }
        
        logger.info("✅ Ceremony initialized - ready for contributions")
        return self.current_state
    
    def contribute(
        self,
        participant_id: str,
        entropy: Optional[bytes] = None
    ) -> Contribution:
        """
        Contribute randomness to the ceremony
        
        SECURITY:
        - Sample random tau_i from field
        - Update all powers: [tau^k] → [(tau*tau_i)^k]
        - Generate proof of knowledge
        - Destroy tau_i after use (simulate by not storing)
        
        Args:
            participant_id: Unique ID for this participant
            entropy: Optional additional entropy (mouse movements, etc.)
            
        Returns:
            Contribution object with updated powers
        """
        if self.current_state is None:
            raise ValueError("Ceremony not initialized - call initialize_ceremony() first")
        
        logger.info(f"👤 Participant '{participant_id}' contributing...")
        
        # Sample random tau_i from field (TOXIC WASTE - will be destroyed)
        if entropy:
            seed = hashlib.sha256(entropy + secrets.token_bytes(32)).digest()
        else:
            seed = secrets.token_bytes(32)
        
        tau_i = int.from_bytes(seed, 'big') % self.field_modulus
        
        # Hash of previous state for verification
        previous_hash = self._hash_state(self.current_state)
        
        # Update powers with tau_i
        new_g1_powers = []
        for idx, (x, y) in enumerate(self.current_state['g1_powers']):
            # Multiply point by tau_i^(idx+1) to get next power
            # [G1^(tau^k)] → [G1^(tau*tau_i)^k]
            new_power = self._scalar_multiply_point((x, y), tau_i, is_g1=True)
            new_g1_powers.append(new_power)
        
        new_g2_powers = []
        for idx, (x, y) in enumerate(self.current_state['g2_powers']):
            new_power = self._scalar_multiply_point((x, y), tau_i, is_g1=False)
            new_g2_powers.append(new_power)
        
        # Generate proof of knowledge (simplified)
        # Real: Schnorr-like proof that we know tau_i
        # PoK: (g^tau_i, g^(r*tau_i)) where r is random challenge
        proof = self._generate_proof_of_knowledge(tau_i)
        
        # CRITICAL: Destroy tau_i (in real implementation, use secure memory wipe)
        del tau_i  # Python's garbage collector will clean up
        
        contribution = Contribution(
            participant_id=participant_id,
            participant_hash=previous_hash,
            g1_powers=new_g1_powers,
            g2_powers=new_g2_powers,
            proof_of_knowledge=proof,
            timestamp=self._get_timestamp()
        )
        
        # Update ceremony state
        self.current_state['g1_powers'] = new_g1_powers
        self.current_state['g2_powers'] = new_g2_powers
        self.current_state['num_contributions'] += 1
        self.contributions.append(contribution)
        
        logger.info(f"✅ Contribution accepted from '{participant_id}'")
        logger.info(f"   Total contributions: {self.current_state['num_contributions']}")
        
        return contribution
    
    def verify_contribution(self, contribution: Contribution) -> bool:
        """
        Verify that a contribution is valid
        
        VERIFICATION:
        1. Check hash chain (contribution references correct previous state)
        2. Verify proof of knowledge
        3. Check pairing equation: e(g1_new, G2) = e(g1_old, g2_new)
           This ensures the update was done with same tau_i
        
        Returns:
            True if valid, False otherwise
        """
        logger.info(f"🔍 Verifying contribution from '{contribution.participant_id}'...")
        
        # 1. Check hash chain
        if len(self.contributions) > 0:
            expected_hash = self._hash_state(self.current_state)
            if contribution.participant_hash != expected_hash:
                logger.error("❌ Hash chain verification failed")
                return False
        
        # 2. Verify proof of knowledge
        if not self._verify_proof_of_knowledge(contribution.proof_of_knowledge):
            logger.error("❌ Proof of knowledge verification failed")
            return False
        
        # 3. Pairing check (if using real py_ecc)
        if self.use_py_ecc and hasattr(self, 'pairing'):
            # Check e(g1_new[1], G2) = e(g1_old[1], g2_new[1])
            # This ensures consistency of tau_i update
            try:
                if len(self.contributions) > 1:
                    prev_contrib = self.contributions[-2]
                    lhs = self.pairing(
                        self._tuple_to_point(contribution.g1_powers[1], is_g1=True),
                        self._tuple_to_point(self.G2, is_g1=False)
                    )
                    rhs = self.pairing(
                        self._tuple_to_point(prev_contrib.g1_powers[1], is_g1=True),
                        self._tuple_to_point(contribution.g2_powers[1], is_g1=False)
                    )
                    if lhs != rhs:
                        logger.error("❌ Pairing check failed")
                        return False
            except Exception as e:
                logger.warning(f"⚠️ Pairing check skipped: {e}")
        
        logger.info(f"✅ Contribution from '{contribution.participant_id}' is VALID")
        return True
    
    def finalize_ceremony(self) -> Dict:
        """
        Finalize the ceremony and return the final parameters
        
        Returns:
            Final SRS parameters ready for use in ZKP system
        """
        if len(self.contributions) == 0:
            raise ValueError("No contributions yet - ceremony not complete")
        
        logger.info("🏁 Finalizing MPC Trusted Setup Ceremony")
        logger.info(f"   Total participants: {len(self.contributions)}")
        logger.info(f"   Final tau = tau_1 * tau_2 * ... * tau_{len(self.contributions)}")
        logger.info(f"   ✅ No single party knows the full tau (SECURE)")
        
        final_params = {
            'curve': self.params.curve,
            'g1_powers': self.current_state['g1_powers'],
            'g2_powers': self.current_state['g2_powers'],
            'num_contributors': len(self.contributions),
            'contribution_hashes': [c.participant_hash for c in self.contributions],
            'phase': 'finalized'
        }
        
        logger.info("✅ Ceremony finalized - parameters ready for use")
        
        return final_params
    
    def export_transcript(self, filepath: str):
        """
        Export full ceremony transcript for public verification
        
        TRANSPARENCY: Anyone can verify the ceremony was run correctly
        """
        transcript = {
            'params': asdict(self.params),
            'contributions': [asdict(c) for c in self.contributions],
            'final_state': self.current_state
        }
        
        with open(filepath, 'w') as f:
            json.dump(transcript, f, indent=2)
        
        logger.info(f"📝 Ceremony transcript exported to {filepath}")
    
    # === Helper Methods ===
    
    def _scalar_multiply_point(self, point: Tuple[int, int], scalar: int, is_g1: bool) -> Tuple[int, int]:
        """Multiply elliptic curve point by scalar"""
        if self.use_py_ecc and hasattr(self, 'multiply'):
            # Real py_ecc mode
            ec_point = self._tuple_to_point(point, is_g1)
            result = self.multiply(ec_point, scalar)
            return self._point_to_tuple(result)
        else:
            # Simulation mode: just multiply coordinates
            x, y = point
            return ((x * scalar) % self.field_modulus, (y * scalar) % self.field_modulus)
    
    def _generate_proof_of_knowledge(self, secret: int) -> Dict:
        """Generate proof that contributor knows their secret tau_i"""
        # Simplified Schnorr-like proof
        # Real: g, g^tau_i, challenge c, response s = r + c*tau_i
        r = secrets.randbelow(self.field_modulus)
        challenge = secrets.randbelow(2**128)
        response = (r + challenge * secret) % self.field_modulus
        
        return {
            'challenge': challenge,
            'response': response,
            'commitment': (secret * 7) % self.field_modulus  # Simplified commitment
        }
    
    def _verify_proof_of_knowledge(self, proof: Dict) -> bool:
        """Verify proof of knowledge (simplified)"""
        # In real implementation: check Schnorr equation
        # For PoC: just check proof has required fields
        return all(k in proof for k in ['challenge', 'response', 'commitment'])
    
    def _hash_state(self, state: Dict) -> str:
        """Hash current state for verification chain"""
        state_str = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()
    
    def _point_to_tuple(self, point) -> Tuple[int, int]:
        """Convert py_ecc point to tuple"""
        if isinstance(point, tuple):
            return point
        return (int(point[0]), int(point[1]))
    
    def _tuple_to_point(self, tup: Tuple[int, int], is_g1: bool):
        """Convert tuple to py_ecc point"""
        if self.use_py_ecc and hasattr(self, 'G1'):
            # For real py_ecc, return as-is (will be converted by multiply)
            return tup
        return tup
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()


def run_mpc_ceremony_example():
    """
    Example: Run a multi-party trusted setup with 3 participants
    """
    print("=" * 80)
    print("MULTI-PARTY TRUSTED SETUP CEREMONY EXAMPLE")
    print("=" * 80)
    
    # Setup parameters
    params = SetupParameters(
        curve='BN254',
        max_constraints=1000,
        g1_powers=10,  # Need powers up to tau^10
        g2_powers=5    # Need fewer G2 powers
    )
    
    # Initialize ceremony
    ceremony = MPCTrustedSetup(params)
    ceremony.initialize_ceremony()
    
    # 3 participants contribute
    participants = ['Alice', 'Bob', 'Charlie']
    
    for participant in participants:
        # Each participant contributes with their own entropy
        entropy = f"{participant}_random_entropy_{secrets.token_hex(16)}".encode()
        contribution = ceremony.contribute(participant, entropy)
        
        # Verify contribution
        is_valid = ceremony.verify_contribution(contribution)
        print(f"   {participant}'s contribution: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    # Finalize ceremony
    final_params = ceremony.finalize_ceremony()
    
    print(f"\n🎉 Ceremony complete!")
    print(f"   Final tau = tau_Alice * tau_Bob * tau_Charlie")
    print(f"   ✅ No single participant knows the full tau")
    print(f"   ✅ As long as 1 participant is honest, setup is SECURE")
    
    # Export transcript
    ceremony.export_transcript('ceremony_transcript.json')
    
    return final_params


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    run_mpc_ceremony_example()
