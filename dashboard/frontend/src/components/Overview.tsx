import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, 
  Shield, 
  Clock, 
  Users, 
  CheckCircle, 
  XCircle,
  ChevronRight,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { Run } from '../types';

export default function Overview() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    
    const loadRuns = async () => {
      try {
        console.log('Overview: Fetching runs...');
        const response = await fetch('/api/runs');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        console.log('Overview: Got runs:', data);
        if (isMounted) {
          setRuns(Array.isArray(data) ? data : []);
          setError(null);
        }
      } catch (err) {
        console.error('Overview: Fetch error:', err);
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to fetch');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadRuns();
    return () => { isMounted = false; };
  }, []);

  // Calculate stats
  const completedRuns = runs.filter(r => r.status === 'completed');
  const totalProofs = completedRuns.reduce((sum, r) => sum + (r.metrics?.total_proofs || 0), 0);
  const avgAccuracy = completedRuns.length > 0
    ? completedRuns.reduce((sum, r) => sum + (r.metrics?.final_global_accuracy || 0), 0) / completedRuns.length
    : 0;
  const avgTime = completedRuns.length > 0
    ? completedRuns.reduce((sum, r) => sum + (r.metrics?.total_time || 0), 0) / completedRuns.length
    : 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-zkp-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="w-12 h-12 text-zkp-error" />
        <p className="text-zkp-error">Error: {error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-zkp-primary rounded-lg text-white"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard Overview</h1>
        <p className="text-gray-400">Zero-Knowledge Proof Federated Learning System</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Shield className="w-6 h-6" />}
          label="Total Proofs"
          value={totalProofs.toString()}
          color="primary"
        />
        <StatCard
          icon={<TrendingUp className="w-6 h-6" />}
          label="Avg Accuracy"
          value={`${(avgAccuracy * 100).toFixed(1)}%`}
          color="success"
        />
        <StatCard
          icon={<Clock className="w-6 h-6" />}
          label="Avg Run Time"
          value={formatDuration(avgTime)}
          color="accent"
        />
        <StatCard
          icon={<Users className="w-6 h-6" />}
          label="Completed Runs"
          value={completedRuns.length.toString()}
          color="secondary"
        />
      </div>

      {/* Recent Runs */}
      <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border">
        <div className="p-4 border-b border-zkp-dark-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Recent Runs</h2>
          <button 
            onClick={() => navigate('/control')}
            className="text-sm text-zkp-primary hover:text-zkp-primary/80 transition-colors"
          >
            Start New Run →
          </button>
        </div>
        
        <div className="divide-y divide-zkp-dark-border">
          {runs.slice(0, 10).map((run) => (
            <RunRow key={run.run_id} run={run} onClick={() => navigate(`/runs/${run.run_id}`)} />
          ))}
          
          {runs.length === 0 && (
            <div className="p-8 text-center text-gray-400">
              <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No runs found. Start a new run to see results here.</p>
            </div>
          )}
        </div>
      </div>

      {/* System Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <InfoCard title="Protocol Information">
          <InfoRow label="Protocol" value="ProtoStar + ProtoGalaxy" />
          <InfoRow label="Curve" value="BN254 (BN128)" />
          <InfoRow label="Security Level" value="128-bit" />
          <InfoRow label="Commitment Scheme" value="KZG Polynomial" />
          <InfoRow label="Constraint System" value="R1CS" />
        </InfoCard>

        <InfoCard title="Verification Properties">
          <div className="space-y-3">
            <PropertyBadge label="Zero Knowledge" active />
            <PropertyBadge label="Soundness" active />
            <PropertyBadge label="Completeness" active />
            <PropertyBadge label="Non-Interactive (Fiat-Shamir)" active />
            <PropertyBadge label="Public Verifiability" active />
          </div>
        </InfoCard>
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error';
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    primary: 'from-zkp-primary/20 to-zkp-primary/5 text-zkp-primary',
    secondary: 'from-zkp-secondary/20 to-zkp-secondary/5 text-zkp-secondary',
    accent: 'from-zkp-accent/20 to-zkp-accent/5 text-zkp-accent',
    success: 'from-zkp-success/20 to-zkp-success/5 text-zkp-success',
    warning: 'from-zkp-warning/20 to-zkp-warning/5 text-zkp-warning',
    error: 'from-zkp-error/20 to-zkp-error/5 text-zkp-error',
  };

  return (
    <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4 card-hover">
      <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-gray-400">{label}</p>
    </div>
  );
}

interface RunRowProps {
  run: Run;
  onClick: () => void;
}

function RunRow({ run, onClick }: RunRowProps) {
  // Handle nested config structure from backend
  const numClients = run.config?.configuration?.num_clients ?? run.config?.num_clients ?? 0;
  const numRounds = run.config?.configuration?.num_rounds ?? run.config?.num_rounds ?? 0;
  
  return (
    <div 
      onClick={onClick}
      className="flex items-center gap-4 p-4 hover:bg-zkp-dark-border/30 cursor-pointer transition-colors"
    >
      <div className="flex-shrink-0">
        {run.status === 'completed' ? (
          <CheckCircle className="w-5 h-5 text-zkp-success" />
        ) : run.status === 'failed' ? (
          <XCircle className="w-5 h-5 text-zkp-error" />
        ) : (
          <Loader2 className="w-5 h-5 text-zkp-warning animate-spin" />
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="font-medium text-white truncate">{run.run_id}</p>
        <p className="text-sm text-gray-400">
          {numClients} clients • {numRounds} rounds
        </p>
      </div>

      <div className="hidden md:block text-right">
        <p className="text-sm text-white">
          {run.metrics?.final_global_accuracy 
            ? `${(run.metrics.final_global_accuracy * 100).toFixed(1)}% accuracy`
            : 'No metrics'
          }
        </p>
        <p className="text-xs text-gray-400">
          {run.timestamp ? formatTimestamp(run.timestamp) : '—'}
        </p>
      </div>

      <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
    </div>
  );
}

interface InfoCardProps {
  title: string;
  children: React.ReactNode;
}

function InfoCard({ title, children }: InfoCardProps) {
  return (
    <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
      <h3 className="font-semibold text-white mb-4">{title}</h3>
      {children}
    </div>
  );
}

interface InfoRowProps {
  label: string;
  value: string;
}

function InfoRow({ label, value }: InfoRowProps) {
  return (
    <div className="flex justify-between py-2 border-b border-zkp-dark-border last:border-0">
      <span className="text-gray-400">{label}</span>
      <span className="text-white font-mono text-sm">{value}</span>
    </div>
  );
}

interface PropertyBadgeProps {
  label: string;
  active?: boolean;
}

function PropertyBadge({ label, active }: PropertyBadgeProps) {
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm mr-2 ${
      active 
        ? 'bg-zkp-success/20 text-zkp-success' 
        : 'bg-gray-700 text-gray-400'
    }`}>
      {active && <div className="w-1.5 h-1.5 rounded-full bg-current" />}
      {label}
    </div>
  );
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds === 0) return '—';
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

function formatTimestamp(timestamp: string): string {
  try {
    return format(parseISO(timestamp), 'MMM d, HH:mm');
  } catch {
    return timestamp;
  }
}
