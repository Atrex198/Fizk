#!/usr/bin/env python3
"""
Groth16 Utilities
==================

Helper functions for serialization, configuration, and common operations.

Author: ZKP-FL Framework
Version: 1.0.0
"""

import json
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load Groth16 configuration from YAML or JSON
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    if path.suffix in ['.yaml', '.yml']:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            config = json.load(f)
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}")
    
    logger.info(f"✅ Config loaded from {config_path}")
    return config


def save_config(config: Dict[str, Any], config_path: str):
    """Save configuration to file"""
    path = Path(config_path)
    
    if path.suffix in ['.yaml', '.yml']:
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    elif path.suffix == '.json':
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}")
    
    logger.info(f"💾 Config saved to {config_path}")


def get_default_config(num_model_params: int, num_clients: int = 1) -> Dict[str, Any]:
    """
    Get default Groth16 configuration
    
    Args:
        num_model_params: Number of model parameters
        num_clients: Number of FL clients
    
    Returns:
        Default configuration
    """
    return {
        'protocol': 'groth16',
        'security_level': 128,
        'curve_name': 'BN128',
        'optimization_level': 'balanced',
        'num_model_params': num_model_params,
        'num_clients': num_clients,
        'num_rounds': 1,
        'trusted_setup': {
            'method': 'development',  # 'development' or 'mpc_ceremony'
            'participants': 1,
            'seed': None
        },
        'performance': {
            'parallel_proving': False,
            'constraint_optimization': True
        },
        'logging': {
            'level': 'INFO',
            'log_to_file': True,
            'log_file': 'groth16.log'
        }
    }


def estimate_resources(num_params: int, num_clients: int, num_rounds: int) -> Dict[str, Any]:
    """
    Estimate computational resources for Groth16
    
    Args:
        num_params: Number of model parameters
        num_clients: Number of clients
        num_rounds: Number of FL rounds
    
    Returns:
        Resource estimates
    """
    # Constraint count estimation (from FL_CIRCUIT_ENCODING_STANDARD.md)
    constraints_per_param = 5  # Forward, backward, update, aggregation
    total_constraints = num_params * constraints_per_param * num_clients * num_rounds
    
    # Memory estimation (rough)
    constraint_memory_kb = total_constraints * 0.1  # ~100 bytes per constraint
    witness_memory_kb = num_params * num_clients * 0.008  # ~8 bytes per value
    
    # Time estimation (rough, hardware-dependent)
    setup_time_minutes = total_constraints / 10000  # ~10k constraints/minute
    proof_time_seconds = total_constraints / 1000  # ~1k constraints/second
    verification_time_ms = 2.5  # Constant for Groth16
    
    return {
        'constraint_count': total_constraints,
        'memory': {
            'constraint_system_kb': constraint_memory_kb,
            'witness_kb': witness_memory_kb,
            'total_kb': constraint_memory_kb + witness_memory_kb,
            'total_mb': (constraint_memory_kb + witness_memory_kb) / 1024
        },
        'time': {
            'setup_minutes': setup_time_minutes,
            'proof_generation_seconds': proof_time_seconds,
            'verification_ms': verification_time_ms
        },
        'proof_size_bytes': 128,
        'verification_key_size_kb': num_params * 0.032  # ~32 bytes per param
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate Groth16 configuration
    
    Args:
        config: Configuration to validate
    
    Returns:
        True if valid, raises ValueError otherwise
    """
    required_fields = ['num_model_params']
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate ranges
    if config['num_model_params'] <= 0:
        raise ValueError("num_model_params must be positive")
    
    if 'security_level' in config:
        if config['security_level'] not in [80, 128, 192, 256]:
            raise ValueError("security_level must be 80, 128, 192, or 256")
    
    if 'curve_name' in config:
        if config['curve_name'] not in ['BN128', 'BLS12_381']:
            logger.warning(f"Unsupported curve: {config['curve_name']}, using BN128")
            config['curve_name'] = 'BN128'
    
    logger.info("✅ Configuration validated")
    return True


def format_proof_size(size_bytes: int) -> str:
    """Format proof size in human-readable form"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def format_time(time_seconds: float) -> str:
    """Format time in human-readable form"""
    if time_seconds < 0.001:
        return f"{time_seconds * 1000000:.2f} μs"
    elif time_seconds < 1:
        return f"{time_seconds * 1000:.2f} ms"
    elif time_seconds < 60:
        return f"{time_seconds:.2f} s"
    else:
        minutes = int(time_seconds // 60)
        seconds = time_seconds % 60
        return f"{minutes}m {seconds:.2f}s"


def setup_logging(config: Dict[str, Any]):
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    level = log_config.get('level', 'INFO')
    
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if log_config.get('log_to_file', False):
        log_file = log_config.get('log_file', 'groth16.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)
        logger.info(f"📝 Logging to {log_file}")


class Groth16Stats:
    """Statistics tracker for Groth16 operations"""
    
    def __init__(self):
        self.proofs_generated = 0
        self.proofs_verified = 0
        self.total_proof_time = 0.0
        self.total_verification_time = 0.0
        self.constraint_count = 0
    
    def record_proof(self, time_seconds: float, constraints: int):
        """Record proof generation"""
        self.proofs_generated += 1
        self.total_proof_time += time_seconds
        self.constraint_count = max(self.constraint_count, constraints)
    
    def record_verification(self, time_seconds: float):
        """Record verification"""
        self.proofs_verified += 1
        self.total_verification_time += time_seconds
    
    def get_summary(self) -> Dict[str, Any]:
        """Get statistics summary"""
        avg_proof_time = (
            self.total_proof_time / self.proofs_generated
            if self.proofs_generated > 0 else 0
        )
        avg_verification_time = (
            self.total_verification_time / self.proofs_verified
            if self.proofs_verified > 0 else 0
        )
        
        return {
            'proofs_generated': self.proofs_generated,
            'proofs_verified': self.proofs_verified,
            'constraint_count': self.constraint_count,
            'avg_proof_time_seconds': avg_proof_time,
            'avg_verification_time_seconds': avg_verification_time,
            'total_proof_time_seconds': self.total_proof_time,
            'total_verification_time_seconds': self.total_verification_time
        }
    
    def print_summary(self):
        """Print statistics summary"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("Groth16 Performance Summary")
        print("=" * 60)
        print(f"Proofs generated:       {summary['proofs_generated']}")
        print(f"Proofs verified:        {summary['proofs_verified']}")
        print(f"Constraint count:       {summary['constraint_count']:,}")
        print(f"Avg proof time:         {format_time(summary['avg_proof_time_seconds'])}")
        print(f"Avg verification time:  {format_time(summary['avg_verification_time_seconds'])}")
        print(f"Total proof time:       {format_time(summary['total_proof_time_seconds'])}")
        print(f"Total verify time:      {format_time(summary['total_verification_time_seconds'])}")
        print("=" * 60 + "\n")
