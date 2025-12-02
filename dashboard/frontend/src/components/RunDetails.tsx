import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Shield,
  Clock,
  Users,
  CheckCircle,
  XCircle,
  Loader2,
  FileText,
  TrendingUp,
  BarChart3,
  GitCompare
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { useApi } from '../hooks/useApi';
import { RunDetails as RunDetailsType } from '../types';

export default function RunDetails() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<RunDetailsType | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const hasFetched = useRef(false);
  const { fetchRunDetails, fetchRunLogs } = useApi();

  useEffect(() => {
    if (!runId || hasFetched.current) return;
    hasFetched.current = true;
    
    setIsLoading(true);
    setHasError(false);
    
    Promise.all([
      fetchRunDetails(runId),
      fetchRunLogs(runId)
    ]).then(([runData, logsData]) => {
      console.log('RunDetails: Fetched run:', runData);
      if (runData) {
        setRun(runData);
      } else {
        setHasError(true);
      }
      setLogs(logsData);
    }).catch(() => {
      setHasError(true);
    }).finally(() => {
      setIsLoading(false);
    });
  }, [runId]); // Only depend on runId

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-zkp-primary" />
      </div>
    );
  }

  if (hasError || !run) {
    return (
      <div className="p-6">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Overview
        </button>
        <div className="bg-zkp-dark-card rounded-xl border border-zkp-error/50 p-8 text-center">
          <XCircle className="w-12 h-12 mx-auto mb-4 text-zkp-error" />
          <p className="text-gray-400">Run not found or failed to load.</p>
        </div>
      </div>
    );
  }

  const status = run.status || 'incomplete';
  const statusColor: Record<string, string> = {
    completed: 'text-zkp-success',
    failed: 'text-zkp-error',
    running: 'text-zkp-warning',
    pending: 'text-gray-400',
    incomplete: 'text-gray-400',
  };

  const StatusIcons: Record<string, typeof CheckCircle> = {
    completed: CheckCircle,
    failed: XCircle,
    running: Loader2,
    pending: Clock,
    incomplete: Clock,
  };
  
  const StatusIcon = StatusIcons[status] || Clock;

  // Helper to get config values (handle nested structure)
  const getConfigValue = (key: string): string | number | undefined => {
    const config = run.config;
    if (!config) return undefined;
    // Check nested configuration first, then top-level
    const nested = config.configuration as Record<string, unknown> | undefined;
    if (nested && key in nested) return nested[key] as string | number;
    return config[key] as string | number | undefined;
  };

  const numClients = getConfigValue('num_clients');
  const numRounds = getConfigValue('num_rounds');
  const localEpochs = getConfigValue('local_epochs');
  const batchSize = getConfigValue('batch_size');
  const learningRate = getConfigValue('learning_rate');
  const securityLevel = getConfigValue('zkp_security_level') || getConfigValue('security_level');

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-lg bg-zkp-dark-card border border-zkp-dark-border hover:border-zkp-primary/50 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <StatusIcon className={`w-6 h-6 ${statusColor[status] || 'text-gray-400'} ${status === 'running' ? 'animate-spin' : ''}`} />
              {run.run_id}
            </h1>
            <p className="text-gray-400">
              {run.timestamp ? formatTimestamp(run.timestamp) : 'No timestamp'}
            </p>
          </div>
        </div>
        
        <button
          onClick={() => navigate(`/compare?run1=${run.run_id}`)}
          className="flex items-center gap-2 px-4 py-2 bg-zkp-primary/20 text-zkp-primary rounded-lg hover:bg-zkp-primary/30 transition-colors"
        >
          <GitCompare className="w-4 h-4" />
          Compare with other run
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5" />}
          label="Clients"
          value={numClients?.toString() || '—'}
        />
        <StatCard
          icon={<BarChart3 className="w-5 h-5" />}
          label="Rounds"
          value={numRounds?.toString() || '—'}
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Accuracy"
          value={run.metrics?.final_global_accuracy 
            ? `${(run.metrics.final_global_accuracy * 100).toFixed(1)}%`
            : '—'
          }
        />
        <StatCard
          icon={<Clock className="w-5 h-5" />}
          label="Duration"
          value={run.metrics?.total_time 
            ? formatDuration(run.metrics.total_time)
            : '—'
          }
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-zkp-primary" />
            Configuration
          </h2>
          <div className="space-y-2">
            <ConfigRow label="Number of Clients" value={numClients ?? '—'} />
            <ConfigRow label="Number of Rounds" value={numRounds ?? '—'} />
            <ConfigRow label="Local Epochs" value={localEpochs ?? '—'} />
            <ConfigRow label="Batch Size" value={batchSize ?? '—'} />
            <ConfigRow label="Learning Rate" value={learningRate ?? '—'} />
            <ConfigRow label="Security Level" value={securityLevel ? `${securityLevel}-bit` : '—'} />
          </div>
        </div>

        {/* Metrics */}
        <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-zkp-success" />
            Metrics
          </h2>
          {run.metrics ? (
            <div className="space-y-2">
              <ConfigRow 
                label="Final Global Accuracy" 
                value={run.metrics.final_global_accuracy != null 
                  ? `${(run.metrics.final_global_accuracy * 100).toFixed(2)}%` 
                  : '—'} 
              />
              <ConfigRow 
                label="Final Global Loss" 
                value={run.metrics.final_global_loss != null 
                  ? run.metrics.final_global_loss.toFixed(4) 
                  : '—'} 
              />
              <ConfigRow 
                label="Total Proofs Generated" 
                value={run.metrics.total_proofs ?? '—'} 
              />
              <ConfigRow 
                label="Proofs Verified" 
                value={run.metrics.proofs_verified ?? '—'} 
              />
              <ConfigRow 
                label="Total Time" 
                value={run.metrics.total_time != null 
                  ? formatDuration(run.metrics.total_time) 
                  : '—'} 
              />
            </div>
          ) : (
            <p className="text-gray-400">No metrics available yet.</p>
          )}
        </div>
      </div>

      {/* Proof Information */}
      <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-zkp-secondary" />
          ZKP Protocol Details
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-zkp-dark/50 rounded-lg border border-zkp-dark-border">
            <p className="text-sm text-gray-400 mb-1">Protocol</p>
            <p className="text-white font-mono">ProtoStar + ProtoGalaxy</p>
          </div>
          <div className="p-4 bg-zkp-dark/50 rounded-lg border border-zkp-dark-border">
            <p className="text-sm text-gray-400 mb-1">Curve</p>
            <p className="text-white font-mono">BN254 (BN128)</p>
          </div>
          <div className="p-4 bg-zkp-dark/50 rounded-lg border border-zkp-dark-border">
            <p className="text-sm text-gray-400 mb-1">Commitment</p>
            <p className="text-white font-mono">KZG Polynomial</p>
          </div>
        </div>
        
        {/* Proof Files */}
        {run.proofs && run.proofs.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Generated Proofs</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {run.proofs.map((proof, idx) => (
                <div key={idx} className="p-3 bg-zkp-dark/30 rounded-lg border border-zkp-dark-border text-sm">
                  <p className="text-white font-mono">{proof.client} / {proof.file}</p>
                  {proof.constraints && (
                    <p className="text-gray-400 text-xs mt-1">
                      {proof.constraints.num_constraints} constraints
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Logs */}
      <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
        <h2 className="text-lg font-semibold text-white mb-4">Execution Logs</h2>
        <div className="bg-black/50 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <div key={index} className={`py-0.5 ${getLogColor(log)}`}>
                {log}
              </div>
            ))
          ) : (
            <p className="text-gray-500">No logs available.</p>
          )}
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
}

