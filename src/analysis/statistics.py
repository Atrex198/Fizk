"""Statistical analysis tools."""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any


class StatisticalAnalyzer:
    """Perform statistical analysis on benchmark results."""
    
    def __init__(self, significance_level: float = 0.05):
        """Initialize statistical analyzer.
        
        Args:
            significance_level: Alpha for hypothesis tests
        """
        self.alpha = significance_level
    
    def confidence_interval(
        self,
        data: np.ndarray,
        confidence: float = 0.95
    ) -> Tuple[float, float, float]:
        """Compute confidence interval for data.
        
        Args:
            data: Data array
            confidence: Confidence level
            
        Returns:
            Tuple of (mean, lower_bound, upper_bound)
        """
        mean = np.mean(data)
        sem = stats.sem(data)
        margin = sem * stats.t.ppf((1 + confidence) / 2, len(data) - 1)
        
        return mean, mean - margin, mean + margin
    
    def compare_techniques(
        self,
        data1: np.ndarray,
        data2: np.ndarray,
        technique1: str,
        technique2: str
    ) -> Dict[str, Any]:
        """Compare two techniques using t-test.
        
        Args:
            data1: Data from first technique
            data2: Data from second technique
            technique1: Name of first technique
            technique2: Name of second technique
            
        Returns:
            Dictionary with comparison results
        """
        t_stat, p_value = stats.ttest_ind(data1, data2)
        
        is_significant = p_value < self.alpha
        better = technique1 if np.mean(data1) < np.mean(data2) else technique2
        
        return {
            "technique1": technique1,
            "technique2": technique2,
            "mean1": np.mean(data1),
            "mean2": np.mean(data2),
            "t_statistic": t_stat,
            "p_value": p_value,
            "is_significant": is_significant,
            "better_technique": better if is_significant else None,
            "effect_size": self._cohens_d(data1, data2)
        }
    
    def _cohens_d(self, data1: np.ndarray, data2: np.ndarray) -> float:
        """Compute Cohen's d effect size."""
        n1, n2 = len(data1), len(data2)
        var1, var2 = np.var(data1, ddof=1), np.var(data2, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        return (np.mean(data1) - np.mean(data2)) / pooled_std
    
    def anova_techniques(
        self,
        df: pd.DataFrame,
        metric: str = 'proof_gen_time_ms'
    ) -> Dict[str, Any]:
        """Perform ANOVA to compare multiple techniques.
        
        Args:
            df: DataFrame with results
            metric: Metric to compare
            
        Returns:
            ANOVA results
        """
        groups = [group[metric].values for name, group in df.groupby('technique')]
        f_stat, p_value = stats.f_oneway(*groups)
        
        return {
            "f_statistic": f_stat,
            "p_value": p_value,
            "is_significant": p_value < self.alpha,
            "num_groups": len(groups)
        }
    
    def fit_scaling_curve(
        self,
        sizes: np.ndarray,
        times: np.ndarray
    ) -> Dict[str, Any]:
        """Fit polynomial to scaling data.
        
        Args:
            sizes: Tensor sizes
            times: Corresponding times
            
        Returns:
            Fitted curve parameters
        """
        # Try linear, log-linear, and quadratic
        log_sizes = np.log(sizes)
        
        # Linear fit
        linear_coef = np.polyfit(sizes, times, 1)
        linear_r2 = self._r_squared(sizes, times, linear_coef)
        
        # Log-linear fit
        log_linear_coef = np.polyfit(log_sizes, times, 1)
        log_linear_r2 = self._r_squared(log_sizes, times, log_linear_coef)
        
        # Quadratic fit
        quad_coef = np.polyfit(sizes, times, 2)
        quad_r2 = self._r_squared(sizes, times, quad_coef)
        
        # Determine best fit
        fits = [
            ("linear", linear_coef, linear_r2),
            ("log_linear", log_linear_coef, log_linear_r2),
            ("quadratic", quad_coef, quad_r2)
        ]
        
        best_fit = max(fits, key=lambda x: x[2])
        
        return {
            "best_fit_type": best_fit[0],
            "coefficients": best_fit[1].tolist(),
            "r_squared": best_fit[2],
            "all_fits": {name: {"coef": coef.tolist(), "r2": r2} for name, coef, r2 in fits}
        }
    
    def _r_squared(self, x: np.ndarray, y: np.ndarray, coef: np.ndarray) -> float:
        """Compute R-squared for polynomial fit."""
        y_pred = np.polyval(coef, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot)
