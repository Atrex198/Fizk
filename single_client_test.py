#!/usr/bin/env python3
"""
Single Client End-to-End Test
=============================

Test just one client connecting to server, doing training, and submitting proof.
This will help isolate the communication issue.
"""

import asyncio
import time
import logging
from phase3_production_communication import ProductionZKFLServer, ServerConfig
from phase3_production_client import ProductionZKFLClient, ClientConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_single_client():
    """Test single client proof submission"""
    print("🔍 SINGLE CLIENT INTEGRATION TEST")
    print("=" * 40)
    
    # Start server
    server_config = ServerConfig(
        host="localhost",
        port=8080,
        max_clients=5,
        enable_authentication=True
    )
    
    server = ProductionZKFLServer(server_config)
    server_task = asyncio.create_task(server.start_server())
    await asyncio.sleep(2)  # Let server start
    
    try:
        # Start single client
        client_config = ClientConfig(
            client_id="single_test_client",
            server_host="localhost", 
            server_port=8080,
            data_partition_id=0
        )
        
        client = ProductionZKFLClient(client_config)
        
        # Start client
        client_started = await client.start_client()
        if not client_started:
            print("❌ Client failed to start")
            return False
        
        print("✅ Client connected successfully")
        
        # Manually trigger a FL round
        print("🔄 Starting federated learning round...")
        
        # Server starts round with this client
        success = await server.start_new_round([client.config.client_id])
        if not success:
            print("❌ Failed to start FL round")
            return False
        
        print("✅ FL round started")
        
        # Wait for client to participate
        await asyncio.sleep(10)  # Give time for training and proof submission
        
        # Check server state
        if server.round_history:
            last_round = server.round_history[-1]  
            print(f"📊 Round completed:")
            print(f"  - Participants: {len(last_round.participants)}")
            print(f"  - Proofs received: {len(last_round.received_proofs)}")
            print(f"  - ZK aggregation: {'✅' if hasattr(last_round, 'zk_proof') and last_round.zk_proof else '❌'}")
            
            if len(last_round.received_proofs) > 0:
                print("✅ SUCCESS: Client submitted proof successfully!")
                return True
            else:
                print("❌ FAILURE: No proofs received")
                return False
        else:
            print("❌ FAILURE: No rounds completed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if 'client' in locals():
            await client.shutdown()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_single_client())
    if success:
        print("\n🎉 Single client test PASSED!")
    else:
        print("\n❌ Single client test FAILED!")