"""Chart generation functions for all 8 visualizations."""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib.figure import Figure


def plot_scaling_comparison(stats: pd.DataFrame) -> Figure:
    """Chart 1: Proof Generation Time vs Tensor Size (log-log scale)."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get unique techniques and sizes
    for technique in stats['technique'].unique():
        subset = stats[stats['technique'] == technique]
        
        # Extract size order (small, medium, large, etc.)
        sizes = subset['tensor_size'].values
        times = subset['proof_gen_time_ms_mean'].values
        
        ax.plot(sizes, times, marker='o', label=technique, linewidth=2)
    
    ax.set_xlabel('Tensor Size', fontsize=14)
    ax.set_ylabel('Proof Generation Time (ms)', fontsize=14)
    ax.set_title('Proof Generation Time Scaling Comparison', fontsize=16, fontweight='bold')
    ax.legend(loc='best', frameon=True)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    
    return fig


def plot_verification_times(stats: pd.DataFrame) -> Figure:
    """Chart 2: Verification Time Comparison (grouped bar chart)."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Prepare data for grouped bar chart
    pivot = stats.pivot_table(
        values='verification_time_ms_mean',
        index='technique',
        columns='tensor_size'
    )
    
    pivot.plot(kind='bar', ax=ax, width=0.8)
    
    ax.set_xlabel('ZKP Technique', fontsize=14)
    ax.set_ylabel('Verification Time (ms)', fontsize=14)
    ax.set_title('Verification Time Comparison Across Tensor Sizes', fontsize=16, fontweight='bold')
    ax.legend(title='Tensor Size', frameon=True)
    ax.grid(True, axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    return fig


def plot_proof_sizes(stats: pd.DataFrame) -> Figure:
    """Chart 3: Proof Size Distribution (box plot)."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create box plot
    techniques = stats['technique'].unique()
    proof_sizes = [
        stats[stats['technique'] == tech]['proof_size_bytes_mean'].values
        for tech in techniques
    ]
    
    bp = ax.boxplot(proof_sizes, labels=techniques, patch_artist=True)
    
    # Color boxes
    colors = sns.color_palette("colorblind", len(techniques))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_xlabel('ZKP Technique', fontsize=14)
    ax.set_ylabel('Proof Size (bytes)', fontsize=14)
    ax.set_title('Proof Size Distribution', fontsize=16, fontweight='bold')
    ax.grid(True, axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    return fig


def plot_memory_heatmap(stats: pd.DataFrame) -> Figure:
    """Chart 4: Memory Consumption Heatmap."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create pivot table for heatmap
    heatmap_data = stats.pivot_table(
        values='memory_usage_mb_mean',
        index='technique',
        columns='tensor_size'
    )
    
    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt='.1f',
        cmap='YlOrRd',
        cbar_kws={'label': 'Memory Usage (MB)'},
        ax=ax
    )
    
    ax.set_xlabel('Tensor Size', fontsize=14)
    ax.set_ylabel('ZKP Technique', fontsize=14)
    ax.set_title('Memory Consumption Heatmap', fontsize=16, fontweight='bold')
    plt.yticks(rotation=0)
    
    return fig


