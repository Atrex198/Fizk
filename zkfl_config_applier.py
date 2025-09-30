#!/usr/bin/env python3
"""
ZK-FL Configuration Applier
Applies configuration changes to the actual ZK-FL system components
"""

import json
import os
import sys
from typing import Dict, Any
from pathlib import Path

class ZKFLConfigApplier:
    """Applies configuration changes to ZK-FL system files"""
    
    def __init__(self, config_file: str = "zkfl_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            print(f"Configuration file {self.config_file} not found!")
            return {}
    
    def apply_to_fl_server(self):
        """Apply configuration to FL server"""
        if not self.config:
            return False
            
        # Read current fl_server.py
        fl_server_file = "fl_server.py"
        if not os.path.exists(fl_server_file):
            print(f"FL server file {fl_server_file} not found!")
            return False
            
        try:
            with open(fl_server_file, 'r') as f:
                content = f.read()
            
            # Update key parameters in the FL server
            replacements = {
                'NUM_CLIENTS = 10': f'NUM_CLIENTS = {self.config.get("num_clients", 10)}',
                'NUM_ROUNDS = 20': f'NUM_ROUNDS = {self.config.get("num_rounds", 20)}',
                'LOCAL_EPOCHS = 5': f'LOCAL_EPOCHS = {self.config.get("local_epochs", 5)}',
                'LEARNING_RATE = 0.001': f'LEARNING_RATE = {self.config.get("learning_rate", 0.001)}',
                'BATCH_SIZE = 32': f'BATCH_SIZE = {self.config.get("batch_size", 32)}',
                'CLIENT_FRACTION = 0.8': f'CLIENT_FRACTION = {self.config.get("client_fraction", 0.8)}'
            }
            
            for old, new in replacements.items():
                if old in content:
                    content = content.replace(old, new)
                    
            # Write back the updated content
            with open(fl_server_file, 'w') as f:
                f.write(content)
                
            print("✅ FL server configuration updated")
            return True
            
        except Exception as e:
            print(f"❌ Error updating FL server: {e}")
            return False
    
    def apply_to_circuit_optimizer(self):
        """Apply configuration to circuit optimizer"""
        try:
            optimizer_file = "advanced_circuit_optimizer.py"
            if not os.path.exists(optimizer_file):
                print(f"Circuit optimizer file {optimizer_file} not found!")
                return False
                
            with open(optimizer_file, 'r') as f:
                content = f.read()
            
            # Update circuit optimization parameters
            replacements = {
                'self.constraint_reduction_factor = 0.4': f'self.constraint_reduction_factor = {self.config.get("constraint_reduction_factor", 0.4)}',
                'self.parallel_workers = 4': f'self.parallel_workers = {self.config.get("parallel_workers", 4)}',
                'self.memory_optimization = True': f'self.memory_optimization = {self.config.get("memory_optimization", True)}',
                'self.batch_size = 8': f'self.batch_size = {self.config.get("batch_processing_size", 8)}'
            }
            
            for old, new in replacements.items():
                if old in content:
                    content = content.replace(old, new)
                    
            with open(optimizer_file, 'w') as f:
                f.write(content)
                
            print("✅ Circuit optimizer configuration updated")
            return True
            
        except Exception as e:
            print(f"❌ Error updating circuit optimizer: {e}")
            return False
    
    def apply_to_non_iid_engine(self):
        """Apply configuration to Non-IID data engine"""
        try:
            engine_file = "non_iid_data_engine.py"
            if not os.path.exists(engine_file):
                print(f"Non-IID engine file {engine_file} not found!")
                return False
                
            with open(engine_file, 'r') as f:
                content = f.read()
            
            # Update Non-IID parameters
            replacements = {
                'alpha=0.5': f'alpha={self.config.get("alpha", 0.5)}',
                'feature_skew_factor=0.3': f'feature_skew_factor={self.config.get("feature_skew_factor", 0.3)}',
                'quantity_imbalance_ratio=0.7': f'quantity_imbalance_ratio={self.config.get("quantity_imbalance_ratio", 0.7)}',
                'min_samples_per_client=50': f'min_samples_per_client={self.config.get("min_samples_per_client", 50)}'
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
                    
            with open(engine_file, 'w') as f:
                f.write(content)
                
            print("✅ Non-IID engine configuration updated")
            return True
            
        except Exception as e:
            print(f"❌ Error updating Non-IID engine: {e}")
            return False
    
    def apply_to_model_architecture(self):
        """Apply configuration to model architecture"""
        try:
            model_file = "train_mlp.py"
            if not os.path.exists(model_file):
                print(f"Model file {model_file} not found!")
                return False
                
            with open(model_file, 'r') as f:
                content = f.read()
            
            # Update model architecture parameters
            hidden_sizes = self.config.get("hidden_sizes", [64, 32, 16])
            dropout_rate = self.config.get("dropout_rate", 0.3)
            
            # Find and replace the MLP class definition
            if "class MLP" in content:
                old_pattern = "self.hidden_sizes = [64, 32, 16]"
                new_pattern = f"self.hidden_sizes = {hidden_sizes}"
                content = content.replace(old_pattern, new_pattern)
                
                old_dropout = "dropout=0.3"
                new_dropout = f"dropout={dropout_rate}"
                content = content.replace(old_dropout, new_dropout)
                    
            with open(model_file, 'w') as f:
                f.write(content)
                
            print("✅ Model architecture configuration updated")
            return True
            
        except Exception as e:
            print(f"❌ Error updating model architecture: {e}")
            return False
    
    def apply_to_dashboard(self):
        """Apply configuration to dashboard"""
        try:
            dashboard_file = "production_dashboard.py"
            if not os.path.exists(dashboard_file):
                print(f"Dashboard file {dashboard_file} not found!")
                return False
                
            with open(dashboard_file, 'r') as f:
                content = f.read()
            
            # Update dashboard parameters
            replacements = {
                'self.max_history_size = 1000': f'self.max_history_size = {self.config.get("metrics_retention_size", 1000)}',
                'time.sleep(2)': f'time.sleep({self.config.get("update_frequency_ms", 2000) / 1000})',
                'timeout=5': f'timeout={self.config.get("websocket_timeout", 60)}'
            }
            
            for old, new in replacements.items():
                if old in content:
                    content = content.replace(old, new)
                    
            with open(dashboard_file, 'w') as f:
                f.write(content)
                
            print("✅ Dashboard configuration updated")
            return True
            
        except Exception as e:
            print(f"❌ Error updating dashboard: {e}")
            return False
    
    def apply_all_configurations(self):
        """Apply configuration to all system components"""
        print("🔧 Applying ZK-FL Configuration Changes...")
        print("=" * 50)
        
        success_count = 0
        total_count = 5
        
        if self.apply_to_fl_server():
            success_count += 1
            
        if self.apply_to_circuit_optimizer():
            success_count += 1
            
        if self.apply_to_non_iid_engine():
            success_count += 1
            
        if self.apply_to_model_architecture():
            success_count += 1
            
        if self.apply_to_dashboard():
            success_count += 1
        
        print(f"\n📊 Configuration Applied: {success_count}/{total_count} components updated")
        
        if success_count == total_count:
            print("🎉 All configurations applied successfully!")
        elif success_count > 0:
            print("⚠️ Some configurations applied with warnings")
        else:
            print("❌ Failed to apply configurations")
            
        return success_count == total_count
    
    def generate_config_summary(self):
        """Generate a summary of current configuration"""
        print("\n📋 Current ZK-FL Configuration Summary:")
        print("=" * 50)
        
        categories = {
            "Federated Learning": ["num_clients", "num_rounds", "client_fraction", "local_epochs", "learning_rate", "batch_size"],
            "Model Architecture": ["input_size", "hidden_sizes", "dropout_rate", "activation_function"],
            "ZKP Circuit": ["constraint_reduction_factor", "parallel_workers", "memory_optimization", "batch_processing_size"],
            "Non-IID Data": ["alpha", "feature_skew_factor", "quantity_imbalance_ratio", "min_samples_per_client"],
            "Performance": ["websocket_timeout", "metrics_retention_size", "update_frequency_ms"],
            "Security": ["zkp_security_level", "proof_verification_strictness", "client_authentication"]
        }
        
        for category, params in categories.items():
            print(f"\n{category}:")
            for param in params:
                value = self.config.get(param, "Not set")
                print(f"  • {param}: {value}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply ZK-FL Configuration Changes")
    parser.add_argument("--config", default="zkfl_config.json", help="Configuration file to apply")
    parser.add_argument("--summary", action="store_true", help="Show configuration summary only")
    parser.add_argument("--component", choices=["fl_server", "circuit_optimizer", "non_iid_engine", "model", "dashboard"], 
                       help="Apply to specific component only")
    
    args = parser.parse_args()
    
    applier = ZKFLConfigApplier(args.config)
    
    if args.summary:
        applier.generate_config_summary()
        return
    
    if args.component:
        print(f"🔧 Applying configuration to {args.component}...")
        
        if args.component == "fl_server":
            success = applier.apply_to_fl_server()
        elif args.component == "circuit_optimizer":
            success = applier.apply_to_circuit_optimizer()
        elif args.component == "non_iid_engine":
            success = applier.apply_to_non_iid_engine()
        elif args.component == "model":
            success = applier.apply_to_model_architecture()
        elif args.component == "dashboard":
            success = applier.apply_to_dashboard()
        
        if success:
            print(f"✅ {args.component} configuration applied successfully!")
        else:
            print(f"❌ Failed to apply {args.component} configuration")
    else:
        applier.apply_all_configurations()
        applier.generate_config_summary()

if __name__ == "__main__":
    main()