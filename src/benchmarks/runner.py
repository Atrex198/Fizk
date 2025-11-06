"""Main benchmark runner."""

import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import numpy as np
from tqdm import tqdm
from loguru import logger
import yaml

from src.zkp_techniques.base import ZKPTechnique
from src.zkp_techniques.stark_real import STARKWrapper
from src.zkp_techniques.groth16_real import Groth16Wrapper
from src.zkp_techniques.zksnark_real import zkSNARKWrapper
from src.zkp_techniques.protostar_real import ProtostarWrapper

# Rust-based implementations (optional, requires compilation)
try:
    from src.zkp_techniques.plonk_real import PLONKWrapper
    from src.zkp_techniques.bulletproofs_real import BulletproofsWrapper
    from src.zkp_techniques.nova_real import NovaWrapper
    from src.zkp_techniques.halo2_real import Halo2Wrapper
    HAS_RUST_ZKP = True
except ImportError:
    logger.warning("Rust ZKP implementations not available. Some techniques will be skipped.")
    logger.warning("To enable all techniques, build Rust bindings: cd rust_zkp && maturin develop --release")
    PLONKWrapper = None
    BulletproofsWrapper = None
    NovaWrapper = None
    Halo2Wrapper = None
    HAS_RUST_ZKP = False
from src.tensor_ops.generator import TensorGenerator
from src.tensor_ops.operations import (
    matrix_multiplication, tensor_contraction, element_wise_ops,
    tensor_decomposition, convolution_2d
)
from .metrics import MetricsCollector
from .profiler import MemoryProfiler


