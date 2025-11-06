"""Result analysis and aggregation."""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger


class ResultAnalyzer:
    """Analyze benchmark results and compute statistics."""
    
    def __init__(self, results_file: Optional[str] = None, results_data: Optional[List[Dict]] = None):
        """Initialize analyzer.
        
        Args:
            results_file: Path to JSON results file
            results_data: Direct results data (alternative to file)
        """
        if results_file:
            with open(results_file, 'r') as f:
                self.results = json.load(f)
        elif results_data:
            self.results = results_data
        else:
            raise ValueError("Must provide either results_file or results_data")
        
        self.df = pd.DataFrame(self.results)
        logger.info(f"Loaded {len(self.results)} benchmark results")
    
    def compute_statistics(self) -> pd.DataFrame:
        """Compute aggregate statistics for all configurations.
        
        Returns:
            DataFrame with statistics
        """
        stats = self.df.groupby(['technique', 'tensor_size', 'operation']).agg({
            'proof_gen_time_ms': ['mean', 'median', 'std', 'min', 'max'],
            'verification_time_ms': ['mean', 'median', 'std'],
            'proof_size_bytes': ['mean', 'std'],
            'memory_usage_mb': ['mean', 'max'],
            'total_ops': 'first',
            'is_valid': 'sum',
            'trial': 'count'
        }).reset_index()
        
        stats.columns = ['_'.join(col).strip('_') for col in stats.columns.values]
        stats['success_rate'] = stats['is_valid_sum'] / stats['trial_count']
        
        return stats
    
    def get_technique_comparison(self, metric: str = 'proof_gen_time_ms') -> pd.DataFrame:
        """Compare techniques across all configurations.
        
        Args:
            metric: Metric to compare
            
        Returns:
            Pivot table with techniques vs tensor sizes
        """
        pivot = self.df.pivot_table(
            values=metric,
            index='tensor_size',
            columns='technique',
            aggfunc='mean'
        )
        return pivot
    
    def get_scaling_analysis(self, technique: str) -> pd.DataFrame:
        """Analyze how a technique scales with tensor size.
        
        Args:
            technique: Technique name
            
        Returns:
            DataFrame with scaling metrics
        """
        subset = self.df[self.df['technique'] == technique]
        
        # Group by tensor size
        scaling = subset.groupby('tensor_size').agg({
            'proof_gen_time_ms': 'mean',
            'verification_time_ms': 'mean',
            'proof_size_bytes': 'mean',
            'memory_usage_mb': 'mean',
            'total_ops': 'first'
        }).reset_index()
        
        # Compute scaling factors
        if len(scaling) > 1:
            baseline = scaling.iloc[0]
            for metric in ['proof_gen_time_ms', 'verification_time_ms', 'memory_usage_mb']:
                scaling[f'{metric}_ratio'] = scaling[metric] / baseline[metric]
        
        return scaling
    
    def export_summary(self, output_file: str):
        """Export summary statistics to CSV.
        
        Args:
            output_file: Output file path
        """
        from pathlib import Path
        
        # Ensure parent directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        stats = self.compute_statistics()
        stats.to_csv(output_file, index=False)
        logger.info(f"Summary exported to {output_file}")
    
    def get_best_technique(
        self,
        metric: str = 'proof_gen_time_ms',
        tensor_size: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find the best performing technique for a given metric.
        
        Args:
            metric: Metric to optimize
            tensor_size: Specific tensor size (optional)
            
        Returns:
            Dictionary with best technique info
        """
        subset = self.df
        if tensor_size:
            subset = subset[subset['tensor_size'] == tensor_size]
        
        technique_means = subset.groupby('technique')[metric].mean()
        best_technique = technique_means.idxmin()
        best_value = technique_means.min()
        
        return {
            "technique": best_technique,
            "value": best_value,
            "metric": metric,
            "tensor_size": tensor_size or "all"
        }
