#!/usr/bin/env python3

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os
import logging
import io
from contextlib import redirect_stdout, redirect_stderr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_protocol_zkp_fl import MultiProtocolZKPFLSystem, UnifiedFLConfig, ZKPProtocolConfig
from real_dataset_loader import RealDatasetLoader

class StreamlitLogHandler(logging.Handler):
    """Custom log handler that captures logs for real-time display in Streamlit"""
    
    def __init__(self):
        super().__init__()
        self.logs = []
        self.max_logs = 1000  # Limit to prevent memory issues
    
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).strftime('%H:%M:%S'),
                'level': record.levelname,
                'message': self.format(record),
                'module': record.name
            }
            
            self.logs.append(log_entry)
            
            # Keep only recent logs
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
        except Exception:
            pass  # Ignore logging errors to prevent recursion
    
    def get_logs(self):
        return self.logs.copy()
    
    def clear_logs(self):
        self.logs.clear()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveFLDashboard:
    """Comprehensive Interactive Dashboard for Multi-Protocol ZKP Federated Learning"""
    
    def __init__(self):
        self.setup_page_config()
        self.data_loader = RealDatasetLoader()
        self.experiment_results = {}
        self.real_time_logs = []
        self.comparison_data = {}
        
        # Initialize log handler for real-time display
        self.log_handler = StreamlitLogHandler()
        self.log_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        
        # Add handler to all relevant loggers
        loggers_to_capture = [
            'multi_protocol_zkp_fl',
            'real_ml_trainer', 
            'nova_prover',
            'protogalaxy_aggregator',
            'real_dataset_loader'
        ]
        
        for logger_name in loggers_to_capture:
            target_logger = logging.getLogger(logger_name)
            target_logger.addHandler(self.log_handler)
            target_logger.setLevel(logging.INFO)
        
    def setup_page_config(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="🚀 ZKP Federated Learning Analytics",
            page_icon="🔐",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin: 0.5rem 0;
        }
        .success-box {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .info-box {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .warning-box {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .sidebar-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render dashboard header"""
        # Main header with gradient styling
        st.markdown("""
        <div class="main-header">
            <h1 style="margin: 0; text-align: center;">🚀 ZKP Federated Learning Analytics Dashboard</h1>
            <p style="margin: 0.5rem 0 0 0; text-align: center; opacity: 0.9;">
                Advanced Multi-Protocol Zero-Knowledge Proof Federated Learning with Real-time Analytics
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature highlights
        st.markdown("""
        <div style="display: flex; justify-content: space-around; margin: 2rem 0;">
            <div class="info-box" style="flex: 1; margin: 0 0.5rem;">
                <h4>🔐 Zero-Knowledge Proofs</h4>
                <p>Cryptographic verification for all client updates with Nova IVC and ProtoStar + ProtoGalaxy protocols</p>
            </div>
            <div class="info-box" style="flex: 1; margin: 0 0.5rem;">
                <h4>📊 Real Federated Learning</h4>
                <p>Legitimate training with proper weight distribution, non-IID data, and post-aggregation testing</p>
            </div>
            <div class="info-box" style="flex: 1; margin: 0 0.5rem;">
                <h4>📈 Interactive Analytics</h4>
                <p>Comprehensive visualizations, real-time monitoring, and protocol performance comparisons</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Protocol comparison info with enhanced styling
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="metric-card" style="border-left-color: #2E86AB;">
                <h4>🌟 Nova IVC Protocol</h4>
                <ul style="margin: 0.5rem 0;">
                    <li><strong>Incremental Verifiable Computation</strong></li>
                    <li><strong>Pasta curves</strong> (Pallas/Vesta)</li>
                    <li><strong>Constant proof size</strong> (~33KB)</li>
                    <li><strong>Sequential verification</strong> with IVC</li>
                    <li><strong>Memory efficient</strong> for long sequences</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card" style="border-left-color: #A23B72;">
                <h4>⚡ ProtoStar + ProtoGalaxy</h4>
                <ul style="margin: 0.5rem 0;">
                    <li><strong>Aggregation-based verification</strong></li>
                    <li><strong>BN128 curves</strong> with optimal pairing</li>
                    <li><strong>Variable proof size</strong> (~2.9KB)</li>
                    <li><strong>Parallel aggregation</strong> capability</li>
                    <li><strong>Efficient batching</strong> for multiple proofs</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def render_experiment_controls(self):
        """Render experiment configuration controls"""
        # Styled sidebar header
        st.sidebar.markdown("""
        <div class="sidebar-header">
            <h2 style="margin: 0;">🔧 Experiment Configuration</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Configure your ZKP-FL experiment</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Protocol selection with enhanced styling
        st.sidebar.markdown("### 🔐 **ZKP Protocol Selection**")
        
        # Add comparison mode option
        experiment_mode = st.sidebar.radio(
            "Experiment Mode",
            ["Single Protocol", "Protocol Comparison"],
            help="🔬 Single Protocol: Run one protocol\n⚔️ Protocol Comparison: Compare Nova vs ProtoStar+ProtoGalaxy"
        )
        
        if experiment_mode == "Single Protocol":
            protocol = st.sidebar.selectbox(
                "Choose Protocol",
                ["nova", "protostar"],
                help="🌟 Nova: Constant-size proofs with IVC\n⚡ ProtoStar: Efficient aggregation"
            )
            
            # Quick protocol info
            if protocol == "nova":
                st.sidebar.success("🌟 **Nova IVC**: Incremental verification with constant proof size")
            else:
                st.sidebar.info("⚡ **ProtoStar + ProtoGalaxy**: Fast aggregation with variable proof size")
        else:
            protocol = "comparison"
            st.sidebar.warning("⚔️ **Comparison Mode**: Will run both Nova and ProtoStar+ProtoGalaxy protocols for performance analysis")
        
        # FL Parameters
        st.sidebar.markdown("### 📊 **Federated Learning Setup**")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            num_clients = st.number_input("👥 Clients", 2, 10, 5, help="Number of federated learning participants")
        with col2:
            num_rounds = st.number_input("🔄 Rounds", 1, 10, 3, help="Training rounds (1 epoch per round)")
            
        data_split = st.sidebar.selectbox(
            "📈 Data Distribution", 
            ["iid", "non_iid"],
            help="📊 IID: Balanced data split\n🌐 Non-IID: Realistic heterogeneous data"
        )
        
        # Data distribution info
        if data_split == "non_iid":
            st.sidebar.warning("🌐 **Non-IID**: Simulates real-world federated scenarios with heterogeneous data")
        else:
            st.sidebar.info("📊 **IID**: Balanced data distribution across all clients")
        
        # ML Parameters
        st.sidebar.markdown("### 🧠 **ML Training Parameters**")
        learning_rate = st.sidebar.number_input("📈 Learning Rate", 0.001, 0.1, 0.01, step=0.001)
        batch_size = st.sidebar.selectbox("📦 Batch Size", [16, 32, 64, 128], index=1)
        # Fixed to 1 epoch for proof generation after each epoch
        local_epochs = 1  # Single epoch per round for ZKP proof generation
        st.sidebar.markdown("""
        <div class="info-box">
            <strong>🔄 Epochs per Round:</strong> Fixed to 1<br>
            <small>ZKP proof generated after each training epoch</small>
        </div>
        """, unsafe_allow_html=True)
        
        # ZKP Parameters
        st.sidebar.markdown("### 🔐 **ZKP Configuration**")
        enable_aggregation = st.sidebar.checkbox("🔗 Enable Proof Aggregation", True, 
                                                help="Enable ProtoGalaxy aggregation for better efficiency")
        security_level = st.sidebar.selectbox("🛡️ Security Level", [128, 192, 256], index=0,
                                            help="Higher levels provide stronger security")
        
        # Dataset selection
        st.sidebar.markdown("### 📈 **Dataset Configuration**")
        dataset_name = st.sidebar.selectbox(
            "🏥 Medical Dataset",
            ["heart_disease", "diabetes", "synthetic"],
            help="🫀 Heart Disease: Real cardiovascular data\n🩺 Diabetes: Metabolic health data\n🧪 Synthetic: Generated medical data"
        )
        
        dataset_size = st.sidebar.slider("📏 Dataset Size", 100, 5000, 1000,
                                        help="Number of samples to use from the dataset")
        
        # Advanced options (collapsible)
        with st.sidebar.expander("⚙️ **Advanced Options**"):
            st.markdown("**Optimization Settings**")
            optimizer = st.selectbox("Optimizer", ["sgd", "adam"], help="Training optimizer algorithm")
            weight_decay = st.number_input("Weight Decay", 0.0, 0.01, 0.001, step=0.0001)
            
            st.markdown("**ZKP Advanced**")
            proof_compression = st.checkbox("🗜️ Proof Compression", True)
            parallel_verification = st.checkbox("⚡ Parallel Verification", False)
        
        return {
            'protocol': protocol,
            'num_clients': num_clients,
            'num_rounds': num_rounds,
            'data_split': data_split,
            'learning_rate': learning_rate,
            'batch_size': batch_size,
            'local_epochs': local_epochs,
            'enable_aggregation': enable_aggregation,
            'security_level': security_level,
            'dataset_name': dataset_name,
            'dataset_size': dataset_size
        }
    
    def create_comprehensive_visualizations(self, results: Dict[str, Any], experiment_id: str):
        """Create comprehensive interactive visualizations"""
        if not results or 'benchmarks' not in results:
            st.warning("No results available for visualization")
            return
            
        benchmarks = results['benchmarks']
        
        # 1. FL Training Progress
        self.render_fl_training_progress(benchmarks, experiment_id)
        
        # 2. ZKP Performance Analytics
        self.render_zkp_performance_analytics(benchmarks, experiment_id)
        
        # 3. Protocol Comparison Charts
        self.render_protocol_comparison(benchmarks, experiment_id)
        
        # 4. Real-time Performance Monitoring
        self.render_realtime_monitoring(benchmarks, experiment_id)
        
        # 5. Detailed Metrics Tables
        self.render_detailed_metrics(benchmarks, experiment_id)
    
    def render_fl_training_progress(self, benchmarks: Dict[str, Any], experiment_id: str):
        """Render federated learning training progress with enhanced interactivity"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h3 style="margin: 0;">🎯 Federated Learning Training Progress</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced interactive training progress with tabs
        if 'rounds' in benchmarks and benchmarks['rounds']:
            # Create tabs for different views
            tab1, tab2 = st.tabs(["📈 Training Progress", "👥 Client Analysis"])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Accuracy progression across rounds
                    if 'fl_metrics' in benchmarks and 'accuracy_progression' in benchmarks['fl_metrics']:
                        accuracy_data = benchmarks['fl_metrics']['accuracy_progression']
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=list(range(1, len(accuracy_data) + 1)),
                            y=accuracy_data,
                            mode='lines+markers',
                            name='Global Model Accuracy',
                            line=dict(color='#667eea', width=4),
                            marker=dict(size=10, color='#764ba2', 
                                      line=dict(width=2, color='white')),
                            hovertemplate='<b>Round %{x}</b><br>Accuracy: %{y:.4f}<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title={
                                'text': "🎯 Model Accuracy Progression",
                        'x': 0.5,
                        'font': {'size': 18, 'family': 'Arial Black'}
                    },
                    xaxis_title="Federated Round",
                    yaxis_title="Accuracy",
                    template="plotly_white",
                    hovermode='x unified',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
                    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray')
                )
                
                st.plotly_chart(fig, width="stretch", key=f"fl_progress_{experiment_id}")
            
        with col2:
            # Client performance distribution
            if 'rounds' in benchmarks and benchmarks['rounds']:
                client_accuracies = []
                rounds = []
                clients = []
                
                for round_data in benchmarks['rounds']:
                    if 'ml_metrics' in round_data and 'client_accuracies' in round_data['ml_metrics']:
                        for client_id, accuracy in round_data['ml_metrics']['client_accuracies'].items():
                            client_accuracies.append(accuracy)
                            rounds.append(round_data['round'])
                            clients.append(client_id)
                
                if client_accuracies:
                    df = pd.DataFrame({
                        'Round': rounds,
                        'Client': clients,
                        'Accuracy': client_accuracies
                    })
                    
                    fig = px.box(df, x='Round', y='Accuracy', 
                               title="📊 Client Accuracy Distribution per Round",
                               color_discrete_sequence=['#667eea'])
                    
                    fig.update_layout(
                        template="plotly_white",
                        title={'x': 0.5, 'font': {'size': 18, 'family': 'Arial Black'}},
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    fig.update_traces(marker_color='#667eea', line_color='#764ba2')
                    st.plotly_chart(fig, width="stretch", key=f"client_accuracies_{experiment_id}")
        
        # Enhanced training metrics summary
        st.markdown("""
        <div class="metric-card" style="margin: 1rem 0;">
            <h4>📈 Training Performance Summary</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            if 'fl_metrics' in benchmarks:
                improvement = benchmarks['fl_metrics'].get('accuracy_improvement', 0)
                st.metric(
                    "📈 Accuracy Improvement",
                    f"{improvement:.4f}",
                    delta=f"+{improvement:.4f}" if improvement > 0 else f"{improvement:.4f}"
                )
        
        with col4:
            if 'fl_metrics' in benchmarks:
                convergence = benchmarks['fl_metrics'].get('convergence_rate', 0)
                st.metric(
                    "🔄 Convergence Rate",
                    f"{convergence:.6f}",
                    help="Average accuracy improvement per round"
                )
        
        with col5:
            total_clients = benchmarks.get('fl_metrics', {}).get('client_count', 0)
            st.metric("👥 Total Clients", total_clients)
            
        with col6:
            total_rounds = benchmarks.get('fl_metrics', {}).get('round_count', 0)
            st.metric("🔄 Training Rounds", total_rounds)
    
    def render_zkp_performance_analytics(self, benchmarks: Dict[str, Any], experiment_id: str):
        """Render ZKP performance analytics"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #A23B72 0%, #667eea 100%); padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h3 style="margin: 0;">🔐 Zero-Knowledge Proof Performance Analytics</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced timing visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Proof generation timing with client breakdown
            if 'zkp_metrics' in benchmarks and 'proof_generation_times' in benchmarks['zkp_metrics']:
                gen_times = benchmarks['zkp_metrics']['proof_generation_times']
                if gen_times:
                    # Create client-wise breakdown
                    if isinstance(gen_times[0], dict) and 'client_id' in gen_times[0]:
                        # Enhanced timing with client information
                        client_ids = [t['client_id'] for t in gen_times]
                        times = [t['time'] for t in gen_times]
                        
                        fig = go.Figure()
                        
                        # Scatter plot showing per-client timing
                        fig.add_trace(go.Scatter(
                            x=client_ids,
                            y=times,
                            mode='markers+lines',
                            name='Proof Generation Time',
                            marker=dict(size=12, color='#A23B72', 
                                      line=dict(width=2, color='white')),
                            line=dict(color='#667eea', width=3),
                            hovertemplate='<b>%{x}</b><br>Time: %{y:.4f}s<extra></extra>'
                        ))
                        
                        # Add average line
                        avg_time = np.mean(times)
                        fig.add_hline(y=avg_time, line_dash="dash", 
                                    line_color="red", opacity=0.7,
                                    annotation_text=f"Avg: {avg_time:.4f}s")
                        
                        fig.update_layout(
                            title={
                                'text': "⚡ Proof Generation Time by Client",
                                'x': 0.5,
                                'font': {'size': 18, 'family': 'Arial Black'}
                            },
                            xaxis_title="Client ID",
                            yaxis_title="Time (seconds)",
                            template="plotly_white",
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                    else:
                        # Simple histogram for basic timing data
                        fig = go.Figure()
                        fig.add_trace(go.Histogram(
                            x=gen_times,
                            name='Proof Generation Time',
                            nbinsx=20,
                            marker_color='#A23B72',
                            opacity=0.8
                        ))
                        
                        fig.update_layout(
                            title="⚡ Proof Generation Time Distribution",
                            xaxis_title="Time (seconds)",
                            yaxis_title="Frequency",
                            template="plotly_white"
                        )
                    
                    st.plotly_chart(fig, width="stretch", key=f"proof_timing_{experiment_id}")
        
        with col2:
            # Proof verification timing with enhanced visualization
            if 'zkp_metrics' in benchmarks and 'proof_verification_times' in benchmarks['zkp_metrics']:
                verify_times = benchmarks['zkp_metrics']['proof_verification_times']
                if verify_times:
                    fig = go.Figure()
                    
                    # Box plot for verification times
                    fig.add_trace(go.Box(
                        y=verify_times,
                        name='Verification Times',
                        boxpoints='all',
                        jitter=0.3,
                        pointpos=-1.8,
                        marker_color='#F18F01',
                        line_color='#667eea',
                        fillcolor='rgba(241, 143, 1, 0.3)'
                    ))
                    
                    fig.update_layout(
                        title={
                            'text': "🔍 Proof Verification Time Analysis",
                            'x': 0.5,
                            'font': {'size': 18, 'family': 'Arial Black'}
                        },
                        yaxis_title="Time (seconds)",
                        template="plotly_white",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, width="stretch", key=f"proof_verification_{experiment_id}")
        
        # Enhanced ZKP performance metrics with better styling
        st.markdown("""
        <div class="metric-card" style="margin: 1rem 0;">
            <h4>🔐 Cryptographic Performance Summary</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Add detailed timing breakdowns
        self.render_detailed_zkp_timing_analysis(benchmarks, experiment_id)
        
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            avg_gen_time = benchmarks.get('performance_analysis', {}).get('avg_proof_generation_time', 0)
            st.metric(
                "⚡ Avg Proof Gen", 
                f"{avg_gen_time:.3f}s",
                help="Average time to generate ZKP proofs across all clients"
            )
        
        with col4:
            avg_verify_time = benchmarks.get('performance_analysis', {}).get('avg_proof_verification_time', 0)
            st.metric(
                "🔍 Avg Verify", 
                f"{avg_verify_time:.3f}s",
                help="Average time to verify ZKP proofs"
            )
        
        with col5:
            avg_proof_size = benchmarks.get('performance_analysis', {}).get('avg_proof_size', 0)
            size_kb = avg_proof_size / 1024 if avg_proof_size > 0 else 0
            st.metric(
                "📏 Avg Proof Size", 
                f"{size_kb:.1f} KB",
                help="Average size of generated ZKP proofs"
            )
        
        with col6:
            success_rate = benchmarks.get('zkp_metrics', {}).get('verification_success_rates', 0)
            success_pct = success_rate * 100 if isinstance(success_rate, float) else success_rate
            st.metric(
                "✅ Success Rate", 
                f"{success_pct:.1f}%",
                help="Percentage of successful proof verifications"
            )
        
        # Protocol efficiency analysis
        if 'performance_analysis' in benchmarks:
            perf = benchmarks['performance_analysis']
            efficiency_ratio = perf.get('efficiency_ratio', 0)
            total_crypto_overhead = perf.get('total_cryptographic_overhead', 0)
            
            st.markdown("""
            <div class="info-box">
                <h5>📊 Efficiency Analysis</h5>
            </div>
            """, unsafe_allow_html=True)
            
            col7, col8 = st.columns(2)
            with col7:
                st.metric(
                    "🔐 Crypto Overhead", 
                    f"{total_crypto_overhead:.2f}s",
                    help="Total time spent on cryptographic operations"
                )
            with col8:
                st.metric(
                    "⚖️ Efficiency Ratio", 
                    f"{efficiency_ratio:.3f}",
                    help="Ratio of ZKP time to ML training time"
                )
    
    def render_detailed_zkp_timing_analysis(self, benchmarks: Dict[str, Any], experiment_id: str):
        """Render detailed ZKP timing analysis with comprehensive breakdowns"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #A23B72 100%); padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h4 style="margin: 0;">⏱️ Detailed ZKP Timing Analysis</h4>
        </div>
        """, unsafe_allow_html=True)
        
        if 'rounds' in benchmarks and benchmarks['rounds']:
            timing_col1, timing_col2, timing_col3 = st.columns(3)
            
            with timing_col1:
                # Round-by-round timing breakdown
                st.markdown("**📊 Round-by-Round Timing**")
                
                round_times = []
                proof_gen_times = []
                proof_verify_times = []
                ml_training_times = []
                
                for round_data in benchmarks['rounds']:
                    round_times.append(round_data.get('time', 0))
                    
                    # Extract ZKP timing if available
                    zkp_timing = round_data.get('zkp_timing', {})
                    if zkp_timing:
                        avg_gen = zkp_timing.get('avg_proof_generation_time', 0)
                        avg_verify = zkp_timing.get('avg_verification_time', 0)
                        proof_gen_times.append(avg_gen)
                        proof_verify_times.append(avg_verify)
                        
                        # Calculate ML time (total - ZKP time)
                        zkp_total = zkp_timing.get('total_cryptographic_time', 0)
                        ml_time = max(0, round_data.get('time', 0) - zkp_total)
                        ml_training_times.append(ml_time)
                
                if round_times:
                    # Create stacked bar chart for timing breakdown
                    fig = go.Figure()
                    
                    rounds = list(range(1, len(round_times) + 1))
                    
                    # Add ML training time
                    if ml_training_times:
                        fig.add_trace(go.Bar(
                            name='ML Training',
                            x=rounds,
                            y=ml_training_times,
                            marker_color='#4CAF50',
                            hovertemplate='Round %{x}<br>ML Time: %{y:.3f}s<extra></extra>'
                        ))
                    
                    # Add proof generation time
                    if proof_gen_times:
                        fig.add_trace(go.Bar(
                            name='Proof Generation',
                            x=rounds,
                            y=proof_gen_times,
                            marker_color='#FF9800',
                            hovertemplate='Round %{x}<br>Proof Gen: %{y:.3f}s<extra></extra>'
                        ))
                    
                    # Add verification time
                    if proof_verify_times:
                        fig.add_trace(go.Bar(
                            name='Proof Verification',
                            x=rounds,
                            y=proof_verify_times,
                            marker_color='#F44336',
                            hovertemplate='Round %{x}<br>Verification: %{y:.3f}s<extra></extra>'
                        ))
                    
                    fig.update_layout(
                        title="⏱️ Time Breakdown per Round",
                        xaxis_title="Round",
                        yaxis_title="Time (seconds)",
                        barmode='stack',
                        template="plotly_white",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=400
                    )
                    
                    st.plotly_chart(fig, width="stretch", key=f"timing_breakdown_{experiment_id}")
            
            with timing_col2:
                # ZKP overhead analysis
                st.markdown("**🔍 ZKP Overhead Analysis**")
                
                total_ml_time = sum(ml_training_times) if ml_training_times else 0
                total_zkp_time = sum(proof_gen_times) + sum(proof_verify_times) if proof_gen_times and proof_verify_times else 0
                total_experiment_time = total_ml_time + total_zkp_time
                
                if total_experiment_time > 0:
                    overhead_data = {
                        'Component': ['ML Training', 'Proof Generation', 'Proof Verification'],
                        'Time': [total_ml_time, sum(proof_gen_times) if proof_gen_times else 0, sum(proof_verify_times) if proof_verify_times else 0],
                        'Percentage': [
                            (total_ml_time / total_experiment_time) * 100,
                            (sum(proof_gen_times) / total_experiment_time * 100) if proof_gen_times else 0,
                            (sum(proof_verify_times) / total_experiment_time * 100) if proof_verify_times else 0
                        ]
                    }
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=overhead_data['Component'],
                        values=overhead_data['Time'],
                        hovertemplate='%{label}<br>Time: %{value:.3f}s<br>Percentage: %{percent}<extra></extra>',
                        marker=dict(colors=['#4CAF50', '#FF9800', '#F44336']),
                        textinfo='label+percent',
                        textposition='auto'
                    )])
                    
                    fig.update_layout(
                        title="⚖️ Time Distribution",
                        template="plotly_white",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=400
                    )
                    
                    st.plotly_chart(fig, width="stretch", key=f"overhead_analysis_{experiment_id}")
                    
                    # Display metrics
                    zkp_overhead_percent = (total_zkp_time / total_experiment_time) * 100 if total_experiment_time > 0 else 0
                    st.metric("ZKP Overhead", f"{zkp_overhead_percent:.1f}%", 
                             delta=f"{total_zkp_time:.3f}s total")
            
            with timing_col3:
                # Performance trends
                st.markdown("**📈 Performance Trends**")
                
                if len(round_times) > 1:
                    # Show trend in round execution time
                    fig = go.Figure()
                    
                    rounds = list(range(1, len(round_times) + 1))
                    
                    fig.add_trace(go.Scatter(
                        x=rounds,
                        y=round_times,
                        mode='lines+markers',
                        name='Round Time',
                        line=dict(color='#667eea', width=3),
                        marker=dict(size=10, color='#A23B72')
                    ))
                    
                    # Add trend line
                    if len(round_times) >= 3:
                        z = np.polyfit(rounds, round_times, 1)
                        p = np.poly1d(z)
                        fig.add_trace(go.Scatter(
                            x=rounds,
                            y=p(rounds),
                            mode='lines',
                            name='Trend',
                            line=dict(color='red', dash='dash'),
                            opacity=0.7
                        ))
                    
                    fig.update_layout(
                        title="⏱️ Round Time Trends",
                        xaxis_title="Round",
                        yaxis_title="Time (seconds)",
                        template="plotly_white",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=400
                    )
                    
                    st.plotly_chart(fig, width="stretch", key=f"performance_trends_{experiment_id}")
                    
                    # Show performance improvement/degradation
                    if len(round_times) >= 2:
                        first_round = round_times[0]
                        last_round = round_times[-1]
                        improvement = ((first_round - last_round) / first_round) * 100
                        
                        st.metric(
                            "Performance Change", 
                            f"{improvement:+.1f}%",
                            delta=f"{last_round - first_round:+.3f}s"
                        )
        else:
            st.info("Run an experiment to see detailed timing analysis!")

    def render_protocol_comparison(self, benchmarks: Dict[str, Any], experiment_id: str):
        """Render protocol comparison visualizations"""
        st.header("⚖️ Protocol Performance Comparison")
        
        # Store current experiment data for comparison
        protocol_name = benchmarks.get('protocol_info', {}).get('name', 'Unknown')
        self.comparison_data[experiment_id] = {
            'protocol': protocol_name,
            'benchmarks': benchmarks,
            'timestamp': datetime.now()
        }
        
        if len(self.comparison_data) > 1:
            # Create comparison charts
            protocols = []
            avg_gen_times = []
            avg_verify_times = []
            avg_proof_sizes = []
            efficiency_ratios = []
            
            for exp_id, data in self.comparison_data.items():
                protocols.append(data['protocol'])
                
                perf_analysis = data['benchmarks'].get('performance_analysis', {})
                avg_gen_times.append(perf_analysis.get('avg_proof_generation_time', 0))
                avg_verify_times.append(perf_analysis.get('avg_proof_verification_time', 0))
                avg_proof_sizes.append(perf_analysis.get('avg_proof_size', 0) / 1024)  # KB
                efficiency_ratios.append(perf_analysis.get('efficiency_ratio', 0))
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Timing comparison
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Proof Generation',
                    x=protocols,
                    y=avg_gen_times,
                    marker_color='#2E86AB'
                ))
                fig.add_trace(go.Bar(
                    name='Proof Verification',
                    x=protocols,
                    y=avg_verify_times,
                    marker_color='#A23B72'
                ))
                
                fig.update_layout(
                    title="🏃 Protocol Timing Comparison",
                    xaxis_title="Protocol",
                    yaxis_title="Time (seconds)",
                    template="plotly_white",
                    barmode='group'
                )
                
                st.plotly_chart(fig, width="stretch", key=f"protocol_comparison_{experiment_id}")
            
            with col2:
                # Proof size and efficiency comparison
                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=("Proof Size (KB)", "Efficiency Ratio"),
                    specs=[[{"secondary_y": False}, {"secondary_y": False}]]
                )
                
                fig.add_trace(
                    go.Bar(x=protocols, y=avg_proof_sizes, name="Proof Size", 
                          marker_color='#F18F01'),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Bar(x=protocols, y=efficiency_ratios, name="Efficiency", 
                          marker_color='#C73E1D'),
                    row=1, col=2
                )
                
                fig.update_layout(
                    title="📊 Size & Efficiency Comparison",
                    template="plotly_white",
                    showlegend=False
                )
                
                st.plotly_chart(fig, width="stretch", key=f"proof_efficiency_{experiment_id}")
        else:
            st.info("Run experiments with different protocols to see comparison charts!")
    
    def render_realtime_monitoring(self, benchmarks: Dict[str, Any], experiment_id: str):
        """Render real-time performance monitoring"""
        st.header("📈 Real-time Performance Monitoring")
        
        if 'rounds' in benchmarks:
            # Round-by-round performance
            rounds_data = benchmarks['rounds']
            
            round_numbers = []
            round_times = []
            zkp_overheads = []
            aggregation_success = []
            
            for round_data in rounds_data:
                round_numbers.append(round_data['round'])
                round_times.append(round_data['time'])
                
                zkp_timing = round_data.get('zkp_timing', {})
                total_zkp_time = (
                    sum([t['time'] for t in zkp_timing.get('proof_generation_times', [])]) +
                    sum(zkp_timing.get('proof_verification_times', []))
                )
                zkp_overheads.append(total_zkp_time)
                aggregation_success.append(round_data.get('aggregation_successful', False))
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Round execution time
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=round_numbers,
                    y=round_times,
                    mode='lines+markers',
                    name='Round Time',
                    line=dict(color='#2E86AB', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="⏱️ Round Execution Time",
                    xaxis_title="Round Number",
                    yaxis_title="Time (seconds)",
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, width="stretch", key=f"round_execution_time_{experiment_id}")
            
            with col2:
                # ZKP overhead per round
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=round_numbers,
                    y=zkp_overheads,
                    mode='lines+markers',
                    name='ZKP Overhead',
                    line=dict(color='#A23B72', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="🔐 ZKP Overhead per Round",
                    xaxis_title="Round Number",
                    yaxis_title="ZKP Time (seconds)",
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, width="stretch", key=f"zkp_overhead_{experiment_id}")
    
    def render_detailed_metrics(self, benchmarks: Dict[str, Any], experiment_id: str):
        """Render detailed metrics tables"""
        st.header("📋 Detailed Performance Metrics")
        
        tab1, tab2, tab3 = st.tabs(["🔐 ZKP Metrics", "📊 FL Metrics", "⚡ Performance Analysis"])
        
        with tab1:
            st.subheader("Zero-Knowledge Proof Metrics")
            
            zkp_metrics = benchmarks.get('zkp_metrics', {})
            security_params = zkp_metrics.get('security_parameters', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.json({
                    "Protocol": security_params.get('protocol', 'N/A'),
                    "Security Level": security_params.get('security_level', 'N/A'),
                    "SRS Size": security_params.get('srs_size', 'N/A'),
                    "Total Proof Generation": len(zkp_metrics.get('proof_generation_times', [])),
                    "Total Proof Verification": len(zkp_metrics.get('proof_verification_times', []))
                })
            
            with col2:
                perf_analysis = benchmarks.get('performance_analysis', {})
                st.json({
                    "Avg Proof Gen Time": f"{perf_analysis.get('avg_proof_generation_time', 0):.4f}s",
                    "Avg Proof Verify Time": f"{perf_analysis.get('avg_proof_verification_time', 0):.4f}s",
                    "Avg Proof Size": f"{perf_analysis.get('avg_proof_size', 0)/1024:.2f} KB",
                    "Total Cryptographic Overhead": f"{perf_analysis.get('total_cryptographic_overhead', 0):.4f}s",
                    "Efficiency Ratio": f"{perf_analysis.get('efficiency_ratio', 0):.4f}"
                })
        
        with tab2:
            st.subheader("Federated Learning Metrics")
            
            fl_metrics = benchmarks.get('fl_metrics', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.json({
                    "Client Count": fl_metrics.get('client_count', 0),
                    "Round Count": fl_metrics.get('round_count', 0),
                    "Initial Global Accuracy": fl_metrics.get('initial_global_accuracy', 'N/A'),
                    "Final Global Accuracy": fl_metrics.get('final_global_accuracy', 'N/A'),
                    "Federated Improvement": fl_metrics.get('federated_improvement', 'N/A')
                })
            
            with col2:
                if 'accuracy_progression' in fl_metrics:
                    accuracy_stats = fl_metrics['accuracy_progression']
                    st.json({
                        "Accuracy Progression": accuracy_stats,
                        "Best Accuracy": max(accuracy_stats) if accuracy_stats else 'N/A',
                        "Worst Accuracy": min(accuracy_stats) if accuracy_stats else 'N/A',
                        "Accuracy Variance": np.var(accuracy_stats) if accuracy_stats else 'N/A'
                    })
        
        with tab3:
            st.subheader("Performance Analysis")
            
            scalability = benchmarks.get('performance_analysis', {}).get('scalability_metrics', {})
            
            st.json({
                "Total Experiment Time": f"{benchmarks.get('total_time', 0):.2f}s",
                "Avg Time per Client": f"{scalability.get('avg_time_per_client', 0):.4f}s",
                "Avg ZKP Time per Client": f"{scalability.get('avg_zkp_time_per_client', 0):.4f}s",
                "ZKP Scalability Factor": f"{scalability.get('zkp_scalability_factor', 0):.4f}",
                "Verification Success Rate": f"{benchmarks.get('zkp_metrics', {}).get('verification_success_rates', 0)*100:.1f}%"
            })
    
    def create_performance_visualizations(self, benchmarks: Dict[str, Any], experiment_id: str):
        """Create comprehensive performance visualizations as required by Final Guide"""
        st.subheader("📊 Performance Visualizations")
        
        # Performance metrics overview
        col1, col2 = st.columns(2)
        
        with col1:
            # FL Performance Chart
            if 'fl_metrics' in benchmarks and 'accuracy_progression' in benchmarks['fl_metrics']:
                accuracy_data = benchmarks['fl_metrics']['accuracy_progression']
                rounds = list(range(1, len(accuracy_data) + 1))
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=rounds,
                    y=accuracy_data,
                    mode='lines+markers',
                    name='Global Model Accuracy',
                    line=dict(color='#2E86AB', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="Global Model Accuracy Convergence",
                    xaxis_title="FL Round",
                    yaxis_title="Accuracy",
                    template="plotly_white",
                    height=400
                )
                
                st.plotly_chart(fig, width="stretch", key=f"perf_accuracy_{experiment_id}")
        
        with col2:
            # ZKP Performance Chart
            if 'zkp_metrics' in benchmarks and 'round_metrics' in benchmarks['zkp_metrics']:
                round_metrics = benchmarks['zkp_metrics']['round_metrics']
                
                if round_metrics:
                    rounds = list(range(1, len(round_metrics) + 1))
                    proof_gen_times = [r.get('avg_proof_generation_time', 0) for r in round_metrics]
                    verification_times = [r.get('avg_verification_time', 0) for r in round_metrics]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=rounds, y=proof_gen_times,
                        mode='lines+markers', name='Proof Generation',
                        line=dict(color='#A23B72', width=3)
                    ))
                    fig.add_trace(go.Scatter(
                        x=rounds, y=verification_times,
                        mode='lines+markers', name='Verification',
                        line=dict(color='#F18F01', width=3)
                    ))
                    
                    fig.update_layout(
                        title="ZKP Performance Over Rounds",
                        xaxis_title="FL Round",
                        yaxis_title="Time (seconds)",
                        template="plotly_white",
                        height=400
                    )
                    
                    st.plotly_chart(fig, width="stretch", key=f"perf_zkp_{experiment_id}")
    
    def display_real_time_metrics(self, benchmarks: Dict[str, Any], experiment_id: str):
        """Display real-time metrics as required by Final Guide"""
        st.subheader("📡 Real-Time Metrics")
        
        # Live metrics display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_round = benchmarks.get('current_round', 0)
            total_rounds = benchmarks.get('total_rounds', 1)
            progress = current_round / total_rounds
            
            st.metric(
                label="FL Progress",
                value=f"{current_round}/{total_rounds}",
                delta=f"{progress*100:.1f}%"
            )
        
        with col2:
            if 'fl_metrics' in benchmarks and 'accuracy_progression' in benchmarks['fl_metrics']:
                accuracy_data = benchmarks['fl_metrics']['accuracy_progression']
                current_accuracy = accuracy_data[-1] if accuracy_data else 0
                prev_accuracy = accuracy_data[-2] if len(accuracy_data) > 1 else 0
                delta_accuracy = current_accuracy - prev_accuracy
                
                st.metric(
                    label="Current Accuracy",
                    value=f"{current_accuracy:.3f}",
                    delta=f"{delta_accuracy:+.3f}" if delta_accuracy != 0 else None
                )
        
        with col3:
            if 'zkp_metrics' in benchmarks and 'round_metrics' in benchmarks['zkp_metrics']:
                round_metrics = benchmarks['zkp_metrics']['round_metrics']
                if round_metrics:
                    avg_proof_time = round_metrics[-1].get('avg_proof_generation_time', 0)
                    st.metric(
                        label="Avg Proof Time",
                        value=f"{avg_proof_time:.2f}s"
                    )
        
        with col4:
            verification_rate = benchmarks.get('zkp_metrics', {}).get('verification_success_rates', 0)
            st.metric(
                label="Verification Success",
                value=f"{verification_rate*100:.1f}%"
            )
    
    def create_performance_summary(self, benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance summary as required by Final Guide statistical analysis"""
        summary = {
            'experiment_metadata': {
                'timestamp': datetime.now().isoformat(),
                'protocol': benchmarks.get('protocol', 'unknown'),
                'total_rounds': benchmarks.get('total_rounds', 0),
                'num_clients': benchmarks.get('num_clients', 0),
                'total_time': benchmarks.get('total_time', 0)
            },
            'fl_performance': {},
            'zkp_performance': {},
            'efficiency_metrics': {},
            'statistical_analysis': {}
        }
        
        # FL Performance Summary
        if 'fl_metrics' in benchmarks:
            fl_metrics = benchmarks['fl_metrics']
            accuracy_data = fl_metrics.get('accuracy_progression', [])
            loss_data = fl_metrics.get('loss_progression', [])
            
            summary['fl_performance'] = {
                'final_accuracy': accuracy_data[-1] if accuracy_data else 0,
                'best_accuracy': max(accuracy_data) if accuracy_data else 0,
                'accuracy_improvement': accuracy_data[-1] - accuracy_data[0] if len(accuracy_data) > 1 else 0,
                'convergence_rounds': len(accuracy_data),
                'final_loss': loss_data[-1] if loss_data else 0,
                'avg_accuracy': np.mean(accuracy_data) if accuracy_data else 0,
                'accuracy_std': np.std(accuracy_data) if accuracy_data else 0
            }
        
        # ZKP Performance Summary
        if 'zkp_metrics' in benchmarks:
            zkp_metrics = benchmarks['zkp_metrics']
            round_metrics = zkp_metrics.get('round_metrics', [])
            
            if round_metrics:
                proof_times = [r.get('avg_proof_generation_time', 0) for r in round_metrics]
                verification_times = [r.get('avg_verification_time', 0) for r in round_metrics]
                proof_sizes = [r.get('avg_proof_size_bytes', 0) for r in round_metrics]
                
                summary['zkp_performance'] = {
                    'avg_proof_generation_time': np.mean(proof_times),
                    'min_proof_generation_time': np.min(proof_times),
                    'max_proof_generation_time': np.max(proof_times),
                    'proof_time_std': np.std(proof_times),
                    'avg_verification_time': np.mean(verification_times),
                    'avg_proof_size_bytes': np.mean(proof_sizes),
                    'avg_proof_size_kb': np.mean(proof_sizes) / 1024,
                    'verification_success_rate': zkp_metrics.get('verification_success_rates', 0),
                    'total_zkp_time': sum(proof_times) + sum(verification_times)
                }
        
        # Efficiency Metrics
        total_time = summary['experiment_metadata']['total_time']
        zkp_time = summary['zkp_performance'].get('total_zkp_time', 0)
        
        summary['efficiency_metrics'] = {
            'zkp_overhead_percentage': (zkp_time / total_time * 100) if total_time > 0 else 0,
            'time_per_round': total_time / max(1, summary['experiment_metadata']['total_rounds']),
            'time_per_client': total_time / max(1, summary['experiment_metadata']['num_clients']),
            'accuracy_per_second': summary['fl_performance'].get('final_accuracy', 0) / max(1, total_time)
        }
        
        return summary
    
    def analyze_protocol_performance(self, benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze protocol performance for statistical comparison as required by Final Guide"""
        analysis = {
            'performance_score': 0,
            'efficiency_rating': 'unknown',
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        protocol = benchmarks.get('protocol', 'unknown')
        summary = self.create_performance_summary(benchmarks)
        
        # Calculate performance score (0-100)
        fl_perf = summary.get('fl_performance', {})
        zkp_perf = summary.get('zkp_performance', {})
        efficiency = summary.get('efficiency_metrics', {})
        
        # Scoring factors
        accuracy_score = min(100, fl_perf.get('final_accuracy', 0) * 100)  # 0-100
        speed_score = min(100, max(0, 100 - efficiency.get('time_per_round', 10)))  # Inverse of time
        zkp_score = min(100, zkp_perf.get('verification_success_rate', 0) * 100)  # 0-100
        
        analysis['performance_score'] = (accuracy_score + speed_score + zkp_score) / 3
        
        # Efficiency rating
        zkp_overhead = efficiency.get('zkp_overhead_percentage', 100)
        if zkp_overhead < 20:
            analysis['efficiency_rating'] = 'excellent'
        elif zkp_overhead < 40:
            analysis['efficiency_rating'] = 'good'
        elif zkp_overhead < 60:
            analysis['efficiency_rating'] = 'moderate'
        else:
            analysis['efficiency_rating'] = 'poor'
        
        # Protocol-specific analysis
        if protocol.lower() == 'nova':
            if zkp_perf.get('avg_proof_size_kb', 0) < 15:  # Nova should have small constant size
                analysis['strengths'].append('Constant proof size (IVC benefit)')
            if efficiency.get('time_per_round', 10) < 5:
                analysis['strengths'].append('Fast incremental verification')
            if zkp_overhead > 50:
                analysis['weaknesses'].append('High computational overhead')
                
        elif protocol.lower() == 'protostar':
            if zkp_perf.get('avg_proof_size_kb', 0) < 5:  # ProtoStar should have small proofs
                analysis['strengths'].append('Small individual proof size')
            if zkp_perf.get('verification_success_rate', 0) > 0.95:
                analysis['strengths'].append('High verification reliability')
            if efficiency.get('time_per_round', 10) > 8:
                analysis['weaknesses'].append('Slower aggregation process')
        
        # General recommendations
        if analysis['performance_score'] < 60:
            analysis['recommendations'].append('Consider optimizing circuit design')
        if efficiency.get('zkp_overhead_percentage', 0) > 40:
            analysis['recommendations'].append('Investigate proof generation optimization')
        if fl_perf.get('final_accuracy', 0) < 0.7:
            analysis['recommendations'].append('Increase local epochs or adjust learning rate')
        
        return analysis
    
    async def run_experiment(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run comprehensive FL experiment"""
        try:
            # Create experiment ID
            experiment_id = f"{config['protocol']}_{int(time.time())}"
            
            st.info(f"🚀 Starting experiment: {experiment_id}")
            
            # Load dataset
            data_loader = RealDatasetLoader()
            
            # Load appropriate dataset
            if config['dataset_name'] == 'heart_disease':
                X, y = data_loader.load_dataset('heart_2020')
                data_loader.datasets['heart_2020'] = {'X': X, 'y': y}
                dataset_key = 'heart_2020'
            elif config['dataset_name'] == 'diabetes':
                X, y = data_loader.load_dataset('cardio')  # Use cardio as alternative medical dataset
                data_loader.datasets['cardio'] = {'X': X, 'y': y}
                dataset_key = 'cardio'
            else:
                # Generate synthetic data for other cases
                np.random.seed(42)
                X = np.random.randn(config['dataset_size'], 10)
                y = np.random.randint(0, 2, config['dataset_size'])
                # Store synthetic dataset
                data_loader.datasets['synthetic'] = {'X': X, 'y': y}
                dataset_key = 'synthetic'
            
            # Split data for clients
            if config['data_split'] == 'iid':
                # For IID, manually create balanced splits
                client_data = {}
                samples_per_client = len(X) // config['num_clients']
                
                for i in range(config['num_clients']):
                    start_idx = i * samples_per_client
                    end_idx = start_idx + samples_per_client if i < config['num_clients'] - 1 else len(X)
                    
                    client_data[f'client_{i}'] = {
                        'X': X[start_idx:end_idx],
                        'y': y[start_idx:end_idx]
                    }
            else:
                # Use the available non-IID partitioning method
                client_data_dict = data_loader.create_non_iid_partition(
                    dataset_key, config['num_clients'], 'medium'
                )
                
                # Convert to expected format
                client_data = {}
                for client_id, data in client_data_dict.items():
                    client_data[f'client_{client_id}'] = {
                        'X': data['X'],
                        'y': data['y']
                    }
            
            # Configure FL system
            zkp_config = ZKPProtocolConfig(
                protocol_type=config['protocol'],
                enable_aggregation=config['enable_aggregation'],
                security_level=config['security_level']
            )
            
            # Determine input features from dataset
            input_features = X.shape[1]
            logger.info(f"📊 Dataset loaded: {X.shape[0]} samples, {input_features} features")
            
            fl_config = UnifiedFLConfig(
                num_rounds=config['num_rounds'],
                learning_rate=config['learning_rate'],
                batch_size=config['batch_size'],
                local_epochs=config['local_epochs'],
                zkp_config=zkp_config
            )
            
            # Initialize FL system
            fl_system = MultiProtocolZKPFLSystem(fl_config)
            
            # Add clients
            for client_id, client_info in client_data.items():
                X_client = client_info['X']
                y_client = client_info['y']
                fl_system.add_client(client_id, X_client, y_client)
            
            # Run federated learning
            results = await fl_system.run_federated_learning()
            
            st.success(f"✅ Experiment {experiment_id} completed successfully!")
            
            # Store results
            self.experiment_results[experiment_id] = results
            
            return results
            
        except Exception as e:
            st.error(f"❌ Experiment failed: {str(e)}")
            logger.error(f"Experiment error: {e}", exc_info=True)
            return None
    
    def run_protocol_comparison(self, config: Dict[str, Any], progress_bar, status_text, logs_container) -> Optional[Dict[str, Any]]:
        """Run comparison between all available protocols"""
        try:
            protocols = ['nova', 'protostar']
            comparison_results = {
                'config': config,
                'protocols': {},
                'comparison_metrics': {},
                'timestamp': int(time.time())
            }
            
            for i, protocol in enumerate(protocols):
                logger.info(f"🔬 Testing protocol {i+1}/{len(protocols)}: {protocol}")
                status_text.text(f"Testing {protocol.replace('_', '+').title()} protocol...")
                progress_bar.progress(10 + (i * 40))
                
                # Update logs
                self.render_live_logs(logs_container)
                
                # Create config for this protocol
                protocol_config = config.copy()
                protocol_config['protocol'] = protocol
                
                # Run experiment with this protocol
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    results = loop.run_until_complete(self.run_experiment_with_updates(
                        protocol_config, progress_bar, status_text, logs_container
                    ))
                    
                    if results:
                        comparison_results['protocols'][protocol] = results
                        logger.info(f"✅ {protocol} protocol completed successfully")
                    else:
                        logger.error(f"❌ {protocol} protocol failed")
                        comparison_results['protocols'][protocol] = None
                        
                finally:
                    loop.close()
                
                # Update progress
                progress_bar.progress(10 + ((i + 1) * 40))
                self.render_live_logs(logs_container)
            
            # Generate comparison metrics
            status_text.text("📊 Generating comparison analysis...")
            progress_bar.progress(95)
            
            comparison_results['comparison_metrics'] = self.generate_comparison_metrics(comparison_results['protocols'])
            
            progress_bar.progress(100)
            status_text.text("✅ Protocol comparison completed!")
            
            # Save comparison results with enhanced organization
            self.save_comparison_report(comparison_results)
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Protocol comparison error: {e}", exc_info=True)
            status_text.text(f"❌ Comparison failed: {str(e)}")
            progress_bar.progress(0)
            return None
    
    def generate_comparison_metrics(self, protocol_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive comparison metrics between protocols"""
        metrics = {
            'performance_comparison': {},
            'efficiency_analysis': {},
            'scalability_metrics': {},
            'security_comparison': {},
            'winner_analysis': {}
        }
        
        successful_protocols = {k: v for k, v in protocol_results.items() if v is not None}
        
        if len(successful_protocols) < 2:
            return metrics
        
        # Performance comparison
        for protocol, results in successful_protocols.items():
            benchmarks = results.get('benchmarks', {})
            
            metrics['performance_comparison'][protocol] = {
                'total_time': benchmarks.get('total_time', 0),
                'avg_proof_generation_time': benchmarks.get('performance_analysis', {}).get('avg_proof_generation_time', 0),
                'avg_proof_verification_time': benchmarks.get('performance_analysis', {}).get('avg_proof_verification_time', 0),
                'avg_proof_size': benchmarks.get('performance_analysis', {}).get('avg_proof_size', 0),
                'final_accuracy': benchmarks.get('fl_metrics', {}).get('accuracy_progression', [0])[-1] if benchmarks.get('fl_metrics', {}).get('accuracy_progression') else 0
            }
        
        # Efficiency analysis
        protocols = list(successful_protocols.keys())
        if len(protocols) >= 2:
            protocol1, protocol2 = protocols[0], protocols[1]
            p1_metrics = metrics['performance_comparison'][protocol1]
            p2_metrics = metrics['performance_comparison'][protocol2]
            
            metrics['efficiency_analysis'] = {
                'time_ratio': p1_metrics['total_time'] / p2_metrics['total_time'] if p2_metrics['total_time'] > 0 else float('inf'),
                'proof_size_ratio': p1_metrics['avg_proof_size'] / p2_metrics['avg_proof_size'] if p2_metrics['avg_proof_size'] > 0 else float('inf'),
                'verification_speed_ratio': p1_metrics['avg_proof_verification_time'] / p2_metrics['avg_proof_verification_time'] if p2_metrics['avg_proof_verification_time'] > 0 else float('inf'),
                'accuracy_difference': abs(p1_metrics['final_accuracy'] - p2_metrics['final_accuracy'])
            }
            
            # Winner analysis
            winner_scores = {}
            for protocol in protocols:
                score = 0
                pm = metrics['performance_comparison'][protocol]
                
                # Lower is better for time and size
                if pm['total_time'] == min(metrics['performance_comparison'][p]['total_time'] for p in protocols):
                    score += 3
                if pm['avg_proof_size'] == min(metrics['performance_comparison'][p]['avg_proof_size'] for p in protocols):
                    score += 2
                if pm['avg_proof_verification_time'] == min(metrics['performance_comparison'][p]['avg_proof_verification_time'] for p in protocols):
                    score += 2
                
                # Higher is better for accuracy
                if pm['final_accuracy'] == max(metrics['performance_comparison'][p]['final_accuracy'] for p in protocols):
                    score += 1
                
                winner_scores[protocol] = score
            
            best_protocol = max(winner_scores.keys(), key=lambda k: winner_scores[k])
            metrics['winner_analysis'] = {
                'scores': winner_scores,
                'best_overall': best_protocol,
                'reasoning': f"{best_protocol} scored highest with {winner_scores[best_protocol]} points"
            }
        else:
            # Default when no protocols or insufficient data
            metrics['winner_analysis'] = {
                'scores': {},
                'best_overall': 'unknown',
                'reasoning': 'Insufficient data for analysis'
            }
        
        return metrics
    
    def save_comparison_report(self, comparison_results: Dict[str, Any]):
        """Save detailed comparison report with enhanced organization"""
        import json
        from pathlib import Path
        from datetime import datetime
        
        # Create comparison directory structure
        timestamp = comparison_results.get('timestamp', int(time.time()))
        date_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d")
        time_str = datetime.fromtimestamp(timestamp).strftime("%H%M%S")
        
        comparison_dir = Path("benchmarks") / "comparisons" / date_str
        comparison_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract experiment configuration
        config = comparison_results.get('config', {})
        num_clients = config.get('num_clients', 'unknown')
        num_rounds = config.get('num_rounds', 'unknown')
        
        # Generate enhanced comparison data
        enhanced_data = {
            'comparison_id': f"comparison_{timestamp}",
            'timestamp': timestamp,
            'date_str': date_str,
            'time_str': time_str,
            'experiment_config': {
                'num_clients': num_clients,
                'num_rounds': num_rounds,
                'dataset': 'Heart Disease (Synthetic)',
                'experiment_type': 'Protocol Comparison'
            },
            'protocols': {},
            'comparison_metrics': comparison_results.get('comparison_metrics', {}),
            'summary': {}
        }
        
        # Extract and organize protocol data
        successful_protocols = 0
        for protocol, results in comparison_results.get('protocols', {}).items():
            if results is not None:
                benchmarks = results.get('benchmarks', {})
                enhanced_data['protocols'][protocol] = {
                    'total_time': benchmarks.get('total_time', 0),
                    'fl_metrics': benchmarks.get('fl_metrics', {}),
                    'zkp_metrics': benchmarks.get('zkp_metrics', {}),
                    'performance_analysis': benchmarks.get('performance_analysis', {}),
                    'status': 'completed'
                }
                successful_protocols += 1
            else:
                enhanced_data['protocols'][protocol] = {
                    'status': 'failed',
                    'error': 'Experiment failed'
                }
        
        # Generate summary statistics
        if successful_protocols >= 2:
            protocols = [p for p, data in enhanced_data['protocols'].items() if data['status'] == 'completed']
            if len(protocols) >= 2:
                p1, p2 = protocols[0], protocols[1]
                
                p1_time = enhanced_data['protocols'][p1]['total_time']
                p2_time = enhanced_data['protocols'][p2]['total_time']
                
                enhanced_data['summary'] = {
                    'total_protocols_tested': len(enhanced_data['protocols']),
                    'successful_protocols': successful_protocols,
                    'faster_protocol': p1 if p1_time < p2_time else p2,
                    'time_difference_seconds': abs(p1_time - p2_time),
                    'speed_improvement_ratio': max(p1_time, p2_time) / min(p1_time, p2_time) if min(p1_time, p2_time) > 0 else 1,
                    'winner_analysis': enhanced_data['comparison_metrics'].get('winner_analysis', {}),
                    'performance_metrics': {
                        'fastest_total_time': min(p1_time, p2_time),
                        'slowest_total_time': max(p1_time, p2_time),
                        'time_saved_seconds': abs(p1_time - p2_time),
                        'improvement_percentage': f"{((max(p1_time, p2_time) - min(p1_time, p2_time)) / max(p1_time, p2_time) * 100):.1f}%" if max(p1_time, p2_time) > 0 else "0%"
                    }
                }
        
        # Save the detailed comparison report
        detailed_filename = f"comparison_c{num_clients}r{num_rounds}_{time_str}.json"
        report_file = comparison_dir / detailed_filename
        
        try:
            with open(report_file, 'w') as f:
                json.dump(enhanced_data, f, indent=2, default=str)
            
            logger.info(f"📊 Detailed comparison report saved to {report_file}")
            
            # Save a latest comparison summary for quick access
            latest_file = Path("benchmarks") / "latest_comparison.json"
            latest_data = {
                'latest_comparison_id': enhanced_data['comparison_id'],
                'report_path': str(report_file),
                'timestamp': timestamp,
                'date': date_str,
                'summary': enhanced_data['summary'],
                'quick_stats': {
                    'protocols_tested': enhanced_data['summary'].get('total_protocols_tested', 0),
                    'successful_tests': enhanced_data['summary'].get('successful_protocols', 0),
                    'winner': enhanced_data['summary'].get('winner_analysis', {}).get('best_overall', 'Unknown')
                }
            }
            
            with open(latest_file, 'w') as f:
                json.dump(latest_data, f, indent=2)
            
            logger.info(f"📋 Latest comparison summary updated")
            
        except Exception as e:
            logger.error(f"Failed to save comparison report: {e}")
    
    
    def create_protocol_comparison_visualizations(self, comparison_results: Dict[str, Any], experiment_id: str):
        """Create comprehensive comparison visualizations"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h3 style="margin: 0;">⚔️ Protocol Performance Comparison</h3>
        </div>
        """, unsafe_allow_html=True)
        
        protocols = comparison_results.get('protocols', {})
        comparison_metrics = comparison_results.get('comparison_metrics', {})
        
        if len(protocols) < 2:
            st.error("Need at least 2 protocols for comparison")
            return
        
        # Create comparison tabs
        tab1, tab2, tab3, tab4 = st.tabs(["⏱️ Performance", "📊 Proof Analysis", "🏆 Winner Analysis", "📈 Detailed Metrics"])
        
        with tab1:
            # Performance comparison charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Total execution time comparison
                protocol_names = []
                total_times = []
                
                for protocol, results in protocols.items():
                    if results:
                        protocol_names.append(protocol.replace('_', '+').title())
                        total_times.append(results.get('benchmarks', {}).get('total_time', 0))
                
                if protocol_names:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=protocol_names,
                            y=total_times,
                            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1'][:len(protocol_names)],
                            text=[f'{t:.2f}s' for t in total_times],
                            textposition='auto'
                        )
                    ])
                    
                    fig.update_layout(
                        title="⏱️ Total Execution Time",
                        yaxis_title="Time (seconds)",
                        template="plotly_white",
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, width="stretch", key=f"time_comparison_{experiment_id}")
            
            with col2:
                # Proof size comparison
                proof_sizes = []
                for protocol, results in protocols.items():
                    if results:
                        proof_sizes.append(results.get('benchmarks', {}).get('performance_analysis', {}).get('avg_proof_size', 0))
                
                if protocol_names and proof_sizes:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=protocol_names,
                            y=proof_sizes,
                            marker_color=['#96CEB4', '#FFEAA7', '#DDA0DD'][:len(protocol_names)],
                            text=[f'{s:.0f} bytes' for s in proof_sizes],
                            textposition='auto'
                        )
                    ])
                    
                    fig.update_layout(
                        title="📊 Average Proof Size",
                        yaxis_title="Size (bytes)",
                        template="plotly_white",
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, width="stretch", key=f"size_comparison_{experiment_id}")
        
        with tab2:
            # Detailed proof analysis
            if 'performance_comparison' in comparison_metrics:
                perf_data = comparison_metrics['performance_comparison']
                
                # Create detailed comparison table
                comparison_table = []
                for protocol, metrics in perf_data.items():
                    comparison_table.append({
                        'Protocol': protocol.replace('_', '+').title(),
                        'Total Time (s)': f"{metrics['total_time']:.3f}",
                        'Avg Proof Gen (ms)': f"{metrics['avg_proof_generation_time']*1000:.2f}",
                        'Avg Proof Verify (ms)': f"{metrics['avg_proof_verification_time']*1000:.2f}",
                        'Avg Proof Size (bytes)': f"{metrics['avg_proof_size']:.0f}",
                        'Final Accuracy': f"{metrics['final_accuracy']:.4f}"
                    })
                
                df = pd.DataFrame(comparison_table)
                st.dataframe(df, width="stretch", hide_index=True)
        
        with tab3:
            # Winner analysis
            if 'winner_analysis' in comparison_metrics:
                winner_data = comparison_metrics.get('winner_analysis', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    best_protocol = winner_data.get('best_overall', 'Unknown')
                    reasoning = winner_data.get('reasoning', 'Analysis pending')
                    
                    st.markdown(f"""
                    ### 🏆 Overall Winner
                    **{best_protocol.replace('_', '+').title()}**
                    
                    {reasoning}
                    """)
                
                with col2:
                    # Score breakdown
                    scores_data = winner_data.get('scores', {})
                    if scores_data:
                        protocols_list = list(scores_data.keys())
                        scores = list(scores_data.values())
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=[p.replace('_', '+').title() for p in protocols_list],
                            y=scores,
                            marker_color=['gold' if s == max(scores) else 'lightblue' for s in scores],
                            text=scores,
                            textposition='auto'
                        )
                    ])
                    
                    fig.update_layout(
                        title="🏆 Protocol Scores",
                        yaxis_title="Score",
                        template="plotly_white",
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, width="stretch", key=f"winner_analysis_{experiment_id}")
        
        with tab4:
            # Show full comparison results
            st.json(comparison_results)

    async def run_experiment_with_updates(self, config: Dict[str, Any], progress_bar, status_text, logs_container) -> Optional[Dict[str, Any]]:
        """Run comprehensive FL experiment with real-time updates"""
        try:
            # Create experiment ID
            experiment_id = f"{config['protocol']}_{int(time.time())}"
            
            status_text.text(f"🚀 Starting experiment: {experiment_id}")
            progress_bar.progress(15)
            
            # Load dataset
            data_loader = RealDatasetLoader()
            
            # Load appropriate dataset
            if config['dataset_name'] == 'heart_disease':
                X, y = data_loader.load_dataset('heart_2020')
                data_loader.datasets['heart_2020'] = {'X': X, 'y': y}
                dataset_key = 'heart_2020'
            elif config['dataset_name'] == 'diabetes':
                X, y = data_loader.load_dataset('cardio')  # Use cardio as alternative medical dataset
                data_loader.datasets['cardio'] = {'X': X, 'y': y}
                dataset_key = 'cardio'
            else:
                # Generate synthetic data for other cases
                np.random.seed(42)
                X = np.random.randn(config['dataset_size'], 10)
                y = np.random.randint(0, 2, config['dataset_size'])
                # Store synthetic dataset
                data_loader.datasets['synthetic'] = {'X': X, 'y': y}
                dataset_key = 'synthetic'
            
            status_text.text("📊 Dataset loaded, splitting data for clients...")
            progress_bar.progress(25)
            
            # Split data for clients
            if config['data_split'] == 'iid':
                # For IID, manually create balanced splits
                client_data = {}
                samples_per_client = len(X) // config['num_clients']
                
                for i in range(config['num_clients']):
                    start_idx = i * samples_per_client
                    end_idx = start_idx + samples_per_client if i < config['num_clients'] - 1 else len(X)
                    
                    client_data[f'client_{i}'] = {
                        'X': X[start_idx:end_idx],
                        'y': y[start_idx:end_idx]
                    }
            else:
                # Use the available non-IID partitioning method
                client_data_dict = data_loader.create_non_iid_partition(
                    dataset_key, config['num_clients'], 'medium'
                )
                
                # Convert to expected format
                client_data = {}
                for client_id, data in client_data_dict.items():
                    client_data[f'client_{client_id}'] = {
                        'X': data['X'],
                        'y': data['y']
                    }
            
            status_text.text("🔧 Initializing ZKP-FL system...")
            progress_bar.progress(35)
            
            # Configure FL system
            zkp_config = ZKPProtocolConfig(
                protocol_type=config['protocol'],
                enable_aggregation=config['enable_aggregation'],
                security_level=config['security_level']
            )
            
            # Determine input features from dataset
            input_features = X.shape[1]
            logger.info(f"📊 Dataset loaded: {X.shape[0]} samples, {input_features} features")
            
            fl_config = UnifiedFLConfig(
                num_rounds=config['num_rounds'],
                learning_rate=config['learning_rate'],
                batch_size=config['batch_size'],
                local_epochs=config['local_epochs'],
                zkp_config=zkp_config
            )
            
            # Initialize FL system
            fl_system = MultiProtocolZKPFLSystem(fl_config)
            
            status_text.text("👥 Adding clients to FL system...")
            progress_bar.progress(45)
            
            # Add clients
            for client_id, client_info in client_data.items():
                X_client = client_info['X']
                y_client = client_info['y']
                fl_system.add_client(client_id, X_client, y_client)
            
            status_text.text("🚀 Running federated learning with ZKP proofs...")
            progress_bar.progress(55)
            
            # Create a task for FL execution and log updating
            async def update_logs_periodically():
                while True:
                    self.render_live_logs(logs_container)
                    await asyncio.sleep(1)  # Update every second
            
            # Start log updating task
            log_task = asyncio.create_task(update_logs_periodically())
            
            try:
                # Run federated learning
                results = await fl_system.run_federated_learning()
                
                status_text.text("✅ Experiment completed successfully!")
                progress_bar.progress(100)
                
                # Final log update
                self.render_live_logs(logs_container)
                
                # Store results
                self.experiment_results[experiment_id] = results
                
                return results
                
            finally:
                # Cancel log updating task
                log_task.cancel()
                try:
                    await log_task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            status_text.text(f"❌ Experiment failed: {str(e)}")
            progress_bar.progress(0)
            logger.error(f"Experiment error: {e}", exc_info=True)
            return None
    
    def render_experiment_logs(self):
        """Render real-time experiment logs"""
        # Logs are now handled by render_live_logs method
        pass
    
    def render_live_logs(self, container):
        """Render live logs in real-time"""
        logs = self.log_handler.get_logs()
        
        if logs:
            # Get recent logs (last 50)
            recent_logs = logs[-50:]
            
            log_text = ""
            for log in recent_logs:
                level_color = {
                    'INFO': '#00ff00',
                    'WARNING': '#ffff00', 
                    'ERROR': '#ff0000',
                    'DEBUG': '#888888'
                }.get(log['level'], '#ffffff')
                
                log_text += f"<div style='color: {level_color}; font-family: monospace; font-size: 12px; margin: 2px 0;'>"
                log_text += f"[{log['timestamp']}] {log['level']}: {log['message']}"
                log_text += "</div>"
            
            container.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; max-height: 400px; overflow-y: auto; font-family: 'Courier New', monospace;">
                <h4 style="color: #ffffff; margin-bottom: 10px;">📡 Live Experiment Logs</h4>
                <div style="background-color: #000000; padding: 10px; border-radius: 5px; border: 1px solid #333;">
                    {log_text if log_text else '<div style="color: #888888;">Waiting for experiment to start...</div>'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            container.markdown("""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; font-family: 'Courier New', monospace;">
                <h4 style="color: #ffffff; margin-bottom: 10px;">📡 Live Experiment Logs</h4>
                <div style="background-color: #000000; padding: 10px; border-radius: 5px; border: 1px solid #333; color: #888888;">
                    Waiting for experiment to start...
                </div>
            </div>
            """, unsafe_allow_html=True)

    def main(self):
        """Main dashboard application"""
        self.render_header()
        
        # Experiment controls
        config = self.render_experiment_controls()
        
        # Enhanced run experiment button with progress
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🚀 **Launch Experiment**")
        
        # Experiment preview
        with st.sidebar.expander("📋 **Experiment Preview**"):
            st.markdown(f"""
            **Protocol:** {config['protocol'].upper()}  
            **Clients:** {config['num_clients']} participants  
            **Rounds:** {config['num_rounds']} training rounds  
            **Data:** {config['data_split'].upper()} distribution  
            **Dataset:** {config['dataset_name'].replace('_', ' ').title()}  
            **Samples:** {config['dataset_size']} per experiment  
            """)
        
        if st.sidebar.button("🚀 **START EXPERIMENT**", type="primary", help="Launch ZKP federated learning experiment"):
            # Clear previous logs and start logging immediately
            self.log_handler.clear_logs()
            logger.info("🚀 Starting new ZKP Federated Learning experiment...")
            logger.info(f"📊 Configuration: {config['num_clients']} clients, {config['num_rounds']} rounds, {config['protocol']} protocol")
            
            # Show experiment status
            st.markdown("""
            <div class="info-box">
                <h4>🚀 Experiment Starting...</h4>
                <p>Initializing ZKP-FL system with your configuration. This may take a few moments.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create live logs container immediately
            logs_container = st.container()
            self.render_live_logs(logs_container)
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Check if comparison mode
            if config['protocol'] == 'comparison':
                # Run protocol comparison
                logger.info("⚔️ Running Protocol Comparison Mode: Nova vs ProtoStar+ProtoGalaxy")
                status_text.text("⚔️ Running comparison of all protocols...")
                progress_bar.progress(5)
                
                comparison_results = self.run_protocol_comparison(config, progress_bar, status_text, logs_container)
                
                if comparison_results:
                    # Display comparison results
                    st.markdown("""
                    <div class="success-box">
                        <h4>⚔️ Protocol Comparison Completed!</h4>
                        <p>All protocols have been tested. Comprehensive comparison analysis ready!</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create comparison visualizations
                    experiment_id = f"comparison_{int(time.time())}"
                    self.create_protocol_comparison_visualizations(comparison_results, experiment_id)
                    
                    # Show raw comparison results
                    with st.expander("🔍 **Detailed Comparison Results**"):
                        st.json(comparison_results)
                else:
                    st.error("❌ Protocol comparison failed")
            
            else:
                # Single protocol execution
                logger.info(f"🔬 Running single protocol experiment: {config['protocol']}")
                
                # Progress indicators
                progress_container = st.container()
                
                with progress_container:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("""
                        <div class="metric-card">
                            <h5>📊 Data Loading</h5>
                            <p>Loading and partitioning dataset...</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown("""
                        <div class="metric-card">
                            <h5>🔐 ZKP Setup</h5>
                            <p>Initializing cryptographic protocols...</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown("""
                        <div class="metric-card">
                            <h5>🧠 FL Training</h5>
                            <p>Preparing federated learning system...</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Use asyncio to run the experiment with real-time updates
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Update status
                    status_text.text("🔄 Starting ZKP-FL experiment...")
                    progress_bar.progress(10)
                    
                    results = loop.run_until_complete(self.run_experiment_with_updates(config, progress_bar, status_text, logs_container))
                    
                    if results:
                        experiment_id = f"{config['protocol']}_{int(time.time())}"
                        
                        # Success notification
                        st.markdown("""
                        <div class="success-box">
                            <h4>🎯 Experiment Completed Successfully!</h4>
                            <p>Your ZKP federated learning experiment has finished. Generating comprehensive visualizations...</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Create comprehensive visualizations
                        self.create_comprehensive_visualizations(results, experiment_id)
                        
                        # Show raw results (expandable)
                        with st.expander("🔍 **Detailed Experiment Results**"):
                            st.json(results)
                            
                    else:
                        st.markdown("""
                        <div class="warning-box">
                            <h4>⚠️ Experiment Failed</h4>
                            <p>The experiment encountered an error. Please check your configuration and try again.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Experiment error: {str(e)}")
                    logger.error(f"Experiment error: {e}")
                            
                finally:
                    loop.close()
        
        # Display saved experiments with enhanced UI
        if self.experiment_results:
            st.markdown("---")
            st.markdown("""
            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; color: white; margin: 2rem 0;">
                <h2 style="margin: 0;">📊 Experiment History & Analytics</h2>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Review and compare your previous ZKP-FL experiments</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🧪 Total Experiments", len(self.experiment_results))
            with col2:
                protocols_used = [r['benchmarks']['protocol_info']['name'] for r in self.experiment_results.values()]
                st.metric("🔐 Protocols Tested", len(set(protocols_used)))
            with col3:
                total_clients = sum([r['benchmarks']['fl_metrics']['client_count'] for r in self.experiment_results.values()])
                st.metric("👥 Total Clients", total_clients)
            with col4:
                avg_time = np.mean([r['benchmarks']['total_time'] for r in self.experiment_results.values()])
                st.metric("⏱️ Avg Runtime", f"{avg_time:.1f}s")
            
            # Experiment tabs
            experiment_tabs = st.tabs([f"📋 Experiment {i+1}" for i in range(len(self.experiment_results))])
            
            for i, (exp_id, results) in enumerate(self.experiment_results.items()):
                with experiment_tabs[i]:
                    # Experiment header with key info
                    protocol_name = results['benchmarks']['protocol_info']['name']
                    total_time = results['benchmarks']['total_time']
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>🔬 {exp_id}</h4>
                        <p><strong>Protocol:</strong> {protocol_name} | <strong>Duration:</strong> {total_time:.2f}s</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    self.create_comprehensive_visualizations(results, exp_id)
        else:
            st.markdown("""
            <div class="info-box">
                <h4>🧪 No Experiments Yet</h4>
                <p>Run your first ZKP federated learning experiment using the controls in the sidebar to see analytics here!</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Real-time logs
        self.render_experiment_logs()

if __name__ == "__main__":
    dashboard = ComprehensiveFLDashboard()
    dashboard.main()