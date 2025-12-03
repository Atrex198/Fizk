import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

interface EllipticCurveVizProps {
  active: boolean;
  srsProgress?: {
    group: 'G1' | 'G2';
    percentage: number;
  };
  srsData?: {
    srs_size: number;
    g1_powers?: number;
    g2_powers?: number;
    tau_commitment?: string;
  };
}

export default function EllipticCurveViz({ active, srsProgress, srsData }: EllipticCurveVizProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showPowers, setShowPowers] = useState(true);
  const [hoveredPower] = useState<number | null>(null);
  const [activeG1Index, setActiveG1Index] = useState(0);
  const [activeG2Index, setActiveG2Index] = useState(0);

  const srsSize = srsData?.srs_size || 64;
  const g1Count = Math.min(srsSize, 8); // Show max 8 points for clarity
  const g2Count = Math.min(Math.ceil(srsSize / 4), 4); // G2 has fewer elements

  // Animate active power index
  useEffect(() => {
    if (!active) return;
    
    const interval = setInterval(() => {
      setActiveG1Index(prev => (prev + 1) % g1Count);
      setActiveG2Index(prev => (prev + 1) % g2Count);
    }, 800);
    
    return () => clearInterval(interval);
  }, [active, g1Count, g2Count]);

  // Canvas animation
  useEffect(() => {
    if (!active || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let t = 0;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw grid
      ctx.strokeStyle = 'rgba(51, 65, 85, 0.3)';
      ctx.lineWidth = 0.5;
      for (let i = 0; i <= canvas.width; i += 30) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, canvas.height);
        ctx.stroke();
      }
      for (let i = 0; i <= canvas.height; i += 30) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(canvas.width, i);
        ctx.stroke();
      }

      // Draw curve y² = x³ + 3 (BN254)
      ctx.strokeStyle = '#475569';
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x <= 300; x += 2) {
        const y = Math.sqrt(Math.pow((x - 50) / 40, 3) + 3) * 35 + 100;
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Mirror curve (bottom half)
      ctx.beginPath();
      for (let x = 0; x <= 300; x += 2) {
        const y = 200 - (Math.sqrt(Math.pow((x - 50) / 40, 3) + 3) * 35 + 100);
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Draw G1 powers (blue points on curve)
      for (let i = 0; i < g1Count; i++) {
        const progress = i / g1Count;
        const px = 60 + progress * 180;
        const py = Math.sqrt(Math.pow((px - 50) / 40, 3) + 3) * 35 + 100;
        
        const isActive = i === activeG1Index;
        const isHovered = hoveredPower === i;
        const radius = isActive ? 8 : isHovered ? 6 : 4;
        
        // Glow for active point
        if (isActive) {
          const gradient = ctx.createRadialGradient(px, py, 0, px, py, 20);
          gradient.addColorStop(0, 'rgba(99, 102, 241, 0.6)');
          gradient.addColorStop(0.5, 'rgba(99, 102, 241, 0.2)');
          gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(px, py, 20, 0, Math.PI * 2);
          ctx.fill();
        }

        // Point
        ctx.fillStyle = isActive ? '#818cf8' : '#6366f1';
        ctx.beginPath();
        ctx.arc(px, py, radius, 0, Math.PI * 2);
        ctx.fill();

        // Label
        if (showPowers && (isActive || isHovered)) {
          ctx.fillStyle = '#e2e8f0';
          ctx.font = 'bold 10px JetBrains Mono, monospace';
          ctx.textAlign = 'center';
          ctx.fillText(`[τ]₁^${i}`, px, py - 15);
        }
      }

      // Draw G2 powers (purple points, larger)
      for (let i = 0; i < g2Count; i++) {
        const progress = i / g2Count;
        const qx = 80 + progress * 140;
        const qy = 200 - (Math.sqrt(Math.pow((qx - 50) / 40, 3) + 3) * 35 + 100);
        
        const isActive = i === activeG2Index;
        const radius = isActive ? 10 : 6;

        // Glow for active
        if (isActive) {
          const gradient = ctx.createRadialGradient(qx, qy, 0, qx, qy, 25);
          gradient.addColorStop(0, 'rgba(139, 92, 246, 0.6)');
          gradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.2)');
          gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(qx, qy, 25, 0, Math.PI * 2);
          ctx.fill();
        }

        // Point (diamond shape for G2)
        ctx.fillStyle = isActive ? '#a78bfa' : '#8b5cf6';
        ctx.beginPath();
        ctx.moveTo(qx, qy - radius);
        ctx.lineTo(qx + radius, qy);
        ctx.lineTo(qx, qy + radius);
        ctx.lineTo(qx - radius, qy);
        ctx.closePath();
        ctx.fill();

        // Label
        if (showPowers && isActive) {
          ctx.fillStyle = '#e2e8f0';
          ctx.font = 'bold 10px JetBrains Mono, monospace';
          ctx.textAlign = 'center';
          ctx.fillText(`[τ]₂^${i}`, qx, qy - 18);
        }
      }

      // Draw pairing line between active G1 and G2
      if (active) {
        const g1x = 60 + (activeG1Index / g1Count) * 180;
        const g1y = Math.sqrt(Math.pow((g1x - 50) / 40, 3) + 3) * 35 + 100;
        const g2x = 80 + (activeG2Index / g2Count) * 140;
        const g2y = 200 - (Math.sqrt(Math.pow((g2x - 50) / 40, 3) + 3) * 35 + 100);

        // Pairing arrow
        ctx.strokeStyle = 'rgba(6, 182, 212, 0.5)';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(g1x, g1y);
        ctx.lineTo(g2x, g2y);
        ctx.stroke();
        ctx.setLineDash([]);

        // Pairing target point
        const midX = (g1x + g2x) / 2;
        const midY = (g1y + g2y) / 2;
        
        ctx.fillStyle = 'rgba(6, 182, 212, 0.8)';
        ctx.beginPath();
        ctx.arc(midX, midY, 6, 0, Math.PI * 2);
        ctx.fill();
        
        // e(G1,G2) label
        ctx.fillStyle = '#06b6d4';
        ctx.font = '9px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        ctx.fillText('e(·,·) → Gₜ', midX, midY - 12);
      }

      t += 0.01;
      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [active, g1Count, g2Count, activeG1Index, activeG2Index, showPowers, hoveredPower]);

  return (
    <div className="space-y-3">
      <div className="relative">
        <canvas 
          ref={canvasRef} 
          width={300} 
          height={200}
          className="w-full h-auto rounded-lg bg-zkp-dark-bg border border-zkp-dark-border"
        />
        
        {/* Curve equation */}
        <div className="absolute top-2 left-2 text-xs text-gray-500 font-mono">
          y² = x³ + 3 (BN254)
        </div>

        {/* Toggle powers button */}
        <button
          onClick={() => setShowPowers(!showPowers)}
          className={clsx(
            "absolute top-2 right-2 text-xs px-2 py-1 rounded transition-colors",
            showPowers 
              ? "bg-zkp-primary/20 text-zkp-primary" 
              : "bg-zkp-dark-border text-gray-400"
          )}
        >
          τ powers
        </button>

        {/* SRS Progress */}
        {srsProgress && (
          <div className="absolute bottom-2 left-2 right-2">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-400">{srsProgress.group} SRS Generation</span>
              <span className="text-zkp-primary">{srsProgress.percentage.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 bg-zkp-dark-border rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-gradient-to-r from-zkp-primary to-zkp-secondary"
                initial={{ width: 0 }}
                animate={{ width: `${srsProgress.percentage}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        )}

        {!active && (
          <div className="absolute inset-0 bg-zkp-dark-bg/80 flex items-center justify-center rounded-lg">
            <span className="text-gray-500 text-sm">Start a run to see animation</span>
          </div>
        )}
      </div>

      {/* SRS Info Cards */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-2 bg-zkp-dark-bg rounded-lg border border-zkp-primary/30">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-zkp-primary" />
            <span className="text-xs text-gray-400">G₁ Powers</span>
          </div>
          <p className="text-lg font-bold text-zkp-primary font-mono">{srsSize}</p>
          <p className="text-xs text-gray-500">[τ]₁, [τ²]₁, ... [τⁿ]₁</p>
        </div>
        
        <div className="p-2 bg-zkp-dark-bg rounded-lg border border-zkp-secondary/30">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-zkp-secondary" style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }} />
            <span className="text-xs text-gray-400">G₂ Powers</span>
          </div>
          <p className="text-lg font-bold text-zkp-secondary font-mono">{Math.ceil(srsSize / 4)}</p>
          <p className="text-xs text-gray-500">[τ]₂, [τ²]₂ (for pairing)</p>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between text-xs text-gray-400 px-1">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-zkp-primary" />
            <span>G₁ ∈ E(𝔽ₚ)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-zkp-secondary" style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }} />
            <span>G₂ ∈ E'(𝔽ₚ²)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-zkp-accent" />
            <span>Gₜ (pairing)</span>
          </div>
        </div>
      </div>

      {/* Tau commitment */}
      {srsData?.tau_commitment && (
        <div className="p-2 bg-zkp-dark-bg rounded-lg border border-zkp-dark-border">
          <p className="text-xs text-gray-400 mb-1">τ Commitment (toxic waste destroyed)</p>
          <p className="text-xs font-mono text-gray-500 truncate">
            {srsData.tau_commitment}
          </p>
        </div>
      )}
    </div>
  );
}
