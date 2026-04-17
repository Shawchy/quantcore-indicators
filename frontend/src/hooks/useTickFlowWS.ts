/**
 * TickFlow WebSocket Hook (useTickFlowWS)
 * 
 * 专门用于连接TickFlow实时行情WebSocket的React Hook。
 * 
 * 特性：
 * - 自动重连机制
 * - 智能订阅管理（去重、批量）
 * - 心跳保活
 * - 与useSmartPolling无缝切换（降级方案）
 * - 完整的类型支持
 * 
 * 使用示例：
 * ```tsx
 * function RealtimeQuotes() {
 *   const { 
 *     quotes,           // 行情数据 {code: quoteData}
 *     isConnected,      // 连接状态
 *     subscribe,        // 订阅函数
 *     unsubscribe,      // 退订函数
 *     lastUpdate        // 最后更新时间
 *   } = useTickFlowWS({
 *     initialSymbols: ['000001', '600000'],
 *     autoConnect: true,
 *     enableFallback: true,  // WebSocket失败时降级为轮询
 *   });
 * 
 *   return (
 *     <div>
 *       状态: {isConnected ? '🟢 已连接' : '🔴 断开'}
 *       {Object.entries(quotes).map(([code, data]) => (
 *         <div key={code}>
 *           {data.name}: ¥{data.last_price} ({data.change_pct}%)
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface QuoteData {
  symbol: string;
  region: string;
  last_price: number;
  prev_close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  amount: number;
  timestamp: number;
  change?: number;
  change_pct?: number;
  turnover_rate?: number;
}

interface UseTickFlowWSOptions {
  /** 初始订阅的标的列表 */
  initialSymbols?: string[];
  /** 是否自动连接 */
  autoConnect?: boolean;
  /** WebSocket URL */
  url?: string;
  /** 重连间隔（毫秒） */
  reconnectInterval?: number;
  /** 最大重连次数 */
  maxReconnectAttempts?: number;
  /** 心跳间隔（毫秒） */
  heartbeatInterval?: number;
  /** 启用轮询降级（WebSocket不可用时） */
  enableFallback?: boolean;
  /** 轮询降级配置 */
  fallbackConfig?: {
    baseInterval?: number;
    userTier?: 'normal' | 'premium' | 'enterprise';
  };
  /** 调试模式 */
  debug?: boolean;
}

interface UseTickFlowWSResult {
  /** 行情数据 {symbol: QuoteData} */
  quotes: Record<string, QuoteData>;
  /** 是否已连接 */
  isConnected: boolean;
  /** 连接中 */
  isConnecting: boolean;
  /** 错误信息 */
  error: string | null;
  /** 当前已订阅的标的列表 */
  subscribedSymbols: string[];
  /** 最后更新时间 */
  lastUpdate: Date | null;
  /** 统计信息 */
  stats: {
    totalMessages: number;
    quotesReceived: number;
    reconnectCount: number;
    isUsingFallback: boolean;
  };
  /** 手动连接 */
  connect: () => void;
  /** 手动断开 */
  disconnect: () => void;
  /** 订阅标的 */
  subscribe: (symbols: string[]) => Promise<void>;
  /** 退订标的 */
  unsubscribe: (symbols: string[]) => Promise<void>;
  /** 发送自定义消息 */
  send: (message: any) => void;
}

