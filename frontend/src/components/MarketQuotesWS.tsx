/**
 * 市场实时行情组件 - WebSocket 版本
 * 使用 WebSocket 接收市场板块行情数据
 */

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  Box,
  Text,
  VStack,
  HStack,
  Spinner,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useToast,
  Button,
  Switch,
  FormControl,
  FormLabel,
} from '@chakra-ui/react';

interface MarketQuote {
  ts_code: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number;
  amount: number;
}

interface MarketQuotesWSProps {
  marketTypes?: string[];
  limit?: number;
  autoRefresh?: boolean;
}

const MarketQuotesWS: React.FC<MarketQuotesWSProps> = ({
  marketTypes = ['沪深 A 股'],
  limit = 50,
  autoRefresh = true,
}) => {
  const toast = useToast();
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [updateCount, setUpdateCount] = useState(0);
  const [sortBy, setSortBy] = useState<'change_pct' | 'price' | 'volume'>('change_pct');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // WebSocket 连接
  const {
    isConnected,
    subscribe,
    unsubscribe,
    getStats,
  } = useWebSocket({
    autoConnect: true,
    subscriptions: autoRefresh ? ['market:quotes'] : [],
    onMessage: useCallback((event: string, data: any) => {
      // 处理市场更新消息
      if (event === 'market_update' && data.topic === 'market:quotes') {
        const newQuotes: MarketQuote[] = data.quotes || [];
        setQuotes(newQuotes.slice(0, limit));
        setLastUpdate(new Date());
        setUpdateCount(prev => prev + 1);
      }
    }, [limit]),
  });

  // 订阅市场行情
  useEffect(() => {
    const topic = 'market:quotes';
    
    if (isConnected && autoRefresh) {
      subscribe(topic)
        .then(() => {
          console.log('[MarketQuotesWS] 订阅成功:', topic);
        })
        .catch(err => {
          console.error('[MarketQuotesWS] 订阅失败:', err);
        });
    }

    return () => {
      if (autoRefresh) {
        unsubscribe(topic).catch(console.error);
      }
    };
  }, [isConnected, autoRefresh, subscribe, unsubscribe]);

  // 排序后的数据
  const sortedQuotes = useMemo(() => {
    return [...quotes].sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });
  }, [quotes, sortBy, sortOrder]);

  // 切换排序
  const handleSort = (field: 'change_pct' | 'price' | 'volume') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  // 格式化涨跌幅颜色
  const getChangeColor = (value: number) => {
    if (value > 0) return 'red.500';
    if (value < 0) return 'green.500';
    return 'gray.500';
  };

  // 格式化数字
  const formatNumber = (num: number, decimals: number = 2) => {
    if (num === null || num === undefined) return '-';
    return num.toFixed(decimals);
  };

  const formatLargeNumber = (num: number) => {
    if (num === null || num === undefined) return '-';
    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(2)}亿`;
    }
    if (num >= 10000) {
      return `${(num / 10000).toFixed(2)}万`;
    }
    return num.toFixed(0);
  };

  return (
    <Box>
      {/* 控制栏 */}
      <HStack justify="space-between" mb={4}>
        <HStack>
          <Text fontSize="lg" fontWeight="bold">
            市场实时行情
          </Text>
          <Badge colorScheme={isConnected ? 'green' : 'red'}>
            {isConnected ? '实时推送' : '未连接'}
          </Badge>
          <Badge colorScheme="purple">
            更新：{updateCount}次
          </Badge>
        </HStack>

        <HStack>
          <FormControl display="flex" alignItems="center" width="auto">
            <FormLabel htmlFor="auto-refresh" mb={0} fontSize="sm">
              自动刷新
            </FormLabel>
            <Switch
              id="auto-refresh"
              isChecked={autoRefresh}
              size="sm"
            />
          </FormControl>
          
          <Button
            size="sm"
            onClick={() => handleSort('change_pct')}
            variant={sortBy === 'change_pct' ? 'solid' : 'outline'}
            colorScheme={sortBy === 'change_pct' ? 'blue' : 'gray'}
          >
            涨跌幅 {sortBy === 'change_pct' ? (sortOrder === 'desc' ? '↓' : '↑') : ''}
          </Button>
          
          <Button
            size="sm"
            onClick={() => handleSort('price')}
            variant={sortBy === 'price' ? 'solid' : 'outline'}
            colorScheme={sortBy === 'price' ? 'blue' : 'gray'}
          >
            价格 {sortBy === 'price' ? (sortOrder === 'desc' ? '↓' : '↑') : ''}
          </Button>
        </HStack>
      </HStack>

      {/* 数据表格 */}
      {!isConnected || quotes.length === 0 ? (
        <Box p={8} textAlign="center" borderWidth={1} borderRadius="lg">
          <VStack>
            <Spinner size="xl" />
            <Text>
              {!isConnected ? '正在连接 WebSocket...' : '等待行情数据...'}
            </Text>
          </VStack>
        </Box>
      ) : (
        <Box borderWidth={1} borderRadius="lg" overflow="hidden">
          <Table variant="simple" size="sm">
            <Thead bg="gray.50">
              <Tr>
                <Th>代码</Th>
                <Th>名称</Th>
                <Th
                  cursor="pointer"
                  onClick={() => handleSort('price')}
                  _hover={{ bg: 'gray.100' }}
                >
                  价格
                </Th>
                <Th
                  cursor="pointer"
                  onClick={() => handleSort('change_pct')}
                  _hover={{ bg: 'gray.100' }}
                  isNumeric
                >
                  涨跌幅
                </Th>
                <Th
                  cursor="pointer"
                  onClick={() => handleSort('volume')}
                  _hover={{ bg: 'gray.100' }}
                  isNumeric
                >
                  成交量
                </Th>
                <Th isNumeric>成交额</Th>
              </Tr>
            </Thead>
            <Tbody>
              {sortedQuotes.map((quote) => (
                <Tr
                  key={quote.ts_code}
                  _hover={{ bg: 'gray.50' }}
                  transition="background-color 0.2s"
                >
                  <Td fontWeight="medium">{quote.ts_code}</Td>
                  <Td>{quote.name}</Td>
                  <Td>{formatNumber(quote.price)}</Td>
                  <Td
                    isNumeric
                    color={getChangeColor(quote.change_pct)}
                    fontWeight="bold"
                  >
                    {quote.change_pct > 0 ? '+' : ''}{formatNumber(quote.change_pct)}%
                  </Td>
                  <Td isNumeric>{formatLargeNumber(quote.volume)}</Td>
                  <Td isNumeric>{formatLargeNumber(quote.amount)}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}

      {/* 更新信息 */}
      <HStack justify="space-between" mt={2}>
        <Text fontSize="xs" color="gray.500">
          数据来源：东方财富网 | WebSocket 实时推送
        </Text>
        <Text fontSize="xs" color="gray.500">
          最后更新：{lastUpdate?.toLocaleTimeString() ?? '-'}
        </Text>
      </HStack>
    </Box>
  );
};

export default MarketQuotesWS;
