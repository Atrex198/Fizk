import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { CryptoEvent } from '../../types';

interface FoldingVizProps {
  active: boolean;
  proofEvents: CryptoEvent[];
}

interface FoldingStep {
  id: number;
  name: string;
  description: string;
  status: 'pending' | 'active' | 'completed';
}

export default function FoldingViz({ active, proofEvents }: FoldingVizProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [accumulators, setAccumulators] = useState<{ id: number; opacity: number }[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const foldingSteps: FoldingStep[] = [
    { id: 1, name: 'Instance Setup', description: 'Initialize accumulator with public inputs', status: 'pending' },
    { id: 2, name: 'Witness Encoding', description: 'Encode witness as polynomial evaluations', status: 'pending' },
    { id: 3, name: 'Error Polynomial', description: 'Compute error polynomial E(X)', status: 'pending' },
    { id: 4, name: 'Folding Challenge', description: 'Fiat-Shamir derive challenge β', status: 'pending' },
    { id: 5, name: 'Accumulator Update', description: 'Fold instance into accumulator', status: 'pending' },
    { id: 6, name: 'Decider Check', description: 'Verify accumulated proof', status: 'pending' },
  ];

  // Animate folding steps based on actual folding events
  useEffect(() => {
    const foldingEvents = proofEvents.filter(e => e.type === 'folding_event');
    if (foldingEvents.length === 0) {
      setCurrentStep(0);
      return;
    }

    // Progress through steps based on actual events
    const stepIndex = Math.min(Math.floor(foldingEvents.length / 2), foldingSteps.length - 1);
    setCurrentStep(stepIndex + 1);

    // Add accumulator when folding completes
    if (foldingEvents.length > accumulators.length) {
      setAccumulators(acc => [...acc.slice(-3), { id: Date.now(), opacity: 1 }]);
    }
  }, [proofEvents]);

  // Canvas animation for folding visualization - only when folding is happening
  useEffect(() => {
    const hasFoldingEvents = proofEvents.filter(e => e.type === 'folding_event').length > 0;
    if (!hasFoldingEvents || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let t = 0;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw folding visual - two instances combining into one
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      // Instance 1 (left)
      const instance1X = centerX - 60 + Math.sin(t * 2) * 20;
      const instance1Y = centerY + Math.cos(t) * 10;

      // Instance 2 (right)
      const instance2X = centerX + 60 - Math.sin(t * 2) * 20;
      const instance2Y = centerY - Math.cos(t) * 10;

      // Accumulator (center)
      const accX = centerX;
      const accY = centerY;

      // Draw connecting lines (folding arrows)
      ctx.strokeStyle = `rgba(99, 102, 241, ${0.3 + Math.sin(t * 3) * 0.2})`;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      
      ctx.beginPath();
      ctx.moveTo(instance1X, instance1Y);
      ctx.lineTo(accX, accY);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(instance2X, instance2Y);
      ctx.lineTo(accX, accY);
      ctx.stroke();

      ctx.setLineDash([]);

      // Draw Instance 1
      drawInstance(ctx, instance1X, instance1Y, '#6366f1', 'I₁', 25 - Math.sin(t * 2) * 5);

      // Draw Instance 2
      drawInstance(ctx, instance2X, instance2Y, '#8b5cf6', 'I₂', 25 - Math.sin(t * 2) * 5);

      // Draw Accumulator (larger, pulsing)
      const accRadius = 35 + Math.sin(t * 2) * 5;
      drawInstance(ctx, accX, accY, '#06b6d4', 'Acc', accRadius, true);

      // Draw folding symbol
      ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
      ctx.font = 'bold 16px JetBrains Mono';
      ctx.textAlign = 'center';
      ctx.fillText('⊕', centerX, centerY + 60);
      ctx.font = '10px JetBrains Mono';
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.fillText('β-fold', centerX, centerY + 75);

      t += 0.02;
      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => cancelAnimationFrame(animationId);
  }, [proofEvents]);

  const stepsWithStatus = foldingSteps.map((step, idx) => ({
    ...step,
    status: idx < currentStep ? 'completed' : idx === currentStep ? 'active' : 'pending'
  }));

  return (
    <div className="space-y-4">
      {/* Folding Animation Canvas */}
      <div className="relative">
        <canvas
          ref={canvasRef}
          width={300}
          height={150}
          className="w-full h-auto rounded-lg bg-zkp-dark-bg"
        />
        
        {/* Accumulator count */}
        <div className="absolute top-2 right-2 flex items-center gap-1">
          <span className="text-xs text-gray-400">Accumulated:</span>
          <span className="text-xs font-mono text-zkp-accent">{accumulators.length}</span>
        </div>
      </div>

      {/* Protocol Steps */}
      <div className="space-y-2">
        {stepsWithStatus.map((step, idx) => (
          <motion.div
            key={step.id}
            className={clsx(
              "flex items-center gap-3 p-2 rounded-lg border text-sm transition-all",
              step.status === 'completed' && "bg-zkp-success/10 border-zkp-success/20",
              step.status === 'active' && "bg-zkp-primary/10 border-zkp-primary/30",
              step.status === 'pending' && "bg-zkp-dark-bg border-zkp-dark-border opacity-50"
            )}
            animate={step.status === 'active' ? { scale: [1, 1.02, 1] } : {}}
            transition={{ repeat: Infinity, duration: 1 }}
          >
            {/* Step Number */}
            <div className={clsx(
              "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold",
              step.status === 'completed' && "bg-zkp-success text-white",
              step.status === 'active' && "bg-zkp-primary text-white",
              step.status === 'pending' && "bg-zkp-dark-border text-gray-500"
            )}>
              {step.status === 'completed' ? '✓' : idx + 1}
            </div>

            {/* Step Info */}
            <div className="flex-1">
              <p className={clsx(
                "font-medium",
                step.status === 'completed' && "text-zkp-success",
                step.status === 'active' && "text-zkp-primary",
                step.status === 'pending' && "text-gray-500"
              )}>
                {step.name}
              </p>
              {step.status === 'active' && (
                <motion.p 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-xs text-gray-400"
                >
                  {step.description}
                </motion.p>
              )}
            </div>

            {/* Progress indicator */}
            {step.status === 'active' && (
              <div className="w-4 h-4 border-2 border-zkp-primary border-t-transparent rounded-full animate-spin" />
            )}
          </motion.div>
        ))}
      </div>

      {/* Proof count from actual events */}
      {proofEvents.length > 0 && (
        <div className="flex items-center justify-between text-sm p-2 bg-zkp-dark-bg rounded-lg">
          <span className="text-gray-400">Proofs Generated:</span>
          <span className="font-mono text-zkp-success">
            {proofEvents.filter(e => e.type === 'proof_verified').length}
          </span>
        </div>
      )}
    </div>
  );
}

function drawInstance(
  ctx: CanvasRenderingContext2D, 
  x: number, 
  y: number, 
  color: string, 
  label: string,
  radius: number,
  isAccumulator: boolean = false
) {
  // Glow
  const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius + 10);
  gradient.addColorStop(0, color + 'cc');
  gradient.addColorStop(0.5, color + '44');
  gradient.addColorStop(1, color + '00');
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(x, y, radius + 10, 0, Math.PI * 2);
  ctx.fill();

  // Circle
  ctx.fillStyle = color + '33';
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Label
  ctx.fillStyle = 'white';
  ctx.font = isAccumulator ? 'bold 14px JetBrains Mono' : '12px JetBrains Mono';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, x, y);
}
