"""Unit tests for ZKP techniques."""

import pytest
import numpy as np
from src.zkp_techniques.stark import STARKWrapper
from src.zkp_techniques.groth16 import Groth16Wrapper
from src.zkp_techniques.mock_techniques import (
    PLONKWrapper, BulletproofsWrapper, Halo2Wrapper,
    ProtostarWrapper, zkSNARKWrapper, NovaWrapper
)


@pytest.fixture
def test_data():
    """Generate test data."""
    return {
        'public_inputs': [10, 10],
        'private_inputs': np.random.rand(10, 10),
        'circuit_description': 'matrix_multiplication'
    }


class TestSTARK:
    """Test STARK wrapper."""
    
    def test_setup(self):
        stark = STARKWrapper()
        setup_time = stark.setup(circuit_size=100)
        assert setup_time >= 0
        assert stark.is_setup
    
    def test_proof_generation(self, test_data):
        stark = STARKWrapper()
        stark.setup(100)
        
        result = stark.generate_proof(**test_data)
        
        assert result.proof is not None
        assert result.generation_time_ms > 0
        assert result.proof_size_bytes > 0
    
    def test_verification(self, test_data):
        stark = STARKWrapper()
        stark.setup(100)
        
        proof_result = stark.generate_proof(**test_data)
        verify_result = stark.verify_proof(proof_result.proof, test_data['public_inputs'])
        
        assert verify_result.is_valid
        assert verify_result.verification_time_ms > 0
    
    def test_properties(self):
        stark = STARKWrapper()
        assert not stark.requires_trusted_setup()
        assert stark.is_transparent()
        assert stark.is_post_quantum()


class TestGroth16:
    """Test Groth16 wrapper."""
    
    def test_setup_required(self, test_data):
        groth16 = Groth16Wrapper()
        
        with pytest.raises(RuntimeError):
            groth16.generate_proof(**test_data)
    
    def test_full_workflow(self, test_data):
        groth16 = Groth16Wrapper()
        groth16.setup(100)
        
        proof_result = groth16.generate_proof(**test_data)
        verify_result = groth16.verify_proof(proof_result.proof, test_data['public_inputs'])
        
        assert verify_result.is_valid
        assert proof_result.proof_size_bytes == 192  # Constant size
    
    def test_properties(self):
        groth16 = Groth16Wrapper()
        assert groth16.requires_trusted_setup()
        assert not groth16.is_transparent()
        assert not groth16.is_post_quantum()


@pytest.mark.parametrize("wrapper_class", [
    PLONKWrapper, BulletproofsWrapper, Halo2Wrapper,
    ProtostarWrapper, zkSNARKWrapper, NovaWrapper
])
class TestAllTechniques:
    """Test all ZKP techniques."""
    
    def test_basic_workflow(self, wrapper_class, test_data):
        wrapper = wrapper_class()
        wrapper.setup(100)
        
        proof_result = wrapper.generate_proof(**test_data)
        verify_result = wrapper.verify_proof(proof_result.proof, test_data['public_inputs'])
        
        assert proof_result.proof is not None
        assert verify_result.is_valid
