/**
 * 实时行情组件 - WebSocket 版本
 * 使用 WebSocket 接收实时股票行情数据
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Box, Text, VStack, HStack, Spinner, Badge, useToast } from '@chakra-ui/react';

interface RealtimeQuoteProps {
  code: string;
  name?: string;
}

interface QuoteData {
  price: number;
  change: number;
  change_pct: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  bid?: Array<{ price: number; volume: number }>;
  ask?: Array<{ price: number; volume: number }>;
}

const RealtimeQuoteWS: React.FC<RealtimeQuoteProps> = ({ code, name }) => {
  const toast = useToast();
  const [quote, setQuote] = useState<QuoteData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [updateCount, setUpdateCount] = useState(0);
  const [latency, setLatency] = useState<number>(0);

  // WebSocket 连接
  const {
    isConnected,
    subscribe,
    unsubscribe,
    ping,
    disconnect,
  } = useWebSocket({
    autoConnect: true,
    onMessage: useCallback((event: string, data: any) => {
      // 处理行情更新消息
      if (event === 'quote_update' && data.topic === `stock:${code}`) {
        const newQuote = data.quote;
        setQuote(newQuote);
        setLastUpdate(new Date());
        setUpdateCount(prev => prev + 1);
      }
    }, [code]),
    onStateChange: useCallback((connected: boolean) => {
      if (connected) {
        toast({
          title: 'WebSocket 已连接',
          description: '开始接收实时行情',
          status: 'success',
          duration: 2000,
          isClosable: true,
        });
      } else {
        toast({
          title: 'WebSocket 已断开',
          description: '尝试重新连接中...',
          status: 'warning',
          duration: 3000,
          isClosable: true,
        });
      }
    }, [toast]),
  });

  // 订阅股票行情
  useEffect(() => {
    const topic = `stock:${code}`;
    
    if (isConnected) {
      subscribe(topic)
        .then(() => {
          console.log('[RealtimeQuoteWS] 订阅成功:', topic);
        })
        .catch(err => {
          console.error('[RealtimeQuoteWS] 订阅失败:', err);
          toast({
            title: '订阅失败',
            description: err.message,
            status: 'error',
            duration: 3000,
          });
        });
    }

    // 清理时取消订阅
    return () => {
      unsubscribe(topic).catch(console.error);
    };
  }, [code, isConnected, subscribe, unsubscribe, toast]);

  // 定期测试延迟
  useEffect(() => {
    if (!isConnected) return;

    const testLatency = async () => {
      try {
        const latency = await ping();
        setLatency(latency);
      } catch (error) {
        console.error('延迟测试失败:', error);
      }
    };

    testLatency();
    const interval = setInterval(testLatency, 10000); // 每 10 秒测试一次

    return () => clearInterval(interval);
  }, [isConnected, ping]);

  // 格式化涨跌幅颜色
  const getChangeColor = (value: number) => {
    if (value > 0) return 'red.500'; // A 股涨为红色
    if (value < 0) return 'green.500'; // A 股跌为绿色
    return 'gray.500';
  };

  // 格式化数字
  const formatNumber = (num: number, decimals: number = 2) => {
    return num?.toFixed(decimals) ?? '-';
  };

  if (!quote) {
    return (
      <Box p={4} borderWidth={1} borderRadius="lg">
        <VStack>
          <Spinner size="lg" />
          <Text>等待行情数据...</Text>
          {!isConnected && (
            <Badge colorScheme="yellow">WebSocket 未连接</Badge>
          )}
        </VStack>
      </Box>
    );
  }

  return (
    <Box p={4} borderWidth={1} borderRadius="lg" bg="white">
      {/* 头部信息 */}
      <HStack justify="space-between" mb={4}>
        <VStack align="start" spacing={0}>
          <Text fontSize="xl" fontWeight="bold">
            {code} {name || ''}
          </Text>
          <Text fontSize="sm" color="gray.500">
            实时更新
          </Text>
        </VStack>
        
        <HStack spacing={2}>
          <Badge colorScheme={isConnected ? 'green' : 'red'}>
            {isConnected ? '已连接' : '未连接'}
          </Badge>
          <Badge colorScheme="blue">
            延迟：{latency}ms
          </Badge>
          <Badge colorScheme="purple">
            更新：{updateCount}次
          </Badge>
        </HStack>
      </HStack>

      {/* 主要行情数据 */}
      <VStack align="stretch" spacing={3} mb={4}>
        <HStack justify="space-between">
          <Text>最新价:</Text>
          <Text fontSize="2xl" fontWeight="bold" color={getChangeColor(quote.change)}>
            {formatNumber(quote.price)}
          </Text>
        </HStack>
        
        <HStack justify="space-between">
          <Text>涨跌幅:</Text>
          <Text fontSize="lg" color={getChangeColor(quote.change)}>
            {quote.change > 0 ? '+' : ''}{formatNumber(quote.change)} ({formatNumber(quote.change_pct)}%)
          </Text>
        </HStack>

        <HStack justify="space-between">
          <Text>今开:</Text>
          <Text>{formatNumber(quote.open)}</Text>
        </HStack>

        <HStack justify="space-between">
          <Text>最高:</Text>
          <Text color="red.500">{formatNumber(quote.high)}</Text>
        </HStack>

        <HStack justify="space-between">
          <Text>最低:</Text>
          <Text color="green.500">{formatNumber(quote.low)}</Text>
        </HStack>

        <HStack justify="space-between">
          <Text>成交量:</Text>
          <Text>{formatNumber(quote.volume, 0)}</Text>
        </HStack>

        <HStack justify="space-between">
          <Text>成交额:</Text>
          <Text>{formatNumber(quote.amount / 10000, 2)}万</Text>
        </HStack>
      </VStack>

      {/* 买卖盘口 */}
      {(quote.bid || quote.ask) && (
        <Box>
          <Text fontWeight="bold" mb={2}>盘口</Text>
          <HStack justify="space-between" spacing={1}>
            {/* 卖盘 */}
            <VStack flex={1} align="stretch" spacing={1}>
              <Text fontSize="sm" color="green.500" fontWeight="bold">卖</Text>
              {quote.ask?.slice(0, 5).map((ask, idx) => (
                <HStack key={`ask-${idx}`} justify="space-between" fontSize="sm">
                  <Text color="green.600">{formatNumber(ask.price)}</Text>
                  <Text>{formatNumber(ask.volume, 0)}</Text>
                </HStack>
              ))}
            </VStack>

            {/* 买盘 */}
            <VStack flex={1} align="stretch" spacing={1}>
              <Text fontSize="sm" color="red.500" fontWeight="bold">买</Text>
              {quote.bid?.slice(0, 5).reverse().map((bid, idx) => (
                <HStack key={`bid-${idx}`} justify="space-between" fontSize="sm">
                  <Text color="red.600">{formatNumber(bid.price)}</Text>
                  <Text>{formatNumber(bid.volume, 0)}</Text>
                </HStack>
              ))}
            </VStack>
          </HStack>
        </Box>
      )}

      {/* 更新时间 */}
      <Text fontSize="xs" color="gray.400" mt={4} textAlign="right">
        最后更新：{lastUpdate?.toLocaleTimeString()}
      </Text>
    </Box>
  );
};

export default RealtimeQuoteWS;
