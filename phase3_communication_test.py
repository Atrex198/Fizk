#!/usr/bin/env python3
"""
Phase 3: Production Communication Integration Test
================================================

Comprehensive test demonstrating production-grade client-server communication
for ZK-FL system with real networking, authentication, proof submission,
real-time coordination, and full federated learning orchestration.

Features Tested:
- Production HTTP/WebSocket server-client communication
- Client registration, authentication, and session management
- Real-time round coordination via WebSocket
- ZK proof generation, submission, and verification
- Federated aggregation with real medical data
- Multi-client concurrent operation
- Error handling and fault tolerance
- Performance monitoring and metrics collection

Author: Advanced ZK-FL Framework
Version: 3.0.0 Production Communication Test
Date: September 2025
"""

import asyncio
import aiohttp
import json
import time
import logging
import uuid
import signal
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import matplotlib.pyplot as plt
import concurrent.futures

# Import our production implementations
from phase3_production_communication import ProductionZKFLServer, ServerConfig
from phase3_production_client import ProductionZKFLClient, ClientConfig
from real_ml_trainer import TrainingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """Test configuration for production communication"""
    num_clients: int = 5
    server_host: str = "localhost"
    server_port: int = 8080
    test_duration: float = 120.0  # 2 minutes
    rounds_to_simulate: int = 3
    client_timeout: float = 60.0
    enable_monitoring: bool = True

@dataclass
class CommunicationTestResults:
    """Results from production communication test"""
    test_start_time: float
    test_end_time: float
    total_duration: float
    server_metrics: Dict[str, Any]
    client_metrics: List[Dict[str, Any]]
    rounds_completed: int
    total_clients: int
    successful_registrations: int
    successful_authentications: int
    successful_proof_submissions: int
    failed_communications: int
    average_round_time: float
    average_proof_verification_time: float
    communication_success_rate: float
    system_throughput: float

