import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Shield, 
  Zap, 
  Check, 
  X, 
  Clock,
  Server,
  GitMerge,
  Lock,
  Unlock
} from 'lucide-react';
import clsx from 'clsx';
import { LogMessage, CryptoEvent, DashboardStatus } from '../types';

// Crypto visualization components
import EllipticCurveViz from './visualizations/EllipticCurveViz';
import ConstraintFlowViz from './visualizations/ConstraintFlowViz';
import FoldingViz from './visualizations/FoldingViz';

interface LiveViewProps {
  messages: LogMessage[];
  events: CryptoEvent[];
  isRunning: boolean;
  currentRun: DashboardStatus['current_run'];
}

export default function LiveView({ messages, events, isRunning, currentRun }: LiveViewProps) {
  const logContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [activePhase, setActivePhase] = useState<string>('setup');

  // Auto-scroll logs
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [messages, autoScroll]);

  // Update active phase from events
  useEffect(() => {
    const lastPhaseMessage = [...messages].reverse().find(m => m.phase);
    if (lastPhaseMessage) {
      setActivePhase(lastPhaseMessage.phase);
    }
  }, [messages]);

  // Extract current metrics from events
  const srsProgress = events.filter(e => e.type === 'srs_progress').slice(-1)[0] as { group?: string; percentage?: number } | undefined;
  const constraintEvents = events.filter(e => e.type === 'constraints_verified');
  const proofEvents = events.filter(e => e.type.includes('proof'));
  const pairingEvents = events.filter(e => e.type === 'pairing_check');

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-zkp-dark-border flex items-center justify-between bg-zkp-dark-card">
        <div className="flex items-center gap-4">
          <div className={clsx(
            "w-3 h-3 rounded-full",
            isRunning ? "bg-zkp-success live-indicator" : "bg-gray-500"
          )} />
          <div>
            <h1 className="text-xl font-bold text-white">Live Process Visualization</h1>
            <p className="text-sm text-gray-400">
              {isRunning 
                ? `Running: ${currentRun?.run_id}` 
                : 'No active run - Start a run to see live visualization'}
            </p>
          </div>
        </div>

        {/* Phase Indicator */}
        <div className="flex items-center gap-2">
          <PhaseIndicator label="Setup" active={activePhase === 'setup'} completed={activePhase !== 'setup'} />
          <div className="w-8 h-0.5 bg-zkp-dark-border" />
          <PhaseIndicator label="Training" active={activePhase === 'training'} completed={['verification', 'aggregation'].includes(activePhase)} />
          <div className="w-8 h-0.5 bg-zkp-dark-border" />
          <PhaseIndicator label="Verification" active={activePhase === 'verification'} completed={activePhase === 'aggregation'} />
          <div className="w-8 h-0.5 bg-zkp-dark-border" />
          <PhaseIndicator label="Aggregation" active={activePhase === 'aggregation'} completed={false} />
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Crypto Visualizations */}
        <div className="w-1/2 p-4 space-y-4 overflow-y-auto">
          {/* Elliptic Curve Operations */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-zkp-accent" />
              <h3 className="font-semibold text-white">Elliptic Curve Operations (BN254)</h3>
            </div>
            <EllipticCurveViz 
              active={isRunning} 
              srsProgress={srsProgress ? { 
                group: (srsProgress.group as 'G1' | 'G2') || 'G1', 
                percentage: srsProgress.percentage || 0 
              } : undefined}
            />
          </div>

          {/* R1CS Constraints Flow */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
            <div className="flex items-center gap-2 mb-4">
              <GitMerge className="w-5 h-5 text-zkp-primary" />
              <h3 className="font-semibold text-white">R1CS Constraint System</h3>
            </div>
            <ConstraintFlowViz 
              active={isRunning}
              constraintEvents={constraintEvents}
            />
          </div>

          {/* Folding Animation */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-zkp-secondary" />
              <h3 className="font-semibold text-white">ProtoStar Folding</h3>
            </div>
            <FoldingViz 
              active={isRunning}
              proofEvents={proofEvents}
            />
          </div>
        </div>

        {/* Right: Logs and Stats */}
        <div className="w-1/2 flex flex-col border-l border-zkp-dark-border">
          {/* Quick Stats */}
          <div className="p-4 border-b border-zkp-dark-border grid grid-cols-4 gap-4">
            <QuickStat 
              icon={<Shield className="w-4 h-4" />}
              label="Proofs"
              value={proofEvents.filter(e => e.type === 'proof_verified').length}
              color="success"
            />
            <QuickStat 
              icon={<Activity className="w-4 h-4" />}
              label="Constraints"
              value={
                constraintEvents.length > 0 
                  ? (constraintEvents[constraintEvents.length - 1] as { count?: number }).count || 0
                  : 0
              }
              color="primary"
            />
            <QuickStat 
              icon={<Check className="w-4 h-4" />}
              label="Pairings"
              value={pairingEvents.filter(e => (e as { status?: string }).status === 'passed').length}
              color="accent"
            />
            <QuickStat 
              icon={<Clock className="w-4 h-4" />}
              label="Events"
              value={events.length}
              color="secondary"
            />
          </div>

          {/* Log Stream */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="px-4 py-2 border-b border-zkp-dark-border flex items-center justify-between">
              <span className="text-sm font-medium text-gray-400">Log Stream</span>
              <label className="flex items-center gap-2 text-sm text-gray-400">
                <input 
                  type="checkbox" 
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="rounded border-zkp-dark-border bg-zkp-dark-bg"
                />
                Auto-scroll
              </label>
            </div>
            <div 
              ref={logContainerRef}
              className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1 bg-zkp-dark-bg"
            >
              <AnimatePresence>
                {messages.map((msg, idx) => (
                  <LogLine key={idx} message={msg} />
                ))}
              </AnimatePresence>
              {messages.length === 0 && (
                <div className="text-gray-500 italic">
                  {isRunning ? 'Waiting for output...' : 'Start a run to see logs'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface PhaseIndicatorProps {
  label: string;
  active: boolean;
  completed: boolean;
}

function PhaseIndicator({ label, active, completed }: PhaseIndicatorProps) {
  return (
    <div className={clsx(
      "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm",
      active && "bg-zkp-primary/20 text-zkp-primary",
      completed && "bg-zkp-success/20 text-zkp-success",
      !active && !completed && "bg-zkp-dark-border text-gray-400"
    )}>
      {completed ? (
        <Check className="w-4 h-4" />
      ) : active ? (
        <div className="w-2 h-2 rounded-full bg-current live-indicator" />
      ) : (
        <div className="w-2 h-2 rounded-full bg-current opacity-50" />
      )}
      {label}
    </div>
  );
}

interface QuickStatProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'primary' | 'secondary' | 'accent' | 'success';
}

function QuickStat({ icon, label, value, color }: QuickStatProps) {
  const colorClasses = {
    primary: 'text-zkp-primary',
    secondary: 'text-zkp-secondary',
    accent: 'text-zkp-accent',
    success: 'text-zkp-success'
  };

  return (
    <div className="text-center">
      <div className={clsx("flex justify-center mb-1", colorClasses[color])}>
        {icon}
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
      <p className="text-xs text-gray-400">{label}</p>
    </div>
  );
}

interface LogLineProps {
  message: LogMessage;
}

function LogLine({ message }: LogLineProps) {
  const getLogColor = () => {
    if (message.message.toLowerCase().includes('error')) return 'text-zkp-error';
    if (message.message.toLowerCase().includes('warning')) return 'text-zkp-warning';
    if (message.message.includes('✓') || message.message.includes('✅')) return 'text-zkp-success';
    if (message.message.includes('❌')) return 'text-zkp-error';
    if (message.event?.type === 'proof_verified') return 'text-zkp-success';
    if (message.event?.type === 'pairing_check' && (message.event as { status?: string }).status === 'passed') return 'text-zkp-success';
    return 'text-gray-300';
  };

  const getEventIcon = () => {
    switch (message.event?.type) {
      case 'proof_generating':
        return <Lock className="w-3 h-3 text-zkp-warning" />;
      case 'proof_verified':
        return <Unlock className="w-3 h-3 text-zkp-success" />;
      case 'pairing_check':
        return (message.event as { status?: string }).status === 'passed' 
          ? <Check className="w-3 h-3 text-zkp-success" />
          : <X className="w-3 h-3 text-zkp-error" />;
      case 'srs_progress':
        return <Zap className="w-3 h-3 text-zkp-accent" />;
      case 'constraints_verified':
        return <GitMerge className="w-3 h-3 text-zkp-primary" />;
      default:
        return <Server className="w-3 h-3 text-gray-500" />;
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={clsx("flex items-start gap-2 py-0.5", getLogColor())}
    >
      <span className="flex-shrink-0 mt-0.5">{getEventIcon()}</span>
      <span className="break-all">{message.message}</span>
    </motion.div>
  );
}
