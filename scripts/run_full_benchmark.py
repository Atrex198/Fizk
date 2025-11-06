#!/usr/bin/env python3
"""Run full benchmark suite as specified in the evaluation plan."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.benchmarks.runner import BenchmarkRunner
from src.analysis.analyzer import ResultAnalyzer
from src.visualization.dashboard import Dashboard
from loguru import logger


def main():
    """Run complete benchmark suite."""
    logger.info("=== ZKP Full Benchmark Suite ===\n")
    logger.info("This will run all 8 techniques across all tensor sizes.")
    logger.info("Estimated time: 30-60 minutes\n")
    
    # Initialize
    runner = BenchmarkRunner("configs/benchmark_config.yaml")
    
    # Run full suite
    logger.info("Starting full benchmark suite...\n")
    results_file = runner.run_full_suite(output_dir="data/raw")
    
    # Analyze
    logger.info("\nAnalyzing results...")
    analyzer = ResultAnalyzer(results_file)
    stats = analyzer.compute_statistics()
    
    # Export summary
    summary_file = "data/processed/summary_statistics.csv"
    analyzer.export_summary(summary_file)
    logger.info(f"Summary exported to: {summary_file}")
    
    # Find best techniques
    logger.info("\n=== Best Techniques ===")
    for metric in ['proof_gen_time_ms', 'verification_time_ms', 'proof_size_bytes']:
        best = analyzer.get_best_technique(metric)
        logger.info(f"{metric}: {best['technique']} ({best['value']:.2f})")
    
    # Generate all visualizations
    logger.info("\nGenerating visualizations...")
    dashboard = Dashboard(stats, output_dir="results/charts")
    dashboard.generate_all_charts()
    
    logger.info("\n✓ Full benchmark suite complete!")
    logger.info(f"  - Raw data: {results_file}")
    logger.info(f"  - Summary: {summary_file}")
    logger.info(f"  - Charts: results/charts/")


if __name__ == "__main__":
    main()
