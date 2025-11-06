#!/usr/bin/env python3
"""Test all ZKP techniques initialization and basic functionality."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.benchmarks.runner import BenchmarkRunner
from loguru import logger

def main():
    print("=" * 60)
    print("ZKP Techniques Initialization Test")
    print("=" * 60)
    print()
    
    try:
        runner = BenchmarkRunner()
        
        print(f"✓ Total techniques initialized: {len(runner.techniques)}")
        print()
        print("Available ZKP Techniques:")
        print("-" * 60)
        
        for name, technique in sorted(runner.techniques.items()):
            print(f"  ✓ {name}")
            print(f"      Type: {technique.get_proof_type()}")
            print(f"      Trusted Setup: {technique.requires_trusted_setup()}")
            print(f"      Transparent: {technique.is_transparent()}")
            print(f"      Post-Quantum: {technique.is_post_quantum()}")
            print()
        
        print("=" * 60)
        print(f"READY TO BENCHMARK: {len(runner.techniques)} techniques")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"✗ Error initializing techniques: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
