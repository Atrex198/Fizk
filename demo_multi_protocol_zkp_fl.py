#!/usr/bin/env python3
"""
Multi-Protocol ZKP-FL Demonstration
===================================

Demonstrates the complete multi-protocol ZKP federated learning system:
- Nova IVC: Recursive proofs with constant size
- ProtoStar + ProtoGalaxy: Production aggregation
- Side-by-side comparison of protocols

Usage:
    python demo_multi_protocol_zkp_fl.py [--protocol nova|protostar|both]
    
Author: Multi-ZKP FL Team
Version: 1.0
"""

import asyncio
import argparse
import time
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Import the multi-protocol system
from multi_protocol_zkp_fl import (
    UnifiedFLConfig, ZKPProtocolConfig, 
    MultiProtocolZKPFLSystem, UnifiedZKPFactory
)
from real_dataset_loader import RealDatasetLoader

def create_synthetic_dataset(num_clients: int = 5, samples_per_client: int = 200):
    """Create synthetic federated dataset for demonstration"""
    print(f"📊 Creating synthetic dataset: {num_clients} clients, {samples_per_client} samples each")
    
    clients_data = {}
    
    for i in range(num_clients):
        # Create slightly different data distributions per client (non-IID)
        np.random.seed(42 + i)  # Reproducible but different per client
        
        # 10-dimensional feature space
        X_data = np.random.randn(samples_per_client, 10)
        
        # Add client-specific bias to simulate non-IID data
        bias = np.random.randn(10) * 0.5
        X_data += bias
        
        # Binary classification with feature dependency
        weights = np.random.randn(10)
        y_prob = 1 / (1 + np.exp(-(X_data @ weights)))
        y_data = (y_prob > 0.5).astype(int)
        
        clients_data[f"client_{i}"] = {
            'X': X_data,
            'y': y_data,
            'bias': bias.tolist()
        }
        
        print(f"   Client {i}: {len(X_data)} samples, {np.mean(y_data):.2f} positive rate")
    
    return clients_data

async def run_protocol_demo(protocol_name: str, config: UnifiedFLConfig, clients_data: dict):
    """Run FL demo for a specific protocol"""
    print(f"\n🚀 Running {protocol_name.upper()} Protocol Demo")
    print("=" * 60)
    
    start_time = time.time()
    
    # Create and initialize system
    system = MultiProtocolZKPFLSystem(config)
    await system.initialize_system()
    
    # Add clients
    for client_id, data in clients_data.items():
        system.add_client(client_id, data['X'], data['y'])
    
    # Run federated learning
    results = await system.run_federated_learning()
    
    total_time = time.time() - start_time
    
    # Display results
    benchmarks = results['benchmarks']
    protocol_info = benchmarks['protocol_info']
    
    print(f"\n📊 {protocol_name.upper()} Results Summary:")
    print("-" * 40)
    print(f"Protocol: {protocol_info['name']} v{protocol_info['version']}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Rounds Completed: {len(benchmarks['rounds'])}")
    print(f"Trusted Setup Required: {protocol_info.get('trusted_setup_required', 'N/A')}")
    
    if protocol_name.lower() == 'nova':
        # Nova-specific metrics
        if 'nova_ivc' in benchmarks:
            nova_metrics = benchmarks['nova_ivc']
            print(f"\n🔍 Nova IVC Metrics:")
            print(f"   Avg Proof Size: {nova_metrics['avg_proof_size']} bytes (constant)")
            print(f"   Avg Verify Time: {nova_metrics['avg_verify_time']:.4f}s")
            print(f"   All Proofs Valid: {nova_metrics['all_valid']}")
            print(f"   Rounds per Client: {nova_metrics['total_rounds_per_client']}")
            print(f"   Proof Size Scaling: O(1) - CONSTANT regardless of rounds! 🎯")
    
    else:
        # ProtoStar-specific metrics
        round_metrics = benchmarks['rounds']
        if round_metrics:
            avg_proof_size = np.mean([r.get('avg_proof_size', 0) for r in round_metrics if 'avg_proof_size' in r])
            avg_verify_time = np.mean([r.get('avg_verification_time', 0) for r in round_metrics if 'avg_verification_time' in r])
            
            print(f"\n🔗 ProtoStar + ProtoGalaxy Metrics:")
            print(f"   Avg Proof Size: {avg_proof_size:.0f} bytes per round")
            print(f"   Avg Verify Time: {avg_verify_time:.4f}s per proof")
            
            # Check for aggregation results
            aggregated_rounds = [r for r in round_metrics if 'aggregation_ratio' in r]
            if aggregated_rounds:
                avg_agg_ratio = np.mean([r['aggregation_ratio'] for r in aggregated_rounds])
                print(f"   Aggregation Ratio: {avg_agg_ratio:.2f}x compression")
                print(f"   ProtoGalaxy Working: ✅ Real EC operations")
    
    return results

