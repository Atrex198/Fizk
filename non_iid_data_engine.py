"""
Non-IID Data Partitioning Engine for Federated Learning Research
Implements sophisticated data heterogeneity simulation using Dirichlet distributions
"""

import numpy as np
import pandas as pd
import torch
from typing import List, Dict, Tuple, Optional, Any
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class NonIIDDataEngine:
    """
    Advanced Non-IID Data Partitioning Engine for Realistic Federated Learning
    
    Supports multiple heterogeneity types:
    - Label distribution skew (Dirichlet-based)
    - Feature distribution shifts
    - Quantity imbalance across clients
    - Temporal pattern differences
    """
    
    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        np.random.seed(random_seed)
        torch.manual_seed(random_seed)
        
        self.partition_stats = {}
        self.heterogeneity_metrics = {}
        
        logger.info(f"🔄 Non-IID Data Engine initialized with seed {random_seed}")
    
    def load_and_prepare_dataset(self, csv_path: str = 'heart_2020_cleaned.csv', 
                                target_column: str = 'HeartDisease') -> Tuple[torch.Tensor, torch.Tensor, List[str]]:
        """Load and prepare dataset for non-IID partitioning"""
        
        logger.info(f"📊 Loading dataset from {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"✅ Loaded dataset: {len(df)} samples, {len(df.columns)} features")
        except FileNotFoundError:
            logger.error(f"❌ Dataset not found: {csv_path}")
            raise
        
        # Prepare features and target
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        if target_column in categorical_columns:
            categorical_columns.remove(target_column)
        
        logger.info(f"📊 Encoding {len(categorical_columns)} categorical columns")
        
        # Encode categorical variables
        df_encoded = df.copy()
        feature_names = []
        
        for col in df.columns:
            if col == target_column:
                continue
                
            if col in categorical_columns:
                # Binary encoding for Yes/No columns
                unique_vals = df_encoded[col].unique()
                if len(unique_vals) == 2 and 'Yes' in unique_vals and 'No' in unique_vals:
                    df_encoded[col] = (df_encoded[col] == 'Yes').astype(int)
                    feature_names.append(f"{col}_binary")
                else:
                    # Label encoding for other categorical variables
                    le = LabelEncoder()
                    df_encoded[col] = le.fit_transform(df_encoded[col])
                    feature_names.append(f"{col}_encoded")
            else:
                feature_names.append(col)
        
        # Extract features and target
        feature_columns = [col for col in df_encoded.columns if col != target_column]
        X = df_encoded[feature_columns].values.astype(float)
        y = (df_encoded[target_column] == 'Yes').astype(int).values
        
        # Normalize features
        scaler = MinMaxScaler()
        X = scaler.fit_transform(X)
        
        # Convert to tensors
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y)
        
        logger.info(f"📊 Dataset prepared:")
        logger.info(f"   Features: {X_tensor.shape}")
        logger.info(f"   Target distribution: {(y_tensor == 1).sum().item()}/{len(y_tensor)} positive")
        logger.info(f"   Feature range: [{X_tensor.min():.3f}, {X_tensor.max():.3f}]")
        
        return X_tensor, y_tensor, feature_names
    
    def create_dirichlet_label_skew(self, y: torch.Tensor, num_clients: int, 
                                   alpha: float, min_samples_per_client: int = 100) -> Dict[int, List[int]]:
        """
        Create label distribution skew using Dirichlet distribution
        
        Args:
            y: Target labels
            num_clients: Number of federated clients
            alpha: Dirichlet concentration parameter (lower = more heterogeneous)
            min_samples_per_client: Minimum samples per client
            
        Returns:
            Dictionary mapping client_id to list of sample indices
        """
        
        logger.info(f"🎲 Creating Dirichlet label skew: α={alpha}, {num_clients} clients")
        
        # Get unique classes and their counts
        classes = torch.unique(y).numpy()
        n_classes = len(classes)
        
        logger.info(f"📊 Classes found: {classes} ({n_classes} classes)")
        
        # Group samples by class
        class_indices = {}
        for cls in classes:
            class_indices[cls] = torch.where(y == cls)[0].numpy()
            logger.info(f"   Class {cls}: {len(class_indices[cls])} samples")
        
        # Generate Dirichlet distribution for each class
        client_class_counts = {}
        for cls in classes:
            # Sample from Dirichlet distribution
            proportions = np.random.dirichlet([alpha] * num_clients)
            
            # Convert proportions to actual counts
            total_samples = len(class_indices[cls])
            counts = (proportions * total_samples).astype(int)
            
            # Ensure all samples are assigned
            remainder = total_samples - counts.sum()
            for i in range(remainder):
                counts[i % num_clients] += 1
            
            client_class_counts[cls] = counts
            logger.info(f"   Class {cls} distribution: {counts}")
        
        # Assign samples to clients
        client_indices = {i: [] for i in range(num_clients)}
        
        for cls in classes:
            np.random.shuffle(class_indices[cls])
            start_idx = 0
            
            for client_id in range(num_clients):
                count = client_class_counts[cls][client_id]
                end_idx = start_idx + count
                
                client_samples = class_indices[cls][start_idx:end_idx]
                client_indices[client_id].extend(client_samples.tolist())
                
                start_idx = end_idx
        
        # Shuffle client indices and ensure minimum samples
        for client_id in range(num_clients):
            np.random.shuffle(client_indices[client_id])
            
            if len(client_indices[client_id]) < min_samples_per_client:
                logger.warning(f"⚠️ Client {client_id} has only {len(client_indices[client_id])} samples")
        
        # Calculate and log heterogeneity statistics
        self._calculate_heterogeneity_stats(y, client_indices, alpha)
        
        return client_indices
    
    def create_feature_distribution_skew(self, X: torch.Tensor, y: torch.Tensor, 
                                       client_indices: Dict[int, List[int]], 
                                       feature_skew_factor: float = 0.2) -> Dict[int, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Apply feature distribution skew to create more realistic heterogeneity
        
        Args:
            X: Feature tensor
            y: Target tensor
            client_indices: Client sample assignments
            feature_skew_factor: Strength of feature distribution skew
            
        Returns:
            Dictionary mapping client_id to (X_client, y_client) tensors
        """
        
        logger.info(f"🔄 Applying feature distribution skew (factor={feature_skew_factor})")
        
        client_data = {}
        n_features = X.shape[1]
        
        for client_id, indices in client_indices.items():
            # Get client data
            X_client = X[indices].clone()
            y_client = y[indices].clone()
            
            # Apply feature-specific skew based on client's label distribution
            client_pos_ratio = (y_client == 1).float().mean().item()
            
            # Create client-specific feature shifts
            for feature_idx in range(n_features):
                # Different clients get different feature emphasis
                if client_id % 3 == 0:  # Emphasize certain features for some clients
                    if feature_idx < n_features // 3:
                        shift = feature_skew_factor * (2 * client_pos_ratio - 1)
                        X_client[:, feature_idx] = torch.clamp(X_client[:, feature_idx] + shift, 0, 1)
                elif client_id % 3 == 1:  # Different pattern for other clients
                    if feature_idx >= n_features // 3 and feature_idx < 2 * n_features // 3:
                        shift = feature_skew_factor * (1 - 2 * client_pos_ratio)
                        X_client[:, feature_idx] = torch.clamp(X_client[:, feature_idx] + shift, 0, 1)
                else:  # Third pattern
                    if feature_idx >= 2 * n_features // 3:
                        shift = feature_skew_factor * np.sin(client_pos_ratio * np.pi)
                        X_client[:, feature_idx] = torch.clamp(X_client[:, feature_idx] + shift, 0, 1)
            
            client_data[client_id] = (X_client, y_client)
            
            logger.info(f"   Client {client_id}: {len(indices)} samples, pos_ratio={client_pos_ratio:.3f}")
        
        return client_data
    
    def create_quantity_imbalance(self, client_data: Dict[int, Tuple[torch.Tensor, torch.Tensor]], 
                                imbalance_factor: float = 2.0) -> Dict[int, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Create quantity imbalance across clients to simulate real-world scenarios
        
        Args:
            client_data: Client data dictionary
            imbalance_factor: Factor controlling quantity imbalance
            
        Returns:
            Updated client data with quantity imbalance
        """
        
        logger.info(f"⚖️ Creating quantity imbalance (factor={imbalance_factor})")
        
        num_clients = len(client_data)
        
        # Generate different client sizes based on power law distribution
        client_size_multipliers = np.random.pareto(imbalance_factor, num_clients)
        client_size_multipliers = client_size_multipliers / client_size_multipliers.max()
        client_size_multipliers = 0.3 + 0.7 * client_size_multipliers  # Scale to [0.3, 1.0]
        
        balanced_client_data = {}
        
        for client_id, (X_client, y_client) in client_data.items():
            # Calculate new client size
            original_size = len(X_client)
            new_size = int(original_size * client_size_multipliers[client_id])
            new_size = max(new_size, 50)  # Ensure minimum samples
            
            if new_size < original_size:
                # Randomly sample subset
                indices = torch.randperm(original_size)[:new_size]
                X_client_new = X_client[indices]
                y_client_new = y_client[indices]
            else:
                # Keep original size if would increase
                X_client_new = X_client
                y_client_new = y_client
            
            balanced_client_data[client_id] = (X_client_new, y_client_new)
            
            logger.info(f"   Client {client_id}: {original_size} → {len(X_client_new)} samples")
        
        return balanced_client_data
    
    def _calculate_heterogeneity_stats(self, y: torch.Tensor, client_indices: Dict[int, List[int]], alpha: float):
        """Calculate comprehensive heterogeneity statistics"""
        
        logger.info("📊 Calculating heterogeneity statistics...")
        
        # Label distribution statistics
        client_label_stats = {}
        all_client_distributions = []
        
        for client_id, indices in client_indices.items():
            client_y = y[indices]
            pos_ratio = (client_y == 1).float().mean().item()
            
            client_label_stats[client_id] = {
                'total_samples': len(indices),
                'positive_ratio': pos_ratio,
                'negative_ratio': 1 - pos_ratio
            }
            
            all_client_distributions.append([1 - pos_ratio, pos_ratio])
        
        # Calculate statistical heterogeneity metrics
        distributions = np.array(all_client_distributions)
        
        # Jensen-Shannon Divergence (measure of distribution similarity)
        def kl_divergence(p, q, eps=1e-10):
            return np.sum(p * np.log((p + eps) / (q + eps)))
        
        def js_divergence(p, q):
            m = 0.5 * (p + q)
            return 0.5 * kl_divergence(p, m) + 0.5 * kl_divergence(q, m)
        
        # Calculate average JS divergence between all client pairs
        js_divergences = []
        num_clients = len(client_indices)
        
        for i in range(num_clients):
            for j in range(i + 1, num_clients):
                js_div = js_divergence(distributions[i], distributions[j])
                js_divergences.append(js_div)
        
        avg_js_divergence = np.mean(js_divergences)
        
        # Calculate coefficient of variation for sample sizes
        sample_sizes = [len(indices) for indices in client_indices.values()]
        cv_sample_sizes = np.std(sample_sizes) / np.mean(sample_sizes)
        
        # Calculate Earth Mover's Distance (Wasserstein distance)
        from scipy.stats import wasserstein_distance
        
        # Global distribution
        global_pos_ratio = (y == 1).float().mean().item()
        global_dist = np.array([1 - global_pos_ratio, global_pos_ratio])
        
        # EMD between each client and global distribution
        emd_scores = []
        for dist in distributions:
            emd = wasserstein_distance([0, 1], [0, 1], global_dist, dist)
            emd_scores.append(emd)
        
        avg_emd = np.mean(emd_scores)
        
        # Store comprehensive statistics
        self.heterogeneity_metrics = {
            'alpha': alpha,
            'num_clients': num_clients,
            'avg_js_divergence': avg_js_divergence,
            'coefficient_variation_sizes': cv_sample_sizes,
            'avg_earth_movers_distance': avg_emd,
            'client_label_distributions': client_label_stats,
            'sample_size_stats': {
                'min': min(sample_sizes),
                'max': max(sample_sizes),
                'mean': np.mean(sample_sizes),
                'std': np.std(sample_sizes)
            }
        }
        
        logger.info(f"📊 Heterogeneity Metrics:")
        logger.info(f"   Average JS Divergence: {avg_js_divergence:.4f}")
        logger.info(f"   Coefficient of Variation (sizes): {cv_sample_sizes:.4f}")
        logger.info(f"   Average Earth Mover's Distance: {avg_emd:.4f}")
        logger.info(f"   Sample sizes: {min(sample_sizes)} - {max(sample_sizes)} (μ={np.mean(sample_sizes):.1f})")
    
    def create_non_iid_partition(self, csv_path: str = 'heart_2020_cleaned.csv', 
                                num_clients: int = 4, alpha: float = 0.5,
                                feature_skew_factor: float = 0.1,
                                quantity_imbalance_factor: float = 1.5,
                                target_column: str = 'HeartDisease') -> Dict[str, Any]:
        """
        Create comprehensive non-IID data partition with multiple heterogeneity types
        
        Args:
            csv_path: Path to dataset CSV
            num_clients: Number of federated clients
            alpha: Dirichlet concentration parameter (lower = more heterogeneous)
            feature_skew_factor: Strength of feature distribution skew
            quantity_imbalance_factor: Factor controlling quantity imbalance
            target_column: Name of target column
            
        Returns:
            Complete non-IID partition with metadata
        """
        
        logger.info(f"🚀 Creating Non-IID Partition:")
        logger.info(f"   Clients: {num_clients}")
        logger.info(f"   Alpha: {alpha} ({'High' if alpha < 1 else 'Medium' if alpha < 5 else 'Low'} heterogeneity)")
        logger.info(f"   Feature skew: {feature_skew_factor}")
        logger.info(f"   Quantity imbalance: {quantity_imbalance_factor}")
        
        # Step 1: Load and prepare dataset
        X, y, feature_names = self.load_and_prepare_dataset(csv_path, target_column)
        
        # Step 2: Create label distribution skew using Dirichlet
        client_indices = self.create_dirichlet_label_skew(y, num_clients, alpha)
        
        # Step 3: Apply feature distribution skew
        client_data = self.create_feature_distribution_skew(X, y, client_indices, feature_skew_factor)
        
        # Step 4: Create quantity imbalance
        client_data = self.create_quantity_imbalance(client_data, quantity_imbalance_factor)
        
        # Step 5: Prepare final partition
        partition_result = {
            'client_data': client_data,
            'global_data': (X, y),
            'feature_names': feature_names,
            'partition_config': {
                'num_clients': num_clients,
                'alpha': alpha,
                'feature_skew_factor': feature_skew_factor,
                'quantity_imbalance_factor': quantity_imbalance_factor,
                'random_seed': self.random_seed
            },
            'heterogeneity_metrics': self.heterogeneity_metrics
        }
        
        # Log final statistics
        logger.info(f"✅ Non-IID Partition Created Successfully:")
        for client_id, (X_client, y_client) in client_data.items():
            pos_ratio = (y_client == 1).float().mean().item()
            logger.info(f"   Client {client_id}: {len(X_client)} samples, {pos_ratio:.1%} positive")
        
        return partition_result
    
    def visualize_partition(self, partition_result: Dict[str, Any], save_path: str = None):
        """Create comprehensive visualizations of the non-IID partition"""
        
        logger.info("📊 Creating partition visualizations...")
        
        client_data = partition_result['client_data']
        config = partition_result['partition_config']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Non-IID Data Partition Analysis (α={config["alpha"]})', fontsize=16)
        
        # 1. Label distribution per client
        ax1 = axes[0, 0]
        client_ids = []
        pos_ratios = []
        sample_counts = []
        
        for client_id, (X_client, y_client) in client_data.items():
            client_ids.append(f'Client {client_id}')
            pos_ratios.append((y_client == 1).float().mean().item())
            sample_counts.append(len(X_client))
        
        bars = ax1.bar(client_ids, pos_ratios, color='skyblue', alpha=0.7)
        ax1.set_ylabel('Positive Class Ratio')
        ax1.set_title('Label Distribution Heterogeneity')
        ax1.set_ylim(0, 1)
        
        # Add sample counts on bars
        for i, (bar, count) in enumerate(zip(bars, sample_counts)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{count} samples', ha='center', va='bottom', fontsize=9)
        
        # 2. Sample size distribution
        ax2 = axes[0, 1]
        ax2.bar(client_ids, sample_counts, color='lightcoral', alpha=0.7)
        ax2.set_ylabel('Number of Samples')
        ax2.set_title('Sample Size Distribution')
        
        # 3. Feature distribution comparison (first few features)
        ax3 = axes[1, 0]
        feature_means = {}
        
        for client_id, (X_client, y_client) in client_data.items():
            feature_means[f'Client {client_id}'] = X_client[:, :5].mean(dim=0).numpy()
        
        x_pos = np.arange(5)
        width = 0.15
        
        for i, (client_name, means) in enumerate(feature_means.items()):
            ax3.bar(x_pos + i * width, means, width, 
                   label=client_name, alpha=0.7)
        
        ax3.set_xlabel('Feature Index')
        ax3.set_ylabel('Mean Feature Value')
        ax3.set_title('Feature Distribution Comparison (First 5 Features)')
        ax3.set_xticks(x_pos + width * 1.5)
        ax3.set_xticklabels([f'F{i}' for i in range(5)])
        ax3.legend()
        
        # 4. Heterogeneity metrics summary
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        metrics = partition_result['heterogeneity_metrics']
        metrics_text = f"""
Heterogeneity Analysis:

JS Divergence: {metrics['avg_js_divergence']:.4f}
(Higher = more heterogeneous)

Sample Size CV: {metrics['coefficient_variation_sizes']:.4f}
(Higher = more imbalanced)

Earth Mover's Distance: {metrics['avg_earth_movers_distance']:.4f}
(Higher = more different from global)

Configuration:
• Alpha: {config['alpha']}
• Feature Skew: {config['feature_skew_factor']}
• Quantity Imbalance: {config['quantity_imbalance_factor']}
• Random Seed: {config['random_seed']}
        """
        
        ax4.text(0.1, 0.9, metrics_text, transform=ax4.transAxes, 
                fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"📊 Visualization saved to {save_path}")
        
        plt.show()
    
    def export_partition_metadata(self, partition_result: Dict[str, Any], 
                                 export_path: str = "non_iid_partition_metadata.json"):
        """Export comprehensive partition metadata for reproducibility"""
        
        logger.info(f"💾 Exporting partition metadata to {export_path}")
        
        # Prepare serializable metadata
        metadata = {
            'partition_config': partition_result['partition_config'],
            'heterogeneity_metrics': partition_result['heterogeneity_metrics'],
            'feature_names': partition_result['feature_names'],
            'client_statistics': {}
        }
        
        # Add client-specific statistics
        for client_id, (X_client, y_client) in partition_result['client_data'].items():
            metadata['client_statistics'][f'client_{client_id}'] = {
                'sample_count': int(len(X_client)),
                'positive_class_ratio': float((y_client == 1).float().mean().item()),
                'feature_means': X_client.mean(dim=0).tolist(),
                'feature_stds': X_client.std(dim=0).tolist()
            }
        
        # Save metadata
        with open(export_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Metadata exported successfully")
        
        return metadata

def create_research_scenarios() -> List[Dict[str, Any]]:
    """Create predefined research scenarios for systematic evaluation"""
    
    scenarios = [
        {
            'name': 'High Heterogeneity',
            'description': 'Simulates very different client populations (e.g., specialized hospitals)',
            'config': {
                'alpha': 0.1,
                'feature_skew_factor': 0.3,
                'quantity_imbalance_factor': 3.0
            }
        },
        {
            'name': 'Medium Heterogeneity', 
            'description': 'Realistic federated learning scenario',
            'config': {
                'alpha': 1.0,
                'feature_skew_factor': 0.15,
                'quantity_imbalance_factor': 2.0
            }
        },
        {
            'name': 'Low Heterogeneity',
            'description': 'Nearly IID scenario for baseline comparison',
            'config': {
                'alpha': 10.0,
                'feature_skew_factor': 0.05,
                'quantity_imbalance_factor': 1.2
            }
        },
        {
            'name': 'Extreme Imbalance',
            'description': 'One dominant client with small satellite clients',
            'config': {
                'alpha': 0.01,
                'feature_skew_factor': 0.4,
                'quantity_imbalance_factor': 5.0
            }
        }
    ]
    
    return scenarios

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    engine = NonIIDDataEngine(random_seed=42)
    
    # Create a medium heterogeneity scenario
    partition = engine.create_non_iid_partition(
        num_clients=4,
        alpha=1.0,
        feature_skew_factor=0.15,
        quantity_imbalance_factor=2.0
    )
    
    # Visualize the partition
    engine.visualize_partition(partition, "non_iid_partition_analysis.png")
    
    # Export metadata
    engine.export_partition_metadata(partition)
    
    print("✅ Non-IID Data Engine demonstration completed!")