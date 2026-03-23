/**
 * 东方财富盘口异动页面
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Select,
  Flex,
  Text,
  Badge,
  Spinner,
  Center,
  VStack,
  HStack,
  Button,
  Grid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react';
import { eastMoneyApi, type StockChange, type ChangeType, type MarketChangesSummary } from '../../services/eastmoney';

const EastMoneyChangesPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [changes, setChanges] = useState<StockChange[]>([]);
  const [changeTypes, setChangeTypes] = useState<ChangeType[]>([]);
  const [selectedType, setSelectedType] = useState('大笔买入');
  const [summary, setSummary] = useState<MarketChangesSummary | null>(null);

  // 获取异动类型列表
  useEffect(() => {
    const fetchChangeTypes = async () => {
      try {
        const result = await eastMoneyApi.getChangeTypes();
        setChangeTypes(result);
      } catch (error) {
        console.error('获取异动类型失败:', error);
      }
    };
    fetchChangeTypes();
  }, []);

  // 获取市场异动汇总
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const result = await eastMoneyApi.getMarketChangesSummary();
        setSummary(result);
      } catch (error) {
        console.error('获取市场异动汇总失败:', error);
      }
    };
    fetchSummary();
  }, []);

  // 获取盘口异动数据
  const fetchChanges = async (type: string) => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockChanges(type);
      setChanges(result);
    } catch (error) {
      console.error('获取盘口异动数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChanges(selectedType);
  }, [selectedType]);

  // 刷新数据
  const handleRefresh = () => {
    fetchChanges(selectedType);
    eastMoneyApi.getMarketChangesSummary().then(setSummary);
  };

  return (
    <Box p={6}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">东方财富盘口异动</Heading>
        <Button onClick={handleRefresh} colorScheme="blue">
          刷新
        </Button>
      </Flex>

      {/* 市场异动汇总 */}
      {summary && (
        <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
          <Stat>
            <StatLabel>总异动次数</StatLabel>
            <StatNumber>{summary.total_changes}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>火箭发射</StatLabel>
            <StatNumber color="red.500">{summary.rocket_launch}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>大笔买入</StatLabel>
            <StatNumber color="green.500">{summary.big_buy}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>大笔卖出</StatLabel>
            <StatNumber color="red.500">{summary.big_sell}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>封涨停板</StatLabel>
            <StatNumber color="red.500">{summary.limit_up}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>封跌停板</StatLabel>
            <StatNumber color="green.500">{summary.limit_down}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>高台跳水</StatLabel>
            <StatNumber color="green.500">{summary.high_dive}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>快速反弹</StatLabel>
            <StatNumber color="orange.500">{summary.fast_rebound}</StatNumber>
          </Stat>
        </Grid>
      )}

      {/* 异动类型选择 */}
      <Flex mb={4} align="center">
        <Text mr={4}>异动类型：</Text>
        <Select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          width="200px"
        >
          {changeTypes.map((type) => (
            <option key={type.key} value={type.name}>
              {type.name}
            </option>
          ))}
        </Select>
      </Flex>

      {/* 异动数据表格 */}
      {loading ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <Box overflowX="auto">
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>时间</Th>
                <Th>代码</Th>
                <Th>名称</Th>
                <Th>板块</Th>
                <Th>相关信息</Th>
                <Th>异动类型</Th>
              </Tr>
            </Thead>
            <Tbody>
              {changes.map((change, index) => (
                <Tr key={index}>
                  <Td>{change.time}</Td>
                  <Td>
                    <Text fontWeight="bold">{change.code}</Text>
                  </Td>
                  <Td>{change.name}</Td>
                  <Td>
                    <Badge colorScheme="blue">{change.board}</Badge>
                  </Td>
                  <Td fontSize="sm">{change.related_info}</Td>
                  <Td>
                    <Badge colorScheme={getChangeTypeColorScheme(change.change_type)}>
                      {change.change_type}
                    </Badge>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
          {changes.length === 0 && (
            <Center h="200px">
              <Text color="gray.500">暂无数据</Text>
            </Center>
          )}
        </Box>
      )}
    </Box>
  );
};

// 获取异动类型的颜色方案
const getChangeTypeColorScheme = (type: string): string => {
  const buyTypes = ['大笔买入', '火箭发射', '快速反弹', '有大买盘', '竞价上涨', '封涨停板', '打开跌停板'];
  const sellTypes = ['大笔卖出', '高台跳水', '加速下跌', '有大卖盘', '竞价下跌', '封跌停板', '打开涨停板'];
  
  if (buyTypes.includes(type)) return 'red';
  if (sellTypes.includes(type)) return 'green';
  return 'blue';
};

export default EastMoneyChangesPage;
