# ZKP-FL Dashboard

A comprehensive visualization dashboard for the Zero-Knowledge Proof Federated Learning system.

## Features

### 🎯 Overview
- System statistics and metrics
- Recent run history
- Protocol information and security properties

### 📊 Live View
- **Elliptic Curve Visualization**: Animated BN254 curve operations showing G1/G2 points
- **R1CS Constraint Flow**: Real-time constraint verification animation
- **ProtoStar Folding**: Visual representation of proof folding/accumulation
- Live log streaming with syntax highlighting
- Phase tracking (Setup → Training → Verification → Aggregation)

### 📈 Run Comparison
- Side-by-side comparison of any two runs
- Accuracy/Loss progression charts
- Configuration diff view
- Performance metrics comparison

### ⚡ Run Control
- One-click run launch
- Configuration presets (Quick Test, Standard, Full Scale, High Security)
- Adjustable parameters:
  - Number of clients (2-10)
  - Training rounds (1-10)
  - Local epochs (1-20)
  - Batch size (16-256)
  - Learning rate (0.001-0.1)
  - Security level (80-256 bit)

## Architecture

```
dashboard/
├── backend/
│   ├── main.py           # FastAPI server with WebSocket support
│   └── requirements.txt   # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Overview.tsx       # Dashboard home
    │   │   ├── LiveView.tsx       # Real-time visualization
    │   │   ├── RunComparison.tsx  # Compare runs
    │   │   ├── RunControl.tsx     # Run configuration
    │   │   └── visualizations/
    │   │       ├── EllipticCurveViz.tsx  # EC animation
    │   │       ├── ConstraintFlowViz.tsx # R1CS flow
    │   │       └── FoldingViz.tsx        # Folding animation
    │   ├── hooks/
    │   │   ├── useApi.ts          # REST API hook
    │   │   └── useWebSocket.ts    # WebSocket hook
    │   ├── types.ts               # TypeScript definitions
    │   ├── App.tsx                # Main app component
    │   └── main.tsx               # Entry point
    └── package.json
```

## Setup

### Backend

```bash
cd dashboard/backend
pip install -r requirements.txt
python main.py
```

The backend will start on `http://localhost:8000`

### Frontend

```bash
cd dashboard/frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:5173`

## Technology Stack

### Backend
- **FastAPI**: High-performance async API framework
- **WebSocket**: Real-time bidirectional communication
- **Pydantic**: Data validation and serialization
- **SQLite**: Lightweight run history storage

### Frontend
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Animations
- **Recharts**: Charts and graphs
- **Vite**: Build tool

## API Endpoints

### REST

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/runs` | List all runs |
| GET | `/api/runs/{id}` | Get run details |
| GET | `/api/runs/{id}/compare/{id2}` | Compare two runs |
| POST | `/api/runs/start` | Start new run |
| POST | `/api/runs/stop` | Stop current run |
| GET | `/api/status` | Get dashboard status |

### WebSocket

Connect to `/ws` for real-time updates:

```typescript
// Message types
type WSMessage = 
  | { type: 'connection_established', is_running: boolean }
  | { type: 'run_started', run_id: string }
  | { type: 'run_completed', duration: number }
  | { type: 'log', message: string, event: CryptoEvent }
```

## Cryptographic Visualizations

### Elliptic Curve (BN254)
The visualization shows:
- Point movement along the curve y² = x³ + 3
- Scalar multiplication animations
- Point addition operations
- SRS generation progress for G1/G2

### R1CS Constraints
Visual representation of:
- Constraint format: A · B = C
- Real-time verification status
- Sparse matrix visualization
- Constraint satisfaction progress

### ProtoStar Folding
Animated display of:
- Instance accumulation
- Folding challenge derivation (β)
- Error polynomial computation
- Decider verification steps

## License

Part of the ZKP-FL project.