export function useTickFlowWS(options: UseTickFlowWSOptions = {}): UseTickFlowWSResult {
  const {
    initialSymbols = [],
    autoConnect = true,
    url = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/quotes`,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
    enableFallback = true,
    fallbackConfig = {},
    debug = false,
  } = options;

  const [quotes, setQuotes] = useState<Record<string, QuoteData>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subscribedSymbols, setSubscribedSymbols] = useState<string[]>(initialSymbols);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isUsingFallback, setIsUsingFallback] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const statsRef = useRef({
    totalMessages: 0,
    quotesReceived: 0,
    reconnectCount: 0,
    isUsingFallback: false,
  });

  /**
   * 处理WebSocket消息
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);
      statsRef.current.totalMessages++;

      switch (message.op) {
        case 'quotes':
          if (message.data && typeof message.data === 'object') {
            setQuotes((prev) => ({
              ...prev,
              ...message.data,
            }));
            setLastUpdate(new Date());
            statsRef.current.quotesReceived++;
          }
          
          if (debug) {
            console.log('[TickFlowWS] Quotes received:', Object.keys(message.data || {}));
          }
          break;

        case 'subscribed':
          setSubscribedSymbols(message.symbols || []);
          if (debug) {
            console.log('[TickFlowWS] Subscribed:', message.symbols);
          }
          break;

        case 'error':
          console.error('[TickFlowWS] Error:', message.message);
          setError(message.message);
          break;

        case 'pong':
          if (debug) console.log('[TickFlowWS] Pong received');
          break;

        default:
          if (debug) console.log('[TickFlowWS] Unknown message:', message.op);
      }
    } catch (e) {
      console.error('[TickFlowWS] Message parse error:', e);
    }
  }, [debug]);

  /**
   * 建立WebSocket连接
   */
  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      debug && console.log('[TickFlowWS] Already connected');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (!mountedRef.current) return;

        debug && console.log('[TickFlowWS] Connected');
        setIsConnected(true);
        setIsConnecting(false);
        reconnectCountRef.current = 0;
        setIsUsingFallback(false);
        statsRef.current.isUsingFallback = false;

        // 订阅初始标的
        if (subscribedSymbols.length > 0) {
          ws.send(JSON.stringify({
            op: 'subscribe',
            symbols: subscribedSymbols,
          }));
        }

        // 启动心跳
        startHeartbeat(ws);
      };

      ws.onmessage = handleMessage;

      ws.onerror = (event) => {
        console.error('[TickFlowWS] Error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        debug && console.log('[TickFlowWS] Disconnected:', event.code, event.reason);
        
        setIsConnected(false);
        setIsConnecting(false);
        stopHeartbeat();

        // 尝试重连
        if (mountedRef.current && reconnectCountRef.current < maxReconnectAttempts) {
          scheduleReconnect();
        } else if (enableFallback && !isUsingFallback) {
          // 降级为轮询
          activateFallback();
        }
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('[TickFlowWS] Connection failed:', e);
      setIsConnecting(false);
      
      if (enableFallback) {
        activateFallback();
      }
    }
  }, [
    url,
    subscribedSymbols,
    handleMessage,
    debug,
    maxReconnectAttempts,
    enableFallback,
    isUsingFallback,
  ]);

  /**
   * 断开连接
   */
  const disconnect = useCallback(() => {
    cleanup();
    setIsConnected(false);
    setSubscribedSymbols([]);
    debug && console.log('[TickFlowWS] Disconnected manually');
  }, [debug]);

  /**
   * 订阅标的
   */
  const subscribe = useCallback(async (symbols: string[]) => {
    if (!symbols.length) return;

    // 更新本地状态
    setSubscribedSymbols((prev) => {
      const newSet = new Set([...prev, ...symbols]);
      return Array.from(newSet);
    });

    // 通过WebSocket发送
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ op: 'subscribe', symbols })
      );
    }

    debug && console.log('[TickFlowWS] Subscribe:', symbols);
  }, [debug]);

  /**
   * 退订标的
   */
  const unsubscribe = useCallback(async (symbols: string[]) => {
    if (!symbols.length) return;

    setSubscribedSymbols((prev) =>
      prev.filter((s) => !symbols.includes(s))
    );

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ op: 'unsubscribe', symbols })
      );
    }

    debug && console.log('[TickFlowWS] Unsubscribe:', symbols);
  }, [debug]);

  /**
   * 发送消息
   */
  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[TickFlowWS] Cannot send: not connected');
    }
  }, []);

  /**
   * 启动心跳
   */
  const startHeartbeat = useCallback((ws: WebSocket) => {
    stopHeartbeat();

    heartbeatTimerRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ op: 'ping' }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  /**
   * 停止心跳
   */
  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  /**
   * 安排重连
   */
  const scheduleReconnect = useCallback(() => {
    if (reconnectTimerRef.current) return;

    reconnectCountRef.current++;
    statsRef.current.reconnectCount = reconnectCountRef.current;

    const delay = Math.min(
      reconnectInterval * reconnectCountRef.current,
      60000
    );

    debug &&
      console.log(
        `[TickFlowWS] Reconnecting in ${delay}ms (attempt ${reconnectCountRef.current})`
      );

    reconnectTimerRef.current = setTimeout(() => {
      reconnectTimerRef.current = null;
      connect();
    }, delay);
  }, [connect, reconnectInterval, debug]);

  /**
   * 激活轮询降级
   */
  const activateFallback = useCallback(() => {
    if (!enableFallback) return;

    debug && console.log('[TickFlowWS] Activating polling fallback...');
    setIsUsingFallback(true);
    statsRef.current.isUsingFallback = true;
    setError('WebSocket不可用，使用轮询模式');

    // 这里可以集成useSmartPolling
    // 或者简单地使用fetch轮询
    if (subscribedSymbols.length > 0) {
      fetchFallbackData();
    }
  }, [enableFallback, subscribedSymbols, debug]);

  /**
   * 降级轮询获取数据
   */
  const fetchFallbackData = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/realtime/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          codes: subscribedSymbols,
          user_tier: fallbackConfig.userTier || 'premium',
        }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setQuotes(result.data);
          setLastUpdate(new Date());
        }
      }
    } catch (e) {
      console.error('[TickFlowWS] Fallback fetch error:', e);
    }
  }, [subscribedSymbols, fallbackConfig]);

  /**
   * 清理资源
   */
  const cleanup = useCallback(() => {
    stopHeartbeat();

    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Normal closure');
      wsRef.current = null;
    }
  }, [stopHeartbeat]);

  // 初始化连接
  useEffect(() => {
    mountedRef.current = true;

    if (autoConnect) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 降级模式下定期刷新
  useEffect(() => {
    if (!isUsingFallback || !autoConnect) return;

    const interval = setInterval(fetchFallbackData, fallbackConfig.baseInterval || 30000);

    return () => clearInterval(interval);
  }, [isUsingFallback, autoConnect, fallbackConfig.baseInterval, fetchFallbackData]);

  return {
    quotes,
    isConnected,
    isConnecting,
    error,
    subscribedSymbols,
    lastUpdate,
    stats: statsRef.current,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    send,
  };
}

export default useTickFlowWS;
