import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  GitCompare, 
  ChevronDown,
  TrendingUp,
  TrendingDown,
  Shield,
  Loader2,
  AlertCircle,
  Layers
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from 'recharts';
import clsx from 'clsx';
import { Run, RunComparison as RunComparisonType, RunDetails } from '../types';

// Extended type for full training results
interface TrainingResults {
  rounds: {
    round_number: number;
    avg_accuracy: number;
    avg_loss: number;
    avg_proof_time: number;
    round_time: number;
    avg_proof_size?: number;
    aggregated_ec_operations?: number;
  }[];
  summary?: {
    final_accuracy: number;
    avg_time_per_round: number;
    total_proofs_generated: number;
  };
}

// Color palette for multiple runs
const RUN_COLORS = [
  '#6366f1', // primary - indigo
  '#8b5cf6', // secondary - violet
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f59e0b', // amber
  '#22c55e', // green
  '#3b82f6', // blue
  '#ef4444', // red
];

export default function RunComparison() {
  const [searchParams] = useSearchParams();
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun1, setSelectedRun1] = useState<string>('');
  const [selectedRun2, setSelectedRun2] = useState<string>('');
  const [comparison, setComparison] = useState<RunComparisonType | null>(null);
  const [run1Details, setRun1Details] = useState<RunDetails | null>(null);
  const [, setRun2Details] = useState<RunDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isComparing, setIsComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // NEW: Compare All mode state
  const [compareAllMode, setCompareAllMode] = useState(false);
  const [allRunsDetails, setAllRunsDetails] = useState<Map<string, TrainingResults>>(new Map());
  const [highlightedRun, setHighlightedRun] = useState<string>('');

  // Fetch runs on mount
  useEffect(() => {
    let isMounted = true;
    
    const loadRuns = async () => {
      try {
        console.log('RunComparison: Fetching runs...');
        const response = await fetch('/api/runs');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        console.log('RunComparison: Got runs:', data);
        
        if (!isMounted) return;
        
        const runsArray = Array.isArray(data) ? data : [];
        setRuns(runsArray);
        
        // Prefer completed runs for auto-selection
        const completedRuns = runsArray.filter((r: Run) => r.status === 'completed');
        const availableRuns = completedRuns.length >= 2 ? completedRuns : runsArray;
        
        // Check URL params first
        const run1Param = searchParams.get('run1');
        const run2Param = searchParams.get('run2');
        
        if (run1Param) {
          setSelectedRun1(run1Param);
          if (run2Param) {
            setSelectedRun2(run2Param);
          } else if (availableRuns.length >= 2) {
            const otherRun = availableRuns.find((r: Run) => r.run_id !== run1Param);
            if (otherRun) setSelectedRun2(otherRun.run_id);
          }
        } else if (availableRuns.length >= 2) {
          setSelectedRun1(availableRuns[0].run_id);
          setSelectedRun2(availableRuns[1].run_id);
        } else if (availableRuns.length === 1) {
          setSelectedRun1(availableRuns[0].run_id);
        }
        
        setError(null);
      } catch (err) {
        console.error('RunComparison: Fetch error:', err);
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
  }, [searchParams]);

  // Fetch comparison when selections change
  useEffect(() => {
    const fetchComparison = async () => {
      if (selectedRun1 && selectedRun2) {
        setIsComparing(true);
        try {
          const [compRes, run1Res, run2Res] = await Promise.all([
            fetch(`/api/runs/${selectedRun1}/compare/${selectedRun2}`),
            fetch(`/api/runs/${selectedRun1}`),
            fetch(`/api/runs/${selectedRun2}`)
          ]);
          if (compRes.ok) setComparison(await compRes.json());
          if (run1Res.ok) setRun1Details(await run1Res.json());
          if (run2Res.ok) setRun2Details(await run2Res.json());
        } catch (err) {
          console.error('Failed to fetch comparison:', err);
        } finally {
          setIsComparing(false);
        }
      } else if (selectedRun1) {
        try {
          const res = await fetch(`/api/runs/${selectedRun1}`);
          if (res.ok) setRun1Details(await res.json());
          setRun2Details(null);
          setComparison(null);
        } catch (err) {
          console.error('Failed to fetch run details:', err);
        }
      }
    };
    
    fetchComparison();
  }, [selectedRun1, selectedRun2]);

  // NEW: Fetch all runs training results for "Compare All" mode
  const fetchAllRunsDetails = useCallback(async () => {
    if (!compareAllMode || runs.length === 0) return;
    
    setIsComparing(true);
    const details = new Map<string, TrainingResults>();
    
    try {
      const completedRuns = runs.filter(r => r.status === 'completed');
      const fetchPromises = completedRuns.map(async (run) => {
        try {
          const res = await fetch(`/api/runs/${run.run_id}/training-results`);
          if (res.ok) {
            const data = await res.json();
            details.set(run.run_id, data);
          }
        } catch (err) {
          console.error(`Failed to fetch training results for ${run.run_id}:`, err);
        }
      });
      
      await Promise.all(fetchPromises);
      setAllRunsDetails(details);
      
      // Auto-select first run as highlighted if not set
      if (!highlightedRun && completedRuns.length > 0) {
        setHighlightedRun(completedRuns[0].run_id);
      }
    } finally {
      setIsComparing(false);
    }
  }, [compareAllMode, runs, highlightedRun]);

  useEffect(() => {
    fetchAllRunsDetails();
  }, [fetchAllRunsDetails]);

  // Prepare chart data - use null for missing rounds so chart doesn't plot them
  const roundsChartData = comparison?.rounds_comparison.map(r => {
    const run1Data = r[selectedRun1] as { accuracy: number } | undefined;
    const run2Data = r[selectedRun2] as { accuracy: number } | undefined;
    return {
      round: `Round ${r.round}`,
      [selectedRun1.slice(-15)]: run1Data ? run1Data.accuracy * 100 : null,
      [selectedRun2.slice(-15)]: run2Data ? run2Data.accuracy * 100 : null,
    };
  }) || [];

  const metricsChartData = comparison ? [
    {
      metric: 'Accuracy',
      [selectedRun1.slice(-15)]: (comparison.metrics_comparison.final_accuracy[selectedRun1] || 0) * 100,
      [selectedRun2.slice(-15)]: (comparison.metrics_comparison.final_accuracy[selectedRun2] || 0) * 100,
    },
    {
      metric: 'Loss',
      [selectedRun1.slice(-15)]: (comparison.metrics_comparison.final_loss[selectedRun1] || 0) * 10,
      [selectedRun2.slice(-15)]: (comparison.metrics_comparison.final_loss[selectedRun2] || 0) * 10,
    },
    {
      metric: 'Time (min)',
      [selectedRun1.slice(-15)]: (comparison.metrics_comparison.total_time[selectedRun1] || 0) / 60,
      [selectedRun2.slice(-15)]: (comparison.metrics_comparison.total_time[selectedRun2] || 0) / 60,
    }
  ] : [];

  // NEW: Prepare "Compare All" chart data
  const allRunsChartData = compareAllMode ? (() => {
    const maxRounds = Math.max(...Array.from(allRunsDetails.values()).map(d => d.rounds?.length || 0));
    const data: Array<Record<string, number | string | null>> = [];
    
    for (let i = 0; i < maxRounds; i++) {
      const roundData: Record<string, number | string | null> = { round: `Round ${i + 1}` };
      allRunsDetails.forEach((details, runId) => {
        const roundInfo = details.rounds?.[i];
        if (roundInfo) {
          roundData[runId.slice(-12)] = (roundInfo.avg_accuracy || 0) * 100;
        } else {
          roundData[runId.slice(-12)] = null;
        }
      });
      data.push(roundData);
    }
    return data;
  })() : [];

  // NEW: Proof timing chart data
  const proofTimingChartData = compareAllMode ? (() => {
    const data: Array<{name: string; proofTime: number; roundTime: number; runId: string}> = [];
    allRunsDetails.forEach((details, runId) => {
      const avgProofTime = details.rounds?.reduce((sum, r) => sum + (r.avg_proof_time || 0), 0) / (details.rounds?.length || 1);
      const avgRoundTime = details.rounds?.reduce((sum, r) => sum + (r.round_time || 0), 0) / (details.rounds?.length || 1);
      data.push({
        name: runId.slice(-12),
        proofTime: avgProofTime || 0,
        roundTime: avgRoundTime || 0,
        runId
      });
    });
    return data;
  })() : (comparison ? [
    {
      name: selectedRun1.slice(-12),
      proofTime: 0,
      roundTime: (comparison.metrics_comparison.total_time[selectedRun1] || 0) / 3,
      runId: selectedRun1
    },
    {
      name: selectedRun2.slice(-12),
      proofTime: 0,
      roundTime: (comparison.metrics_comparison.total_time[selectedRun2] || 0) / 3,
      runId: selectedRun2
    }
  ] : []);

  if (error) {
    return (
      <div className="p-6">
        <div className="flex flex-col items-center justify-center py-12 gap-4">
          <AlertCircle className="w-12 h-12 text-zkp-error" />
          <p className="text-zkp-error">Error: {error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-zkp-primary rounded-lg text-white"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Debug info
  console.log('RunComparison render:', { 
    runsCount: runs.length, 
    selectedRun1, 
    selectedRun2, 
    isLoading,
    hasComparison: !!comparison,
    hasRun1Details: !!run1Details 
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Run Comparison</h1>
          <p className="text-gray-400">Compare metrics and performance across different runs</p>
        </div>
        
        {/* Compare All Toggle */}
        <button
          onClick={() => setCompareAllMode(!compareAllMode)}
          className={clsx(
            "flex items-center gap-2 px-4 py-2 rounded-lg transition-colors",
            compareAllMode 
              ? "bg-zkp-primary text-white" 
              : "bg-zkp-dark-card border border-zkp-dark-border text-gray-400 hover:text-white"
          )}
        >
          <Layers className="w-4 h-4" />
          Compare All Runs
        </button>
      </div>

      {/* Compare All Mode - Highlighted Run Selector */}
      {compareAllMode && (
        <div className="bg-zkp-dark-card rounded-xl border border-zkp-primary/50 p-4">
          <label className="block text-sm font-medium text-zkp-primary mb-2">
            Highlighted Run (vs all others)
          </label>
          <div className="relative">
            <select
              value={highlightedRun}
              onChange={(e) => setHighlightedRun(e.target.value)}
              className="w-full px-4 py-2 bg-zkp-dark-bg rounded-lg border border-zkp-primary text-white appearance-none focus:outline-none focus:ring-2 focus:ring-zkp-primary"
            >
              <option value="">Select highlighted run...</option>
              {runs
                .filter(r => r.status === 'completed')
                .map(run => (
                  <option key={run.run_id} value={run.run_id}>
                    {run.run_id}
                  </option>
                ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {allRunsDetails.size} runs loaded for comparison
          </p>
        </div>
      )}

      {/* Normal Mode - Run Selectors */}
      {!compareAllMode && (
        <div className="grid grid-cols-2 gap-4">
          <RunSelector
            label="First Run"
            runs={runs}
            selectedId={selectedRun1}
            onChange={setSelectedRun1}
            excludeId={selectedRun2}
            color="primary"
          />
          <RunSelector
            label="Second Run"
            runs={runs}
            selectedId={selectedRun2}
            onChange={setSelectedRun2}
            excludeId={selectedRun1}
            color="secondary"
          />
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-zkp-primary" />
          <span className="ml-3 text-gray-400">Loading runs...</span>
        </div>
      )}

      {/* Loading comparison */}
      {!isLoading && isComparing && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-zkp-secondary" />
          <span className="ml-3 text-gray-400">Loading comparison data...</span>
        </div>
      )}

      {/* ===================== COMPARE ALL MODE ===================== */}
      {!isLoading && !isComparing && compareAllMode && allRunsDetails.size > 0 && (
        <>
          {/* All Runs Accuracy Over Rounds */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
            <h3 className="font-semibold text-white mb-4">
              Accuracy Over Rounds - All Runs
              {highlightedRun && (
                <span className="ml-2 text-sm text-zkp-primary">
                  (Highlighted: {highlightedRun.slice(-12)})
                </span>
              )}
            </h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={allRunsChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="round" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                  formatter={(value: number) => [`${value?.toFixed(1)}%`, 'Accuracy']}
                />
                <Legend />
                {Array.from(allRunsDetails.keys()).map((runId, idx) => (
                  <Line 
                    key={runId}
                    type="monotone" 
                    dataKey={runId.slice(-12)} 
                    stroke={runId === highlightedRun ? '#f59e0b' : RUN_COLORS[idx % RUN_COLORS.length]}
                    strokeWidth={runId === highlightedRun ? 3 : 1.5}
                    dot={runId === highlightedRun ? { fill: '#f59e0b', r: 4 } : false}
                    opacity={runId === highlightedRun ? 1 : 0.6}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Proof Timing Comparison */}
            <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
              <h3 className="font-semibold text-white mb-4">Average Proof Generation Time (seconds)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={proofTimingChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} angle={-45} textAnchor="end" height={60} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => [`${value?.toFixed(2)}s`, 'Proof Time']}
                  />
                  <Bar 
                    dataKey="proofTime" 
                    fill="#8b5cf6"
                    radius={[4, 4, 0, 0]}
                  >
                    {proofTimingChartData.map((entry, index) => (
                      <Cell
                        key={`bar-${index}`}
                        fill={entry.runId === highlightedRun ? '#f59e0b' : RUN_COLORS[index % RUN_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Round Time Comparison */}
            <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
              <h3 className="font-semibold text-white mb-4">Average Round Time (seconds)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={proofTimingChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} angle={-45} textAnchor="end" height={60} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => [`${value?.toFixed(1)}s`, 'Round Time']}
                  />
                  <Bar 
                    dataKey="roundTime" 
                    fill="#6366f1"
                    radius={[4, 4, 0, 0]}
                  >
                    {proofTimingChartData.map((entry, index) => (
                      <Cell
                        key={`bar-${index}`}
                        fill={entry.runId === highlightedRun ? '#f59e0b' : RUN_COLORS[index % RUN_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Final Accuracy Comparison Bar */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
            <h3 className="font-semibold text-white mb-4">Final Accuracy Comparison</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart 
                data={Array.from(allRunsDetails.entries()).map(([runId, details], idx) => ({
                  name: runId.slice(-12),
                  accuracy: (details.summary?.final_accuracy || details.rounds?.[details.rounds.length - 1]?.avg_accuracy || 0) * 100,
                  runId,
                  color: runId === highlightedRun ? '#f59e0b' : RUN_COLORS[idx % RUN_COLORS.length]
                }))}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" fontSize={12} />
                <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={10} width={100} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                  formatter={(value: number) => [`${value?.toFixed(1)}%`, 'Accuracy']}
                />
                <Bar 
                  dataKey="accuracy" 
                  radius={[0, 4, 4, 0]}
                >
                  {Array.from(allRunsDetails.entries()).map(([runId], index) => (
                    <Cell
                      key={`bar-${index}`}
                      fill={runId === highlightedRun ? '#f59e0b' : RUN_COLORS[index % RUN_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Summary Stats Table */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
            <h3 className="font-semibold text-white mb-4">All Runs Summary</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zkp-dark-border">
                    <th className="text-left py-2 px-3 text-gray-400">Run ID</th>
                    <th className="text-right py-2 px-3 text-gray-400">Final Accuracy</th>
                    <th className="text-right py-2 px-3 text-gray-400">Avg Proof Time</th>
                    <th className="text-right py-2 px-3 text-gray-400">Avg Round Time</th>
                    <th className="text-right py-2 px-3 text-gray-400">Total Proofs</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from(allRunsDetails.entries()).map(([runId, details]) => {
                    const avgProofTime = details.rounds?.reduce((sum, r) => sum + (r.avg_proof_time || 0), 0) / (details.rounds?.length || 1);
                    const avgRoundTime = details.rounds?.reduce((sum, r) => sum + (r.round_time || 0), 0) / (details.rounds?.length || 1);
                    const finalAcc = details.summary?.final_accuracy || details.rounds?.[details.rounds.length - 1]?.avg_accuracy || 0;
                    
                    return (
                      <tr 
                        key={runId} 
                        className={clsx(
                          "border-b border-zkp-dark-border/50",
                          runId === highlightedRun && "bg-amber-500/10"
                        )}
                      >
                        <td className={clsx(
                          "py-2 px-3 font-mono text-xs",
                          runId === highlightedRun ? "text-amber-400 font-semibold" : "text-white"
                        )}>
                          {runId.slice(-20)}
                          {runId === highlightedRun && <span className="ml-2">⭐</span>}
                        </td>
                        <td className="text-right py-2 px-3 text-zkp-success">{(finalAcc * 100).toFixed(1)}%</td>
                        <td className="text-right py-2 px-3 text-white">{avgProofTime?.toFixed(2)}s</td>
                        <td className="text-right py-2 px-3 text-white">{avgRoundTime?.toFixed(1)}s</td>
                        <td className="text-right py-2 px-3 text-gray-400">{details.summary?.total_proofs_generated || '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Compare All - No Data */}
      {!isLoading && !isComparing && compareAllMode && allRunsDetails.size === 0 && (
        <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-12 text-center">
          <Layers className="w-12 h-12 mx-auto mb-4 text-gray-500" />
          <h3 className="text-lg font-semibold text-white mb-2">No Completed Runs</h3>
          <p className="text-gray-400">Complete some runs to compare them in "Compare All" mode.</p>
        </div>
      )}

      {/* ===================== NORMAL TWO-RUN COMPARISON ===================== */}
      {/* Comparison Content */}
      {!isLoading && !isComparing && !compareAllMode && comparison && (
        <>
          {/* Check if metrics are available */}
          {Object.keys(comparison.metrics_comparison).length === 0 ? (
            <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-8 text-center">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
              <h3 className="text-lg font-semibold text-white mb-2">Metrics Not Yet Available</h3>
              <p className="text-gray-400">
                The selected runs are still in progress or haven't completed successfully.
                Metrics will appear once the runs finish.
              </p>
              <div className="mt-4 grid grid-cols-2 gap-4 text-left">
                <div className="bg-zkp-dark-bg rounded-lg p-4">
                  <p className="text-sm text-gray-400 mb-2">Run 1: {selectedRun1}</p>
                  <p className="text-xs text-gray-500">Status: {runs.find(r => r.run_id === selectedRun1)?.status || 'unknown'}</p>
                </div>
                <div className="bg-zkp-dark-bg rounded-lg p-4">
                  <p className="text-sm text-gray-400 mb-2">Run 2: {selectedRun2}</p>
                  <p className="text-xs text-gray-500">Status: {runs.find(r => r.run_id === selectedRun2)?.status || 'unknown'}</p>
                </div>
              </div>
            </div>
          ) : (
          <>
          {/* Quick Comparison Cards */}
          <div className="grid grid-cols-3 gap-4">
            <ComparisonCard
              label="Final Accuracy"
              value1={comparison.metrics_comparison.final_accuracy?.[selectedRun1] ?? 0}
              value2={comparison.metrics_comparison.final_accuracy?.[selectedRun2] ?? 0}
              format={(v) => `${(v * 100).toFixed(1)}%`}
              higherIsBetter
            />
            <ComparisonCard
              label="Final Loss"
              value1={comparison.metrics_comparison.final_loss?.[selectedRun1] ?? 0}
              value2={comparison.metrics_comparison.final_loss?.[selectedRun2] ?? 0}
              format={(v) => v.toFixed(4)}
              higherIsBetter={false}
            />
            <ComparisonCard
              label="Total Time"
              value1={comparison.metrics_comparison.total_time?.[selectedRun1] ?? 0}
              value2={comparison.metrics_comparison.total_time?.[selectedRun2] ?? 0}
              format={(v) => `${(v / 60).toFixed(1)} min`}
              higherIsBetter={false}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2 gap-4">
            {/* Accuracy Over Rounds */}
            <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
              <h3 className="font-semibold text-white mb-4">Accuracy Over Rounds</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={roundsChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="round" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 100]} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey={selectedRun1.slice(-15)} 
                    stroke="#6366f1" 
                    strokeWidth={2}
                    dot={{ fill: '#6366f1' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey={selectedRun2.slice(-15)} 
                    stroke="#8b5cf6" 
                    strokeWidth={2}
                    dot={{ fill: '#8b5cf6' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Final Metrics Bar Chart */}
            <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
              <h3 className="font-semibold text-white mb-4">Final Metrics Comparison</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={metricsChartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" stroke="#94a3b8" fontSize={12} />
                  <YAxis type="category" dataKey="metric" stroke="#94a3b8" fontSize={12} width={80} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Bar dataKey={selectedRun1.slice(-15)} fill="#6366f1" radius={[0, 4, 4, 0]} />
                  <Bar dataKey={selectedRun2.slice(-15)} fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Config Comparison */}
          <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
            <h3 className="font-semibold text-white mb-4">Configuration Comparison</h3>
            <div className="grid grid-cols-2 gap-4">
              <ConfigTable config={comparison.configs[0]} label={selectedRun1} />
              <ConfigTable config={comparison.configs[1]} label={selectedRun2} />
            </div>
          </div>
          </>
          )}
        </>
      )}

      {/* Single Run View */}
      {!isLoading && !isComparing && !comparison && run1Details && (
        <SingleRunView run={run1Details} />
      )}

      {/* Both runs selected but no comparison yet */}
      {!isLoading && !isComparing && !comparison && selectedRun1 && selectedRun2 && (
        <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-8 text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
          <h3 className="text-lg font-semibold text-white mb-2">Comparison Data Unavailable</h3>
          <p className="text-gray-400">
            Could not load comparison between the selected runs.
            Try selecting different runs or check if the backend is running.
          </p>
        </div>
      )}

      {/* No runs selected */}
      {!isLoading && !selectedRun1 && runs.length > 0 && (
        <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-12 text-center">
          <GitCompare className="w-12 h-12 mx-auto mb-4 text-gray-500" />
          <p className="text-gray-400">Select runs to compare</p>
        </div>
      )}

      {/* No runs available */}
      {runs.length === 0 && !isLoading && (
        <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-12 text-center">
          <Shield className="w-12 h-12 mx-auto mb-4 text-gray-500" />
          <h3 className="text-lg font-semibold text-white mb-2">No Runs Available</h3>
          <p className="text-gray-400">Start a new run from the Run Control page to see results here.</p>
        </div>
      )}
    </div>
  );
}

interface RunSelectorProps {
  label: string;
  runs: Run[];
  selectedId: string;
  onChange: (id: string) => void;
  excludeId: string;
  color: 'primary' | 'secondary';
}

function RunSelector({ label, runs, selectedId, onChange, excludeId, color }: RunSelectorProps) {
  const colorClasses = {
    primary: 'border-zkp-primary focus:ring-zkp-primary',
    secondary: 'border-zkp-secondary focus:ring-zkp-secondary'
  };

  // Helper to get config value (handles nested config.configuration)
  const getConfigValue = (run: Run, key: string): number => {
    const config = run.config as Record<string, unknown>;
    if (!config) return 0;
    // Check nested configuration first
    const nested = config.configuration as Record<string, unknown> | undefined;
    if (nested && key in nested) {
      return (nested[key] as number) || 0;
    }
    // Fallback to top-level
    return (config[key] as number) || 0;
  };

  return (
    <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
      <label className="block text-sm font-medium text-gray-400 mb-2">{label}</label>
      <div className="relative">
        <select
          value={selectedId}
          onChange={(e) => onChange(e.target.value)}
          className={clsx(
            "w-full px-4 py-2 bg-zkp-dark-bg rounded-lg border appearance-none focus:outline-none focus:ring-2",
            colorClasses[color],
            "text-white"
          )}
        >
          <option value="">Select a run...</option>
          {runs
            .filter(r => r.run_id !== excludeId)
            .map(run => (
              <option key={run.run_id} value={run.run_id}>
                {run.run_id} ({run.status})
              </option>
            ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
      </div>
      {selectedId && (
        <div className="mt-2 text-xs text-gray-400">
          {getConfigValue(runs.find(r => r.run_id === selectedId)!, 'num_clients')} clients, 
          {' '}{getConfigValue(runs.find(r => r.run_id === selectedId)!, 'num_rounds')} rounds
        </div>
      )}
    </div>
  );
}

interface ComparisonCardProps {
  label: string;
  value1: number;
  value2: number;
  format: (v: number) => string;
  higherIsBetter: boolean;
}

function ComparisonCard({ label, value1, value2, format, higherIsBetter }: ComparisonCardProps) {
  const diff = value1 - value2;
  const isBetter = higherIsBetter ? diff > 0 : diff < 0;
  const isWorse = higherIsBetter ? diff < 0 : diff > 0;

  return (
    <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
      <p className="text-sm text-gray-400 mb-2">{label}</p>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-zkp-primary">{format(value1 || 0)}</p>
          <p className="text-lg text-zkp-secondary">{format(value2 || 0)}</p>
        </div>
        {Math.abs(diff) > 0.0001 && (
          <div className={clsx(
            "flex items-center gap-1 text-sm px-2 py-1 rounded",
            isBetter && "bg-zkp-success/20 text-zkp-success",
            isWorse && "bg-zkp-error/20 text-zkp-error"
          )}>
            {isBetter ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            {format(Math.abs(diff))}
          </div>
        )}
      </div>
    </div>
  );
}

interface ConfigTableProps {
  config: Record<string, unknown>;
  label: string;
}

function ConfigTable({ config, label }: ConfigTableProps) {
  return (
    <div className="bg-zkp-dark-bg rounded-lg p-4">
      <p className="text-sm font-medium text-gray-400 mb-3 truncate">{label}</p>
      <div className="space-y-2 text-sm">
        {Object.entries(config || {}).map(([key, value]) => (
          <div key={key} className="flex justify-between">
            <span className="text-gray-400">{key}</span>
            <span className="text-white font-mono">{String(value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface SingleRunViewProps {
  run: RunDetails;
}

function SingleRunView({ run }: SingleRunViewProps) {
  return (
    <div className="space-y-4">
      <div className="bg-zkp-dark-card rounded-xl border border-zkp-dark-border p-4">
        <h3 className="font-semibold text-white mb-4">Run Details: {run.run_id}</h3>
        
        {/* Rounds */}
        {run.rounds && run.rounds.length > 0 && (
          <div className="space-y-3">
            {run.rounds.map((round, idx) => (
              <div key={idx} className="bg-zkp-dark-bg rounded-lg p-3">
                <p className="text-sm font-medium text-white mb-2">Round {round.round_number}</p>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {round.clients.map((client, cidx) => (
                    <div key={cidx} className="flex items-center gap-2">
                      <Shield className={clsx(
                        "w-3 h-3",
                        client.proof_verified ? "text-zkp-success" : "text-zkp-error"
                      )} />
                      <span className="text-gray-400">{client.client_id}</span>
                      <span className="text-white">{(client.accuracy * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
