import { useState, useEffect, useCallback, useRef } from 'react';
import { WSMessage, LogMessage, CryptoEvent, DashboardStatus } from '../types';

const WS_URL = import.meta.env.DEV ? 'ws://localhost:8000/ws' : `ws://${window.location.host}/ws`;

interface UseWebSocketReturn {
  connected: boolean;
  messages: LogMessage[];
  events: CryptoEvent[];
  status: DashboardStatus | null;
  send: (data: object) => void;
  clearMessages: () => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<LogMessage[]>([]);
  const [events, setEvents] = useState<CryptoEvent[]>([]);
  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      wsRef.current = null;

      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('Attempting to reconnect...');
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const data: WSMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'connection_established':
            setStatus({
              is_running: data.is_running as boolean,
              current_run: data.current_run as DashboardStatus['current_run'],
              connected_clients: 1
            });
            break;

          case 'log':
            const logMsg = data as LogMessage;
            setMessages(prev => [...prev.slice(-500), logMsg]); // Keep last 500 messages
            if (logMsg.event && logMsg.event.type !== 'log') {
              setEvents(prev => [...prev.slice(-100), logMsg.event]); // Keep last 100 events
            }
            break;

          case 'run_started':
            setStatus(prev => prev ? {
              ...prev,
              is_running: true,
              current_run: {
                run_id: data.run_id as string,
                config: data.config as DashboardStatus['current_run'] extends null ? never : NonNullable<DashboardStatus['current_run']>['config'],
                status: 'running',
                start_time: Date.now() / 1000
              }
            } : null);
            setMessages([]); // Clear messages for new run
            setEvents([]);
            break;

          case 'run_completed':
          case 'run_stopped':
          case 'run_error':
            setStatus(prev => prev ? {
              ...prev,
              is_running: false,
              current_run: null
            } : null);
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();

    // Ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setEvents([]);
  }, []);

  return { connected, messages, events, status, send, clearMessages };
}
