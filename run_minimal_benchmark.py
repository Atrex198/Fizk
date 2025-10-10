#!/usr/bin/env python3
"""
Minimal Production Multi-Protocol Benchmark Test
==============================================

Tests the core benchmark functionality with available protocols
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_minimal_benchmark():
    """Run minimal benchmark test with available protocols"""
    print("🚀 Minimal Production Multi-Protocol Benchmark")
    print("=" * 50)
    
    try:
        from production_multi_protocol_benchmark import (
            ProductionBenchmarkConfig,
            ProductionMetricsCollector,
            ProductionProtocolRunner
        )
        
        # Create minimal configuration
        config = ProductionBenchmarkConfig(
            num_clients=2,
            num_rounds=2,
            local_epochs=1,
            zkp_security_level=128,  # Reduced for testing
            batch_size=16
        )
        
        # Initialize metrics
        metrics = ProductionMetricsCollector(config)
        
        # Initialize runner
        runner = ProductionProtocolRunner(config, metrics)
        
        # Initialize system
        print("🔧 Initializing system...")
        await runner.initialize_system()
        
        # Check available protocols
        available_protocols = list(runner.protocols.keys())
        print(f"📊 Available protocols: {available_protocols}")
        
        if not available_protocols:
            print("❌ No protocols available for benchmarking")
            return False
        
        # Run mini benchmark
        print("🏁 Running mini benchmark...")
        results = await runner.run_comprehensive_benchmark()
        
        # Print results summary
        print("\n" + "="*60)
        print("🏆 FAIR MULTI-PROTOCOL BENCHMARK RESULTS")
        print("="*60)
        
        for protocol_name, protocol_results in results['protocols'].items():
            print(f"\n{protocol_name.upper()} Results:")
            
            # Individual round metrics
            if 'rounds' in protocol_results and protocol_results['rounds']:
                last_round = protocol_results['rounds'][-1]
                print(f"  📊 Individual Round Metrics:")
                print(f"     Avg Accuracy: {last_round['round_metrics']['avg_accuracy']:.4f}")
                print(f"     Avg Loss: {last_round['round_metrics']['avg_loss']:.4f}")
                print(f"     Individual Proof Size: {last_round['round_metrics']['total_proof_size']} bytes")
                print(f"     Individual Generation Time: {last_round['round_metrics']['avg_proof_generation_time']*1000:.2f} ms")
            
            # Protocol-specific aggregation results
            if 'final_performance' in protocol_results and protocol_results['final_performance']:
                perf = protocol_results['final_performance']
                print(f"  🔗 Protocol-Specific Aggregation:")
                print(f"     Method: {perf.get('aggregation_method', 'Unknown')}")
                print(f"     Scaling: {perf.get('size_scaling', 'Unknown')}")
                print(f"     Key Advantage: {perf.get('key_advantage', 'Unknown')}")
                
                if 'aggregated_proof_size' in perf:
                    print(f"     Aggregated Proof Size: {perf['aggregated_proof_size']} bytes")
                if 'compression_ratio' in perf:
                    print(f"     Compression Ratio: {perf['compression_ratio']:.2f}x")
                if 'verification_speedup' in perf:
                    print(f"     Verification Speedup: {perf['verification_speedup']:.2f}x")
            
            # Protocol-specific features
            if 'protocol_specific_features' in protocol_results:
                features = protocol_results['protocol_specific_features']
                print(f"  ⚡ Unique Features:")
                for key, value in features.items():
                    if key != 'key_advantage':  # Already shown above
                        print(f"     {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n📈 Fair Comparison Analysis:")
        print("   Each protocol optimized for its strengths:")
        print("   • Nova: Constant-size proofs through IVC")
        print("   • ProtoStar: Logarithmic compression via ProtoGalaxy")
        print("   • Bulletproofs: Batch verification speedup")
        print("   This comparison shows real-world deployment advantages!")
        
        print("\n✅ Mini benchmark completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_minimal_benchmark())
    sys.exit(0 if success else 1)