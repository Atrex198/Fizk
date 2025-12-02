import { useState, useCallback } from 'react';
import { Run, RunDetails, RunConfig, RunComparison, DashboardStatus } from '../types';

const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : '';

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = useCallback(async (): Promise<Run[]> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/runs`);
      if (!response.ok) throw new Error('Failed to fetch runs');
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRunDetails = useCallback(async (runId: string): Promise<RunDetails | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/runs/${runId}`);
      if (!response.ok) throw new Error(`Failed to fetch run ${runId}`);
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const compareRuns = useCallback(async (runId1: string, runId2: string): Promise<RunComparison | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/runs/${runId1}/compare/${runId2}`);
      if (!response.ok) throw new Error('Failed to compare runs');
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const startRun = useCallback(async (config: RunConfig): Promise<{ run_id: string } | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/runs/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start run');
      }
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const stopRun = useCallback(async (): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/runs/stop`, {
        method: 'POST'
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to stop run');
      }
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const getStatus = useCallback(async (): Promise<DashboardStatus | null> => {
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      return data;
    } catch (err) {
      return null;
    }
  }, []);

  const fetchRunLogs = useCallback(async (runId: string): Promise<string[]> => {
    try {
      const response = await fetch(`${API_BASE}/api/runs/${runId}/logs`);
      if (!response.ok) throw new Error('Failed to fetch logs');
      const data = await response.json();
      return data.logs || [];
    } catch (err) {
      return [];
    }
  }, []);

  return {
    loading,
    error,
    fetchRuns,
    fetchRunDetails,
    compareRuns,
    startRun,
    stopRun,
    getStatus,
    fetchRunLogs
  };
}
