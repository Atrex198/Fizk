#!/usr/bin/env python3
"""
Debug proof transmission between client and server
"""

import asyncio
import json
from phase3_production_client import ProductionZKFLClient, ClientConfig
from real_ml_trainer import TrainingResult

async def test_proof_generation():
    """Test proof generation and serialization"""
    print("🔍 Testing proof generation...")
    
    client_config = ClientConfig(
        client_id="debug_client",
        server_host="localhost",
        server_port=8080,
        data_partition_id=0
    )
    
    client = ProductionZKFLClient(client_config)
    
    # Load data and initialize
    await client._load_data_partition()
    client.current_round = 1
    
    # Get actual model parameters by creating a small model
    import torch
    dummy_model = client.ml_trainer.model
    model_params = {name: param.clone() for name, param in dummy_model.named_parameters()}
    param_updates = {name: torch.randn_like(param) * 0.01 for name, param in model_params.items()}
    
    # Create a realistic training result
    training_result = TrainingResult(
        initial_loss=0.7,
        final_loss=0.5,
        initial_accuracy=0.6,
        final_accuracy=0.8,
        epochs_completed=5,
        training_time=2.0,
        model_parameters=model_params,
        parameter_updates=param_updates,
        gradient_norms=[0.1, 0.05, 0.02],
        convergence_achieved=True
    )
    
    # Generate proof
    proof_data = await client._generate_zk_proof(training_result)
    
    print(f"Generated proof keys: {list(proof_data.keys())}")
    print(f"Proof type: {type(proof_data['proof'])}")
    
    # Try to serialize to JSON to test
    try:
        json_str = json.dumps(proof_data)
        print("✅ JSON serialization successful")
        print(f"JSON size: {len(json_str)} bytes")
        
        # Parse back to verify
        parsed = json.loads(json_str)
        print("✅ JSON parsing successful")
        
        # Check proof structure
        if 'proof' in parsed and isinstance(parsed['proof'], dict):
            print(f"✅ Proof is dict with keys: {list(parsed['proof'].keys())}")
        else:
            print(f"❌ Proof structure issue: {type(parsed.get('proof'))}")
            
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_proof_generation())