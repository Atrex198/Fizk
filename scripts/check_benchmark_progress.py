#!/usr/bin/env python3
"""Quick script to check benchmark progress."""

import json
from pathlib import Path
from datetime import datetime

# Find the most recent results file
data_dir = Path('data/raw')
if not data_dir.exists():
    print("No data/raw directory found")
    exit(1)

result_files = sorted(data_dir.glob('results_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)

if not result_files:
    print("No results files found yet")
    exit(0)

latest_file = result_files[0]
print(f"Latest results file: {latest_file.name}")
print(f"Modified: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
print()

with open(latest_file) as f:
    results = json.load(f)

print(f"Total results: {len(results)}")

# Count by technique
by_technique = {}
for r in results:
    tech = r['technique']
    by_technique[tech] = by_technique.get(tech, 0) + 1

print("\nBy technique:")
for tech, count in sorted(by_technique.items()):
    print(f"  {tech}: {count}")

# Success rate
valid_count = sum(1 for r in results if r.get('is_valid', False))
print(f"\nSuccess rate: {valid_count}/{len(results)} ({100*valid_count/len(results):.1f}%)")
