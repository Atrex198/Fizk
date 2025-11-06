# ZKP Performance Evaluation System

A comprehensive benchmarking framework for evaluating Zero-Knowledge Proof techniques on tensor operations.

## Features

- **8 ZKP Techniques**: STARK, Groth16, PLONK, Bulletproofs, Halo2, Protostar, zkSNARK, Nova
- **5 Tensor Operations**: Matrix multiplication, tensor contraction, element-wise ops, decomposition, convolution
- **Comprehensive Metrics**: Proof generation time, verification time, proof size, memory usage
- **Statistical Analysis**: Mean, median, std deviation, confidence intervals
- **Rich Visualizations**: 8 different chart types for performance analysis

## Project Structure

```
zkp-evaluation/
├── src/
│   ├── zkp_techniques/      # ZKP wrapper implementations
│   ├── tensor_ops/          # Tensor operation generators
│   ├── benchmarks/          # Benchmarking framework
│   ├── analysis/            # Data analysis tools
│   └── visualization/       # Plotting and dashboard
├── data/
│   ├── raw/                 # Raw benchmark results
│   └── processed/           # Aggregated statistics
├── results/
│   ├── charts/              # Generated visualizations
│   └── reports/             # Analysis reports
├── tests/                   # Unit tests
├── configs/                 # Configuration files
├── notebooks/               # Jupyter notebooks for exploration
└── scripts/                 # Utility scripts

```

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```python
from src.benchmarks.runner import BenchmarkRunner
from src.analysis.analyzer import ResultAnalyzer
from src.visualization.dashboard import Dashboard

# Run benchmarks
runner = BenchmarkRunner()
runner.run_full_suite()

# Analyze results
analyzer = ResultAnalyzer('data/raw/results.json')
stats = analyzer.compute_statistics()

# Generate visualizations
dashboard = Dashboard(stats)
dashboard.generate_all_charts()
```

## Usage

See `notebooks/demo.ipynb` for detailed examples and tutorials.

## License

MIT
