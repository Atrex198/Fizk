# ZKP-FL Dashboard

A sleek, modern dashboard for visualizing Federated Learning with Zero-Knowledge Proofs metrics.

## Features

- 📊 **Real-time Metrics Visualization** - View accuracy, loss, proof times, and verification rates
- 📈 **Historical Comparison** - Compare current run against all previous runs
- 🔐 **ZKP Details** - See security parameters, SRS size, curve info, and proof statistics
- 🎯 **Current Run Highlighting** - Latest run is visually highlighted in all charts
- 📱 **Responsive Design** - Works on desktop and tablet screens

## Quick Start

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies (Flask is likely already installed)
pip install flask

# Run the dashboard
python app.py
```

Then open http://localhost:5000 in your browser.

## Screenshots

### Main Dashboard
- Hero section showing current run metrics
- Comparative charts for accuracy, loss, proof time, and verification rate
- Round-by-round progress visualization

### ZKP Details
- Security level and curve information
- SRS configuration
- Per-round verification status table

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main dashboard page |
| `GET /api/runs` | List all training runs |
| `GET /api/run/<name>` | Get specific run details |
| `GET /api/compare` | Get comparative metrics across all runs |
| `GET /api/run/<name>/proofs` | Get proof details for a run |

## Metrics Explained

### Federated Learning Metrics
- **Final Accuracy**: Model accuracy after all training rounds
- **Final Loss**: Cross-entropy loss at end of training
- **Accuracy Improvement**: Change from first to last round

### ZKP Metrics
- **Proof Size**: Size of generated ZKP proof in bytes
- **Proof Time**: Time to generate a single proof
- **Verification Rate**: Percentage of proofs that passed verification
- **EC Operations**: Number of elliptic curve operations in aggregation

## Customization

The dashboard reads from `production_zkp_fl_results_real/` directory. Modify `RESULTS_DIR` in `app.py` to change the data source.

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, Chart.js
- **Styling**: Custom CSS with CSS Variables (no framework)
- **Charts**: Chart.js with annotation plugin
