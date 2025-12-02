import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface EllipticCurveVizProps {
  active: boolean;
  srsProgress?: {
    group: 'G1' | 'G2';
    percentage: number;
  };
}

export default function EllipticCurveViz({ active, srsProgress }: EllipticCurveVizProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Animate point moving along curve
  useEffect(() => {
    if (!active || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let t = 0;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw curve
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 0; x <= 300; x += 2) {
        const y = Math.sqrt(Math.pow((x - 50) / 40, 3) + 3) * 35 + 112;
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Mirror curve
      ctx.beginPath();
      for (let x = 0; x <= 300; x += 2) {
        const y = 225 - (Math.sqrt(Math.pow((x - 50) / 40, 3) + 3) * 35 + 112);
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Draw moving point (G1 element)
      const px = 50 + t * 200;
      const py = Math.sqrt(Math.pow((px - 50) / 40, 3) + 3) * 35 + 112;

      // Glow effect
      const gradient = ctx.createRadialGradient(px, py, 0, px, py, 15);
      gradient.addColorStop(0, 'rgba(99, 102, 241, 0.8)');
      gradient.addColorStop(0.5, 'rgba(99, 102, 241, 0.3)');
      gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(px, py, 15, 0, Math.PI * 2);
      ctx.fill();

      // Point
      ctx.fillStyle = '#6366f1';
      ctx.beginPath();
      ctx.arc(px, py, 5, 0, Math.PI * 2);
      ctx.fill();

      // Second point (scalar multiplication result)
      const qx = 80 + Math.sin(t * Math.PI * 2) * 50 + t * 100;
      const qy = 225 - (Math.sqrt(Math.pow((qx - 50) / 40, 3) + 3) * 35 + 112);

      // Glow for Q
      const gradient2 = ctx.createRadialGradient(qx, qy, 0, qx, qy, 15);
      gradient2.addColorStop(0, 'rgba(139, 92, 246, 0.8)');
      gradient2.addColorStop(0.5, 'rgba(139, 92, 246, 0.3)');
      gradient2.addColorStop(1, 'rgba(139, 92, 246, 0)');
      ctx.fillStyle = gradient2;
      ctx.beginPath();
      ctx.arc(qx, qy, 15, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#8b5cf6';
      ctx.beginPath();
      ctx.arc(qx, qy, 5, 0, Math.PI * 2);
      ctx.fill();

      // Draw line between points (for point addition visualization)
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.3)';
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(qx, qy);
      ctx.stroke();
      ctx.setLineDash([]);

      t += 0.003;
      if (t > 1) t = 0;

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [active]);

  return (
    <div className="relative">
      <canvas 
        ref={canvasRef} 
        width={300} 
        height={225}
        className="w-full h-auto rounded-lg bg-zkp-dark-bg"
      />
      
      {/* Labels */}
      <div className="absolute top-2 left-2 text-xs text-gray-500">
        y² = x³ + 3 (BN254)
      </div>

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

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-zkp-primary" />
          <span>G1 Point</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-zkp-secondary" />
          <span>G2 Point</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-zkp-accent" />
          <span>Pairing</span>
        </div>
      </div>

      {!active && (
        <div className="absolute inset-0 bg-zkp-dark-bg/80 flex items-center justify-center rounded-lg">
          <span className="text-gray-500 text-sm">Start a run to see animation</span>
        </div>
      )}
    </div>
  );
}
