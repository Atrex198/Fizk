# ZKP Evaluation System - Architecture Overview

## System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                           │
├─────────────────────────────────────────────────────────────┤
│  CLI Scripts  │  Python API  │  Jupyter Notebook            │
│  run_demo.py  │  Import src  │  demo.ipynb                  │
│  run_full.py  │              │                               │
└────────┬────────────────┬─────────────────┬─────────────────┘
         │                │                 │
         ▼                ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│              BENCHMARK RUNNER (benchmarks/)                  │
├─────────────────────────────────────────────────────────────┤
│  • BenchmarkRunner: Orchestrates test execution             │
│  • MetricsCollector: Gathers performance data               │
│  • MemoryProfiler: Monitors resource usage                  │
└────────┬────────────────────────────────────────────────────┘
         │
         ├──────────────┬──────────────┬────────────────┐
         ▼              ▼              ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────────┐
│ ZKP TECHNIQUES│ │ TENSOR OPS   │ │  CONFIG  │ │   MEMORY    │
├──────────────┤ ├──────────────┤ ├──────────┤ ├─────────────┤
│ • STARK      │ │ • MatMul     │ │ • YAML   │ │ • psutil    │
│ • Groth16    │ │ • Convol.    │ │ • Sizes  │ │ • profiling │
│ • PLONK      │ │ • Contract.  │ │ • Trials │ └─────────────┘
│ • Bullet.    │ │ • Element    │ │ • Metrics│
│ • Halo2      │ │ • Decomp.    │ └──────────┘
│ • Protostar  │ └──────────────┘
│ • zkSNARK    │
│ • Nova       │
└────────┬─────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA STORAGE                             │
├─────────────────────────────────────────────────────────────┤
│  data/raw/            │  data/processed/                    │
│  • results_*.json     │  • summary_statistics.csv           │
│  • Individual trials  │  • Aggregated metrics               │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                 ANALYSIS ENGINE (analysis/)                  │
├─────────────────────────────────────────────────────────────┤
│  • ResultAnalyzer: Aggregate and process data               │
│  • StatisticalAnalyzer: T-tests, ANOVA, regression          │
│  • Scaling analysis, confidence intervals                   │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│            VISUALIZATION DASHBOARD (visualization/)          │
├─────────────────────────────────────────────────────────────┤
│  8 Chart Types:                                             │
│  1. Scaling Comparison (line, log-log)                      │
│  2. Verification Times (grouped bar)                        │
│  3. Proof Sizes (box plot)                                  │
│  4. Memory Heatmap                                          │
│  5. Trade-off Analysis (scatter)                            │
│  6. Scalability Factor (line)                               │
│  7. Performance Radar (spider)                              │
│  8. Timeline Comparison (stacked bar)                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTPUT ARTIFACTS                           │
├─────────────────────────────────────────────────────────────┤
│  results/charts/      │  results/reports/                   │
│  • *.png charts       │  • Analysis reports                 │
│  • High-res figures   │  • Recommendations                  │
└─────────────────────────────────────────────────────────────┘
```

## Component Interactions

### 1. Benchmark Execution Flow
```
Config Loading → Technique Initialization → For Each (Technique × Size × Operation × Trial):
    Generate Tensor → Setup ZKP → Generate Proof → Verify Proof → Collect Metrics
→ Save Results → Analysis → Visualization
```

### 2. Data Pipeline
```
Raw Trials (JSON) → Aggregation (pandas) → Statistics (scipy) → Charts (matplotlib)
```

### 3. ZKP Technique Interface
```python
class ZKPTechnique:
    setup(circuit_size) → setup_time
    generate_proof(inputs) → ProofResult(proof, time, size, memory)
    verify_proof(proof) → VerificationResult(valid, time)