def plot_tradeoff_analysis(stats: pd.DataFrame) -> Figure:
    """Chart 5: Performance-Size Trade-off (scatter plot)."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Scatter plot with different colors for each technique
    techniques = stats['technique'].unique()
    colors = sns.color_palette("colorblind", len(techniques))
    
    for i, technique in enumerate(techniques):
        subset = stats[stats['technique'] == technique]
        ax.scatter(
            subset['proof_size_bytes_mean'],
            subset['proof_gen_time_ms_mean'],
            label=technique,
            s=100,
            alpha=0.6,
            color=colors[i]
        )
    
    ax.set_xlabel('Proof Size (bytes)', fontsize=14)
    ax.set_ylabel('Proof Generation Time (ms)', fontsize=14)
    ax.set_title('Proof Size vs Generation Time Trade-off', fontsize=16, fontweight='bold')
    ax.legend(loc='best', frameon=True)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    return fig


def plot_performance_radar(stats: pd.DataFrame) -> Figure:
    """Chart 7: Composite Performance Score (radar/spider chart)."""
    from math import pi
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Normalize metrics (inverse for times - lower is better)
    metrics = ['proof_gen_time_ms_mean', 'verification_time_ms_mean', 
               'proof_size_bytes_mean', 'memory_usage_mb_mean']
    
    # Aggregate by technique
    technique_stats = stats.groupby('technique')[metrics].mean()
    
    # Normalize (inverse and scale to 0-1)
    for col in metrics:
        max_val = technique_stats[col].max()
        technique_stats[col + '_norm'] = 1 - (technique_stats[col] / max_val)
    
    # Setup radar chart
    categories = ['Speed\n(Gen)', 'Speed\n(Verify)', 'Size\n(Proof)', 'Memory']
    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12)
    
    # Plot each technique
    colors = sns.color_palette("colorblind", len(technique_stats))
    for i, (technique, row) in enumerate(technique_stats.iterrows()):
        values = [row[m + '_norm'] for m in metrics]
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=technique, color=colors[i])
        ax.fill(angles, values, alpha=0.15, color=colors[i])
    
    ax.set_ylim(0, 1)
    ax.set_title('Composite Performance Comparison\n(Normalized - Larger is Better)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    ax.grid(True)
    
    return fig


def plot_scalability_factor(stats: pd.DataFrame) -> Figure:
    """Chart 6: Scalability Factor Analysis."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Calculate time increase ratio from smallest to largest size
    size_order = ['small', 'medium', 'large', 'very_large', 'extreme']
    available_sizes = [s for s in size_order if s in stats['tensor_size'].values]
    
    for technique in stats['technique'].unique():
        subset = stats[stats['technique'] == technique]
        subset = subset[subset['tensor_size'].isin(available_sizes)]
        subset = subset.sort_values('tensor_size', 
                                    key=lambda x: x.map({s: i for i, s in enumerate(available_sizes)}))
        
        if len(subset) > 0:
            times = subset['proof_gen_time_ms_mean'].values
            baseline = times[0] if len(times) > 0 else 1
            ratios = times / baseline
            
            ax.plot(range(len(ratios)), ratios, marker='o', label=technique, linewidth=2)
    
    ax.set_xlabel('Tensor Size Step', fontsize=14)
    ax.set_ylabel('Time Increase Ratio (vs Smallest)', fontsize=14)
    ax.set_title('Scalability Factor: Performance Degradation', fontsize=16, fontweight='bold')
    ax.set_xticks(range(len(available_sizes)))
    ax.set_xticklabels(available_sizes, rotation=45)
    ax.legend(loc='best', frameon=True)
    ax.grid(True, alpha=0.3)
    
    return fig


def plot_timeline_comparison(stats: pd.DataFrame) -> Figure:
    """Chart 8: Timeline Comparison (stacked area)."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get average times by technique
    timeline_data = stats.groupby('technique').agg({
        'proof_gen_time_ms_mean': 'mean',
        'verification_time_ms_mean': 'mean',
    }).reset_index()
    
    # Add setup time (mock for techniques that need it)
    setup_times = {
        'STARK': 0, 'Groth16': 10, 'PLONK': 5, 'Bulletproofs': 0,
        'Halo2': 0, 'Protostar': 0, 'zkSNARK': 8, 'Nova': 0
    }
    timeline_data['setup_time'] = timeline_data['technique'].map(setup_times)
    
    # Create stacked bar chart
    techniques = timeline_data['technique']
    x_pos = np.arange(len(techniques))
    
    p1 = ax.bar(x_pos, timeline_data['setup_time'], label='Setup')
    p2 = ax.bar(x_pos, timeline_data['proof_gen_time_ms_mean'], 
                bottom=timeline_data['setup_time'], label='Proof Generation')
    p3 = ax.bar(x_pos, timeline_data['verification_time_ms_mean'],
                bottom=timeline_data['setup_time'] + timeline_data['proof_gen_time_ms_mean'],
                label='Verification')
    
    ax.set_xlabel('ZKP Technique', fontsize=14)
    ax.set_ylabel('Cumulative Time (ms)', fontsize=14)
    ax.set_title('Total Overhead: Setup + Generation + Verification', fontsize=16, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(techniques, rotation=45, ha='right')
    ax.legend(loc='best', frameon=True)
    ax.grid(True, axis='y', alpha=0.3)
    
    return fig
