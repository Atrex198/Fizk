import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Play, 
  Square, 
  Settings2, 
  Users, 
  RotateCcw, 
  Gauge,
  Boxes,
  GraduationCap,
  Shield,
  Loader2,
  AlertCircle
} from 'lucide-react';
import clsx from 'clsx';
import { RunConfig, DashboardStatus } from '../types';

interface RunControlProps {
  isRunning: boolean;
  currentRun: DashboardStatus['current_run'];
  onStart: (config: RunConfig) => Promise<void>;
  onStop: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

export default function RunControl({ 
  isRunning, 
  currentRun, 
  onStart, 
  onStop, 
  loading,
  error
}: RunControlProps) {
  const [config, setConfig] = useState<RunConfig>({
    num_clients: 3,
    num_rounds: 3,
    local_epochs: 2,  // Lower to prevent client drift
    batch_size: 64,
    learning_rate: 0.001,  // Lower to prevent overshooting
    security_level: 128
  });

  const handleStart = async () => {
    await onStart(config);
  };

  const handleStop = async () => {
    await onStop();
  };

  const updateConfig = <K extends keyof RunConfig>(key: K, value: RunConfig[K]) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  // Calculate estimated time
  const estimatedTime = ((config.num_clients || 3) * (config.num_rounds || 3) * (config.local_epochs || 2) * 2) + 60; // rough estimate

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Run Control</h1>
        <p className="text-gray-400">Configure and launch ZKP-FL training runs</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Federated Learning Settings */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-6">
            <div className="flex items-center gap-2 mb-6">
              <Settings2 className="w-5 h-5 text-zkp-primary" />
              <h2 className="text-lg font-semibold text-white">Federated Learning Configuration</h2>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <ConfigSlider
                icon={<Users className="w-4 h-4" />}
                label="Number of Clients"
                value={config.num_clients || 3}
                min={2}
                max={10}
                step={1}
                onChange={(v) => updateConfig('num_clients', v)}
                description="Federated learning participants"
              />

              <ConfigSlider
                icon={<RotateCcw className="w-4 h-4" />}
                label="Training Rounds"
                value={config.num_rounds || 3}
                min={1}
                max={10}
                step={1}
                onChange={(v) => updateConfig('num_rounds', v)}
                description="Global aggregation cycles"
              />

              <ConfigSlider
                icon={<GraduationCap className="w-4 h-4" />}
                label="Local Epochs"
                value={config.local_epochs || 5}
                min={1}
                max={20}
                step={1}
                onChange={(v) => updateConfig('local_epochs', v)}
                description="Epochs per client per round"
              />

              <ConfigSlider
                icon={<Boxes className="w-4 h-4" />}
                label="Batch Size"
                value={config.batch_size || 64}
                min={16}
                max={256}
                step={16}
                onChange={(v) => updateConfig('batch_size', v)}
                description="Training batch size"
              />

              <ConfigSlider
                icon={<Gauge className="w-4 h-4" />}
                label="Learning Rate"
                value={config.learning_rate || 0.01}
                min={0.001}
                max={0.1}
                step={0.001}
                onChange={(v) => updateConfig('learning_rate', Math.round(v * 1000) / 1000)}
                format={(v) => v.toFixed(3)}
                description="Gradient descent step size"
              />

              <ConfigSlider
                icon={<Shield className="w-4 h-4" />}
                label="Security Level"
                value={config.security_level || 128}
                min={80}
                max={256}
                step={8}
                onChange={(v) => updateConfig('security_level', v)}
                format={(v) => `${v}-bit`}
                description="ZKP security parameter"
              />
            </div>
          </div>

          {/* Presets */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-6">
            <h3 className="font-semibold text-white mb-4">Quick Presets</h3>
            <div className="flex gap-3">
              <PresetButton
                label="Quick Test"
                description="2 clients, 1 round"
                onClick={() => setConfig({
                  num_clients: 2,
                  num_rounds: 1,
                  local_epochs: 1,
                  batch_size: 64,
                  learning_rate: 0.001,
                  security_level: 128
                })}
              />
              <PresetButton
                label="Standard"
                description="3 clients, 3 rounds"
                onClick={() => setConfig({
                  num_clients: 3,
                  num_rounds: 3,
                  local_epochs: 2,
                  batch_size: 64,
                  learning_rate: 0.001,
                  security_level: 128
                })}
                active
              />
              <PresetButton
                label="Full Scale"
                description="5 clients, 5 rounds"
                onClick={() => setConfig({
                  num_clients: 5,
                  num_rounds: 5,
                  local_epochs: 3,
                  batch_size: 32,
                  learning_rate: 0.0005,
                  security_level: 128
                })}
              />
              <PresetButton
                label="High Security"
                description="256-bit security"
                onClick={() => setConfig({
                  num_clients: 3,
                  num_rounds: 3,
                  local_epochs: 2,
                  batch_size: 64,
                  learning_rate: 0.001,
                  security_level: 256
                })}
              />
            </div>
          </div>
        </div>

        {/* Control Panel */}
        <div className="space-y-6">
          {/* Run Button */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-6">
            <h3 className="font-semibold text-white mb-4">Control</h3>
            
            {isRunning ? (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStop}
                disabled={loading}
                className="w-full py-4 rounded-xl bg-zkp-error/20 hover:bg-zkp-error/30 border border-zkp-error text-zkp-error font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Square className="w-5 h-5" />
                )}
                Stop Run
              </motion.button>
            ) : (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStart}
                disabled={loading}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-zkp-primary to-zkp-secondary text-white font-semibold flex items-center justify-center gap-2 glow-primary transition-all disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Play className="w-5 h-5" />
                )}
                Start Run
              </motion.button>
            )}

            {error && (
              <div className="mt-4 p-3 rounded-lg bg-zkp-error/10 border border-zkp-error/30 flex items-center gap-2 text-zkp-error text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}
          </div>

          {/* Status */}
          {isRunning && currentRun && (
            <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-6">
              <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-zkp-success live-indicator" />
                Running
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Run ID</span>
                  <span className="text-white font-mono text-xs">{currentRun.run_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Elapsed</span>
                  <span className="text-white">
                    <ElapsedTime startTime={currentRun.start_time} />
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Estimate */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-6">
            <h3 className="font-semibold text-white mb-4">Estimates</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Total Proofs</span>
                <span className="text-white font-mono">{(config.num_clients || 3) * (config.num_rounds || 3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Est. Time</span>
                <span className="text-white font-mono">~{Math.round(estimatedTime / 60)} min</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Constraints/Proof</span>
                <span className="text-white font-mono">~11,000</span>
              </div>
            </div>
          </div>

          {/* Current Config Summary */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-6">
            <h3 className="font-semibold text-white mb-4">Configuration Summary</h3>
            <div className="text-xs font-mono bg-zkp-dark-bg rounded-lg p-3 text-gray-300 whitespace-pre">
{JSON.stringify(config, null, 2)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface ConfigSliderProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  description?: string;
  format?: (value: number) => string;
}

function ConfigSlider({ icon, label, value, min, max, step, onChange, description, format }: ConfigSliderProps) {
  const displayValue = format ? format(value) : value;
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-gray-400">
          {icon}
          <span className="text-sm">{label}</span>
        </div>
        <span className="text-white font-semibold">{displayValue}</span>
      </div>
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="w-full h-2 bg-zkp-dark-bg rounded-lg appearance-none cursor-pointer slider-thumb"
          style={{
            background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${percentage}%, #1e293b ${percentage}%, #1e293b 100%)`
          }}
        />
      </div>
      {description && (
        <p className="text-xs text-gray-500">{description}</p>
      )}
    </div>
  );
}

interface PresetButtonProps {
  label: string;
  description: string;
  onClick: () => void;
  active?: boolean;
}

function PresetButton({ label, description, onClick, active }: PresetButtonProps) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "flex-1 p-3 rounded-lg border text-left transition-all",
        active 
          ? "bg-zkp-primary/20 border-zkp-primary" 
          : "bg-zkp-dark-bg border-zkp-dark-border hover:border-zkp-primary/50"
      )}
    >
      <p className="text-sm font-medium text-white">{label}</p>
      <p className="text-xs text-gray-400">{description}</p>
    </button>
  );
}

interface ElapsedTimeProps {
  startTime: number;
}

function ElapsedTime({ startTime }: ElapsedTimeProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Math.floor(Date.now() / 1000 - startTime));
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  return <span>{minutes}:{seconds.toString().padStart(2, '0')}</span>;
}
