#!/usr/bin/env python3
"""
Run ZKP Benchmark Suite with Real Cryptographic Implementations

This script benchmarks STARK and Groth16 with actual cryptographic operations:
- Real FRI protocol for STARK
- Real elliptic curve pairings for Groth16
- Real Merkle trees and finite field arithmetic
- No mocks or simulations

Usage:
    python run_benchmark.py [--quick] [--size SIZE]
    
    --quick: Run quick benchmark (fewer trials, smaller sizes)
    --size: Specify tensor size (small/medium/large)
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.benchmarks.runner import BenchmarkRunner
from src.analysis.analyzer import ResultAnalyzer
from src.visualization.dashboard import Dashboard
from loguru import logger
import json


def run_quick_benchmark():
    """Run quick benchmark for testing (small tensors, fewer trials)."""
    logger.info("=== Quick ZKP Benchmark (Real Cryptography) ===\n")
    logger.info("Testing STARK and Groth16 with REAL cryptographic operations")
    logger.info("No mocks, no simulations - all proofs are cryptographically sound\n")
    
    # Custom config for quick test
    config = {
        "tensor_sizes": {
            "tiny": {"2d": [8, 8], "elements": 64},
            "small": {"2d": [16, 16], "elements": 256},
        },
        "operations": [
            {"name": "matrix_multiplication", "enabled": True},
        ],
        "benchmark": {"trials_per_config": 3, "timeout_seconds": 600},
    }
    
    runner = BenchmarkRunner()
    runner.config = config
    runner.techniques = runner._initialize_techniques()
    
    logger.info(f"Techniques to benchmark: {list(runner.techniques.keys())}\n")
    
    # Run benchmark
    results_file = runner.run_full_suite(output_dir="data/raw")
    
    # Quick analysis
    with open(results_file) as f:
        results = json.load(f)
    
    logger.info("\n=== Quick Results Summary ===\n")
    
    for technique in set(r['technique'] for r in results):
        technique_results = [r for r in results if r['technique'] == technique]
        avg_proof_time = sum(r['proof_gen_time_ms'] for r in technique_results) / len(technique_results)
        avg_verify_time = sum(r['verification_time_ms'] for r in technique_results) / len(technique_results)
        avg_proof_size = sum(r['proof_size_bytes'] for r in technique_results) / len(technique_results)
        all_valid = all(r['is_valid'] for r in technique_results)
        
        logger.info(f"{technique}:")
        logger.info(f"  Avg Proof Gen Time: {avg_proof_time:.2f} ms")
        logger.info(f"  Avg Verify Time: {avg_verify_time:.2f} ms")
        logger.info(f"  Avg Proof Size: {avg_proof_size:.0f} bytes")
        logger.info(f"  All Proofs Valid: {'✓' if all_valid else '✗'}")
        logger.info("")
    
    return results_file


def run_full_benchmark(size_filter=None):
    """Run full benchmark suite with real cryptography."""
    logger.info("=== Full ZKP Benchmark Suite (Real Cryptography) ===\n")
    logger.info("This will benchmark STARK and Groth16 with:")
    logger.info("  - Real FRI protocol (STARK)")
    logger.info("  - Real BN254 elliptic curve pairings (Groth16)")
    logger.info("  - Real Merkle trees and finite field arithmetic")
    logger.info("  - Multiple tensor sizes and trials\n")
    
    # Initialize with default config or custom sizes
    runner = BenchmarkRunner("configs/benchmark_config.yaml")
    
    if size_filter:
        # Filter to specific size
        runner.config["tensor_sizes"] = {
            k: v for k, v in runner.config["tensor_sizes"].items() 
            if k == size_filter
        }
        logger.info(f"Filtering to size: {size_filter}")
    
    logger.info(f"Techniques: {list(runner.techniques.keys())}")
    logger.info(f"Tensor sizes: {list(runner.config['tensor_sizes'].keys())}")
    logger.info(f"Trials per config: {runner.config['benchmark']['trials_per_config']}\n")
    
    # Run full suite
    logger.info("Starting benchmark (this may take several minutes)...\n")
    results_file = runner.run_full_suite(output_dir="data/raw")
    
    # Analyze results
    logger.info("\nAnalyzing results...")
    analyzer = ResultAnalyzer(results_file)
    stats = analyzer.compute_statistics()
    
    # Export summary
    summary_file = "data/processed/summary_statistics.csv"
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    analyzer.export_summary(summary_file)
    logger.info(f"Summary exported to: {summary_file}")
    
    # Print key findings
    logger.info("\n=== Key Findings ===\n")
    
    for metric in ['proof_gen_time_ms', 'verification_time_ms', 'proof_size_bytes']:
        best = analyzer.get_best_technique(metric)
        logger.info(f"Best for {metric}:")
        logger.info(f"  {best['technique']} - {best['value']:.2f}")
    
    # Generate visualizations
    logger.info("\nGenerating visualizations...")
    dashboard = Dashboard(stats, output_dir="results/charts")
    dashboard.generate_all_charts()
    
    logger.info("\n" + "="*60)
    logger.info("✓ Benchmark Complete!")
    logger.info("="*60)
    logger.info(f"Raw data: {results_file}")
    logger.info(f"Summary: {summary_file}")
    logger.info(f"Charts: results/charts/")
    logger.info("="*60)
    
    return results_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run ZKP benchmarks with real cryptographic implementations"
    )
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="Run quick benchmark (smaller sizes, fewer trials)"
    )
    parser.add_argument(
        "--size",
        choices=["small", "medium", "large"],
        help="Run benchmark for specific tensor size only"
    )
    
    args = parser.parse_args()
    
    try:
        if args.quick:
            results_file = run_quick_benchmark()
        else:
            results_file = run_full_benchmark(size_filter=args.size)
        
        logger.info(f"\n✓ Success! Results saved to: {results_file}")
        
    except Exception as e:
        logger.error(f"\n✗ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