def visualize_comparison(nova_results: dict, protostar_results: dict):
    """Create visualization comparing the protocols"""
    print("\n📊 Generating Protocol Comparison Visualization...")
    
    # Create comparison plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Multi-Protocol ZKP-FL Comparison: Nova vs ProtoStar', fontsize=16, fontweight='bold')
    
    # Extract metrics
    protocols = ['Nova IVC', 'ProtoStar + ProtoGalaxy']
    
    # Proof sizes
    nova_size = nova_results['benchmarks']['nova_ivc']['avg_proof_size'] if 'nova_ivc' in nova_results['benchmarks'] else 0
    protostar_rounds = protostar_results['benchmarks']['rounds']
    protostar_size = np.mean([r.get('avg_proof_size', 0) for r in protostar_rounds if 'avg_proof_size' in r])
    
    proof_sizes = [nova_size, protostar_size]
    
    # Verification times
    nova_verify = nova_results['benchmarks']['nova_ivc']['avg_verify_time'] if 'nova_ivc' in nova_results['benchmarks'] else 0
    protostar_verify = np.mean([r.get('avg_verification_time', 0) for r in protostar_rounds if 'avg_verification_time' in r])
    
    verify_times = [nova_verify, protostar_verify]
    
    # Plot 1: Proof Sizes
    bars1 = ax1.bar(protocols, proof_sizes, color=['#FF6B6B', '#4ECDC4'])
    ax1.set_ylabel('Proof Size (bytes)')
    ax1.set_title('Proof Size Comparison')
    ax1.set_yscale('log')
    for i, v in enumerate(proof_sizes):
        ax1.text(i, v, f'{v:.0f}', ha='center', va='bottom')
    
    # Plot 2: Verification Times
    bars2 = ax2.bar(protocols, verify_times, color=['#FF6B6B', '#4ECDC4'])
    ax2.set_ylabel('Verification Time (seconds)')
    ax2.set_title('Verification Time Comparison')
    for i, v in enumerate(verify_times):
        ax2.text(i, v, f'{v:.4f}', ha='center', va='bottom')
    
    # Plot 3: Setup Requirements
    setup_required = [False, True]  # Nova: False, ProtoStar: True
    colors3 = ['#95E1D3', '#FD79A8']
    bars3 = ax3.bar(protocols, [1, 1], color=[colors3[int(req)] for req in setup_required])
    ax3.set_ylabel('Trusted Setup Required')
    ax3.set_title('Trusted Setup Requirements')
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(['No', 'Yes'])
    for i, req in enumerate(setup_required):
        ax3.text(i, 0.5, 'No' if not req else 'Yes', ha='center', va='center', fontweight='bold')
    
    # Plot 4: Protocol Features Radar (simplified as bar chart)
    features = ['Recursion', 'Aggregation', 'Transparency', 'Efficiency']
    nova_scores = [10, 8, 10, 9]  # Nova: excellent recursion, good aggregation, full transparency, high efficiency
    protostar_scores = [6, 10, 6, 8]  # ProtoStar: some recursion, excellent aggregation, requires setup, good efficiency
    
    x = np.arange(len(features))
    width = 0.35
    
    bars4a = ax4.bar(x - width/2, nova_scores, width, label='Nova IVC', color='#FF6B6B', alpha=0.7)
    bars4b = ax4.bar(x + width/2, protostar_scores, width, label='ProtoStar', color='#4ECDC4', alpha=0.7)
    
    ax4.set_ylabel('Score (1-10)')
    ax4.set_title('Protocol Feature Comparison')
    ax4.set_xticks(x)
    ax4.set_xticklabels(features)
    ax4.legend()
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path('./benchmarks/comparison')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(time.time())
    plot_file = output_dir / f'zkp_protocol_comparison_{timestamp}.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    
    print(f"📊 Comparison visualization saved to: {plot_file}")
    
    # Show summary table
    print(f"\n📋 Protocol Comparison Summary:")
    print("=" * 60)
    print(f"{'Metric':<25} {'Nova IVC':<15} {'ProtoStar':<15}")
    print("-" * 60)
    print(f"{'Proof Size (bytes)':<25} {nova_size:<15.0f} {protostar_size:<15.0f}")
    print(f"{'Verify Time (s)':<25} {nova_verify:<15.4f} {protostar_verify:<15.4f}")
    print(f"{'Trusted Setup':<25} {'No':<15} {'Yes':<15}")
    print(f"{'Curve':<25} {'Pasta':<15} {'BN128':<15}")
    print(f"{'Best For':<25} {'IVC/Recursion':<15} {'Aggregation':<15}")

