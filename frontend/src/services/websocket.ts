/**
 * WebSocket 客户端服务
 * 提供 WebSocket 连接、订阅、消息处理等功能
 */

type MessageHandler = (data: any) => void;

interface WebSocketMessage {
  type: 'system' | 'data' | 'error' | 'auth';
  event: string;
  topic?: string;
  data: any;
}

interface ConnectionStats {
  isConnected: boolean;
  connectionId?: string;
  subscriptions: Set<string>;
  lastHeartbeat?: Date;
  reconnectCount: number;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private stats: ConnectionStats = {
    isConnected: false,
    subscriptions: new Set(),
    reconnectCount: 0,
  };
  
  // 配置
  private readonly reconnectDelay = 3000; // 重连延迟（毫秒）
  private readonly maxReconnectDelay = 30000; // 最大重连延迟
  private readonly heartbeatInterval = 30000; // 心跳间隔（毫秒）
  private readonly connectionTimeout = 10000; // 连接超时（毫秒）

  constructor(baseUrl?: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = baseUrl || window.location.host;
    this.url = `${protocol}//${host}/api/v1/ws`;
  }

  /**
   * 连接 WebSocket 服务器
   */
  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 关闭现有连接
        this.disconnect();

        // 构建连接 URL
        const url = token ? `${this.url}?token=${token}` : this.url;
        
        console.log('[WebSocket] 正在连接:', url);
        this.ws = new WebSocket(url);

        // 连接成功
        this.ws.onopen = () => {
          console.log('[WebSocket] 连接成功');
          this.stats.isConnected = true;
          this.stats.reconnectCount = 0;
          
          // 启动心跳
          this.startHeartbeat();
          
          // 重新订阅之前的主题
          this.resubscribeAll();
          
          resolve();
        };

