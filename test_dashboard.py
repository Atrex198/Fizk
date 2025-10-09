#!/usr/bin/env python3
"""
Test script for the ZKP FL Dashboard
===================================

This script tests the core functionality before launching the full dashboard.
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add current directory to path
sys.path.append('.')

async def test_basic_functionality():
    """Test basic FL functionality with both protocols"""
    
    print("🔧 Testing ZKP FL Dashboard Components")
    print("="*60)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from multi_protocol_zkp_fl import ZKPProtocolConfig, UnifiedFLConfig, MultiProtocolZKPFLSystem
        from zkp_fl_dashboard import FederatedDataGenerator
        print("   ✅ All imports successful")
        
        # Test data generation
        print("\n📊 Testing federated data generation...")
        client_data = FederatedDataGenerator.generate_heterogeneous_data(
            "synthetic", 3, "medium"
        )
        print(f"   ✅ Generated data for {len(client_data)} clients")
        for client_name, data in client_data.items():
            print(f"     {client_name}: {data['size']} samples, classes: {data['class_distribution']}")
        
        # Test Nova protocol
        print("\n🌟 Testing Nova IVC...")
        nova_config = UnifiedFLConfig(
            zkp_config=ZKPProtocolConfig(
                protocol_type='nova',
                enable_aggregation=True,
                security_level=80
            ),
            num_clients=2,
            num_rounds=1,
            local_epochs=2,  # Quick test
            dataset_name='synthetic',
            batch_size=16
        )
        
        fl_system_nova = MultiProtocolZKPFLSystem(nova_config)
        
        # Add clients
        for client_name, data in list(client_data.items())[:2]:  # Only first 2 clients
            fl_system_nova.add_client(
                client_id=client_name,
                X_data=data['X_train'],
                y_data=data['y_train']
            )
        
        print("   Running Nova experiment...")
        start_time = time.time()
        nova_results = await fl_system_nova.run_federated_learning()
        nova_time = time.time() - start_time
        
        print(f"   ✅ Nova completed in {nova_time:.2f}s")
        
        # Check proof storage
        nova_proof_dir = Path("proofs/nova")
        if nova_proof_dir.exists():
            nova_proof_files = list(nova_proof_dir.glob("**/*.pkl"))
            print(f"   💾 Nova proofs saved: {len(nova_proof_files)} files")
        
        # Test ProtoStar protocol
        print("\n⚡ Testing ProtoStar + ProtoGalaxy...")
        protostar_config = UnifiedFLConfig(
            zkp_config=ZKPProtocolConfig(
                protocol_type='protostar',
                enable_aggregation=True,
                security_level=128  # Use minimum required
            ),
            num_clients=2,
            num_rounds=1,
            local_epochs=2,  # Quick test
            dataset_name='synthetic',
            batch_size=16
        )
        
        fl_system_protostar = MultiProtocolZKPFLSystem(protostar_config)
        
        # Add clients
        for client_name, data in list(client_data.items())[:2]:  # Only first 2 clients
            fl_system_protostar.add_client(
                client_id=client_name,
                X_data=data['X_train'],
                y_data=data['y_train']
            )
        
        print("   Running ProtoStar experiment...")
        start_time = time.time()
        protostar_results = await fl_system_protostar.run_federated_learning()
        protostar_time = time.time() - start_time
        
        print(f"   ✅ ProtoStar completed in {protostar_time:.2f}s")
        
        # Check proof storage
        protostar_proof_dir = Path("proofs/protostar")
        if protostar_proof_dir.exists():
            protostar_proof_files = list(protostar_proof_dir.glob("**/*.pkl"))
            print(f"   💾 ProtoStar proofs saved: {len(protostar_proof_files)} files")
        
        # Summary
        print(f"\n🎯 Test Summary:")
        print(f"   Nova time: {nova_time:.2f}s")
        print(f"   ProtoStar time: {protostar_time:.2f}s")
        print(f"   Speedup: {max(nova_time, protostar_time) / min(nova_time, protostar_time):.1f}x")
        
        print(f"\n✅ All tests passed! Dashboard ready to use.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set quick test environment
    os.environ['QUICK_TEST'] = '1'
    
    # Run tests
    success = asyncio.run(test_basic_functionality())
    
    if success:
        print(f"\n🚀 Ready to launch dashboard!")
        print(f"   Run: streamlit run zkp_fl_dashboard.py")
    else:
        print(f"\n🔧 Please fix the issues above before launching dashboard")
        sys.exit(1)