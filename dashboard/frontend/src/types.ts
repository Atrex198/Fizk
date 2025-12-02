// Types for the ZKP-FL Dashboard

export interface RunConfig {
  num_clients?: number;
  num_rounds?: number;
  local_epochs?: number;
  batch_size?: number;
  learning_rate?: number;
  security_level?: number;
  // Nested configuration from backend
  configuration?: {
    num_clients?: number;
    num_rounds?: number;
    local_epochs?: number;
    batch_size?: number;
    learning_rate?: number;
    zkp_security_level?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface Run {
  run_id: string;
  timestamp?: string;
  config: RunConfig;
  status: 'completed' | 'running' | 'failed' | 'incomplete';
  metrics?: RunMetrics;
  path?: string;
  duration?: number;
}

export interface RunMetrics {
  final_global_accuracy?: number;
  final_global_loss?: number;
  total_time?: number;
  total_proofs?: number;
  proofs_verified?: number;
  rounds?: RoundData[];
}

export interface RoundData {
  round_number: number;
  client_results: ClientResult[];
  aggregation?: {
    method: string;
    participants: number;
  };
}

export interface ClientResult {
  client_id: string;
  training_metrics?: {
    accuracy: number;
    loss: number;
    samples: number;
  };
  proof_verified?: boolean;
  proof_metadata?: {
    proof_generation_time: number;
    constraints: number;
    witness_size: number;
  };
}

export interface ProofDetails {
  client: string;
  file: string;
  constraints: {
    num_constraints: number;
    num_variables: number;
    num_witness: number;
  };
  crypto_properties: {
    curve: string;
    security_level: number;
    protocol: string;
  };
}

export interface RunDetails extends Run {
  proofs: ProofDetails[];
  models: string[];
  rounds: RoundInfo[];
}

export interface RoundInfo {
  round_number: number;
  clients: {
    client_id: string;
    accuracy: number;
    loss: number;
    proof_verified: boolean;
    proof_time?: number;
  }[];
  aggregation?: {
    method: string;
    participants: number;
  };
}

export interface RunComparison {
  runs: [string, string];
  configs: [RunConfig, RunConfig];
  metrics_comparison: {
    final_accuracy: Record<string, number>;
    final_loss: Record<string, number>;
    total_time: Record<string, number>;
  };
  rounds_comparison: {
    round: number;
    [key: string]: {
      accuracy: number;
      loss: number;
    } | number;
  }[];
}

// WebSocket message types
export type WSMessageType = 
  | 'connection_established'
  | 'run_started'
  | 'run_completed'
  | 'run_stopped'
  | 'run_error'
  | 'log'
  | 'pong';

export interface WSMessage {
  type: WSMessageType;
  [key: string]: unknown;
}

export interface LogMessage extends WSMessage {
  type: 'log';
  message: string;
  phase: string;
  event: CryptoEvent;
}

export interface CryptoEvent {
  type: string;
  raw?: string;
  [key: string]: unknown;
}

export interface SRSProgressEvent extends CryptoEvent {
  type: 'srs_progress';
  group: 'G1' | 'G2';
  current: number;
  total: number;
  percentage: number;
}

export interface ConstraintsEvent extends CryptoEvent {
  type: 'constraints_verified' | 'constraint_failed';
  count?: number;
  status?: string;
  message?: string;
}

export interface ProofEvent extends CryptoEvent {
  type: 'proof_generating' | 'proof_generated' | 'proof_verified';
}

export interface PairingEvent extends CryptoEvent {
  type: 'pairing_check';
  status: 'passed' | 'failed' | 'in_progress';
}

export interface MetricsEvent extends CryptoEvent {
  type: 'metrics_update';
  accuracy?: number;
  loss?: number;
}

// Dashboard state
export interface DashboardStatus {
  is_running: boolean;
  current_run: {
    run_id: string;
    config: RunConfig;
    status: string;
    start_time: number;
  } | null;
  connected_clients: number;
}