        // 接收消息
        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] 消息解析失败:', error, event.data);
          }
        };

        // 连接错误
        this.ws.onerror = (error) => {
          console.error('[WebSocket] 连接错误:', error);
          reject(error);
        };

        // 连接关闭
        this.ws.onclose = (event) => {
          console.log('[WebSocket] 连接关闭:', event.code, event.reason);
          this.stats.isConnected = false;
          
          // 停止心跳
          this.stopHeartbeat();
          
          // 自动重连
          this.scheduleReconnect(token);
        };

        // 连接超时处理
        const timeoutId = setTimeout(() => {
          if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            reject(new Error('连接超时'));
          }
        }, this.connectionTimeout);

        // 连接成功后清除超时
        const originalOnOpen = this.ws.onopen;
        this.ws.onopen = () => {
          clearTimeout(timeoutId);
          if (originalOnOpen) originalOnOpen.call(this.ws);
        };

      } catch (error) {
        console.error('[WebSocket] 连接失败:', error);
        reject(error);
      }
    });
  }

  /**
   * 断开连接
   */
  disconnect() {
    // 清除定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    this.stopHeartbeat();

    // 关闭连接
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.stats.isConnected = false;
    console.log('[WebSocket] 连接已断开');
  }

  /**
   * 订阅主题
   */
  subscribe(topic: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected()) {
        reject(new Error('WebSocket 未连接'));
        return;
      }

      const message: WebSocketMessage = {
        type: 'system',
        event: 'subscribe',
        data: { topic }
      };

      this.send(message);
      this.stats.subscriptions.add(topic);
      
      console.log('[WebSocket] 订阅主题:', topic);
      resolve();
    });
  }

  /**
   * 取消订阅
   */
  unsubscribe(topic: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected()) {
        reject(new Error('WebSocket 未连接'));
        return;
      }

      const message: WebSocketMessage = {
        type: 'system',
        event: 'unsubscribe',
        data: { topic }
      };

      this.send(message);
      this.stats.subscriptions.delete(topic);
      
      console.log('[WebSocket] 取消订阅:', topic);
      resolve();
    });
  }

  /**
   * 发送心跳
   */
  sendHeartbeat() {
    if (!this.isConnected()) return;

    const message: WebSocketMessage = {
      type: 'system',
      event: 'heartbeat',
      data: {
        timestamp: new Date().toISOString()
      }
    };

    this.send(message);
  }

  /**
   * 发送 Ping 测试延迟
   */
  ping(): Promise<number> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected()) {
        reject(new Error('WebSocket 未连接'));
        return;
      }

      const startTime = Date.now();
      const message: WebSocketMessage = {
        type: 'system',
        event: 'ping',
        data: {
          timestamp: startTime.toString()
        }
      };

      // 临时监听 pong 响应
      const handler = (data: any) => {
        if (data.event === 'pong') {
          const latency = Date.now() - startTime;
          this.removeMessageHandler('pong', handler);
          resolve(latency);
        }
      };

      this.addMessageHandler('pong', handler);
      this.send(message);

      // 超时处理
      setTimeout(() => {
        this.removeMessageHandler('pong', handler);
        reject(new Error('Ping 超时'));
      }, 5000);
    });
  }

  /**
   * 发送消息
   */
  send(message: WebSocketMessage) {
    if (!this.isConnected() || !this.ws) {
      console.warn('[WebSocket] 消息发送失败 - 未连接');
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('[WebSocket] 消息发送错误:', error);
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage) {
    const { type, event, topic, data } = message;

    console.log('[WebSocket] 收到消息:', type, event, topic, data);

    // 更新统计
    if (type === 'system') {
      if (event === 'heartbeat_ack') {
        this.stats.lastHeartbeat = new Date();
      } else if (event === 'connected') {
        this.stats.connectionId = data.connection_id;
      } else if (event === 'subscribed') {
        this.stats.subscriptions.add(data.topic);
      } else if (event === 'unsubscribed') {
        this.stats.subscriptions.delete(data.topic);
      }
    }

    // 调用消息处理器
    const handlers = this.messageHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error('[WebSocket] 消息处理错误:', error);
        }
      });
    }

    // 特定主题的消息
    if (topic) {
      const topicHandlers = this.messageHandlers.get(`topic:${topic}`);
      if (topicHandlers) {
        topicHandlers.forEach(handler => {
          try {
            handler({ ...message, topic });
          } catch (error) {
            console.error('[WebSocket] 主题消息处理错误:', error);
          }
        });
      }
    }
  }

  /**
   * 添加消息处理器
   */
  addMessageHandler(event: string, handler: MessageHandler) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, new Set());
    }
    this.messageHandlers.get(event)!.add(handler);
  }

  /**
   * 移除消息处理器
   */
  removeMessageHandler(event: string, handler: MessageHandler) {
    const handlers = this.messageHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * 添加主题消息处理器
   */
  addTopicHandler(topic: string, handler: MessageHandler) {
    const eventKey = `topic:${topic}`;
    this.addMessageHandler(eventKey, handler);
  }

  /**
   * 移除主题消息处理器
   */
  removeTopicHandler(topic: string, handler: MessageHandler) {
    const eventKey = `topic:${topic}`;
    this.removeMessageHandler(eventKey, handler);
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(token?: string) {
    if (this.reconnectTimer) return;

    // 指数退避策略
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.stats.reconnectCount),
      this.maxReconnectDelay
    );

    console.log(`[WebSocket] 将在 ${delay}ms 后重连...`);

    this.reconnectTimer = window.setTimeout(() => {
      this.stats.reconnectCount++;
      this.reconnectTimer = null;
      this.connect(token).catch(err => {
        console.error('[WebSocket] 重连失败:', err);
      });
    }, delay);
  }

  /**
   * 启动心跳
   */
  private startHeartbeat() {
    this.stopHeartbeat();

    this.heartbeatTimer = window.setInterval(() => {
      this.sendHeartbeat();
    }, this.heartbeatInterval);
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 重新订阅所有主题
   */
  private resubscribeAll() {
    this.stats.subscriptions.forEach(topic => {
      this.subscribe(topic).catch(err => {
        console.error('[WebSocket] 重新订阅失败:', topic, err);
      });
    });
  }

  /**
   * 检查是否已连接
   */
  isConnected(): boolean {
    return this.stats.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 获取连接统计
   */
  getStats(): ConnectionStats {
    return { ...this.stats };
  }

  /**
   * 获取 WebSocket 状态
   */
  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

// 导出单例
export const wsService = new WebSocketService();
export default wsService;