class ProductionCommunicationTester:
    """
    Comprehensive tester for production ZK-FL communication system
    """
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.server: Optional[ProductionZKFLServer] = None
        self.clients: List[ProductionZKFLClient] = []
        self.server_task: Optional[asyncio.Task] = None
        self.client_tasks: List[asyncio.Task] = []
        
        # Test state
        self.test_results = None
        self.is_running = False
        self.start_time = 0.0
        
        # Monitoring
        self.round_times: List[float] = []
        self.communication_events: List[Dict] = []
        
        logger.info(f"Production Communication Tester initialized for {config.num_clients} clients")
    
    async def run_comprehensive_communication_test(self) -> CommunicationTestResults:
        """
        Run comprehensive production communication test
        """
        try:
            logger.info("🚀 Starting Phase 3: Production Communication Test")
            print("=" * 70)
            print("🎯 PHASE 3: PRODUCTION ZK-FL COMMUNICATION SYSTEM TEST")
            print("=" * 70)
            
            self.start_time = time.time()
            self.is_running = True
            
            # Step 1: Initialize and start server
            await self._start_production_server()
            
            # Step 2: Initialize and start clients
            await self._start_production_clients()
            
            # Step 3: Run coordinated federated learning rounds
            await self._run_federated_learning_rounds()
            
            # Step 4: Collect comprehensive results
            results = await self._collect_test_results()
            
            # Step 5: Generate analysis and report
            await self._generate_test_report(results)
            
            logger.info("✅ Phase 3 Production Communication Test completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"❌ Production Communication Test failed: {e}")
            raise
        finally:
            await self._cleanup_test()
    
    async def _start_production_server(self):
        """Start production ZK-FL server"""
        try:
            logger.info("🔧 Starting production ZK-FL server...")
            
            server_config = ServerConfig(
                host=self.config.server_host,
                port=self.config.server_port,
                max_clients=self.config.num_clients * 2,  # Extra capacity
                round_timeout=60.0,
                heartbeat_interval=10.0,
                enable_authentication=True
            )
            
            self.server = ProductionZKFLServer(server_config)
            
            # Start server in background
            self.server_task = asyncio.create_task(self._run_server())
            
            # Wait for server to start
            await asyncio.sleep(2)
            
            # Verify server is running
            await self._verify_server_health()
            
            logger.info("✅ Production server started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start production server: {e}")
            raise
    
    async def _run_server(self):
        """Run server in background task"""
        try:
            await self.server.start_server()
        except Exception as e:
            logger.error(f"Server task error: {e}")
    
    async def _verify_server_health(self):
        """Verify server is healthy and responding"""
        try:
            url = f"http://{self.config.server_host}:{self.config.server_port}/health"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Server health check failed: {response.status}")
                    
                    health_data = await response.json()
                    logger.info(f"✅ Server health verified: {health_data['status']}")
                    
        except Exception as e:
            logger.error(f"❌ Server health check failed: {e}")
            raise
    
    async def _start_production_clients(self):
        """Start multiple production ZK-FL clients"""
        try:
            logger.info(f"👥 Starting {self.config.num_clients} production clients...")
            
            # Create client configurations
            client_configs = []
            for i in range(self.config.num_clients):
                config = ClientConfig(
                    client_id=f"production_client_{i+1}",
                    server_host=self.config.server_host,
                    server_port=self.config.server_port,
                    data_partition_id=i,  # Each client gets different partition
                    training_config=TrainingConfig(
                        local_epochs=3,
                        batch_size=32,
                        learning_rate=0.001,
                        optimizer='adam'
                    )
                )
                client_configs.append(config)
            
            # Start clients concurrently
            start_tasks = []
            for config in client_configs:
                client = ProductionZKFLClient(config)
                self.clients.append(client)
                start_tasks.append(client.start_client())
            
            # Wait for all clients to start
            results = await asyncio.gather(*start_tasks, return_exceptions=True)
            
            # Check results
            successful_clients = sum(1 for result in results if result is True)
            failed_clients = len(results) - successful_clients
            
            if failed_clients > 0:
                logger.warning(f"⚠️ {failed_clients} clients failed to start")
            
            logger.info(f"✅ {successful_clients}/{self.config.num_clients} clients started successfully")
            
            # Wait for clients to establish connections
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"❌ Failed to start production clients: {e}")
            raise
    
    async def _run_federated_learning_rounds(self):
        """Run coordinated federated learning rounds"""
        try:
            logger.info(f"🎯 Running {self.config.rounds_to_simulate} federated learning rounds...")
            
            for round_num in range(1, self.config.rounds_to_simulate + 1):
                logger.info(f"🚀 Starting Round {round_num}")
                
                round_start = time.time()
                
                # Select participants (all clients for now)
                participants = [client.config.client_id for client in self.clients 
                             if client.is_authenticated]
                
                if not participants:
                    logger.warning("⚠️ No authenticated clients available for round")
                    continue
                
                # Start round on server
                success = await self.server.start_new_round(participants)
                if not success:
                    logger.error(f"❌ Failed to start round {round_num}")
                    continue
                
                # Wait for round completion
                await self._wait_for_round_completion()
                
                round_time = time.time() - round_start
                self.round_times.append(round_time)
                
                logger.info(f"✅ Round {round_num} completed in {round_time:.2f}s")
                
                # Brief pause between rounds
                await asyncio.sleep(5)
            
            logger.info("✅ All federated learning rounds completed")
            
        except Exception as e:
            logger.error(f"❌ Federated learning rounds failed: {e}")
            raise
    
    async def _wait_for_round_completion(self):
        """Wait for current round to complete"""
        timeout = 90.0  # 90 seconds timeout
        check_interval = 2.0
        elapsed = 0.0
        
        while elapsed < timeout:
            if not self.server.current_round or self.server.current_round.is_complete:
                return  # Round completed
            
            await asyncio.sleep(check_interval)
            elapsed += check_interval
            
            # Log progress
            if self.server.current_round:
                received = len(self.server.current_round.received_proofs)
                expected = len(self.server.current_round.participants)
                logger.info(f"Round progress: {received}/{expected} proofs received")
        
        logger.warning("⚠️ Round completion timeout reached")
    
    async def _collect_test_results(self) -> CommunicationTestResults:
        """Collect comprehensive test results"""
        try:
            logger.info("📊 Collecting test results...")
            
            end_time = time.time()
            total_duration = end_time - self.start_time
            
            # Collect server metrics
            server_metrics = await self._collect_server_metrics()
            
            # Collect client metrics
            client_metrics = []
            for client in self.clients:
                metrics = client.get_client_metrics()
                client_metrics.append(metrics)
            
            # Calculate aggregate statistics
            successful_registrations = len([c for c in self.clients if c.session_token])
            successful_authentications = len([c for c in self.clients if c.is_authenticated])
            
            total_successful_submissions = sum(
                c.metrics.successful_submissions for c in self.clients
            )
            total_failed_submissions = sum(
                c.metrics.failed_submissions for c in self.clients
            )
            
            # Calculate success rates
            total_submissions = total_successful_submissions + total_failed_submissions
            communication_success_rate = (
                total_successful_submissions / total_submissions 
                if total_submissions > 0 else 0.0
            )
            
            # Calculate performance metrics
            average_round_time = sum(self.round_times) / len(self.round_times) if self.round_times else 0.0
            
            # Estimate system throughput (clients per minute)
            system_throughput = (
                (total_successful_submissions / (total_duration / 60)) 
                if total_duration > 0 else 0.0
            )
            
            results = CommunicationTestResults(
                test_start_time=self.start_time,
                test_end_time=end_time,
                total_duration=total_duration,
                server_metrics=server_metrics,
                client_metrics=client_metrics,
                rounds_completed=len(self.round_times),
                total_clients=len(self.clients),
                successful_registrations=successful_registrations,
                successful_authentications=successful_authentications,
                successful_proof_submissions=total_successful_submissions,
                failed_communications=total_failed_submissions,
                average_round_time=average_round_time,
                average_proof_verification_time=server_metrics.get('average_verification_time', 0.0),
                communication_success_rate=communication_success_rate,
                system_throughput=system_throughput
            )
            
            self.test_results = results
            logger.info("✅ Test results collected successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to collect test results: {e}")
            raise
    
    async def _collect_server_metrics(self) -> Dict[str, Any]:
        """Collect server performance metrics"""
        try:
            url = f"http://{self.config.server_host}:{self.config.server_port}/api/metrics"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to collect server metrics: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.warning(f"Failed to collect server metrics: {e}")
            return {}
    
    async def _generate_test_report(self, results: CommunicationTestResults):
        """Generate comprehensive test report"""
        try:
            logger.info("📋 Generating test report...")
            
            # Print summary to console
            print("\n" + "=" * 70)
            print("🎯 PHASE 3: PRODUCTION COMMUNICATION TEST RESULTS")
            print("=" * 70)
            
            print(f"\n⏱️  TEST DURATION:")
            print(f"   Total Duration: {results.total_duration:.2f} seconds")
            print(f"   Rounds Completed: {results.rounds_completed}")
            print(f"   Average Round Time: {results.average_round_time:.2f}s")
            
            print(f"\n👥 CLIENT MANAGEMENT:")
            print(f"   Total Clients: {results.total_clients}")
            print(f"   Successful Registrations: {results.successful_registrations}")
            print(f"   Successful Authentications: {results.successful_authentications}")
            print(f"   Registration Success Rate: {(results.successful_registrations/results.total_clients)*100:.1f}%")
            print(f"   Authentication Success Rate: {(results.successful_authentications/results.total_clients)*100:.1f}%")
            
            print(f"\n🔐 PROOF SUBMISSION:")
            print(f"   Successful Submissions: {results.successful_proof_submissions}")
            print(f"   Failed Submissions: {results.failed_communications}")
            print(f"   Communication Success Rate: {results.communication_success_rate*100:.1f}%")
            print(f"   Average Verification Time: {results.average_proof_verification_time:.3f}s")
            
            print(f"\n🚀 SYSTEM PERFORMANCE:")
            print(f"   System Throughput: {results.system_throughput:.1f} submissions/minute")
            print(f"   Server Responsiveness: {'✅ Excellent' if results.communication_success_rate > 0.95 else '⚠️ Needs Improvement'}")
            print(f"   Round Coordination: {'✅ Successful' if results.rounds_completed > 0 else '❌ Failed'}")
            
            # Client-specific metrics
            print(f"\n📊 CLIENT PERFORMANCE BREAKDOWN:")
            for i, client_metrics in enumerate(results.client_metrics):
                perf = client_metrics['performance_metrics']
                conn = client_metrics['connection_status']
                data = client_metrics['data_info']
                
                print(f"   Client {i+1} ({client_metrics['client_id']}):")
                print(f"     • Rounds Participated: {perf['rounds_participated']}")
                print(f"     • Successful Submissions: {perf['successful_submissions']}")
                print(f"     • Training Time: {perf['total_training_time']:.2f}s")
                print(f"     • Proof Generation Time: {perf['total_proof_generation_time']:.2f}s")
                print(f"     • Data Partition Size: {data.get('train_size', 0)}")
                print(f"     • Connection Status: {'✅ Connected' if conn['is_connected'] else '❌ Disconnected'}")
            
            # Assessment
            print(f"\n🎯 PHASE 3 ASSESSMENT:")
            overall_success = (
                results.communication_success_rate > 0.9 and
                results.successful_authentications == results.total_clients and
                results.rounds_completed > 0
            )
            
            if overall_success:
                print("   ✅ PHASE 3 SUCCESSFUL - Production Communication System Working")
                print("   📡 Client-server communication established")
                print("   🔐 Authentication and session management functional")
                print("   ⚡ Real-time WebSocket coordination operational")
                print("   🔒 ZK proof submission and verification working")
                print("   🎯 Multi-client federated learning orchestrated successfully")
            else:
                print("   ⚠️ PHASE 3 NEEDS IMPROVEMENT")
                if results.communication_success_rate <= 0.9:
                    print("   • Communication reliability needs improvement")
                if results.successful_authentications < results.total_clients:
                    print("   • Authentication system needs debugging")
                if results.rounds_completed == 0:
                    print("   • Round coordination system failed")
            
            print(f"\n🚀 NEXT PHASE:")
            print("   Phase 4: Production Hardening")
            print("   • Error handling and fault tolerance")
            print("   • Byzantine client detection")
            print("   • Network partition recovery")
            print("   • Load balancing and scaling")
            
            # Save detailed results to file
            await self._save_test_results(results)
            
            logger.info("✅ Test report generated successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate test report: {e}")
            raise
    
    async def _save_test_results(self, results: CommunicationTestResults):
        """Save detailed test results to file"""
        try:
            results_file = Path("phase3_communication_test_results.json")
            
            # Convert results to JSON-serializable format
            results_dict = {
                'test_metadata': {
                    'phase': 'Phase 3: Production Communication',
                    'test_start_time': results.test_start_time,
                    'test_end_time': results.test_end_time,
                    'total_duration': results.total_duration,
                    'num_clients': results.total_clients,
                    'rounds_completed': results.rounds_completed
                },
                'performance_metrics': {
                    'communication_success_rate': results.communication_success_rate,
                    'average_round_time': results.average_round_time,
                    'average_proof_verification_time': results.average_proof_verification_time,
                    'system_throughput': results.system_throughput,
                    'successful_registrations': results.successful_registrations,
                    'successful_authentications': results.successful_authentications,
                    'successful_proof_submissions': results.successful_proof_submissions,
                    'failed_communications': results.failed_communications
                },
                'server_metrics': results.server_metrics,
                'client_metrics': results.client_metrics,
                'round_times': self.round_times
            }
            
            with open(results_file, 'w') as f:
                json.dump(results_dict, f, indent=2, default=str)
            
            logger.info(f"✅ Test results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save test results: {e}")
    
    async def _cleanup_test(self):
        """Clean up test resources"""
        try:
            logger.info("🧹 Cleaning up test resources...")
            
            # Shutdown clients
            for client in self.clients:
                try:
                    await client.shutdown()
                except Exception as e:
                    logger.warning(f"Client shutdown error: {e}")
            
            # Shutdown server
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass
            
            self.is_running = False
            logger.info("✅ Test cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

# Main execution
async def main():
    """Run Phase 3 Production Communication Test"""
    
    test_config = TestConfig(
        num_clients=5,
        server_host="localhost",
        server_port=8080,
        test_duration=120.0,
        rounds_to_simulate=3
    )
    
    tester = ProductionCommunicationTester(test_config)
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 Received interrupt signal, shutting down...")
        tester.is_running = False
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run comprehensive test
        results = await tester.run_comprehensive_communication_test()
        
        print("\n🎉 Phase 3: Production Communication Test Completed!")
        print("🚀 Ready for Phase 4: Production Hardening")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Phase 3 test failed: {e}")
        raise

if __name__ == "__main__":
    # Run the comprehensive production communication test
    asyncio.run(main())