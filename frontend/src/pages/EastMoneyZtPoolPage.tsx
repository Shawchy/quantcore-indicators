/**
 * 东方财富涨停板行情页面
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Flex, Grid, Heading, Input, InputGroup, Spinner, Stat, Table, Text } from '@chakra-ui/react'
import { eastMoneyApi, type StockZtPool } from '@/services/akshare/index';

const EastMoneyZtPoolPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [ztStocks, setZtStocks] = useState<StockZtPool[]>([]);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0].replace(/-/g, ''));

  // 获取涨停股池数据
  const fetchZtPool = async (selectedDate: string) => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getZtPool(selectedDate);
      setZtStocks(result.data || []);
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
          <InputGroup width="200px" endAddon="日期">
            <Input
              type="date"
              value={date.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}
              onChange={handleDateChange}
            />
          </InputGroup>
          <Button onClick={handleRefresh} colorPalette="blue">
            刷新
          </Button>
        </Flex>
      </Flex>

      {/* 统计信息 */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
        <Stat.Root>
          <Stat.Label>涨停总数</Stat.Label>
          <Stat.ValueText color="red.500">{stats.total}</Stat.ValueText>
        </Stat.Root>
        <Stat.Root>
          <Stat.Label>首板</Stat.Label>
          <Stat.ValueText>{stats.firstBoard}</Stat.ValueText>
        </Stat.Root>
        <Stat.Root>
          <Stat.Label>连板</Stat.Label>
          <Stat.ValueText color="orange.500">{stats.continuous}</Stat.ValueText>
        </Stat.Root>
        <Stat.Root>
          <Stat.Label>最高连板</Stat.Label>
          <Stat.ValueText color="purple.500">{stats.maxContinuous}</Stat.ValueText>
        </Stat.Root>
      </Grid>

      {/* 涨停股池表格 */}
      {loading ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <Box overflowX="auto">
          <Table.Root  size="sm">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>序号</Table.ColumnHeader>
                <Table.ColumnHeader>代码</Table.ColumnHeader>
                <Table.ColumnHeader>名称</Table.ColumnHeader>
                <Table.ColumnHeader>涨跌幅</Table.ColumnHeader>
                <Table.ColumnHeader>最新价</Table.ColumnHeader>
                <Table.ColumnHeader>换手率</Table.ColumnHeader>
                <Table.ColumnHeader>流通市值</Table.ColumnHeader>
                <Table.ColumnHeader>总市值</Table.ColumnHeader>
                <Table.ColumnHeader>封板资金</Table.ColumnHeader>
                <Table.ColumnHeader>首次封板</Table.ColumnHeader>
                <Table.ColumnHeader>最后封板</Table.ColumnHeader>
                <Table.ColumnHeader>炸板次数</Table.ColumnHeader>
                <Table.ColumnHeader>连板数</Table.ColumnHeader>
                <Table.ColumnHeader>涨停统计</Table.ColumnHeader>
                <Table.ColumnHeader>所属行业</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {ztStocks.map((stock) => (
                <Table.Row key={stock.serial_no}>
                  <Table.Cell>{stock.serial_no}</Table.Cell>
                  <Table.Cell>
                    <Text fontWeight="bold">{stock.code}</Text>
                  </Table.Cell>
                  <Table.Cell>{stock.name}</Table.Cell>
                  <Table.Cell color="red.500">{stock.change_pct.toFixed(2)}%</Table.Cell>
                  <Table.Cell>{stock.latest_price.toFixed(2)}</Table.Cell>
                  <Table.Cell>{stock.turnover_rate.toFixed(2)}%</Table.Cell>
                  <Table.Cell>{(stock.float_mv / 10000).toFixed(2)}亿</Table.Cell>
                  <Table.Cell>{(stock.total_mv / 10000).toFixed(2)}亿</Table.Cell>
                  <Table.Cell color="red.500">{(stock.seal_fund / 10000).toFixed(0)}万</Table.Cell>
                  <Table.Cell>{stock.first_seal_time}</Table.Cell>
                  <Table.Cell>{stock.last_seal_time}</Table.Cell>
                  <Table.Cell>
                    {stock.open_count > 0 ? (
                      <Badge colorPalette="orange">{stock.open_count}次</Badge>
                    ) : (
                      <Text>-</Text>
                    )}
                  </Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette={stock.continuous_count > 1 ? 'purple' : 'blue'}>
                      {stock.continuous_count}连板
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>{stock.zt_stats}</Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette="green">{stock.industry}</Badge>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
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
