"""
Protostar IVC Implementation for Zero-Knowledge Federated Learning
Provides incremental verifiable computation for FL training rounds
NOW WITH REAL CRYPTOGRAPHIC IMPLEMENTATION
"""

import json
import numpy as np
import torch
from typing import Dict, List, Optional, Tuple
import logging
import hashlib
from collections import defaultdict

# Import the real cryptographic implementation
from real_protostar_ivc import RealProtostarIVC

logger = logging.getLogger(__name__)

class ProtostarIVC:
    """
    Protostar IVC Wrapper - Now uses REAL cryptographic implementation
    
    This class now delegates to RealProtostarIVC which provides actual
    cryptographic proofs with R1CS constraints, polynomial commitments,
    and proper folding scheme from the Protostar paper.
    """
    
    def __init__(self):
        """Initialize with real cryptographic Protostar IVC"""
        # Use the real implementation instead of mock
        self.real_ivc = RealProtostarIVC(trusted_setup_size=512)
        
        # Keep compatibility fields for existing code
        self.accumulator = None
        self.rounds_folded = 0
        self.accumulated_weights = {}
        self.verification_history = []
        
        logger.info("✅ Protostar IVC initialized with REAL cryptographic implementation")
        
    def initialize_accumulator(self, initial_weights: Dict[str, torch.Tensor], 
                              round_number: int = 1) -> Dict:
        """
        Initialize the Protostar IVC accumulator with the first FL round
        NOW USING REAL CRYPTOGRAPHIC IMPLEMENTATION
        
        Args:
            initial_weights: Model weights from first training round
            round_number: FL round number (should be 1 for initialization)
            
        Returns:
            Dictionary containing REAL cryptographic proof with R1CS constraints
        """
        try:
            logger.info(f"🔧 Initializing REAL Protostar IVC with cryptographic proofs")
            
            # Delegate to real implementation
            result = self.real_ivc.initialize_accumulator(initial_weights, round_number)
            
            # Update compatibility fields
            self.rounds_folded = self.real_ivc.rounds_folded
            self.accumulator = {
                "real_cryptographic_proof": True,
                "r1cs_constraints": result["metadata"]["r1cs_constraints"],
                "polynomial_commitments": len(self.real_ivc.accumulated_commitments),
                "accumulator_state": result["proof"]["accumulator_commitment"]
            }
            
            # Update verification history
            self.verification_history.append({
                "round": round_number,
                "method": "REAL_CRYPTOGRAPHIC_R1CS", 
                "constraints": result["metadata"]["r1cs_constraints"],
                "commitment": result["proof"]["accumulator_commitment"]
            })
            
            logger.info(f"✅ REAL Protostar IVC initialized: {result['metadata']['r1cs_constraints']} R1CS constraints")
            return result
            
        except Exception as e:
            logger.error(f"Real IVC initialization failed: {e}")
            raise
    
    def fold_round(self, new_weights: Dict[str, torch.Tensor], 
                   round_number: int) -> Dict:
        """
        Fold a new FL training round into the existing accumulator
        NOW USING REAL CRYPTOGRAPHIC FOLDING
        
        Args:
            new_weights: Model weights from new training round
            round_number: FL round number being folded in
            
        Returns:
            Dictionary containing REAL cryptographic proof with updated accumulator
        """
        try:
            logger.info(f"🔧 Folding round {round_number} using REAL Protostar cryptography")
            
            # Delegate to real implementation
            result = self.real_ivc.fold_round(new_weights, round_number)
            
            # Update compatibility fields
            self.rounds_folded = self.real_ivc.rounds_folded
            self.accumulator = {
                "real_cryptographic_proof": True,
                "r1cs_constraints": result["metadata"]["r1cs_constraints"],
                "polynomial_commitments": len(self.real_ivc.accumulated_commitments),
                "accumulator_state": result["proof"]["accumulator_commitment"],
                "folding_challenge": result["proof"]["folding_challenge"],
                "error_term": result["proof"]["error_term"]
            }
            
            # Update verification history  
            self.verification_history.append({
                "round": round_number,
                "method": "REAL_CRYPTOGRAPHIC_FOLDING",
                "constraints": result["metadata"]["r1cs_constraints"],
                "commitment": result["proof"]["accumulator_commitment"],
                "challenge": result["proof"]["folding_challenge"]
            })
            
            logger.info(f"✅ REAL folding complete: round {round_number}, {result['metadata']['r1cs_constraints']} constraints")
            return result
            
        except Exception as e:
            logger.error(f"Real folding failed: {e}")
            raise
    
    def verify_accumulator(self, proof_data: bytes) -> bool:
        """
        Verify the current accumulator state using REAL cryptographic verification
        
        Args:
            proof_data: Serialized proof data
            
        Returns:
            Boolean indicating REAL cryptographic verification result
        """
        try:
            logger.info("🔧 Performing REAL cryptographic verification")
            
            # Delegate to real implementation
            result = self.real_ivc.verify_accumulator(proof_data)
            
            if result:
                logger.info(f"✅ REAL cryptographic verification passed ({self.real_ivc.rounds_folded} rounds)")
            else:
                logger.error("❌ REAL cryptographic verification failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Real verification failed: {e}")
            return False
    
    def export_final_weights(self) -> Dict[str, torch.Tensor]:
        """
        Export the final accumulated weights back to PyTorch format
        FROM REAL CRYPTOGRAPHIC ACCUMULATOR
        
        Returns:
            Dictionary of accumulated model weights
        """
        try:
            logger.info("🔧 Exporting weights from REAL cryptographic accumulator")
            
            # Delegate to real implementation
            torch_weights = self.real_ivc.export_final_weights()
            
            logger.info(f"✅ Exported accumulated weights from {self.real_ivc.rounds_folded} real cryptographic rounds")
            return torch_weights
            
        except Exception as e:
            logger.error(f"Real weight export failed: {e}")
            raise
    
    def get_accumulator_summary(self) -> Dict:
        """Get summary of current REAL cryptographic accumulator state"""
        if self.real_ivc is None or self.real_ivc.accumulator_instance is None:
            return {"status": "uninitialized"}
        
        # Get real implementation summary
        real_summary = self.real_ivc.get_accumulator_summary()
        
        # Add compatibility fields
        real_summary.update({
            "verification_history_entries": len(self.verification_history),
            "cryptographic_implementation": "REAL_PROTOSTAR_IVC",
            "mock_implementation": False
        })
        
        return real_summary
        
        return real_summary
    
    # ============= COMPATIBILITY METHODS =============
    # These provide backward compatibility for existing code
    
    def _weights_to_field_elements(self, weights: Dict[str, torch.Tensor]) -> Dict[str, List]:
        """Compatibility method - delegates to real implementation"""
        return self.real_ivc._weights_to_field_elements(weights)
    
    def _serialize_accumulator_state(self) -> str:
        """Compatibility method - gets real proof data"""
        if self.real_ivc and self.real_ivc.accumulator_instance:
            return self.real_ivc._generate_accumulator_proof()
        else:
            return json.dumps({"status": "uninitialized"})
    
    # ============= LEGACY METHODS (NO LONGER USED) =============
    # These are kept for compatibility but do nothing since we use real crypto
    
    def _compute_weight_commitments(self, weights: Dict[str, List]) -> List[str]:
        """Legacy method - real commitments now handled by RealProtostarIVC"""
        logger.warning("Using legacy method - real commitments handled by cryptographic implementation")
        return ["REAL_CRYPTOGRAPHIC_COMMITMENT"]
    
    def _fold_weights(self, new_weights: Dict[str, List]):
        """Legacy method - real folding now handled by RealProtostarIVC"""
        logger.warning("Using legacy method - real folding handled by cryptographic implementation")
        pass
    
    def _generate_challenge(self, weights: Dict[str, List], round_num: int) -> str:
        """Legacy method - real challenges now handled by RealProtostarIVC"""
        logger.warning("Using legacy method - real challenges handled by cryptographic implementation")
        return "REAL_CRYPTOGRAPHIC_CHALLENGE"