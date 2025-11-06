"""Main visualization dashboard."""

import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional
import pandas as pd
from loguru import logger

from .charts import (
    plot_scaling_comparison,
    plot_verification_times,
    plot_proof_sizes,
    plot_memory_heatmap,
    plot_tradeoff_analysis,
    plot_performance_radar,
    plot_scalability_factor,
    plot_timeline_comparison,
)


class Dashboard:
    """Generate all visualizations for benchmark results."""
    
    def __init__(self, stats: pd.DataFrame, output_dir: str = "results/charts"):
        """Initialize dashboard.
        
        Args:
            stats: Statistics DataFrame from analyzer
            output_dir: Directory to save charts
        """
        self.stats = stats
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        sns.set_theme(style="whitegrid", palette="colorblind")
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['font.size'] = 12
        
        logger.info(f"Dashboard initialized. Charts will be saved to {output_dir}")
    
    def generate_all_charts(self):
        """Generate all 8 charts from the evaluation plan."""
        logger.info("Generating all charts...")
        
        charts = [
            ("scaling_comparison", plot_scaling_comparison),
            ("verification_times", plot_verification_times),
            ("proof_sizes", plot_proof_sizes),
            ("memory_heatmap", plot_memory_heatmap),
            ("tradeoff_analysis", plot_tradeoff_analysis),
            ("performance_radar", plot_performance_radar),
            ("scalability_factor", plot_scalability_factor),
            ("timeline_comparison", plot_timeline_comparison),
        ]
        
        for name, plot_func in charts:
            try:
                fig = plot_func(self.stats)
                output_path = self.output_dir / f"{name}.png"
                fig.savefig(output_path, bbox_inches='tight', dpi=300)
                plt.close(fig)
                logger.info(f"Generated {name}.png")
            except Exception as e:
                logger.error(f"Error generating {name}: {e}")
        
        logger.info("All charts generated successfully")
    
    def generate_chart(self, chart_name: str):
        """Generate a specific chart.
        
        Args:
            chart_name: Name of the chart to generate
        """
        chart_funcs = {
            "scaling_comparison": plot_scaling_comparison,
            "verification_times": plot_verification_times,
            "proof_sizes": plot_proof_sizes,
            "memory_heatmap": plot_memory_heatmap,
            "tradeoff_analysis": plot_tradeoff_analysis,
            "performance_radar": plot_performance_radar,
            "scalability_factor": plot_scalability_factor,
            "timeline_comparison": plot_timeline_comparison,
        }
        
        if chart_name not in chart_funcs:
            raise ValueError(f"Unknown chart: {chart_name}")
        
        fig = chart_funcs[chart_name](self.stats)
        output_path = self.output_dir / f"{chart_name}.png"
        fig.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close(fig)
        
        logger.info(f"Generated {chart_name}.png")
        return output_path
