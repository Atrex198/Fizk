# Unified ZKP-Federated Learning Architecture
**Multi-Protocol Zero-Knowledge Proof System for Federated Learning**

---

**Version**: 1.0.0  
**Date**: October 6, 2025  
**Authors**: Advanced ZK-FL Research Team  
**Protocols Supported**: ProtoStar, PLONK, Groth16, Bulletproofs, Nova

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [Unified ZKP Interface](#3-unified-zkp-interface)
4. [Federated Learning Layer](#4-federated-learning-layer)
5. [Protocol Integration](#5-protocol-integration)
6. [Data Flow](#6-data-flow)
7. [Configuration System](#7-configuration-system)
8. [Benchmarking Framework](#8-benchmarking-framework)
9. [Implementation Guidelines](#9-implementation-guidelines)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Global Server                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Federated Learning Orchestrator                  │  │
│  │  - Round Management                                           │  │
│  │  - Client Coordination                                        │  │
│  │  - Model Aggregation (FedAvg)                                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────▼───────────────────────────────────┐  │
│  │           Unified ZKP Verification Layer                      │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │    Protocol-Agnostic Interface (IZKPProtocol)          │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │                              │                                │  │
│  │  ┌──────────┬─────────┬──────────┬──────────┬──────────┐    │  │
│  │  │ProtoStar │  PLONK  │ Groth16  │Bulletproof│  Nova   │    │  │
│  │  │ Verifier │Verifier │ Verifier │ Verifier  │Verifier │    │  │
│  │  └──────────┴─────────┴──────────┴──────────┴──────────┘    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────▼───────────────────────────────────┐  │
│  │           Benchmarking & Metrics Collection                   │  │
│  │  - Real-time Performance Metrics                              │  │
│  │  - Historical Analysis                                        │  │
│  │  - Comparative Statistics                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │ Network
                              │
        ┌─────────────────────┴─────────────────────┐
        │                     │                      │
┌───────▼───────┐    ┌───────▼───────┐    ┌────────▼──────┐
│   Client 1    │    │   Client 2    │    │   Client N    │
│ ┌───────────┐ │    │ ┌───────────┐ │    │ ┌───────────┐ │
│ │  ML       │ │    │ │  ML       │ │    │ │  ML       │ │
│ │  Trainer  │ │    │ │  Trainer  │ │    │ │  Trainer  │ │
│ └─────┬─────┘ │    │ └─────┬─────┘ │    │ └─────┬─────┘ │
│       │       │    │       │       │    │       │       │
│ ┌─────▼─────┐ │    │ ┌─────▼─────┐ │    │ ┌─────▼─────┐ │
│ │    ZKP    │ │    │ │    ZKP    │ │    │ │    ZKP    │ │
│ │  Prover   │ │    │ │  Prover   │ │    │ │  Prover   │ │
│ └───────────┘ │    │ └───────────┘ │    │ └───────────┘ │
│ Protocol: X   │    │ Protocol: X   │    │ Protocol: X   │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 1.2 Key Components

1. **Global Server**
   - Federated learning coordinator
   - Protocol-agnostic ZKP verifier
   - Model aggregator
   - Metrics collector

2. **Clients**
   - Local ML training
   - ZKP proof generation
   - Model update submission

3. **ZKP Layer**
   - Unified interface
   - Multiple protocol implementations
   - Proof verification
   - Proof aggregation (where supported)

4. **Benchmarking System**
   - Real-time metrics
   - Historical analysis
   - Protocol comparison

---

## 2. Architecture Principles

### 2.1 Design Goals

1. **Protocol Agnostic**: FL system doesn't know about specific ZKP protocols
2. **Hot-Swappable**: Change protocols without modifying FL code
3. **Extensible**: Easy to add new ZKP protocols
4. **Comparable**: Fair benchmarking across protocols
5. **Production-Ready**: Real cryptography, not simulations

### 2.2 Separation of Concerns

```
┌─────────────────────────────────────────────┐
│         Federated Learning Layer            │
│  Concerns: Training, Aggregation, Rounds    │
│  Knows: Model weights, metrics, clients     │
│  Doesn't know: Proof internals, curves      │
└─────────────────────────────────────────────┘
                    │
          Uses abstract interface
                    │
┌─────────────────────────────────────────────┐
│         Unified ZKP Interface               │
│  Concerns: Proof format, verification API   │
│  Knows: Protocol capabilities, metadata     │
│  Doesn't know: FL specifics                 │
└─────────────────────────────────────────────┘
                    │
          Implemented by each protocol
                    │
┌─────────────────────────────────────────────┐
│         Protocol Implementations            │
│  Concerns: Cryptography, proof generation   │
│  Knows: Curves, constraints, commitments    │
│  Doesn't know: FL rounds, aggregation       │
└─────────────────────────────────────────────┘
```

### 2.3 Configuration-Driven Architecture

- **Compile-time protocol selection**: One protocol per experiment
- **Runtime configuration**: Parameters (setup size, security level)
- **Experiment reproducibility**: Configuration files for each run

---

## 3. Unified ZKP Interface

### 3.1 Core Abstractions

#### 3.1.1 `IZKPProtocol` Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ProtocolType(Enum):
    """Supported ZKP protocols"""
    PROTOSTAR = "protostar_ivc"
    PLONK = "plonk_kzg"
    GROTH16 = "groth16"
    BULLETPROOFS = "bulletproofs"
    NOVA = "nova_folding"

@dataclass
class ProofMetadata:
    """Standardized metadata for all proofs"""
    protocol_name: str
    protocol_type: ProtocolType
    proof_version: str
    
    # Proof characteristics
    proof_size_bytes: int
    constraint_count: int
    security_level: int
    
    # Generation info
    generation_time: float
    round_number: int
    client_id: str
    timestamp: float
    
    # Verification components
    verification_method: str
    requires_trusted_setup: bool
    trusted_setup_size: Optional[int]
    
    # Cryptographic details
    curve_name: Optional[str]
    field_modulus: Optional[str]
    commitment_scheme: Optional[str]
    
    # Optional aggregation info
    supports_aggregation: bool
    aggregation_method: Optional[str]

@dataclass
class VerificationResult:
    """Standardized verification result"""
    is_valid: bool
    verification_time: float
    error_message: Optional[str]
    
    # Detailed verification info
    constraint_satisfaction: bool
    commitment_verification: bool
    cryptographic_soundness: bool
    
    # Performance metrics
    verification_complexity: str  # e.g., "O(1)", "O(log n)"
    gas_cost_estimate: Optional[int]  # For blockchain deployment

@dataclass
class ProofObject:
    """Standardized proof structure"""
    metadata: ProofMetadata
    proof_data: Dict[str, Any]  # Protocol-specific proof
    public_inputs: List[str]    # Public parameters
    auxiliary_data: Dict[str, Any]  # Extra protocol-specific data

class IZKPProtocol(ABC):
    """
    Unified interface for all ZKP protocols
    
    All protocol implementations must inherit from this interface
    to ensure compatibility with the FL system.
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize protocol with configuration
        
        Args:
            config: Protocol-specific configuration
                - trusted_setup_size: int (if applicable)
                - security_level: int
                - curve_name: str (if applicable)
                - optimization_level: str ("fast", "small", "balanced")
        """
        pass
    
    @abstractmethod
    def setup(self) -> Dict[str, Any]:
        """
        Perform protocol setup (if required)
        
        Returns:
            setup_artifacts: Dictionary containing:
                - proving_key: Any (if applicable)
                - verification_key: Any
                - public_parameters: Any
                - setup_time: float
        """
        pass
    
    @abstractmethod
    def generate_proof(
        self,
        statement: Dict[str, Any],
        witness: Dict[str, Any],
        round_number: int,
        client_id: str
    ) -> ProofObject:
        """
        Generate zero-knowledge proof
        
        Args:
            statement: Public statement to prove
                - model_architecture: str
                - initial_weights_commitment: str
                - final_weights_commitment: str
                - training_config: Dict
            witness: Private witness (model weights, training process)
                - model_weights: Dict[str, List[float]]
                - training_history: List[Dict]
                - random_seed: int
            round_number: FL round number
            client_id: Client identifier
        
        Returns:
            ProofObject with metadata and proof data
        """
        pass
    
    @abstractmethod
    def verify_proof(
        self,
        proof: ProofObject,
        statement: Dict[str, Any]
    ) -> VerificationResult:
        """
        Verify zero-knowledge proof
        
        Args:
            proof: ProofObject to verify
            statement: Public statement that was proven
        
        Returns:
            VerificationResult with validity and metrics
        """
        pass
    
    @abstractmethod
    def aggregate_proofs(
        self,
        proofs: List[ProofObject],
        aggregation_method: str = "default"
    ) -> Optional[ProofObject]:
        """
        Aggregate multiple proofs (if supported)
        
        Args:
            proofs: List of proofs to aggregate
            aggregation_method: Aggregation strategy
        
        Returns:
            Aggregated ProofObject or None if not supported
        """
        pass
    
    @abstractmethod
    def get_protocol_info(self) -> Dict[str, Any]:
        """
        Get protocol capabilities and characteristics
        
        Returns:
            Protocol information:
                - protocol_name: str
                - supports_ivc: bool
                - supports_aggregation: bool
                - trusted_setup_required: bool
                - quantum_resistant: bool
                - typical_proof_size_kb: float
                - typical_verification_time_ms: float
        """
        pass
    
    @abstractmethod
    def serialize_proof(self, proof: ProofObject) -> bytes:
        """Serialize proof for transmission"""
        pass
    
    @abstractmethod
    def deserialize_proof(self, data: bytes) -> ProofObject:
        """Deserialize proof from bytes"""
        pass
```

### 3.2 Statement and Witness Format

#### 3.2.1 Training Statement (Public)

```python
@dataclass
class TrainingStatement:
    """Public statement about training process"""
    
    # Model specification
    model_architecture: str  # e.g., "3-layer-feedforward"
    input_features: int
    output_classes: int
    
    # Training configuration
    local_epochs: int  # Always 10 per round
    batch_size: int
    learning_rate: float
    optimizer: str
    
    # Data specification
    num_samples: int
    dataset_commitment: str  # Hash of dataset distribution
    
    # Weight commitments (Merkle root or polynomial commitment)
    initial_weights_commitment: str
    final_weights_commitment: str
    
    # Training metrics (claimed values)
    claimed_accuracy: float
    claimed_loss: float
    
    # Round information
    round_number: int
    fl_round_total: int  # Total rounds this client will do
```

#### 3.2.2 Training Witness (Private)

```python
@dataclass
class TrainingWitness:
    """Private witness for training process"""
    
    # Model weights (secret)
    initial_weights: Dict[str, List[float]]
    final_weights: Dict[str, List[float]]
    intermediate_weights: List[Dict[str, List[float]]]  # Per-epoch snapshots
    
    # Training data
    X_train: np.ndarray  # Training features
    y_train: np.ndarray  # Training labels
    
    # Training process
    gradient_history: List[Dict[str, List[float]]]  # Gradients per epoch
    loss_history: List[float]  # Loss per epoch (10 values)
    accuracy_history: List[float]  # Accuracy per epoch
    
    # Randomness
    random_seed: int
    random_state: Any  # For reproducibility
    
    # Commitment openings
    weight_commitment_randomness: str
```

### 3.3 Protocol Factory

```python
class ZKPProtocolFactory:
    """Factory for creating protocol instances"""
    
    _protocols = {
        ProtocolType.PROTOSTAR: 'ProtoStarProtocol',
        ProtocolType.PLONK: 'PLONKProtocol',
        ProtocolType.GROTH16: 'Groth16Protocol',
        ProtocolType.BULLETPROOFS: 'BulletproofsProtocol',
        ProtocolType.NOVA: 'NovaProtocol'
    }
    
    @staticmethod
    def create_protocol(
        protocol_type: ProtocolType,
        config: Dict[str, Any]
    ) -> IZKPProtocol:
        """
        Create protocol instance
        
        Args:
            protocol_type: Type of protocol to create
            config: Protocol configuration
        
        Returns:
            IZKPProtocol implementation
        """
        protocol_class_name = ZKPProtocolFactory._protocols[protocol_type]
        protocol_class = globals()[protocol_class_name]
        return protocol_class(config)
    
    @staticmethod
    def get_available_protocols() -> List[ProtocolType]:
        """Get list of available protocols"""
        return list(ZKPProtocolFactory._protocols.keys())
```

---

## 4. Federated Learning Layer

### 4.1 FL Orchestrator

```python
class FederatedLearningOrchestrator:
    """
    Protocol-agnostic federated learning coordinator
    
    This class knows NOTHING about specific ZKP protocols.
    It only uses the IZKPProtocol interface.
    """
    
    def __init__(
        self,
        num_clients: int,
        num_rounds: int,
        zkp_protocol: IZKPProtocol,
        dataset_loader: Any,
        config: Dict[str, Any]
    ):
        self.num_clients = num_clients
        self.num_rounds = num_rounds
        self.zkp_protocol = zkp_protocol  # Abstract interface
        self.dataset_loader = dataset_loader
        self.config = config
        
        self.clients = []
        self.global_model = None
        self.round_results = []
    
    async def setup(self):
        """Setup FL system"""
        # 1. Setup ZKP protocol (if needed)
        setup_artifacts = self.zkp_protocol.setup()
        
        # 2. Load dataset
        X_data, y_data = self.dataset_loader.load_dataset()
        
        # 3. Initialize clients
        for i in range(self.num_clients):
            client = FLClient(
                client_id=f"client_{i:03d}",
                X_data=X_data[i],
                y_data=y_data[i],
                zkp_protocol=self.zkp_protocol,
                config=self.config
            )
            self.clients.append(client)
    
    async def run_federated_round(self, round_number: int) -> Dict:
        """
        Execute one federated round
        
        Returns:
            round_results: Aggregated metrics and verification info
        """
        # Phase 1: Client Training & Proof Generation
        client_updates = []
        for client in self.clients:
            update = await client.train_and_prove(
                global_weights=self.global_model,
                round_number=round_number
            )
            client_updates.append(update)
        
        # Phase 2: Proof Verification
        verified_updates = []
        verification_results = []
        
        for update in client_updates:
            result = self.zkp_protocol.verify_proof(
                proof=update['proof'],
                statement=update['statement']
            )
            verification_results.append(result)
            
            if result.is_valid:
                verified_updates.append(update)
        
        # Phase 3: Proof Aggregation (if supported)
        aggregated_proof = None
        if len(verified_updates) > 1:
            proofs = [u['proof'] for u in verified_updates]
            aggregated_proof = self.zkp_protocol.aggregate_proofs(proofs)
        
        # Phase 4: Model Aggregation (FedAvg)
        self.global_model = self._aggregate_models(verified_updates)
        
        # Phase 5: Compile results
        round_result = {
            'round_number': round_number,
            'total_clients': len(client_updates),
            'verified_clients': len(verified_updates),
            'verification_rate': len(verified_updates) / len(client_updates),
            'verification_results': verification_results,
            'aggregated_proof': aggregated_proof,
            'global_model_accuracy': self._evaluate_global_model(),
            'protocol_metrics': self._extract_protocol_metrics(
                verification_results, aggregated_proof
            )
        }
        
        return round_result
    
    def _aggregate_models(self, verified_updates: List[Dict]) -> Dict:
        """Federated averaging"""
        total_samples = sum(u['num_samples'] for u in verified_updates)
        
        averaged_weights = {}
        for key in verified_updates[0]['model_weights'].keys():
            weighted_sum = sum(
                np.array(u['model_weights'][key]) * (u['num_samples'] / total_samples)
                for u in verified_updates
            )
            averaged_weights[key] = weighted_sum.tolist()
        
        return averaged_weights
    
    def _extract_protocol_metrics(
        self,
        verification_results: List[VerificationResult],
        aggregated_proof: Optional[ProofObject]
    ) -> Dict:
        """Extract protocol-specific metrics for benchmarking"""
        return {
            'avg_proof_size_bytes': np.mean([
                v.is_valid for v in verification_results  # Access proof size from results
            ]),
            'avg_verification_time': np.mean([
                v.verification_time for v in verification_results
            ]),
            'total_verification_time': sum(
                v.verification_time for v in verification_results
            ),
            'aggregation_enabled': aggregated_proof is not None,
            'aggregated_proof_size': (
                aggregated_proof.metadata.proof_size_bytes 
                if aggregated_proof else None
            )
        }
```

### 4.2 FL Client

```python
class FLClient:
    """
    Federated learning client with ZKP proof generation
    
    Protocol-agnostic: Uses IZKPProtocol interface
    """
    
    def __init__(
        self,
        client_id: str,
        X_data: np.ndarray,
        y_data: np.ndarray,
        zkp_protocol: IZKPProtocol,
        config: Dict[str, Any]
    ):
        self.client_id = client_id
        self.X_data = X_data
        self.y_data = y_data
        self.zkp_protocol = zkp_protocol
        self.config = config
        
        # ML trainer
        self.ml_trainer = RealMLTrainer(
            input_features=X_data.shape[1],
            config=config['training']
        )
    
    async def train_and_prove(
        self,
        global_weights: Optional[Dict],
        round_number: int
    ) -> Dict:
        """
        Train locally and generate ZKP proof
        
        Returns:
            client_update: Model weights, metrics, and proof
        """
        # 1. Initialize weights
        if global_weights:
            initial_weights = global_weights
        else:
            initial_weights = self.ml_trainer.initialize_weights()
        
        # 2. Train for 10 epochs (1 round = 10 epochs)
        training_result = await self.ml_trainer.train_local_model(
            X_train=self.X_data,
            y_train=self.y_data,
            initial_weights=initial_weights,
            epochs=10  # Fixed per round
        )
        
        final_weights = training_result.final_weights
        
        # 3. Prepare statement (public)
        statement = TrainingStatement(
            model_architecture=self.config['model']['architecture'],
            input_features=self.X_data.shape[1],
            output_classes=len(np.unique(self.y_data)),
            local_epochs=10,
            batch_size=self.config['training']['batch_size'],
            learning_rate=self.config['training']['learning_rate'],
            optimizer=self.config['training']['optimizer'],
            num_samples=len(self.X_data),
            dataset_commitment=self._commit_dataset(),
            initial_weights_commitment=self._commit_weights(initial_weights),
            final_weights_commitment=self._commit_weights(final_weights),
            claimed_accuracy=training_result.final_accuracy,
            claimed_loss=training_result.final_loss,
            round_number=round_number,
            fl_round_total=self.config['num_rounds']
        )
        
        # 4. Prepare witness (private)
        witness = TrainingWitness(
            initial_weights=initial_weights,
            final_weights=final_weights,
            intermediate_weights=training_result.epoch_weights,
            X_train=self.X_data,
            y_train=self.y_data,
            gradient_history=training_result.gradient_history,
            loss_history=training_result.loss_history,
            accuracy_history=training_result.accuracy_history,
            random_seed=self.config['random_seed'],
            random_state=training_result.random_state,
            weight_commitment_randomness=self._get_commitment_randomness()
        )
        
        # 5. Generate proof (protocol-agnostic call)
        proof = self.zkp_protocol.generate_proof(
            statement=statement.__dict__,
            witness=witness.__dict__,
            round_number=round_number,
            client_id=self.client_id
        )
        
        # 6. Return update
        return {
            'client_id': self.client_id,
            'round_number': round_number,
            'model_weights': final_weights,
            'num_samples': len(self.X_data),
            'training_metrics': {
                'accuracy': training_result.final_accuracy,
                'loss': training_result.final_loss
            },
            'statement': statement,
            'proof': proof
        }
    
    def _commit_weights(self, weights: Dict) -> str:
        """Create commitment to weights (Merkle root or hash)"""
        weight_bytes = json.dumps(weights, sort_keys=True).encode()
        return hashlib.sha256(weight_bytes).hexdigest()
    
    def _commit_dataset(self) -> str:
        """Create commitment to dataset distribution"""
        data_hash = hashlib.sha256(self.X_data.tobytes()).hexdigest()
        label_hash = hashlib.sha256(self.y_data.tobytes()).hexdigest()
        return hashlib.sha256(f"{data_hash}{label_hash}".encode()).hexdigest()
```

---

## 5. Protocol Integration

### 5.1 Integration Checklist

For each protocol implementation, ensure:

- [ ] Inherits from `IZKPProtocol`
- [ ] Implements all abstract methods
- [ ] Returns standardized `ProofObject`
- [ ] Provides `VerificationResult` with detailed metrics
- [ ] Handles serialization/deserialization
- [ ] Provides protocol info via `get_protocol_info()`
- [ ] Documents protocol-specific configuration
- [ ] Includes unit tests for interface compliance

### 5.2 Protocol Wrapper Template

```python
class NewProtocolWrapper(IZKPProtocol):
    """Wrapper for [Protocol Name] implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Initialize protocol-specific components
        self._setup_protocol()
    
    def _setup_protocol(self):
        """Initialize protocol internals"""
        # Protocol-specific initialization
        pass
    
    def setup(self) -> Dict[str, Any]:
        """Perform trusted setup if needed"""
        # Generate keys, parameters, etc.
        pass
    
    def generate_proof(self, statement, witness, round_number, client_id):
        """Generate proof using protocol's native API"""
        # 1. Convert statement/witness to protocol format
        # 2. Generate proof
        # 3. Wrap in ProofObject
        # 4. Add metadata
        pass
    
    def verify_proof(self, proof, statement):
        """Verify proof using protocol's native API"""
        # 1. Extract proof data
        # 2. Verify cryptographically
        # 3. Return VerificationResult
        pass
    
    # Implement remaining methods...
```

---

## 6. Data Flow

### 6.1 Complete FL Round Flow

```
TIME: Round N (All clients do same number of rounds)

[Client 1]                  [Client 2]              [Client N]
   │                            │                        │
   │ 1. Receive global weights  │                        │
   ├────────────────────────────┴────────────────────────┤
   │                                                      │
   │ 2. Train for 10 epochs (local)                      │
   │    - Epoch 1, 2, 3, ..., 10                         │
   │    - Collect gradients, metrics                     │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │ 3. Generate ZKP Proof                               │
   │    statement: {initial_commit, final_commit, ...}   │
   │    witness: {weights, gradients, data}              │
   │    proof: ProofObject                               │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │ 4. Send to server: {weights, metrics, proof}        │
   └──────────────────┬─────────────────┬─────────────────┘
                      │                 │
                      ▼                 ▼
              ┌─────────────────────────────┐
              │     Global Server           │
              ├─────────────────────────────┤
              │ 5. Verify Proofs (parallel) │
              │    - Client 1 proof ✓       │
              │    - Client 2 proof ✓       │
              │    - Client N proof ✗ FAIL  │
              ├─────────────────────────────┤
              │ 6. Aggregate Proofs         │
              │    [Proof 1, Proof 2] → Agg │
              ├─────────────────────────────┤
              │ 7. Model Aggregation        │
              │    global = FedAvg(verified)│
              ├─────────────────────────────┤
              │ 8. Collect Metrics          │
              │    - Proof sizes            │
              │    - Verification times     │
              │    - Accuracy improvement   │
              └─────────────────────────────┘
                      │
                      │ 9. Broadcast new global model
                      │
              ┌───────┴────────┬──────────────┐
              ▼                ▼              ▼
         [Client 1]      [Client 2]    [Client N]
         Round N+1       Round N+1     Round N+1
```

### 6.2 Proof Generation Pipeline

```
[ML Training Complete]
         │
         ▼
┌────────────────────────┐
│  Extract Training Info │
│  - Initial weights     │
│  - Final weights       │
│  - Gradients (10 epoch)│
│  - Metrics             │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Create Statement      │
│  (Public)              │
│  - Weight commitments  │
│  - Claimed metrics     │
│  - Configuration       │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Create Witness        │
│  (Private)             │
│  - Actual weights      │
│  - Training data       │
│  - Randomness          │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Protocol-Specific     │
│  Proof Generation      │
│  - Build circuit       │
│  - Generate proof      │
│  - Add metadata        │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Wrap in ProofObject   │
│  - metadata            │
│  - proof_data          │
│  - public_inputs       │
└──────────┬─────────────┘
           │
           ▼
    [Send to Server]
```

---

## 7. Configuration System

### 7.1 Experiment Configuration

```yaml
# experiment_config.yaml

experiment:
  name: "Multi-Protocol ZKP-FL Comparison"
  protocol: "plonk"  # protostar, plonk, groth16, bulletproofs, nova
  seed: 42

federated_learning:
  num_clients: 5
  num_rounds: 10  # All clients do 10 rounds
  dataset: "cardio"
  
  aggregation:
    method: "fedavg"
    weighting: "sample_count"

client_training:
  local_epochs: 10  # Per round, always 10
  batch_size: 64
  learning_rate: 0.01
  optimizer: "adam"
  loss_function: "cross_entropy"

model:
  architecture: "3-layer-feedforward"
  input_features: 11  # From dataset
  hidden_layers: [64, 32]
  output_classes: 2

zkp_protocol:
  # Common settings
  security_level: 128
  optimization: "balanced"  # fast, small, balanced
  
  # Protocol-specific settings
  protostar:
    trusted_setup_size: 1024
    curve: "bn128"
    ivc_enabled: true
    aggregation: "protogalaxy"
  
  plonk:
    trusted_setup_size: 1024
    curve: "bn254"
    custom_gates: false
    kzg_commitment: true
  
  groth16:
    curve: "bn128"
    circuit_optimization: "auto"
    proving_key_cache: true
  
  bulletproofs:
    curve: "ristretto255"
    range_proof_bits: 64
    aggregation_mode: "batch"
  
  nova:
    primary_curve: "pallas"
    secondary_curve: "vesta"
    folding_scheme: "standard"
    ivc_depth: 10

benchmarking:
  collect_realtime: true
  collect_historical: true
  metrics:
    - proof_generation_time
    - proof_size
    - verification_time
    - constraint_count
    - aggregation_time
    - communication_overhead
    - memory_usage
    - accuracy_improvement
  
  comparison_metrics:
    - speed_ranking
    - size_ranking
    - security_ranking
    - efficiency_ranking
  
  export:
    format: ["json", "csv", "markdown"]
    visualization: true
    statistical_analysis: true
```

### 7.2 Configuration Loader

```python
class ExperimentConfig:
    """Load and validate experiment configuration"""
    
    @staticmethod
    def load_from_yaml(config_file: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate configuration
        ExperimentConfig._validate(config)
        
        return config
    
    @staticmethod
    def _validate(config: Dict):
        """Validate configuration completeness"""
        required_sections = [
            'experiment', 'federated_learning',
            'client_training', 'model', 'zkp_protocol'
        ]
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate protocol-specific settings
        protocol = config['experiment']['protocol']
        if protocol not in config['zkp_protocol']:
            raise ValueError(f"Missing settings for protocol: {protocol}")
```

---

## 8. Benchmarking Framework

### 8.1 Metrics Collection

```python
class ProtocolBenchmark:
    """Collect and analyze protocol metrics"""
    
    def __init__(self, experiment_config: Dict):
        self.config = experiment_config
        self.metrics = {
            'realtime': [],
            'historical': []
        }
    
    def record_round_metrics(self, round_number: int, round_results: Dict):
        """Record metrics from a single round"""
        verification_results = round_results['verification_results']
        
        round_metrics = {
            'round_number': round_number,
            'timestamp': time.time(),
            
            # Proof generation metrics (average across clients)
            'avg_proof_generation_time': np.mean([
                # Extract from client updates
            ]),
            'avg_proof_size_bytes': np.mean([
                v.is_valid for v in verification_results
            ]),
            'avg_constraint_count': np.mean([
                # Extract from proof metadata
            ]),
            
            # Verification metrics
            'total_verification_time': round_results['protocol_metrics']['total_verification_time'],
            'avg_verification_time': round_results['protocol_metrics']['avg_verification_time'],
            'verification_rate': round_results['verification_rate'],
            
            # Aggregation metrics (if applicable)
            'aggregation_enabled': round_results['aggregated_proof'] is not None,
            'aggregation_time': 0,  # Extract from aggregated proof
            'aggregated_proof_size': round_results['protocol_metrics']['aggregated_proof_size'],
            
            # FL metrics
            'global_model_accuracy': round_results['global_model_accuracy'],
            'num_verified_clients': round_results['verified_clients'],
            
            # Communication metrics
            'total_communication_bytes': self._calculate_communication(round_results),
            'communication_per_client': self._calculate_per_client_comm(round_results)
        }
        
        self.metrics['realtime'].append(round_metrics)
    
    def generate_comparison_report(self, all_experiment_metrics: List[Dict]) -> Dict:
        """
        Generate comparative analysis across all protocols
        
        Args:
            all_experiment_metrics: Metrics from multiple protocol runs
        
        Returns:
            Comparative analysis report
        """
        comparison = {
            'protocols': [],
            'rankings': {},
            'statistical_tests': {},
            'visualizations': []
        }
        
        # Compare each protocol
        for experiment in all_experiment_metrics:
            protocol_summary = {
                'protocol_name': experiment['protocol'],
                'avg_proof_size_kb': np.mean([
                    m['avg_proof_size_bytes'] / 1024
                    for m in experiment['metrics']['realtime']
                ]),
                'avg_generation_time': np.mean([
                    m['avg_proof_generation_time']
                    for m in experiment['metrics']['realtime']
                ]),
                'avg_verification_time': np.mean([
                    m['avg_verification_time']
                    for m in experiment['metrics']['realtime']
                ]),
                'final_accuracy': experiment['metrics']['realtime'][-1]['global_model_accuracy'],
                'total_communication_mb': sum([
                    m['total_communication_bytes'] / (1024**2)
                    for m in experiment['metrics']['realtime']
                ])
            }
            comparison['protocols'].append(protocol_summary)
        
        # Rank protocols
        comparison['rankings'] = self._rank_protocols(comparison['protocols'])
        
        # Statistical significance testing
        comparison['statistical_tests'] = self._run_statistical_tests(all_experiment_metrics)
        
        return comparison
    
    def _rank_protocols(self, protocols: List[Dict]) -> Dict:
        """Rank protocols across different metrics"""
        rankings = {}
        
        metrics_to_rank = [
            ('avg_proof_size_kb', False),  # Lower is better
            ('avg_generation_time', False),
            ('avg_verification_time', False),
            ('final_accuracy', True),  # Higher is better
            ('total_communication_mb', False)
        ]
        
        for metric, higher_better in metrics_to_rank:
            sorted_protocols = sorted(
                protocols,
                key=lambda p: p[metric],
                reverse=higher_better
            )
            rankings[metric] = [p['protocol_name'] for p in sorted_protocols]
        
        return rankings
```

### 8.2 Visualization

```python
class ProtocolVisualizer:
    """Generate comparative visualizations"""
    
    @staticmethod
    def plot_proof_sizes(comparison_data: Dict):
        """Plot proof size comparison"""
        # Bar chart of average proof sizes
        pass
    
    @staticmethod
    def plot_verification_times(comparison_data: Dict):
        """Plot verification time comparison"""
        # Line chart of verification times across rounds
        pass
    
    @staticmethod
    def plot_accuracy_convergence(comparison_data: Dict):
        """Plot accuracy convergence for all protocols"""
        # Multiple line chart showing accuracy over rounds
        pass
    
    @staticmethod
    def generate_comparative_dashboard(comparison_data: Dict):
        """Generate comprehensive comparison dashboard"""
        # Multi-panel dashboard with all metrics
        pass
```

---

## 9. Implementation Guidelines

### 9.1 For Protocol Implementers

**Your colleagues implementing each protocol should:**

1. **Study the protocol documentation** in `Final_Guide/[PROTOCOL]_IMPLEMENTATION.md`
2. **Inherit from `IZKPProtocol`** interface
3. **Implement all required methods** following the signatures
4. **Return standardized structures** (`ProofObject`, `VerificationResult`)
5. **Add protocol to factory** in `ZKPProtocolFactory`
6. **Write unit tests** for interface compliance
7. **Document protocol-specific configuration** in YAML schema
8. **Test with dummy FL round** before full integration

### 9.2 Testing Protocol Integration

```python
def test_protocol_integration(protocol: IZKPProtocol):
    """Test that protocol properly implements interface"""
    
    # Test setup
    setup_result = protocol.setup()
    assert 'verification_key' in setup_result
    
    # Test proof generation
    dummy_statement = create_dummy_statement()
    dummy_witness = create_dummy_witness()
    
    proof = protocol.generate_proof(
        statement=dummy_statement,
        witness=dummy_witness,
        round_number=1,
        client_id="test_client"
    )
    
    assert isinstance(proof, ProofObject)
    assert proof.metadata.protocol_name == protocol.get_protocol_info()['protocol_name']
    
    # Test verification
    result = protocol.verify_proof(proof, dummy_statement)
    assert isinstance(result, VerificationResult)
    assert result.is_valid == True
    
    # Test serialization
    serialized = protocol.serialize_proof(proof)
    deserialized = protocol.deserialize_proof(serialized)
    assert deserialized.metadata.proof_size_bytes == proof.metadata.proof_size_bytes
    
    print(f"✅ {protocol.get_protocol_info()['protocol_name']} integration test passed!")
```

### 9.3 Development Workflow

```
1. Choose protocol to implement
   ↓
2. Read ARCHITECTURE.md (this file)
   ↓
3. Read [PROTOCOL]_IMPLEMENTATION.md
   ↓
4. Create protocol wrapper class
   ↓
5. Implement IZKPProtocol methods
   ↓
6. Run integration tests
   ↓
7. Add to protocol factory
   ↓
8. Test with single FL round
   ↓
9. Run full experiment
   ↓
10. Contribute metrics to comparison
```

### 9.4 Directory Structure

```
Fizk/
├── Final_Guide/
│   ├── ARCHITECTURE.md (this file)
│   ├── PROTOSTAR_IMPLEMENTATION.md
│   ├── PLONK_IMPLEMENTATION.md
│   ├── GROTH16_IMPLEMENTATION.md
│   ├── BULLETPROOFS_IMPLEMENTATION.md
│   └── NOVA_IMPLEMENTATION.md
├── zkp_protocols/
│   ├── __init__.py
│   ├── base.py (IZKPProtocol interface)
│   ├── protostar_protocol.py
│   ├── plonk_protocol.py
│   ├── groth16_protocol.py
│   ├── bulletproofs_protocol.py
│   └── nova_protocol.py
├── fl_system/
│   ├── __init__.py
│   ├── orchestrator.py (FederatedLearningOrchestrator)
│   ├── client.py (FLClient)
│   └── aggregation.py
├── benchmarking/
│   ├── __init__.py
│   ├── metrics.py (ProtocolBenchmark)
│   └── visualization.py (ProtocolVisualizer)
├── configs/
│   ├── protostar_experiment.yaml
│   ├── plonk_experiment.yaml
│   ├── groth16_experiment.yaml
│   ├── bulletproofs_experiment.yaml
│   └── nova_experiment.yaml
├── real_dataset_loader.py
├── real_ml_trainer.py
└── main_experiment.py
```

---

## 10. Summary

### Key Principles

1. **Protocol Agnostic FL**: FL system uses abstract `IZKPProtocol` interface
2. **Standardized Formats**: All proofs use `ProofObject` with metadata
3. **Plug-and-Play**: Change protocols via configuration file
4. **Fair Comparison**: Unified benchmarking framework
5. **Research Ready**: Real cryptography, not simulations

### Next Steps

1. ✅ Read this architecture document
2. 📖 Read protocol-specific implementation guide
3. 💻 Implement your protocol wrapper
4. 🧪 Test with integration tests
5. 🚀 Run full experiment
6. 📊 Contribute to comparative analysis

---

**For questions or clarifications, refer to protocol-specific guides in `Final_Guide/`.**

**End of Architecture Document**