class BenchmarkRunner:
    """Run comprehensive ZKP benchmarks."""

    def __init__(self, config_path: str = "configs/benchmark_config.yaml"):
        """Initialize benchmark runner.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.results = []
        self.tensor_gen = TensorGenerator(seed=42)
        self.metrics_collector = MetricsCollector()
        self.memory_profiler = MemoryProfiler()
        
        # Initialize ZKP techniques
        self.techniques = self._initialize_techniques()
        
        logger.info(f"BenchmarkRunner initialized with {len(self.techniques)} techniques")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "tensor_sizes": {
                "small": {"2d": [10, 10], "elements": 100},
                "medium": {"2d": [50, 50], "elements": 2500},
                "large": {"2d": [100, 100], "elements": 10000},
            },
            "operations": [
                {"name": "matrix_multiplication", "enabled": True},
            ],
            "benchmark": {"trials_per_config": 5, "timeout_seconds": 3600},
            # Groth16 is disabled by default because the current implementation
            # is a simplified prototype and may fail verification. Enable explicitly
            # in your config only after replacing with a verified implementation.
            "enable_groth16": False,
        }

    def _initialize_techniques(self) -> Dict[str, ZKPTechnique]:
        """Initialize all ZKP technique wrappers."""
        techniques = {}
        
        # Python-based implementations (always available)
        techniques["STARK"] = STARKWrapper()
        techniques["zkSNARK"] = zkSNARKWrapper()
        techniques["Protostar"] = ProtostarWrapper()
        
        # Groth16 - optional, disabled by default
        if self.config.get("enable_groth16", False):
            try:
                techniques["Groth16"] = Groth16Wrapper()
                logger.info("Groth16 enabled (note: simplified prototype)")
            except Exception as e:
                logger.error(f"Failed to initialize Groth16: {e}")
        
        # Rust-based implementations (requires compilation)
        if HAS_RUST_ZKP:
            if PLONKWrapper:
                try:
                    techniques["PLONK"] = PLONKWrapper()
                except Exception as e:
                    logger.warning(f"Failed to initialize PLONK: {e}")
            
            if BulletproofsWrapper:
                try:
                    techniques["Bulletproofs"] = BulletproofsWrapper()
                except Exception as e:
                    logger.warning(f"Failed to initialize Bulletproofs: {e}")
            
            if NovaWrapper:
                try:
                    techniques["Nova"] = NovaWrapper()
                except Exception as e:
                    logger.warning(f"Failed to initialize Nova: {e}")
            
            if Halo2Wrapper:
                try:
                    techniques["Halo2"] = Halo2Wrapper()
                except Exception as e:
                    logger.warning(f"Failed to initialize Halo2: {e}")
        else:
            logger.info("Rust ZKP bindings not available. Only Python implementations will be tested.")
            logger.info("To enable all techniques, build Rust bindings: cd rust_zkp && maturin develop --release")
        
        # Filter based on config
        if "zkp_techniques" in self.config:
            enabled = {t["name"] for t in self.config["zkp_techniques"] if t.get("enabled", True)}
            techniques = {k: v for k, v in techniques.items() if k in enabled}
        
        return techniques

    def run_full_suite(self, output_dir: str = "data/raw") -> str:
        """Run complete benchmark suite.
        
        Args:
            output_dir: Directory to save results
            
        Returns:
            Path to results file
        """
        logger.info("Starting full benchmark suite")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        tensor_sizes = self.config.get("tensor_sizes", {})
        operations = self.config.get("operations", [])
        trials = self.config["benchmark"].get("trials_per_config", 5)
        
        total_runs = len(self.techniques) * len(tensor_sizes) * len(operations) * trials
        
        with tqdm(total=total_runs, desc="Running benchmarks") as pbar:
            for technique_name, technique in self.techniques.items():
                for size_name, size_config in tensor_sizes.items():
                    for operation in operations:
                        if not operation.get("enabled", True):
                            continue
                        
                        op_name = operation["name"]
                        
                        for trial in range(trials):
                            try:
                                result = self._run_single_benchmark(
                                    technique_name,
                                    technique,
                                    size_name,
                                    size_config,
                                    op_name,
                                    trial
                                )
                                self.results.append(result)
                            except Exception as e:
                                logger.error(f"Error in {technique_name}/{size_name}/{op_name}: {e}")
                            
                            pbar.update(1)
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = Path(output_dir) / f"results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Benchmark complete. Results saved to {results_file}")
        return str(results_file)

    def _run_single_benchmark(
        self,
        technique_name: str,
        technique: ZKPTechnique,
        size_name: str,
        size_config: Dict,
        operation_name: str,
        trial: int
    ) -> Dict[str, Any]:
        """Run a single benchmark configuration.
        
        Returns:
            Dictionary with benchmark results
        """
        # Generate test data
        tensor_dims = size_config["2d"]
        A = self.tensor_gen.generate_matrix(tensor_dims[0], tensor_dims[1])
        B = self.tensor_gen.generate_matrix(tensor_dims[1], tensor_dims[0])
        
        # Perform operation to get expected result
        if operation_name == "matrix_multiplication":
            op_result = matrix_multiplication(A, B)
        else:
            op_result = {"result": A, "operation": operation_name}
        
        # Setup ZKP technique
        circuit_size = size_config["elements"]
        setup_time = technique.setup(circuit_size)
        
        # Generate proof
        with self.memory_profiler.profile() as mem_usage:
            proof_result = technique.generate_proof(
                public_inputs=op_result["output_shape"] if "output_shape" in op_result else None,
                private_inputs=A,
                circuit_description=operation_name
            )
        
        # Verify proof
        verify_result = technique.verify_proof(
            proof=proof_result.proof,
            public_inputs=op_result.get("output_shape")
        )
        
        # Collect metrics
        result = {
            "technique": technique_name,
            "tensor_size": size_name,
            "tensor_dimensions": tensor_dims,
            "operation": operation_name,
            "trial": trial,
            "proof_gen_time_ms": proof_result.generation_time_ms,
            "verification_time_ms": verify_result.verification_time_ms,
            "proof_size_bytes": proof_result.proof_size_bytes,
            "memory_usage_mb": mem_usage.peak_mb,
            "setup_time_ms": setup_time,
            "is_valid": verify_result.is_valid,
            "timestamp": time.time(),
            "total_ops": op_result.get("total_ops", circuit_size),
        }
        
        return result

    def run_single_test(
        self,
        technique_name: str,
        size_name: str = "small",
        operation: str = "matrix_multiplication"
    ) -> Dict[str, Any]:
        """Run a single test for debugging/development.
        
        Args:
            technique_name: Name of ZKP technique
            size_name: Tensor size configuration
            operation: Operation to test
            
        Returns:
            Benchmark result dictionary
        """
        if technique_name not in self.techniques:
            raise ValueError(f"Unknown technique: {technique_name}")
        
        technique = self.techniques[technique_name]
        size_config = self.config["tensor_sizes"][size_name]
        
        return self._run_single_benchmark(
            technique_name,
            technique,
            size_name,
            size_config,
            operation,
            trial=0
        )