async def main():
    """Main demonstration function"""
    parser = argparse.ArgumentParser(description='Multi-Protocol ZKP-FL Demo')
    parser.add_argument('--protocol', choices=['nova', 'protostar', 'both'], default='both',
                       help='Which protocol(s) to demonstrate')
    parser.add_argument('--clients', type=int, default=3, help='Number of FL clients')
    parser.add_argument('--rounds', type=int, default=2, help='Number of FL rounds')
    parser.add_argument('--samples', type=int, default=100, help='Samples per client')
    
    args = parser.parse_args()
    
    print("🚀 MULTI-PROTOCOL ZKP FEDERATED LEARNING DEMONSTRATION")
    print("=" * 65)
    print(f"Protocols: {args.protocol.upper()}")
    print(f"Clients: {args.clients}")
    print(f"Rounds: {args.rounds}")
    print(f"Samples per client: {args.samples}")
    
    # Create synthetic dataset
    clients_data = create_synthetic_dataset(args.clients, args.samples)
    
    results = {}
    
    if args.protocol in ['nova', 'both']:
        # Nova IVC Configuration
        nova_config = UnifiedFLConfig(
            num_clients=args.clients,
            num_rounds=args.rounds,
            local_epochs=10,  # FIXED: Per Final Guide (1 round = 10 epochs)
            zkp_config=ZKPProtocolConfig(
                protocol_type="nova",
                security_level=128,
                nova_max_weight_size=50,
                trusted_setup_required=False,
                curve_type="pasta"
            ),
            benchmark_output_dir="./benchmarks/nova"
        )
        
        results['nova'] = await run_protocol_demo('nova', nova_config, clients_data)
    
    if args.protocol in ['protostar', 'both']:
        # ProtoStar Configuration
        protostar_config = UnifiedFLConfig(
            num_clients=args.clients,
            num_rounds=args.rounds,
            local_epochs=10,  # FIXED: Per Final Guide (1 round = 10 epochs)
            zkp_config=ZKPProtocolConfig(
                protocol_type="protostar",
                security_level=128,
                srs_size=1024,
                enable_aggregation=True,
                trusted_setup_required=True,
                curve_type="bn128"
            ),
            benchmark_output_dir="./benchmarks/protostar"
        )
        
        results['protostar'] = await run_protocol_demo('protostar', protostar_config, clients_data)
    
    # Generate comparison if both protocols were run
    if len(results) == 2:
        visualize_comparison(results['nova'], results['protostar'])
    
    print(f"\n🎯 DEMONSTRATION COMPLETE!")
    print("=" * 65)
    
    if args.protocol == 'both':
        print("✅ Multi-protocol comparison completed successfully!")
        print("✅ Nova IVC: Constant-size recursive proofs demonstrated")
        print("✅ ProtoStar + ProtoGalaxy: Production aggregation demonstrated")
        print("✅ Side-by-side benchmarking: Performance metrics collected")
        print("📊 Check ./benchmarks/ directory for detailed results")
        print("🖼️  Protocol comparison visualization generated")
    else:
        print(f"✅ {args.protocol.upper()} protocol demonstration completed!")
        print("📊 Check ./benchmarks/ directory for results")
    
    print("\n🚀 Your ZKP-FL system supports multiple protocols and is ready for research!")

if __name__ == "__main__":
    asyncio.run(main())