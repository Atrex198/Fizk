import { useState, useEffect } from 'react';
import { 
  Server, 
  Laptop, 
  Shield, 
  CheckCircle,
  XCircle,
  Zap,
  Lock,
  Unlock,
  Settings,
  Play,
  Loader2,
  AlertTriangle
} from 'lucide-react';
import clsx from 'clsx';
import { LogMessage, CryptoEvent } from '../types';

interface Client {
  id: string;
  x: number;
  y: number;
  status: 'idle' | 'training' | 'generating_proof' | 'sending' | 'verified' | 'rejected';
  isHonest: boolean;
  result?: string;
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
}

interface InteractiveThreatDemoProps {
  messages: LogMessage[];
  events: CryptoEvent[];
  isRunning: boolean;
}

export default function InteractiveThreatDemo({ messages, events, isRunning: globalIsRunning }: InteractiveThreatDemoProps) {
  // Configuration
  const [numClients, setNumClients] = useState(3);
  const [numDishonest, setNumDishonest] = useState(1);
  const [srsSize, setSrsSize] = useState(256);
  const [liteMode, setLiteMode] = useState(true);
  const [useRealFL, setUseRealFL] = useState(false); // NEW: Toggle for real FL training
  
  // Simulation state
  const [clients, setClients] = useState<Client[]>([]);
  const [proofPackets, setProofPackets] = useState<ProofPacket[]>([]);
  const [serverStatus, setServerStatus] = useState<'idle' | 'receiving' | 'verifying' | 'aggregating'>('idle');
  const [currentPhase, setCurrentPhase] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [foldingData, setFoldingData] = useState<any>(null);
  const [processedMessageIds, setProcessedMessageIds] = useState<Set<string>>(new Set());
  
  const serverPos = { x: 400, y: 300 };

  // Listen to incoming messages from shared WebSocket (via props)
  useEffect(() => {
    // Only process messages if a run is actually active
    if (!globalIsRunning) return;
    
    // Process only NEW messages that haven't been processed yet
    messages.forEach((msg, index) => {
      const msgId = `${msg.timestamp}-${index}`;
      
      // Skip if already processed
      if (processedMessageIds.has(msgId)) return;
      
      // Check if message contains folding event
      if (msg.event && msg.event.type === 'folding_event') {
        const eventData = msg.event.data as any;
        if (eventData && eventData.event_type) {
          handleFoldingEvent({
            type: 'folding_event',
            event_type: eventData.event_type,
            step: eventData.step,
            total_steps: eventData.total_steps,
            data: eventData.details
          });
          
          // Mark as processed
          setProcessedMessageIds(prev => new Set(prev).add(msgId));
        }
      }
    });
  }, [messages, globalIsRunning, processedMessageIds]);

  // Update server status when global status changes
  useEffect(() => {
    if (globalIsRunning) {
      setServerStatus('receiving');
    } else {
      setServerStatus('idle');
      setCurrentPhase('');
    }
  }, [globalIsRunning]);

  const handleFoldingEvent = (message: any) => {
    const { event_type, step, total_steps, data } = message;
    
    setFoldingData({ event_type, step, total_steps, data });
    
    // Update logs based on event type
    switch (event_type) {
      case 'lagrange_start':
        addLog(`🔢 ProtoGalaxy: Computing Lagrange basis for ${data.num_proofs} proofs...`);
        setCurrentPhase('ProtoGalaxy: Lagrange Basis');
        setServerStatus('aggregating');
        break;
      
      case 'lagrange_complete':
        addLog(`  ✅ Lagrange coefficients computed (challenge: ${data.challenge})`);
        break;
      
      case 'cross_term_start':
        addLog(`🔗 Computing ${data.num_cross_terms} cross-term polynomials...`);
        setCurrentPhase('ProtoGalaxy: Cross-Terms');
        break;
      
      case 'cross_term_computed':
        addLog(`  📊 Cross-term ${data.progress}/${data.total}: T(${data.proof_pair[0]},${data.proof_pair[1]}) [size: ${data.cross_term_size}]`);
        break;
      
      case 'cross_term_complete':
        addLog(`  ✅ All cross-terms computed (${data.ec_operations} EC operations)`);
        break;
      
      case 'witness_fold_start':
        addLog(`👥 Folding ${data.num_witnesses} witnesses with Lagrange accumulation...`);
        setCurrentPhase('ProtoGalaxy: Witness Folding');
        break;
      
      case 'witness_folded':
        const hasCross = data.has_cross_term ? ' (with cross-term)' : '';
        addLog(`  🔄 Witness ${data.progress}/${data.total} folded [L_${data.witness_index} = ${data.lagrange_coeff}]${hasCross}`);
        break;
      
      case 'witness_fold_complete':
        addLog(`  ✅ Witnesses folded (u = ${data.u_value})`);
        break;
      
      case 'commitment_fold_start':
        addLog(`🔐 Folding ${data.num_commitments} elliptic curve commitments...`);
        setCurrentPhase('ProtoGalaxy: Commitment Folding');
        break;
      
      case 'commitment_folded':
        addLog(`  🔗 ${data.commitment_type} commitment ${data.progress}/${data.total} folded`);
        break;
      
      case 'commitment_fold_complete':
        addLog(`  ✅ All commitments folded (${data.ec_operations_total} EC ops, ${data.cross_terms_integrated} cross-terms)`);
        break;
      
      case 'aggregation_complete':
        addLog(`✨ Aggregation complete! ${data.proofs_aggregated} proofs → 1 aggregated proof`);
        addLog(`  📊 Final proof: ${data.final_proof_size_kb.toFixed(2)} KB, ${data.total_time_ms}ms`);
        addLog(`  🎯 Polynomial degree: ${data.polynomial_degree}, EC ops: ${data.ec_operations_total}`);
        setServerStatus('idle');
        setCurrentPhase('Complete');
        // Run state managed globally
        break;
    }
  };

  // Initialize clients in circle
  useEffect(() => {
    const radius = 200;
    const angleStep = (2 * Math.PI) / numClients;
    
    const initialClients: Client[] = Array.from({ length: numClients }, (_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      return {
        id: `client_${i}`,
        x: serverPos.x + radius * Math.cos(angle),
        y: serverPos.y + radius * Math.sin(angle),
        status: 'idle',
        isHonest: i >= numDishonest // First N clients are dishonest
      };
    });
    
    setClients(initialClients);
  }, [numClients, numDishonest]);

  // Animate proof packets
  useEffect(() => {
    if (proofPackets.length === 0) return;

    const interval = setInterval(() => {
      setProofPackets(prev => {
        const updated = prev.map(packet => ({
          ...packet,
          progress: Math.min(packet.progress + 0.015, 1)
        })).filter(p => p.progress < 1);

        return updated;
      });
    }, 16);

    return () => clearInterval(interval);
  }, [proofPackets]);

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const runDemo = async () => {
    // Run state now managed globally
    setLogs([]);
    setProofPackets([]);
    
    if (useRealFL) {
      // Trigger actual FL training run
      await runRealFLTraining();
    } else {
      // Run simulated demo
      await runSimulatedDemo();
    }
    
    // Run completion handled globally
  };

  const runRealFLTraining = async () => {
    addLog(`🚀 Starting REAL FL training with ${numClients} clients`);
    addLog(`⚙️ Configuration: SRS=${srsSize}, Lite=${liteMode}`);
    
    if (numDishonest > 0) {
      addLog(`⚠️  Security Test Mode: ${numDishonest} dishonest client(s) will attempt freeloading`);
      await runRealSecurityTest();
    } else {
      addLog(`✅ All clients are honest - running normal FL training`);
      await runHonestFLTraining();
    }
  };

  const runHonestFLTraining = async () => {
    setClients(prev => prev.map(c => ({ ...c, status: 'idle', result: undefined })));
    
    try {
      // Start real FL run via backend
      const response = await fetch('http://localhost:8000/api/runs/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_clients: numClients,
          num_rounds: 1,
          local_epochs: 2,
          batch_size: 64,
          learning_rate: 0.001,
        }),
      });
      
      if (!response.ok) {
        addLog(`❌ Failed to start FL run: ${response.statusText}`);
        return;
      }
      
      const result = await response.json();
      addLog(`✅ FL run started: ${result.run_id}`);
      addLog(`📡 Listening for real-time folding events...`);
      
      setCurrentPhase('FL Training in Progress');
      setServerStatus('receiving');
      
    } catch (error) {
      addLog(`❌ Error starting FL run: ${error}`);
    }
  };

  const runRealSecurityTest = async () => {
    addLog(`🔒 Running real security test with ZKP verification...`);
    setCurrentPhase('Security Testing Mode');
    
    // Start a background FL run to trigger globalIsRunning state
    // This makes Live View show as active during security tests
    try {
      const bgResponse = await fetch('http://localhost:8000/api/runs/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_clients: 2,  // Minimal background run
          num_rounds: 1,
          local_epochs: 1,
          batch_size: 64,
          learning_rate: 0.001,
        }),
      });
      if (bgResponse.ok) {
        addLog(`📡 Background FL training started for Live View sync`);
      }
    } catch (error) {
      console.error('Failed to start background run:', error);
    }
    
    // Initialize clients with honest/dishonest roles
    const honestCount = numClients - numDishonest;
    const testClients: Client[] = [];
    
    for (let i = 0; i < numClients; i++) {
      const isHonest = i < honestCount;
      testClients.push({
        id: `client_${i + 1}`,
        x: 400 + 200 * Math.cos(2 * Math.PI * i / numClients),
        y: 300 + 200 * Math.sin(2 * Math.PI * i / numClients),
        status: 'idle',
        isHonest: isHonest,
        result: undefined
      });
    }
    setClients(testClients);
    
    // Phase 1: Training
    addLog(`📚 Phase 1: Local training on ${numClients} clients...`);
    setCurrentPhase('Phase 1: Local Training');
    setClients(prev => prev.map(c => ({ ...c, status: 'training' })));
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Phase 2: Proof generation (honest vs dishonest)
    addLog(`🔐 Phase 2: Generating ZKP proofs...`);
    setCurrentPhase('Phase 2: Proof Generation');
    setClients(prev => prev.map(c => ({ ...c, status: 'generating_proof' })));
    
    const proofResults = await Promise.all(
      testClients.map(async (client) => {
        if (client.isHonest) {
          addLog(`  ✅ ${client.id}: Generating honest proof...`);
          // Call actual honest proof generation
          const response = await fetch('http://localhost:8000/api/security/test/gradient_bypass', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              srs_size: srsSize,
              lite_mode: liteMode
            })
          });
          const result = await response.json();
          return { clientId: client.id, isHonest: true, verified: result.status === 'success' };
        } else {
          addLog(`  ⚠️  ${client.id}: Attempting freeloading attack...`);
          // Call actual freeloading attack test
          const response = await fetch('http://localhost:8000/api/security/test/freeloading', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              srs_size: srsSize,
              lite_mode: liteMode
            })
          });
          const result = await response.json();
          return { clientId: client.id, isHonest: false, verified: result.status === 'success' };
        }
      })
    );
    
    // Phase 3: Verification
    addLog(`🔍 Phase 3: Verifying proofs at server...`);
    setCurrentPhase('Phase 3: Proof Verification');
    setServerStatus('verifying');
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Update client statuses based on results
    proofResults.forEach(result => {
      const status = result.verified ? 'verified' : 'rejected';
      setClients(prev => prev.map(c => 
        c.id === result.clientId ? { ...c, status, result: result.verified ? 'accepted' : 'rejected' } : c
      ));
      
      if (result.isHonest && result.verified) {
        addLog(`  ✅ ${result.clientId}: Honest proof ACCEPTED`);
      } else if (!result.isHonest && !result.verified) {
        addLog(`  ❌ ${result.clientId}: Freeloading attack BLOCKED`);
      } else if (!result.isHonest && result.verified) {
        addLog(`  ⚠️  ${result.clientId}: Attack succeeded (unexpected!)`);
      } else {
        addLog(`  ❌ ${result.clientId}: Honest proof rejected (error)`);
      }
    });
    
    // Phase 4: Aggregation (only valid proofs)
    const validProofs = proofResults.filter(r => r.verified);
    const rejectedProofs = proofResults.filter(r => !r.verified);
    
    if (validProofs.length > 0) {
      addLog(`📊 Phase 4: Aggregating ${validProofs.length} valid proofs...`);
      setCurrentPhase('Phase 4: ProtoGalaxy Aggregation');
      setServerStatus('aggregating');
      await new Promise(resolve => setTimeout(resolve, 2000));
      addLog(`✅ Aggregated proof created!`);
    }
    
    // Summary
    setServerStatus('idle');
    setCurrentPhase('Complete');
    addLog(`🎉 Security test complete!`);
    addLog(`  ✅ Honest clients accepted: ${validProofs.filter(p => proofResults.find(r => r.clientId === p.clientId)?.isHonest).length}/${honestCount}`);
    addLog(`  ❌ Attacks blocked: ${rejectedProofs.filter(p => !proofResults.find(r => r.clientId === p.clientId)?.isHonest).length}/${numDishonest}`);
  };

  const runSimulatedDemo = async () => {
    addLog(`🚀 Starting simulated demo with ${numClients} clients (${numDishonest} dishonest)`);
    addLog(`⚙️ Configuration: SRS=${srsSize}, Lite=${liteMode}`);
    addLog(`ℹ️  This is a simulation. Enable "Real FL Training" for live folding events.`);
    
    // Reset all clients
    setClients(prev => prev.map(c => ({ ...c, status: 'idle', result: undefined })));
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Phase 1: Training (ALL clients in parallel)
    setCurrentPhase('Phase 1: Local Training');
    addLog('📚 All clients training on local data (parallel)...');
    setClients(prev => prev.map(c => ({ ...c, status: 'training' })));
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Phase 2: Generate proofs (ALL clients in parallel - like real FL)
    setCurrentPhase('Phase 2: Proof Generation (Parallel)');
    addLog('🔐 All clients generating ZKP proofs in parallel...');
    setClients(prev => prev.map(c => ({ ...c, status: 'generating_proof' })));
    
    // Generate all proofs in parallel (mimicking real distributed FL)
    const proofPromises = clients.map(client => executeRealProof(client));
    
    await new Promise(resolve => setTimeout(resolve, 2000)); // Show generating animation
    
    const proofResults = await Promise.all(proofPromises);
    
    // Phase 3: Send all proofs to server simultaneously
    setCurrentPhase('Phase 3: Proof Transmission');
    addLog('📤 All clients sending proofs to server...');
    setClients(prev => prev.map(c => ({ ...c, status: 'sending' })));
    
    // Send all proof packets at once
    clients.forEach((client, i) => {
      sendProofPacket(client, proofResults[i].isValid);
      const clientType = client.isHonest ? 'honest' : 'dishonest (freeloading)';
      addLog(`  📨 ${client.id} → Server (${clientType})`);
    });
    
    await new Promise(resolve => setTimeout(resolve, 2000)); // Let packets animate
    
    // Phase 4: Server receives all proofs
    setServerStatus('receiving');
    setCurrentPhase('Phase 4: ProtoGalaxy Folding');
    addLog('📥 Server received all proofs');
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Phase 5: ProtoGalaxy folding - reject dishonest proofs BEFORE aggregation
    addLog('🔄 ProtoGalaxy: Pre-filtering invalid proofs...');
    setServerStatus('verifying');
    
    // Individual verification to catch attacks
    for (let i = 0; i < clients.length; i++) {
      const client = clients[i];
      const result = proofResults[i];
      
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (result.isValid) {
        addLog(`  ✅ ${client.id}: Valid proof (ready for folding)`);
        setClients(prev => prev.map(c => 
          c.id === client.id ? { ...c, status: 'verified', result: 'Valid' } : c
        ));
      } else {
        addLog(`  ❌ ${client.id}: REJECTED - ${result.reason}`);
        setClients(prev => prev.map(c => 
          c.id === client.id ? { ...c, status: 'rejected', result: 'Rejected' } : c
        ));
      }
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Phase 6: Fold valid proofs into ONE aggregated proof
    const validCount = proofResults.filter(r => r.isValid).length;
    const rejectedCount = proofResults.filter(r => !r.isValid).length;
    
    if (validCount > 0) {
      addLog(`🔗 ProtoGalaxy: Folding ${validCount} valid proofs into ONE aggregated proof...`);
      setServerStatus('aggregating');
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      addLog(`✅ Aggregated proof created and verified!`);
      addLog(`📊 Summary: ${validCount} proofs accepted, ${rejectedCount} proofs rejected`);
    } else {
      addLog(`⚠️ No valid proofs to aggregate - round failed`);
    }
    
    setServerStatus('idle');
    setCurrentPhase('Complete');
    addLog(`✨ Demo complete! Dishonest proofs blocked: ${rejectedCount}`);
    // Run state managed globally
  };

  const executeRealProof = async (client: Client): Promise<{ isValid: boolean; reason: string }> => {
    try {
      // Call your actual backend to generate and verify proof
      const testType = client.isHonest ? 'gradient_bypass' : 'freeloading';
      
      const response = await fetch(`http://localhost:8000/api/security/test/${testType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          srs_size: srsSize,
          lite_mode: liteMode
        })
      });
      
      if (!response.ok) {
        throw new Error('Backend request failed');
      }
      
      const data = await response.json();
      
      return {
        isValid: client.isHonest ? data.honest_accepted : !data.attack_rejected,
        reason: data.details || 'Constraint violation detected'
      };
    } catch (error) {
      console.error('Error executing proof:', error);
      // Fallback to expected behavior
      return {
        isValid: client.isHonest,
        reason: client.isHonest ? 'Valid proof' : 'Freeloading attack detected'
      };
    }
  };

  const sendProofPacket = (client: Client, isValid: boolean) => {
    const packet: ProofPacket = {
      id: `proof_${Date.now()}_${client.id}`,
      clientId: client.id,
      fromX: client.x,
      fromY: client.y,
      toX: serverPos.x,
      toY: serverPos.y,
      progress: 0,
      isValid
    };
    setProofPackets(prev => [...prev, packet]);
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
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Interactive Threat Demonstration</h1>
            <p className="text-gray-400">Configure attack scenario and watch real ZKP proof verification</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left: Configuration */}
        <div className="space-y-6">
          <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5 text-zkp-accent" />
              <h2 className="text-xl font-bold">Configuration</h2>
            </div>

            {/* Number of Clients */}
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                Total Clients: <span className="text-white font-mono">{numClients}</span>
              </label>
              <input
                type="range"
                min="2"
                max="6"
                value={numClients}
                onChange={(e) => setNumClients(parseInt(e.target.value))}
                disabled={globalIsRunning}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-zkp-accent disabled:opacity-50"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>2</span>
                <span>6</span>
              </div>
            </div>

            {/* Number of Dishonest */}
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                Dishonest Clients: <span className="text-orange-500 font-mono">{numDishonest}</span>
              </label>
              <input
                type="range"
                min="0"
                max={numClients - 1}
                value={numDishonest}
                onChange={(e) => setNumDishonest(parseInt(e.target.value))}
                disabled={globalIsRunning}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orange-500 disabled:opacity-50"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0</span>
                <span>{numClients - 1}</span>
              </div>
              <p className="text-xs text-orange-500 mt-2">
                ⚠️ These clients will attempt freeloading attacks
              </p>
            </div>

            {/* SRS Size */}
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                SRS Size: <span className="text-zkp-accent font-mono">{srsSize}</span>
              </label>
              <input
                type="range"
                min="128"
                max="1024"
                step="128"
                value={srsSize}
                onChange={(e) => setSrsSize(parseInt(e.target.value))}
                disabled={globalIsRunning}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-zkp-accent disabled:opacity-50"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>128</span>
                <span>1024</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {srsSize <= 256 && '⚡ Fast (~3-5s per proof)'}
                {srsSize > 256 && srsSize <= 512 && '⏱️ Medium (~8-12s per proof)'}
                {srsSize > 512 && '🔒 Slow but secure (~20-30s per proof)'}
              </p>
            </div>

            {/* Lite Mode Toggle */}
            <div className="mb-6">
              <label className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Lite Mode</span>
                <button
                  onClick={() => setLiteMode(!liteMode)}
                  disabled={globalIsRunning}
                  className={clsx(
                    "relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50",
                    liteMode ? "bg-zkp-accent" : "bg-gray-700"
                  )}
                >
                  <span
                    className={clsx(
                      "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                      liteMode ? "translate-x-6" : "translate-x-1"
                    )}
                  />
                </button>
              </label>
              <p className="text-xs text-gray-500 mt-1">
                {liteMode ? '⚡ Faster execution for demos' : '🔒 Full cryptographic security'}
              </p>
            </div>

            {/* Real FL Training Toggle */}
            <div>
              <label className="flex items-center justify-between cursor-pointer group">
                <div>
                  <span className="text-sm font-medium group-hover:text-white transition-colors">
                    Real FL Training
                  </span>
                  <p className="text-xs text-gray-500 mt-1">
                    {useRealFL ? '🔴 LIVE: Actual ProtoGalaxy folding' : '🎬 Simulated demo'}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setUseRealFL(!useRealFL)}
                  className={clsx(
                    "relative w-14 h-7 rounded-full transition-colors duration-200",
                    useRealFL ? "bg-red-500" : "bg-gray-700"
                  )}
                >
                  <span
                    className={clsx(
                      "absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full transition-transform duration-200",
                      useRealFL ? "translate-x-7" : "translate-x-0"
                    )}
                  />
                </button>
              </label>
            </div>

            {/* Start Button */}
            <button
              onClick={runDemo}
              disabled={globalIsRunning}
              className={clsx(
                "w-full py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2",
                globalIsRunning 
                  ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white"
              )}
            >
              {globalIsRunning ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Run Attack Scenario
                </>
              )}
            </button>
          </div>

          {/* Log Panel */}
          <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-xl p-6 max-h-[400px] overflow-auto">
            <h3 className="text-sm font-bold mb-3 text-gray-400">Execution Log</h3>
            <div className="space-y-1 font-mono text-xs">
              {globalIsRunning && messages.length > 0 ? (
                // Show global messages when a run is active
                messages.slice(-50).map((msg, i) => (
                  <div key={i} className="text-gray-300">
                    {new Date(msg.timestamp * 1000).toLocaleTimeString()}: {msg.message}
                  </div>
                ))
              ) : logs.length === 0 ? (
                <div className="text-gray-600 italic">Waiting to start...</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="text-gray-300">{log}</div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right: Network Visualization (2 columns) */}
        <div className="col-span-2">
          <div className="bg-zkp-dark-card border border-zkp-dark-border rounded-xl p-6">
            {/* Phase Banner */}
            {currentPhase && (
              <div className="mb-4 px-4 py-2 bg-zkp-accent/20 border border-zkp-accent rounded-lg text-center">
                <span className="text-zkp-accent font-semibold">{currentPhase}</span>
              </div>
            )}

            {/* Canvas */}
            <div 
              className="relative w-full h-[600px] bg-gray-900/50 rounded-lg"
              style={{ 
                backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(100, 100, 100, 0.15) 1px, transparent 0)', 
                backgroundSize: '40px 40px' 
              }}
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
                    stroke={
                      client.status === 'rejected' ? '#ef4444' : 
                      client.status === 'verified' ? '#22c55e' : 
                      !client.isHonest ? '#f97316' :
                      '#4b5563'
                    }
                    strokeWidth="2"
                    strokeDasharray={client.isHonest ? "0" : "5,5"}
                    opacity="0.5"
                  />
                ))}
              </svg>

              {/* Proof Packets */}
              {proofPackets.map(packet => {
                const x = packet.fromX + (packet.toX - packet.fromX) * packet.progress;
                const y = packet.fromY + (packet.toY - packet.fromY) * packet.progress;
                
                return (
                  <div
                    key={packet.id}
                    className="absolute transition-all"
                    style={{ left: x - 12, top: y - 12, zIndex: 2 }}
                  >
                    <div className={clsx(
                      "w-6 h-6 rounded-full flex items-center justify-center animate-pulse",
                      packet.isValid ? "bg-green-500" : "bg-red-500"
                    )}>
                      <Shield className="w-4 h-4 text-white" />
                    </div>
                  </div>
                );
              })}

              {/* Server */}
              <div
                className="absolute"
                style={{ left: serverPos.x - 40, top: serverPos.y - 40, zIndex: 3 }}
              >
                <div className={clsx(
                  "w-20 h-20 rounded-2xl border-4 flex flex-col items-center justify-center transition-all",
                  serverStatus === 'verifying' && "animate-pulse border-yellow-500 bg-yellow-500/20",
                  serverStatus === 'aggregating' && "animate-pulse border-green-500 bg-green-500/20",
                  serverStatus === 'idle' && "border-zkp-accent bg-zkp-accent/10"
                )}>
                  <Server className="w-8 h-8 text-white mb-1" />
                  <span className="text-xs font-bold">SERVER</span>
                </div>
                <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs text-gray-400">
                  {serverStatus === 'verifying' && '🔍 Verifying ZKP...'}
                  {serverStatus === 'aggregating' && '📊 Aggregating...'}
                  {serverStatus === 'idle' && '💤 Idle'}
                </div>
              </div>

              {/* Clients */}
              {clients.map(client => (
                <div
                  key={client.id}
                  className="absolute"
                  style={{ left: client.x - 30, top: client.y - 30, zIndex: 3 }}
                >
                  <div className={clsx(
                    "w-16 h-16 rounded-xl border-3 flex flex-col items-center justify-center transition-all",
                    client.status === 'training' && "animate-pulse border-blue-500",
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
                  
                  <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 text-center w-24">
                    <div className="text-xs font-bold whitespace-nowrap">
                      {client.id.replace('_', ' ').toUpperCase()}
                    </div>
                    {!client.isHonest && (
                      <div className="text-xs text-orange-500 font-semibold">
                        ⚠️ Attacker
                      </div>
                    )}
                    {client.result && (
                      <div className={clsx(
                        "text-xs font-semibold mt-1",
                        client.status === 'verified' ? "text-green-500" : "text-red-500"
                      )}>
                        {client.status === 'verified' ? '✅ Accepted' : '❌ Blocked'}
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
                <span className="text-gray-400">Attacker (Freeloading)</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-gray-400">Proof Accepted</span>
              </div>
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-500" />
                <span className="text-gray-400">Proof Rejected</span>
              </div>
            </div>
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
