/**
 * 东方财富涨停板行情页面
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
  Flex,
  Text,
  Badge,
  Spinner,
  Center,
  Button,
  Grid,
  Stat,
  StatLabel,
  StatNumber,
  Input,
  InputGroup,
  InputRightAddon,
} from '@chakra-ui/react';
import { eastMoneyApi, type StockZtPool } from '../../services/eastmoney';

const EastMoneyZtPoolPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [ztStocks, setZtStocks] = useState<StockZtPool[]>([]);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0].replace(/-/g, ''));

  // 获取涨停股池数据
  const fetchZtPool = async (selectedDate: string) => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getZtPool(selectedDate);
      setZtStocks(result);
    } catch (error) {
      console.error('获取涨停股池数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchZtPool(date);
  }, [date]);

  // 刷新数据
  const handleRefresh = () => {
    fetchZtPool(date);
  };

  // 日期变更
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = e.target.value.replace(/-/g, '');
    setDate(newDate);
  };

  // 统计数据
  const stats = {
    total: ztStocks.length,
    firstBoard: ztStocks.filter(s => s.continuous_count === 1).length,
    continuous: ztStocks.filter(s => s.continuous_count > 1).length,
    maxContinuous: Math.max(...ztStocks.map(s => s.continuous_count), 0),
  };

  return (
    <Box p={6}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">东方财富涨停板行情</Heading>
        <Flex gap={4} align="center">
          <InputGroup width="200px">
            <Input
              type="date"
              value={date.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}
              onChange={handleDateChange}
            />
            <InputRightAddon>日期</InputRightAddon>
          </InputGroup>
          <Button onClick={handleRefresh} colorScheme="blue">
            刷新
          </Button>
        </Flex>
      </Flex>

      {/* 统计信息 */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
        <Stat>
          <StatLabel>涨停总数</StatLabel>
          <StatNumber color="red.500">{stats.total}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>首板</StatLabel>
          <StatNumber>{stats.firstBoard}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>连板</StatLabel>
          <StatNumber color="orange.500">{stats.continuous}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>最高连板</StatLabel>
          <StatNumber color="purple.500">{stats.maxContinuous}</StatNumber>
        </Stat>
      </Grid>

      {/* 涨停股池表格 */}
      {loading ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <Box overflowX="auto">
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>序号</Th>
                <Th>代码</Th>
                <Th>名称</Th>
                <Th>涨跌幅</Th>
                <Th>最新价</Th>
                <Th>换手率</Th>
                <Th>流通市值</Th>
                <Th>总市值</Th>
                <Th>封板资金</Th>
                <Th>首次封板</Th>
                <Th>最后封板</Th>
                <Th>炸板次数</Th>
                <Th>连板数</Th>
                <Th>涨停统计</Th>
                <Th>所属行业</Th>
              </Tr>
            </Thead>
            <Tbody>
              {ztStocks.map((stock) => (
                <Tr key={stock.serial_no}>
                  <Td>{stock.serial_no}</Td>
                  <Td>
                    <Text fontWeight="bold">{stock.code}</Text>
                  </Td>
                  <Td>{stock.name}</Td>
                  <Td color="red.500">{stock.change_pct.toFixed(2)}%</Td>
                  <Td>{stock.latest_price.toFixed(2)}</Td>
                  <Td>{stock.turnover_rate.toFixed(2)}%</Td>
                  <Td>{(stock.float_mv / 10000).toFixed(2)}亿</Td>
                  <Td>{(stock.total_mv / 10000).toFixed(2)}亿</Td>
                  <Td color="red.500">{(stock.seal_fund / 10000).toFixed(0)}万</Td>
                  <Td>{stock.first_seal_time}</Td>
                  <Td>{stock.last_seal_time}</Td>
                  <Td>
                    {stock.open_count > 0 ? (
                      <Badge colorScheme="orange">{stock.open_count}次</Badge>
                    ) : (
                      <Text>-</Text>
                    )}
                  </Td>
                  <Td>
                    <Badge colorScheme={stock.continuous_count > 1 ? 'purple' : 'blue'}>
                      {stock.continuous_count}连板
                    </Badge>
                  </Td>
                  <Td>{stock.zt_stats}</Td>
                  <Td>
                    <Badge colorScheme="green">{stock.industry}</Badge>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
          {ztStocks.length === 0 && (
            <Center h="200px">
              <Text color="gray.500">暂无数据</Text>
            </Center>
          )}
        </Box>
      )}
    </Box>
  );
};

export default EastMoneyZtPoolPage;
