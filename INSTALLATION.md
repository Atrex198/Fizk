# ZKP Evaluation System - Installation Guide

## Prerequisites

- Python 3.9 or higher
- 16GB RAM (recommended)
- 10GB free disk space

## Installation Steps

### 1. Clone or Navigate to the Repository

```bash
cd /home/ariva/work/final_project/review_benchmark
```

### 2. Run Installation Script

#### For Fish Shell:
```fish
chmod +x install.fish
./install.fish
```

#### For Bash/Zsh:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install package
pip install -e .

# Create directories
mkdir -p data/{raw,processed} results/{charts,reports}
```

### 3. Verify Installation

```python
python -c "from src.benchmarks.runner import BenchmarkRunner; print('✓ Installation successful!')"
```

## Quick Start

### Run Demo
```bash
python scripts/run_demo.py
```

This will:
- Run a single benchmark test
- Execute a small benchmark suite
- Generate analysis and visualizations
- Save results to `data/raw/` and charts to `results/charts/`

### Run Full Benchmark
```bash
python scripts/run_full_benchmark.py
```

This will run all 8 ZKP techniques across all tensor sizes (takes 30-60 minutes).

## Usage Examples

### Python API

```python
from src.benchmarks.runner import BenchmarkRunner
from src.analysis.analyzer import ResultAnalyzer
from src.visualization.dashboard import Dashboard

# Initialize and run
runner = BenchmarkRunner()
results_file = runner.run_full_suite()

# Analyze
analyzer = ResultAnalyzer(results_file)
stats = analyzer.compute_statistics()

# Visualize
dashboard = Dashboard(stats)
dashboard.generate_all_charts()
```

### Jupyter Notebook

```bash
jupyter notebook notebooks/demo.ipynb
```

## Configuration

Edit `configs/benchmark_config.yaml` to customize:
- ZKP techniques to evaluate
- Tensor sizes to test
- Number of trials per configuration
- Operations to benchmark

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
zkp-evaluation/
├── src/                     # Source code
│   ├── zkp_techniques/     # ZKP wrappers
│   ├── tensor_ops/         # Tensor operations
│   ├── benchmarks/         # Benchmarking framework
│   ├── analysis/           # Data analysis
│   └── visualization/      # Charts and dashboards
├── scripts/                # Executable scripts
├── tests/                  # Unit tests
├── notebooks/              # Jupyter notebooks
├── configs/                # Configuration files
├── data/                   # Data storage
└── results/                # Generated results
```

## Troubleshooting

### Import Errors
Make sure you've activated the virtual environment:
```bash
source venv/bin/activate  # or venv/bin/activate.fish
```

### Memory Issues
Reduce tensor sizes in `configs/benchmark_config.yaml` or run benchmarks for individual techniques.

### Missing Dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

## Next Steps

1. Review the evaluation plan: `zkp_evaluation_plan.md`
2. Run demo: `python scripts/run_demo.py`
3. Explore the Jupyter notebook: `notebooks/demo.ipynb`
4. Run full benchmark: `python scripts/run_full_benchmark.py`
5. Analyze results in `results/charts/`

## Support

For issues or questions, refer to the documentation or check the code comments.
