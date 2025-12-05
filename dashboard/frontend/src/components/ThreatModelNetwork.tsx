import { useState, useEffect, useRef } from 'react';
import { 
  Server, 
  Laptop, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  Lock,
  Unlock,
  Activity
} from 'lucide-react';
import clsx from 'clsx';

interface Client {
  id: string;
  x: number;
  y: number;
  status: 'idle' | 'training' | 'generating_proof' | 'sending' | 'verified' | 'rejected';
  isHonest: boolean;
  attackType?: string;
}

interface ProofPacket {
  id: string;
  clientId: string;
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  progress: number;
  isValid: boolean;
  attackType?: string;
}

interface ThreatModelNetworkProps {
  // Real-time WebSocket connection
  messages?: any[];
  events?: any[];
  isRunning?: boolean;
  // Or standalone simulation mode
  simulationMode?: boolean;
  numClients?: number;
  simulationSpeed?: number;
}

export default function ThreatModelNetwork({ 
  messages = [],
  events = [],
  isRunning: externalRunning = false,
  simulationMode = false,
  numClients = 4, 
  simulationSpeed = 1 
}: ThreatModelNetworkProps) {
  const [clients, setClients] = useState<Client[]>([]);
  const [proofPackets, setProofPackets] = useState<ProofPacket[]>([]);
  const [serverStatus, setServerStatus] = useState<'idle' | 'receiving' | 'verifying' | 'aggregating'>('idle');
  const [round, setRound] = useState(1);
  const [isRunning, setIsRunning] = useState(false);
  const [mode, setMode] = useState<'simulation' | 'live'>(simulationMode ? 'simulation' : 'live');
  const [stats, setStats] = useState({
    proofsReceived: 0,
    proofsAccepted: 0,
    proofsRejected: 0,
    attacksBlocked: 0
  });
  
  const canvasRef = useRef<HTMLDivElement>(null);
  
  // Server position (center)
  const serverPos = { x: 400, y: 300 };

  // Initialize clients in a circle around server
  useEffect(() => {
    const radius = 200;
    const angleStep = (2 * Math.PI) / numClients;
    
    const initialClients: Client[] = Array.from({ length: numClients }, (_, i) => {
      const angle = i * angleStep - Math.PI / 2; // Start from top
      return {
        id: `client_${i}`,
        x: serverPos.x + radius * Math.cos(angle),
        y: serverPos.y + radius * Math.sin(angle),
        status: 'idle',
        isHonest: i !== 1, // Client 1 is malicious for demo
        attackType: i === 1 ? 'freeloading' : undefined
      };
    });
    
    setClients(initialClients);
  }, [numClients]);

  // Simulation engine (for standalone mode)
  useEffect(() => {
    if (mode !== 'simulation' || !isRunning || clients.length === 0) return;

    const interval = setInterval(() => {
      runSimulationStep();
    }, 1000 / simulationSpeed);

    return () => clearInterval(interval);
  }, [mode, isRunning, clients, simulationSpeed]);

  // Real-time event processing (for live mode)
  useEffect(() => {
    if (mode !== 'live' || !events || events.length === 0) return;

    const latestEvent = events[events.length - 1];
    
    // Parse training events
    if (latestEvent.type === 'training_started') {
      const clientId = latestEvent.client_id || 'client_0';
      setClients(prev => prev.map(c => 
        c.id === clientId ? { ...c, status: 'training' } : c
      ));
    } else if (latestEvent.type === 'proof_generation_start') {
      const clientId = latestEvent.client_id || 'client_0';
      setClients(prev => prev.map(c => 
        c.id === clientId ? { ...c, status: 'generating_proof' } : c
      ));
    } else if (latestEvent.type === 'proof_generated') {
      const clientId = latestEvent.client_id || 'client_0';
      setClients(prev => prev.map(c => 
        c.id === clientId ? { ...c, status: 'sending' } : c
      ));
      // Send proof packet
      const client = clients.find(c => c.id === clientId);
      if (client) sendProof(client);
    } else if (latestEvent.type === 'proof_verified') {
      const clientId = latestEvent.client_id || 'client_0';
      const isValid = latestEvent.is_valid !== false;
      setClients(prev => prev.map(c => 
        c.id === clientId ? { ...c, status: isValid ? 'verified' : 'rejected' } : c
      ));
      setStats(s => ({
        ...s,
        proofsReceived: s.proofsReceived + 1,
        proofsAccepted: isValid ? s.proofsAccepted + 1 : s.proofsAccepted,
        proofsRejected: !isValid ? s.proofsRejected + 1 : s.proofsRejected,
        attacksBlocked: !isValid ? s.attacksBlocked + 1 : s.attacksBlocked
      }));
    } else if (latestEvent.type === 'aggregation_start') {
      setServerStatus('aggregating');
    } else if (latestEvent.type === 'round_complete') {
      setRound(latestEvent.round || round + 1);
      setServerStatus('idle');
      setClients(prev => prev.map(c => ({ ...c, status: 'idle' })));
    }
  }, [events, mode, clients, round]);

  // Sync with external running state
  useEffect(() => {
    if (mode === 'live') {
      setIsRunning(externalRunning);
      if (!externalRunning) {
        // Reset on stop
        setClients(prev => prev.map(c => ({ ...c, status: 'idle' })));
        setProofPackets([]);
        setServerStatus('idle');
      }
    }
  }, [externalRunning, mode]);

  // Animate proof packets
  useEffect(() => {
    if (proofPackets.length === 0) return;

    const interval = setInterval(() => {
      setProofPackets(prev => {
        const updated = prev.map(packet => ({
          ...packet,
          progress: Math.min(packet.progress + 0.02, 1)
        })).filter(p => p.progress < 1);

        // Check if any packets reached server
        const completed = prev.filter(p => p.progress >= 1);
        if (completed.length > 0) {
          setServerStatus('verifying');
          
          completed.forEach(packet => {
            setTimeout(() => {
              verifyProof(packet);
            }, 500);
          });
        }

        return updated;
      });
    }, 16); // 60fps

    return () => clearInterval(interval);
  }, [proofPackets]);

  const runSimulationStep = () => {
    setClients(prev => {
      const updated = [...prev];
      let allIdle = true;

      updated.forEach((client, i) => {
        if (client.status === 'idle') {
          // Start training
          updated[i] = { ...client, status: 'training' };
        } else if (client.status === 'training') {
          // Generate proof
          updated[i] = { ...client, status: 'generating_proof' };
        } else if (client.status === 'generating_proof') {
          // Send proof
          updated[i] = { ...client, status: 'sending' };
          sendProof(client);
        } else if (client.status !== 'idle') {
          allIdle = false;
        }
      });

      // If all done, check if should start aggregation
      if (allIdle && serverStatus === 'idle') {
        const acceptedCount = updated.filter(c => c.status === 'verified').length;
        if (acceptedCount > 0) {
          setTimeout(() => {
            setServerStatus('aggregating');
            setTimeout(() => {
              // Reset for next round
              setClients(updated.map(c => ({ ...c, status: 'idle' })));
              setServerStatus('idle');
              setRound(r => r + 1);
            }, 2000);
          }, 1000);
        }
      }

      return updated;
    });
  };

  const sendProof = (client: Client) => {
    const packet: ProofPacket = {
      id: `proof_${Date.now()}_${client.id}`,
      clientId: client.id,
      fromX: client.x,
      fromY: client.y,
      toX: serverPos.x,
      toY: serverPos.y,
      progress: 0,
      isValid: client.isHonest,
      attackType: client.attackType
    };

    setProofPackets(prev => [...prev, packet]);
    setStats(s => ({ ...s, proofsReceived: s.proofsReceived + 1 }));
  };

  const verifyProof = (packet: ProofPacket) => {
    setClients(prev => prev.map(c => {
      if (c.id === packet.clientId) {
        if (packet.isValid) {
          setStats(s => ({ ...s, proofsAccepted: s.proofsAccepted + 1 }));
          return { ...c, status: 'verified' };
        } else {
          setStats(s => ({ 
            ...s, 
            proofsRejected: s.proofsRejected + 1,
            attacksBlocked: s.attacksBlocked + 1 
          }));
          return { ...c, status: 'rejected' };
        }
      }
      return c;
    }));

    setTimeout(() => setServerStatus('idle'), 500);
  };

  const startSimulation = () => {
    setIsRunning(true);
    setStats({ proofsReceived: 0, proofsAccepted: 0, proofsRejected: 0, attacksBlocked: 0 });
    setRound(1);
  };

  const stopSimulation = () => {
    setIsRunning(false);
    setClients(prev => prev.map(c => ({ ...c, status: 'idle' })));
    setProofPackets([]);
    setServerStatus('idle');
  };

  const getClientColor = (client: Client) => {
    if (client.status === 'rejected') return 'text-red-500';
    if (client.status === 'verified') return 'text-green-500';
    if (!client.isHonest) return 'text-orange-500';
    return 'text-blue-400';
  };

  const getClientIcon = (client: Client) => {
    if (client.status === 'rejected') return <XCircle className="w-6 h-6" />;
    if (client.status === 'verified') return <CheckCircle className="w-6 h-6" />;
    if (!client.isHonest) return <Unlock className="w-6 h-6" />;
    return <Lock className="w-6 h-6" />;
  };

  return (
    <div className="min-h-screen bg-zkp-dark-bg text-white p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-zkp-accent to-violet-600 flex items-center justify-center">
              <Activity className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Threat Model Visualization</h1>
              <p className="text-gray-400">Network Topology with Proof Flow Animation</p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            {/* Mode Toggle */}
            <div className="flex items-center gap-2 bg-zkp-dark-card border border-zkp-dark-border rounded-lg p-1">
              <button
                onClick={() => setMode('live')}
                className={clsx(
                  "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                  mode === 'live' ? "bg-zkp-accent text-white" : "text-gray-400 hover:text-white"
                )}
              >
                🔴 Live
              </button>
              <button
                onClick={() => setMode('simulation')}
                className={clsx(
                  "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                  mode === 'simulation' ? "bg-zkp-accent text-white" : "text-gray-400 hover:text-white"
                )}
              >
                🎮 Demo
              </button>
            </div>

            {/* Start/Stop Button (only in simulation mode) */}
            {mode === 'simulation' && (
              !isRunning ? (
                <button
                  onClick={startSimulation}
                  className="px-6 py-3 bg-zkp-accent hover:bg-zkp-accent/80 rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <Zap className="w-5 h-5" />
                  Start Demo
                </button>
              ) : (
                <button
                  onClick={stopSimulation}
                  className="px-6 py-3 bg-red-500 hover:bg-red-600 rounded-lg font-medium transition-colors"
                >
                  Stop Demo
                </button>
              )
            )}

            {/* Live mode status */}
            {mode === 'live' && (
              <div className={clsx(
                "px-6 py-3 rounded-lg font-medium flex items-center gap-2",
                externalRunning ? "bg-green-500/20 text-green-400" : "bg-gray-700 text-gray-400"
              )}>
                {externalRunning ? (
                  <>
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                    Monitoring Live Run
                  </>
                ) : (
                  <>No Active Run - Start from Run Control</>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Stats Bar */}
        <div className="mt-6 grid grid-cols-5 gap-4">
          <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-lg p-4">
            <div className="text-gray-400 text-sm mb-1">Round</div>
            <div className="text-2xl font-bold text-zkp-accent">{round}</div>
          </div>
          <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-lg p-4">
            <div className="text-gray-400 text-sm mb-1">Proofs Received</div>
            <div className="text-2xl font-bold">{stats.proofsReceived}</div>
          </div>
          <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-lg p-4">
            <div className="text-gray-400 text-sm mb-1">Accepted</div>
            <div className="text-2xl font-bold text-green-500">{stats.proofsAccepted}</div>
          </div>
          <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-lg p-4">
            <div className="text-gray-400 text-sm mb-1">Rejected</div>
            <div className="text-2xl font-bold text-red-500">{stats.proofsRejected}</div>
          </div>
          <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-lg p-4">
            <div className="text-gray-400 text-sm mb-1">Attacks Blocked</div>
            <div className="text-2xl font-bold text-orange-500">{stats.attacksBlocked}</div>
          </div>
        </div>
      </div>

      {/* Network Canvas */}
      <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-xl p-8 relative overflow-hidden">
        <div 
          ref={canvasRef}
          className="relative w-full h-[600px] bg-gray-900/50 rounded-lg"
          style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(100, 100, 100, 0.15) 1px, transparent 0)', backgroundSize: '40px 40px' }}
        >
          {/* Connection Lines */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
            {clients.map(client => (
              <line
                key={`line-${client.id}`}
                x1={client.x}
                y1={client.y}
                x2={serverPos.x}
                y2={serverPos.y}
                stroke={client.status === 'rejected' ? '#ef4444' : client.status === 'verified' ? '#22c55e' : '#4b5563'}
                strokeWidth="2"
                strokeDasharray={client.isHonest ? "0" : "5,5"}
                opacity="0.3"
              />
            ))}
          </svg>

          {/* Proof Packets (animated) */}
          {proofPackets.map(packet => {
            const x = packet.fromX + (packet.toX - packet.fromX) * packet.progress;
            const y = packet.fromY + (packet.toY - packet.fromY) * packet.progress;
            
            return (
              <div
                key={packet.id}
                className="absolute transition-all duration-100"
                style={{ 
                  left: x - 12, 
                  top: y - 12,
                  zIndex: 2
                }}
              >
                <div className={clsx(
                  "w-6 h-6 rounded-full flex items-center justify-center animate-pulse",
                  packet.isValid ? "bg-green-500" : "bg-red-500"
                )}>
                  <Shield className="w-4 h-4 text-white" />
                </div>
                {!packet.isValid && (
                  <div className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs bg-red-500 px-2 py-0.5 rounded">
                    {packet.attackType}
                  </div>
                )}
              </div>
            );
          })}

          {/* Server (Center) */}
          <div
            className="absolute transition-all duration-300"
            style={{ 
              left: serverPos.x - 40, 
              top: serverPos.y - 40,
              zIndex: 3
            }}
          >
            <div className={clsx(
              "w-20 h-20 rounded-2xl border-4 flex flex-col items-center justify-center transition-all",
              serverStatus === 'verifying' && "animate-pulse border-yellow-500 bg-yellow-500/20",
              serverStatus === 'aggregating' && "animate-pulse border-green-500 bg-green-500/20",
              serverStatus === 'receiving' && "border-blue-500 bg-blue-500/20",
              serverStatus === 'idle' && "border-zkp-accent bg-zkp-accent/10"
            )}>
              <Server className="w-8 h-8 text-white mb-1" />
              <span className="text-xs font-bold">SERVER</span>
            </div>
            <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs text-gray-400">
              {serverStatus === 'verifying' && '🔍 Verifying...'}
              {serverStatus === 'aggregating' && '📊 Aggregating...'}
              {serverStatus === 'receiving' && '📥 Receiving...'}
              {serverStatus === 'idle' && '💤 Idle'}
            </div>
          </div>

          {/* Clients */}
          {clients.map(client => (
            <div
              key={client.id}
              className="absolute transition-all duration-300"
              style={{ 
                left: client.x - 30, 
                top: client.y - 30,
                zIndex: 3
              }}
            >
              <div className={clsx(
                "w-16 h-16 rounded-xl border-3 flex flex-col items-center justify-center transition-all",
                client.status === 'training' && "animate-pulse",
                client.status === 'generating_proof' && "animate-pulse border-purple-500",
                client.status === 'verified' && "border-green-500 bg-green-500/20",
                client.status === 'rejected' && "border-red-500 bg-red-500/20 shake",
                client.status === 'idle' && !client.isHonest && "border-orange-500",
                client.status === 'idle' && client.isHonest && "border-gray-600"
              )}>
                <Laptop className={clsx("w-6 h-6 mb-1", getClientColor(client))} />
                <div className="absolute -top-1 -right-1">
                  {getClientIcon(client)}
                </div>
              </div>
              
              {/* Client Label */}
              <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 text-center">
                <div className="text-xs font-bold whitespace-nowrap">
                  {client.id.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-xs text-gray-500">
                  {client.status.replace('_', ' ')}
                </div>
                {!client.isHonest && (
                  <div className="text-xs text-orange-500 font-semibold">
                    ⚠️ Attacker
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-6 flex items-center justify-center gap-8 text-sm">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-blue-400" />
            <span className="text-gray-400">Honest Client</span>
          </div>
          <div className="flex items-center gap-2">
            <Unlock className="w-4 h-4 text-orange-500" />
            <span className="text-gray-400">Malicious Client</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-gray-400">Valid Proof</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-gray-400">Invalid Proof (Rejected)</span>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }
        .shake {
          animation: shake 0.5s;
        }
      `}</style>
    </div>
  );
}