function StatCard({ icon, label, value }: StatCardProps) {
  return (
    <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="text-zkp-primary">{icon}</div>
        <span className="text-sm text-gray-400">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

interface ConfigRowProps {
  label: string;
  value: string | number;
}

function ConfigRow({ label, value }: ConfigRowProps) {
  return (
    <div className="flex justify-between py-2 border-b border-zkp-dark-border last:border-0">
      <span className="text-gray-400">{label}</span>
      <span className="text-white font-mono text-sm">{value}</span>
    </div>
  );
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds === 0) return '—';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

function formatTimestamp(timestamp: string): string {
  try {
    return format(parseISO(timestamp), 'MMMM d, yyyy HH:mm:ss');
  } catch {
    return timestamp;
  }
}

function getLogColor(log: string): string {
  if (log.includes('ERROR') || log.includes('error') || log.includes('Failed')) {
    return 'text-zkp-error';
  }
  if (log.includes('WARNING') || log.includes('warning')) {
    return 'text-zkp-warning';
  }
  if (log.includes('SUCCESS') || log.includes('success') || log.includes('Verified') || log.includes('✓')) {
    return 'text-zkp-success';
  }
  if (log.includes('PROOF') || log.includes('proof') || log.includes('ZKP')) {
    return 'text-zkp-secondary';
  }
  return 'text-gray-300';
}
