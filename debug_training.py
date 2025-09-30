#!/usr/bin/env python3
"""
Quick test to isolate the training pipeline issue
"""

import asyncio
import numpy as np
from phase3_production_client import ProductionZKFLClient, ClientConfig
from real_ml_trainer import TrainingConfig

async def test_training_pipeline():
    """Test the training pipeline in isolation"""
    
    print("🔍 Testing training pipeline in isolation...")
    
    try:
        # Create client config
        client_config = ClientConfig(
            client_id="test_client",
            server_host="localhost",
            server_port=8080,
            data_partition_id=0,
            training_config=TrainingConfig(local_epochs=1, batch_size=32)
        )
        
        # Create client
        client = ProductionZKFLClient(client_config)
        
        print("📊 Loading data partition...")
        await client._load_data_partition()
        
        print(f"✅ Data loaded: {client.data_metadata}")
        
        print("🎯 Testing local training...")
        
        # Create fake global model
        fake_global_model = {
            'model_parameters': {},
            'round_number': 1
        }
        
        # Set round number for proof generation
        client.current_round = 1
        
        # Test training
        training_result = await client._perform_local_training(fake_global_model)
        
        print(f"✅ Training successful: {training_result}")
        
        print("🔐 Testing ZK proof generation...")
        proof_data = await client._generate_zk_proof(training_result)
        
        print(f"✅ Proof generation successful!")
        print(f"   Proof keys: {list(proof_data.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Training pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_training_pipeline())
    if success:
        print("\n🎉 Training pipeline working correctly!")
    else:
        print("\n💥 Training pipeline needs fixing!")