```

## Key Design Patterns

### 1. Strategy Pattern
- `ZKPTechnique` base class with multiple implementations
- Allows easy addition of new ZKP systems

### 2. Template Method
- `BenchmarkRunner` defines benchmark protocol
- Each technique implements specific proof operations

### 3. Factory Pattern
- `TensorGenerator` creates different tensor types
- Configurable via parameters

### 4. Observer Pattern
- `MetricsCollector` observes and records measurements
- Decoupled from benchmark execution

### 5. Builder Pattern
- `Dashboard` builds visualizations step-by-step
- Flexible chart generation

## Data Models

### ProofResult
```
proof: Any                    # The actual proof object
generation_time_ms: float     # Time to generate
proof_size_bytes: int         # Proof size
memory_usage_mb: float        # Peak memory
setup_time_ms: float          # Setup overhead
metadata: Dict                # Additional info
```

### VerificationResult
```
is_valid: bool                # Verification success
verification_time_ms: float   # Time to verify
metadata: Dict                # Additional info
```

### BenchmarkRecord
```
technique: str                # ZKP technique name
tensor_size: str              # Size label
operation: str                # Operation type
trial: int                    # Trial number
proof_gen_time_ms: float      # Metrics...
verification_time_ms: float
proof_size_bytes: int
memory_usage_mb: float
...
```

## Extension Points

### Adding New ZKP Technique
1. Create class inheriting from `ZKPTechnique`
2. Implement abstract methods: `setup()`, `generate_proof()`, `verify_proof()`
3. Add to config YAML
4. Import in `runner.py`

### Adding New Tensor Operation
1. Add function to `src/tensor_ops/operations.py`
2. Return dict with `result`, `operation`, `total_ops`
3. Add to config YAML
4. Update `runner.py` operation mapping

### Adding New Chart
1. Add function to `src/visualization/charts.py`
2. Accept `stats` DataFrame parameter
3. Return matplotlib Figure
4. Register in `Dashboard.generate_all_charts()`

### Adding New Metric
1. Update `ProofResult` or `VerificationResult` dataclass
2. Collect in ZKP technique implementation
3. Add to `MetricsCollector`
4. Include in analysis and visualization

## Performance Considerations

### Memory Management
- Use generators for large datasets
- Profile with `MemoryProfiler`
- Limit tensor sizes if needed

### Parallel Execution
- Current: Sequential execution
- Future: Parallel trials with multiprocessing
- Use `trials_per_config` to control load

### Data Storage
- JSON for raw data (human-readable)
- CSV for statistics (Excel-compatible)
- HDF5 for very large datasets (future)

### Visualization Performance
- Generate charts on-demand
- Cache computed statistics
- Use sampling for very large datasets

## Testing Strategy

### Unit Tests
- `test_tensor_ops.py`: Tensor generation and operations
- `test_zkp_techniques.py`: ZKP wrapper functionality

### Integration Tests
- Full benchmark runs with small datasets
- Verify data pipeline integrity

### Validation Tests
- Cross-check with theoretical bounds
- Verify statistical properties
- Ensure reproducibility with seeds

## Configuration Management

### YAML Structure
```yaml
environment:        # System settings
zkp_techniques:     # Which techniques to test
tensor_sizes:       # Size configurations
operations:         # Operations to benchmark
benchmark:          # Execution parameters
metrics:            # What to measure
analysis:           # Statistical settings
visualization:      # Chart settings
```

### Override Hierarchy
1. Default values in code
2. YAML configuration file
3. Command-line arguments (future)
4. Environment variables (future)

## Logging and Monitoring

### Log Levels
- DEBUG: Detailed execution info
- INFO: Progress and results
- WARNING: Non-critical issues
- ERROR: Failures and exceptions

### Progress Tracking
- tqdm progress bars for long operations
- Real-time console updates
- Estimated time remaining

## Error Handling

### Graceful Degradation
- Continue on individual test failures
- Log errors without stopping suite
- Report success rate at end

### Validation
- Check tensor shapes before operations
- Verify proof validity
- Validate configuration parameters

## Future Architecture Improvements

1. **Plugin System**: Dynamic loading of ZKP techniques
2. **Distributed Execution**: Celery/Dask for parallel benchmarks
3. **Real-time Dashboard**: Web interface with live updates
4. **Database Backend**: PostgreSQL/MongoDB for results
5. **API Server**: REST API for remote execution
6. **Containerization**: Docker for reproducibility
7. **CI/CD Integration**: Automated benchmarking

---

This architecture provides:
- ✅ Modularity
- ✅ Extensibility
- ✅ Testability
- ✅ Maintainability
- ✅ Scalability
- ✅ Reproducibility
