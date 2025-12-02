import { useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { 
  Activity, 
  BarChart3, 
  GitCompare, 
  Play, 
  Settings,
  Shield,
  Wifi,
  WifiOff
} from 'lucide-react';
import clsx from 'clsx';

import { useWebSocket } from './hooks/useWebSocket';
import { useApi } from './hooks/useApi';
import { RunConfig } from './types';

import Overview from './components/Overview';
import LiveView from './components/LiveView';
import RunComparison from './components/RunComparison';
import RunControl from './components/RunControl';
import RunDetails from './components/RunDetails';

function App() {
  const { connected, messages, events, status } = useWebSocket();
  const { loading, error, startRun, stopRun } = useApi();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleStartRun = useCallback(async (config: RunConfig) => {
    const result = await startRun(config);
    if (result) {
      console.log('Run started:', result.run_id);
    }
  }, [startRun]);

  const handleStopRun = useCallback(async () => {
    const success = await stopRun();
    if (success) {
      console.log('Run stopped');
    }
  }, [stopRun]);

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-zkp-dark-bg">
        {/* Sidebar */}
        <aside 
          className={clsx(
            "flex flex-col bg-zkp-dark-card border-r border-zkp-dark-border transition-all duration-300",
            sidebarCollapsed ? "w-16" : "w-64"
          )}
        >
          {/* Logo */}
          <div className="flex items-center gap-3 p-4 border-b border-zkp-dark-border">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-zkp-primary to-zkp-secondary flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            {!sidebarCollapsed && (
              <div>
                <h1 className="font-bold text-white">ZKP-FL</h1>
                <p className="text-xs text-gray-400">Dashboard</p>
              </div>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            <NavItem to="/" icon={<Activity />} label="Overview" collapsed={sidebarCollapsed} />
            <NavItem to="/live" icon={<BarChart3 />} label="Live View" collapsed={sidebarCollapsed} />
            <NavItem to="/compare" icon={<GitCompare />} label="Compare" collapsed={sidebarCollapsed} />
            <NavItem to="/control" icon={<Play />} label="Run Control" collapsed={sidebarCollapsed} />
          </nav>

          {/* Connection Status */}
          <div className="p-4 border-t border-zkp-dark-border">
            <div className={clsx(
              "flex items-center gap-2 text-sm",
              connected ? "text-zkp-success" : "text-zkp-error"
            )}>
              {connected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              {!sidebarCollapsed && (
                <span>{connected ? 'Connected' : 'Disconnected'}</span>
              )}
            </div>
            {status?.is_running && !sidebarCollapsed && (
              <div className="mt-2 flex items-center gap-2 text-sm text-zkp-accent">
                <div className="w-2 h-2 rounded-full bg-zkp-accent live-indicator" />
                <span>Run in progress</span>
              </div>
            )}
          </div>

          {/* Collapse Toggle */}
          <button 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-4 border-t border-zkp-dark-border hover:bg-zkp-dark-border/50 transition-colors"
          >
            <Settings className={clsx(
              "w-5 h-5 text-gray-400 transition-transform",
              sidebarCollapsed && "rotate-180"
            )} />
          </button>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/runs/:runId" element={<RunDetails />} />
            <Route 
              path="/live" 
              element={
                <LiveView 
                  messages={messages} 
                  events={events} 
                  isRunning={status?.is_running || false}
                  currentRun={status?.current_run || null}
                />
              } 
            />
            <Route path="/compare" element={<RunComparison />} />
            <Route 
              path="/control" 
              element={
                <RunControl 
                  isRunning={status?.is_running || false}
                  currentRun={status?.current_run || null}
                  onStart={handleStartRun}
                  onStop={handleStopRun}
                  loading={loading}
                  error={error}
                />
              } 
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  collapsed: boolean;
}

function NavItem({ to, icon, label, collapsed }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => clsx(
        "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
        isActive 
          ? "bg-zkp-primary/20 text-zkp-primary" 
          : "text-gray-400 hover:text-white hover:bg-zkp-dark-border/50",
        collapsed && "justify-center"
      )}
    >
      <span className="w-5 h-5">{icon}</span>
      {!collapsed && <span className="font-medium">{label}</span>}
    </NavLink>
  );
}

export default App;
