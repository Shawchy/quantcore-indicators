/**
 * WebSocket React Hook
 * 提供 WebSocket 连接的 React Hooks 接口
 */

import { useEffect, useCallback, useRef, useState } from 'react';
import wsService from '../services/websocket';

interface UseWebSocketOptions {
  /** 是否自动连接 */
  autoConnect?: boolean;
  /** 连接成功后自动订阅的主题 */
  subscriptions?: string[];
  /** 消息处理器 */
  onMessage?: (event: string, data: any) => void;
  /** 连接状态变化回调 */
  onStateChange?: (isConnected: boolean) => void;
}

interface UseWebSocketReturn {
  /** 是否已连接 */
  isConnected: boolean;
  /** 连接 ID */
  connectionId?: string;
  /** 订阅的主题集合 */
  subscriptions: Set<string>;
  /** 连接函数 */
  connect: () => Promise<void>;
  /** 断开连接 */
  disconnect: () => void;
  /** 订阅主题 */
  subscribe: (topic: string) => Promise<void>;
  /** 取消订阅 */
  unsubscribe: (topic: string) => Promise<void>;
  /** 发送心跳 */
  sendHeartbeat: () => void;
  /** 测试延迟 */
  ping: () => Promise<number>;
  /** 获取统计信息 */
  getStats: () => any;
}

/**
 * WebSocket Hook
 * 
 * @param options 配置选项
 * @returns WebSocket 操作接口
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    autoConnect = true,
    subscriptions = [],
    onMessage,
    onStateChange,
  } = options;

  const [isConnected, setIsConnected] = useState(wsService.isConnected());
  const [connectionId, setConnectionId] = useState<string | undefined>();
  const [subs, setSubs] = useState<Set<string>>(new Set());
  
  const messageHandlerRef = useRef(onMessage);
  messageHandlerRef.current = onMessage;

  const stateChangeHandlerRef = useRef(onStateChange);
  stateChangeHandlerRef.current = onStateChange;

  // 处理消息
  const handleMessage = useCallback((event: string, data: any) => {
    if (messageHandlerRef.current) {
      messageHandlerRef.current(event, data);
    }

    // 更新连接 ID
    if (event === 'connected') {
      setConnectionId(data.connection_id);
    }
  }, []);

  // 处理状态变化
  const handleStateChange = useCallback((connected: boolean) => {
    setIsConnected(connected);
    if (stateChangeHandlerRef.current) {
      stateChangeHandlerRef.current(connected);
    }
  }, []);

  // 更新订阅主题
  const updateSubscriptions = useCallback(() => {
    const stats = wsService.getStats();
    setSubs(new Set(stats.subscriptions));
  }, []);

  // 连接函数
  const connect = useCallback(async () => {
    try {
      // 从 Redux store 获取 token
      const storeModule = (window as any).__store__;
      const token = storeModule?.getState?.()?.auth?.token;
      
      await wsService.connect(token);
      handleStateChange(true);
      updateSubscriptions();
      
      console.log('[useWebSocket] 连接成功');
    } catch (error) {
      console.error('[useWebSocket] 连接失败:', error);
      handleStateChange(false);
      throw error;
    }
  }, [handleStateChange, updateSubscriptions]);

  // 断开连接
  const disconnect = useCallback(() => {
    wsService.disconnect();
    handleStateChange(false);
    setConnectionId(undefined);
    setSubs(new Set());
  }, [handleStateChange]);

  // 订阅主题
  const subscribe = useCallback(async (topic: string) => {
    await wsService.subscribe(topic);
    updateSubscriptions();
  }, [updateSubscriptions]);

  // 取消订阅
  const unsubscribe = useCallback(async (topic: string) => {
    await wsService.unsubscribe(topic);
    updateSubscriptions();
  }, [updateSubscriptions]);

  // 发送心跳
  const sendHeartbeat = useCallback(() => {
    wsService.sendHeartbeat();
  }, []);

  // 测试延迟
  const ping = useCallback(async () => {
    return await wsService.ping();
  }, []);

  // 获取统计信息
  const getStats = useCallback(() => {
    return wsService.getStats();
  }, []);

  // 初始化连接和事件监听
  useEffect(() => {
    // 添加消息监听器
    const globalHandler = (event: string, data: any) => {
      handleMessage(event, data);
    };

    wsService.addMessageHandler('*', globalHandler);

    // 自动连接
    if (autoConnect && !isConnected) {
      connect().catch(console.error);
    }

    // 自动订阅
    if (isConnected && subscriptions.length > 0) {
      subscriptions.forEach(topic => {
        wsService.subscribe(topic).catch(console.error);
      });
    }

    // 清理
    return () => {
      wsService.removeMessageHandler('*', globalHandler);
      if (!autoConnect) {
        disconnect();
      }
    };
  }, [autoConnect, isConnected, subscriptions, connect, disconnect, handleMessage]);

  return {
    isConnected,
    connectionId,
    subscriptions: subs,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendHeartbeat,
    ping,
    getStats,
  };
}

export default useWebSocket;
