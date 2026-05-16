/**
 * 东方财富盘口异动页面
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Flex, Grid, Heading, NativeSelect, Spinner, Stat, Table, Text } from '@chakra-ui/react'
import { eastMoneyApi, type StockChange, type ChangeType, type MarketChangesSummary } from '@/services/akshare/index';

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
        setChangeTypes(result.data || []);
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
        setSummary(result.data || null);
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
      setChanges(result.data || []);
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
    eastMoneyApi.getMarketChangesSummary().then(r => setSummary(r.data || null));
  };

  return (
    <Box p={6}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">东方财富盘口异动</Heading>
        <Button onClick={handleRefresh} colorPalette="blue">
          刷新
        </Button>
      </Flex>

      {/* 市场异动汇总 */}
      {summary && (
        <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
          <Stat.Root>
            <Stat.Label>总异动次数</Stat.Label>
            <Stat.ValueText>{summary.total_changes}</Stat.ValueText>
          </Stat.Root>
          <Stat.Root>
            <Stat.Label>火箭发射</Stat.Label>
            <Stat.ValueText color="red.500">{summary.rocket_launch}</Stat.ValueText>
          </Stat.Root>
          <Stat.Root>
            <Stat.Label>大笔买入</Stat.Label>
            <Stat.ValueText color="green.500">{summary.big_buy}</Stat.ValueText>
          </Stat.Root>
          <Stat.Root>
            <Stat.Label>大笔卖出</Stat.Label>
            <Stat.ValueText color="red.500">{summary.big_sell}</Stat.ValueText>
          </Stat.Root>
          <Stat.Root>
            <Stat.Label>封涨停板</Stat.Label>
            <Stat.ValueText color="red.500">{summary.limit_up}</Stat.ValueText>
          </Stat.Root>
          <Stat.Root>
            <Stat.Label>封跌停板</Stat.Label>
            <Stat.ValueText color="green.500">{summary.limit_down}</Stat.ValueText>
          </Stat.Root>
          <Stat.Root>
            <Stat.Label>高台跳水</Stat.Label>
            <Stat.ValueText color="green.500">{summary.high_dive}</Stat.ValueText>
          </Stat.Root>
          <Stat.Root>
            <Stat.Label>快速反弹</Stat.Label>
            <Stat.ValueText color="orange.500">{summary.fast_rebound}</Stat.ValueText>
          </Stat.Root>
        </Grid>
      )}

      {/* 异动类型选择 */}
      <Flex mb={4} align="center">
        <Text mr={4}>异动类型：</Text>
        <NativeSelect.Root><NativeSelect.Field
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          width="200px"
        >
          {changeTypes.map((type) => (
            <option key={type.key} value={type.name}>
              {type.name}
            </option>
          ))}
        </NativeSelect.Field></NativeSelect.Root>
      </Flex>

      {/* 异动数据表格 */}
      {loading ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <Box overflowX="auto">
          <Table.Root  size="sm">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>时间</Table.ColumnHeader>
                <Table.ColumnHeader>代码</Table.ColumnHeader>
                <Table.ColumnHeader>名称</Table.ColumnHeader>
                <Table.ColumnHeader>板块</Table.ColumnHeader>
                <Table.ColumnHeader>相关信息</Table.ColumnHeader>
                <Table.ColumnHeader>异动类型</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {changes.map((change, index) => (
                <Table.Row key={index}>
                  <Table.Cell>{change.time}</Table.Cell>
                  <Table.Cell>
                    <Text fontWeight="bold">{change.code}</Text>
                  </Table.Cell>
                  <Table.Cell>{change.name}</Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette="blue">{change.board}</Badge>
                  </Table.Cell>
                  <Table.Cell fontSize="sm">{change.related_info}</Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette={getChangeTypeColorScheme(change.change_type)}>
                      {change.change_type}
                    </Badge>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
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
