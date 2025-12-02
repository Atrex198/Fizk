import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X } from 'lucide-react';
import clsx from 'clsx';
import { CryptoEvent } from '../../types';

interface ConstraintFlowVizProps {
  active: boolean;
  constraintEvents: CryptoEvent[];
}

interface Constraint {
  id: number;
  a: string;
  b: string;
  c: string;
  status: 'pending' | 'checking' | 'satisfied' | 'failed';
}

export default function ConstraintFlowViz({ active, constraintEvents }: ConstraintFlowVizProps) {
  const [constraints, setConstraints] = useState<Constraint[]>([]);
  const [totalConstraints, setTotalConstraints] = useState(0);
  const [verifiedCount, setVerifiedCount] = useState(0);

  // Generate sample constraints for visualization
  useEffect(() => {
    if (!active) return;

    const sampleConstraints: Constraint[] = [
      { id: 1, a: 'w₁ · w₂', b: '= w₃', c: '(gradient norm)', status: 'pending' },
      { id: 2, a: 'w₄ + w₅', b: '= w₆', c: '(weight update)', status: 'pending' },
      { id: 3, a: 'w₇ · σ(w₈)', b: '= w₉', c: '(activation)', status: 'pending' },
      { id: 4, a: 'Σwᵢ', b: '≤ B', c: '(norm bound)', status: 'pending' },
      { id: 5, a: 'hash(w)', b: '= h', c: '(commitment)', status: 'pending' },
    ];

    setConstraints(sampleConstraints);

    // Animate constraints being checked
    let currentIdx = 0;
    const interval = setInterval(() => {
      if (currentIdx < sampleConstraints.length) {
        setConstraints(prev => 
          prev.map((c, i) => 
            i === currentIdx 
              ? { ...c, status: 'checking' as const }
              : i < currentIdx 
                ? { ...c, status: 'satisfied' as const }
                : c
          )
        );
        currentIdx++;
      } else {
        // All satisfied
        setConstraints(prev => 
          prev.map(c => ({ ...c, status: 'satisfied' as const }))
        );
        currentIdx = 0;
      }
    }, 800);

    return () => clearInterval(interval);
  }, [active]);

  // Update from actual events
  useEffect(() => {
    const lastEvent = constraintEvents[constraintEvents.length - 1] as { count?: number } | undefined;
    if (lastEvent?.count) {
      setTotalConstraints(lastEvent.count);
      setVerifiedCount(lastEvent.count);
    }
  }, [constraintEvents]);

  return (
    <div className="space-y-4">
      {/* R1CS Formula */}
      <div className="bg-zkp-dark-bg rounded-lg p-3 font-mono text-sm">
        <div className="text-gray-400 text-xs mb-2">R1CS Constraint Format</div>
        <div className="text-zkp-primary">
          A · B = C
        </div>
        <div className="text-xs text-gray-500 mt-1">
          (Left) · (Right) = (Output)
        </div>
      </div>

      {/* Constraint List */}
      <div className="space-y-2">
        <AnimatePresence>
          {constraints.map((constraint) => (
            <motion.div
              key={constraint.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className={clsx(
                "flex items-center gap-3 p-2 rounded-lg border font-mono text-sm transition-all",
                constraint.status === 'satisfied' && "bg-zkp-success/10 border-zkp-success/30",
                constraint.status === 'failed' && "bg-zkp-error/10 border-zkp-error/30",
                constraint.status === 'checking' && "bg-zkp-warning/10 border-zkp-warning/30 animate-pulse",
                constraint.status === 'pending' && "bg-zkp-dark-bg border-zkp-dark-border"
              )}
            >
              <div className="flex-shrink-0 w-5 h-5">
                {constraint.status === 'satisfied' && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-5 h-5 rounded-full bg-zkp-success flex items-center justify-center"
                  >
                    <Check className="w-3 h-3 text-white" />
                  </motion.div>
                )}
                {constraint.status === 'failed' && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-5 h-5 rounded-full bg-zkp-error flex items-center justify-center"
                  >
                    <X className="w-3 h-3 text-white" />
                  </motion.div>
                )}
                {constraint.status === 'checking' && (
                  <div className="w-5 h-5 rounded-full border-2 border-zkp-warning border-t-transparent animate-spin" />
                )}
                {constraint.status === 'pending' && (
                  <div className="w-5 h-5 rounded-full border-2 border-zkp-dark-border" />
                )}
              </div>

              <div className="flex-1 flex items-center gap-2">
                <span className="text-zkp-primary">{constraint.a}</span>
                <span className="text-gray-400">{constraint.b}</span>
                <span className="text-gray-500 text-xs">{constraint.c}</span>
              </div>

              <div className="text-xs text-gray-500">
                #{constraint.id}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between text-sm">
        <div className="text-gray-400">
          Constraints Verified:
        </div>
        <div className="font-mono">
          <span className="text-zkp-success">{verifiedCount || constraints.filter(c => c.status === 'satisfied').length}</span>
          <span className="text-gray-500"> / </span>
          <span className="text-white">{totalConstraints || constraints.length}</span>
        </div>
      </div>

      {/* Matrix visualization (simplified) */}
      <div className="bg-zkp-dark-bg rounded-lg p-3">
        <div className="text-xs text-gray-400 mb-2">Sparse Matrix (A, B, C)</div>
        <div className="grid grid-cols-3 gap-2 text-xs font-mono">
          <MatrixPreview label="A" active={active} color="primary" />
          <MatrixPreview label="B" active={active} color="secondary" />
          <MatrixPreview label="C" active={active} color="accent" />
        </div>
      </div>

      {!active && (
        <div className="absolute inset-0 bg-zkp-dark-bg/80 flex items-center justify-center rounded-lg">
          <span className="text-gray-500 text-sm">Waiting for constraints...</span>
        </div>
      )}
    </div>
  );
}

interface MatrixPreviewProps {
  label: string;
  active: boolean;
  color: 'primary' | 'secondary' | 'accent';
}

function MatrixPreview({ label, active, color }: MatrixPreviewProps) {
  const colorClasses = {
    primary: 'bg-zkp-primary',
    secondary: 'bg-zkp-secondary',
    accent: 'bg-zkp-accent'
  };

  return (
    <div className="space-y-1">
      <div className="text-gray-500 text-center">{label}</div>
      <div className="grid grid-cols-4 gap-0.5">
        {Array.from({ length: 16 }).map((_, i) => (
          <motion.div
            key={i}
            className={clsx(
              "w-2 h-2 rounded-sm",
              Math.random() > 0.7 ? colorClasses[color] : "bg-zkp-dark-border"
            )}
            animate={active ? {
              opacity: [0.3, 1, 0.3],
            } : {}}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: i * 0.05
            }}
          />
        ))}
      </div>
    </div>
  );
}
