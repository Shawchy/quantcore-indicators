/**
 * 东方财富综合涨停板行情页面
 * 包含：涨停股池、昨日涨停、强势股、次新股
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
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,

} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockZtPool,
  type StockZtPrevious,
  type StockZtStrong,
  type StockZtSubNew,
} from '@/services/akshare/index';

const EastMoneyZtBoardPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [ztPool, setZtPool] = useState<StockZtPool[]>([]);
  const [ztPrevious, setZtPrevious] = useState<StockZtPrevious[]>([]);
  const [ztStrong, setZtStrong] = useState<StockZtStrong[]>([]);
  const [ztSubNew, setZtSubNew] = useState<StockZtSubNew[]>([]);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0].replace(/-/g, ''));
  const [, setActiveTab] = useState(0);

  // 获取涨停股池数据
  const fetchZtPool = async (selectedDate: string) => {
    try {
      const result = await eastMoneyApi.getZtPool(selectedDate);
      setZtPool(result.data || []);
    } catch (error) {
      console.error('获取涨停股池数据失败:', error);
    }
  };

  // 获取昨日涨停数据
  const fetchZtPrevious = async (selectedDate: string) => {
    try {
      const result = await eastMoneyApi.getZtPoolPrevious(selectedDate);
      setZtPrevious(result.data || []);
    } catch (error) {
      console.error('获取昨日涨停数据失败:', error);
    }
  };

  // 获取强势股数据
  const fetchZtStrong = async (selectedDate: string) => {
    try {
      const result = await eastMoneyApi.getZtPoolStrong(selectedDate);
      setZtStrong(result.data || []);
    } catch (error) {
      console.error('获取强势股数据失败:', error);
    }
  };

  // 获取次新股数据
  const fetchZtSubNew = async (selectedDate: string) => {
    try {
      const result = await eastMoneyApi.getZtPoolSubNew(selectedDate);
      setZtSubNew(result.data || []);
    } catch (error) {
      console.error('获取次新股数据失败:', error);
    }
  };

  // 获取所有数据
  const fetchAllData = async (selectedDate: string) => {
    setLoading(true);
    try {
      await Promise.all([
        fetchZtPool(selectedDate),
        fetchZtPrevious(selectedDate),
        fetchZtStrong(selectedDate),
        fetchZtSubNew(selectedDate),
      ]);
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData(date);
  }, [date]);

  // 刷新数据
  const handleRefresh = () => {
    fetchAllData(date);
  };

  // 日期变更
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = e.target.value.replace(/-/g, '');
    setDate(newDate);
  };

  // 涨停股池统计
  const ztPoolStats = {
    total: ztPool.length,
    firstBoard: ztPool.filter(s => s.continuous_count === 1).length,
    continuous: ztPool.filter(s => s.continuous_count > 1).length,
    maxContinuous: Math.max(...ztPool.map(s => s.continuous_count), 0),
  };

  // 昨日涨停统计
  const ztPreviousStats = {
    total: ztPrevious.length,
    up: ztPrevious.filter(s => s.change_pct > 0).length,
    down: ztPrevious.filter(s => s.change_pct < 0).length,
    avgChange: ztPrevious.length > 0 
      ? ztPrevious.reduce((sum, s) => sum + s.change_pct, 0) / ztPrevious.length 
      : 0,
  };

  // 强势股统计
  const ztStrongStats = {
    total: ztStrong.length,
    newHigh: ztStrong.filter(s => s.is_new_high === '是').length,
    positive: ztStrong.filter(s => s.change_pct > 0).length,
    avgVolumeRatio: ztStrong.length > 0
      ? ztStrong.reduce((sum, s) => sum + s.volume_ratio, 0) / ztStrong.length
      : 0,
  };

  // 次新股统计
  const ztSubNewStats = {
    total: ztSubNew.length,
    positive: ztSubNew.filter(s => s.change_pct > 0).length,
    negative: ztSubNew.filter(s => s.change_pct < 0).length,
    avgTurnover: ztSubNew.length > 0
      ? ztSubNew.reduce((sum, s) => sum + s.turnover_rate, 0) / ztSubNew.length
      : 0,
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
          <Button onClick={handleRefresh} colorScheme="blue" isLoading={loading}>
            刷新
          </Button>
        </Flex>
      </Flex>

      <Tabs onChange={(index) => setActiveTab(index)} colorScheme="blue">
        <TabList>
          <Tab>涨停股池</Tab>
          <Tab>昨日涨停</Tab>
          <Tab>强势股</Tab>
          <Tab>次新股</Tab>
        </TabList>

        <TabPanels>
          {/* 涨停股池 */}
          <TabPanel>
            <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
              <Stat>
                <StatLabel>涨停总数</StatLabel>
                <StatNumber color="red.500">{ztPoolStats.total}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>首板</StatLabel>
                <StatNumber>{ztPoolStats.firstBoard}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>连板</StatLabel>
                <StatNumber color="orange.500">{ztPoolStats.continuous}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>最高连板</StatLabel>
                <StatNumber color="purple.500">{ztPoolStats.maxContinuous}</StatNumber>
              </Stat>
            </Grid>

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
                    {ztPool.map((stock) => (
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
                {ztPool.length === 0 && (
                  <Center h="200px">
                    <Text color="gray.500">暂无数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </TabPanel>

          {/* 昨日涨停 */}
          <TabPanel>
            <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
              <Stat>
                <StatLabel>股票总数</StatLabel>
                <StatNumber color="blue.500">{ztPreviousStats.total}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>上涨</StatLabel>
                <StatNumber color="red.500">{ztPreviousStats.up}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>下跌</StatLabel>
                <StatNumber color="green.500">{ztPreviousStats.down}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>平均涨幅</StatLabel>
                <StatNumber color={ztPreviousStats.avgChange > 0 ? 'red.500' : 'green.500'}>
                  {ztPreviousStats.avgChange.toFixed(2)}%
                </StatNumber>
              </Stat>
            </Grid>

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
                      <Th>涨停价</Th>
                      <Th>换手率</Th>
                      <Th>涨速</Th>
                      <Th>振幅</Th>
                      <Th>昨日封板</Th>
                      <Th>昨日连板</Th>
                      <Th>涨停统计</Th>
                      <Th>所属行业</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {ztPrevious.map((stock) => (
                      <Tr key={stock.serial_no}>
                        <Td>{stock.serial_no}</Td>
                        <Td>
                          <Text fontWeight="bold">{stock.code}</Text>
                        </Td>
                        <Td>{stock.name}</Td>
                        <Td color={stock.change_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.change_pct.toFixed(2)}%
                        </Td>
                        <Td>{stock.latest_price.toFixed(2)}</Td>
                        <Td>{stock.limit_up_price.toFixed(2)}</Td>
                        <Td>{stock.turnover_rate.toFixed(2)}%</Td>
                        <Td color={stock.speed_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.speed_pct.toFixed(2)}%
                        </Td>
                        <Td>{stock.amplitude.toFixed(2)}%</Td>
                        <Td>{stock.yesterday_seal_time}</Td>
                        <Td>
                          <Badge colorScheme={stock.yesterday_continuous > 1 ? 'purple' : 'blue'}>
                            {stock.yesterday_continuous}连板
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
                {ztPrevious.length === 0 && (
                  <Center h="200px">
                    <Text color="gray.500">暂无数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </TabPanel>

          {/* 强势股 */}
          <TabPanel>
            <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
              <Stat>
                <StatLabel>股票总数</StatLabel>
                <StatNumber color="blue.500">{ztStrongStats.total}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>创新高</StatLabel>
                <StatNumber color="red.500">{ztStrongStats.newHigh}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>上涨</StatLabel>
                <StatNumber color="red.500">{ztStrongStats.positive}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>平均量比</StatLabel>
                <StatNumber color="orange.500">{ztStrongStats.avgVolumeRatio.toFixed(2)}</StatNumber>
              </Stat>
            </Grid>

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
                      <Th>涨停价</Th>
                      <Th>换手率</Th>
                      <Th>涨速</Th>
                      <Th>量比</Th>
                      <Th>是否新高</Th>
                      <Th>涨停统计</Th>
                      <Th>入选理由</Th>
                      <Th>所属行业</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {ztStrong.map((stock) => (
                      <Tr key={stock.serial_no}>
                        <Td>{stock.serial_no}</Td>
                        <Td>
                          <Text fontWeight="bold">{stock.code}</Text>
                        </Td>
                        <Td>{stock.name}</Td>
                        <Td color={stock.change_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.change_pct.toFixed(2)}%
                        </Td>
                        <Td>{stock.latest_price.toFixed(2)}</Td>
                        <Td>{stock.limit_up_price.toFixed(2)}</Td>
                        <Td>{stock.turnover_rate.toFixed(2)}%</Td>
                        <Td color={stock.speed_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.speed_pct.toFixed(2)}%
                        </Td>
                        <Td color={stock.volume_ratio > 1 ? 'red.500' : 'green.500'}>
                          {stock.volume_ratio.toFixed(2)}
                        </Td>
                        <Td>
                          {stock.is_new_high === '是' ? (
                            <Badge colorScheme="red">是</Badge>
                          ) : (
                            <Text>-</Text>
                          )}
                        </Td>
                        <Td>{stock.zt_stats}</Td>
                        <Td>
                          <Badge colorScheme="purple">{stock.reason}</Badge>
                        </Td>
                        <Td>
                          <Badge colorScheme="green">{stock.industry}</Badge>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                {ztStrong.length === 0 && (
                  <Center h="200px">
                    <Text color="gray.500">暂无数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </TabPanel>

          {/* 次新股 */}
          <TabPanel>
            <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
              <Stat>
                <StatLabel>股票总数</StatLabel>
                <StatNumber color="blue.500">{ztSubNewStats.total}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>上涨</StatLabel>
                <StatNumber color="red.500">{ztSubNewStats.positive}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>下跌</StatLabel>
                <StatNumber color="green.500">{ztSubNewStats.negative}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>平均换手</StatLabel>
                <StatNumber color="orange.500">{ztSubNewStats.avgTurnover.toFixed(2)}%</StatNumber>
              </Stat>
            </Grid>

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
                      <Th>涨停价</Th>
                      <Th>换手率</Th>
                      <Th>开板几日</Th>
                      <Th>开板日期</Th>
                      <Th>上市日期</Th>
                      <Th>是否新高</Th>
                      <Th>涨停统计</Th>
                      <Th>所属行业</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {ztSubNew.map((stock) => (
                      <Tr key={stock.serial_no}>
                        <Td>{stock.serial_no}</Td>
                        <Td>
                          <Text fontWeight="bold">{stock.code}</Text>
                        </Td>
                        <Td>{stock.name}</Td>
                        <Td color={stock.change_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.change_pct.toFixed(2)}%
                        </Td>
                        <Td>{stock.latest_price.toFixed(2)}</Td>
                        <Td>{stock.limit_up_price.toFixed(2)}</Td>
                        <Td color={stock.turnover_rate > 10 ? 'red.500' : 'green.500'}>
                          {stock.turnover_rate.toFixed(2)}%
                        </Td>
                        <Td>{stock.open_days}天</Td>
                        <Td>{stock.open_date}</Td>
                        <Td>{stock.list_date}</Td>
                        <Td>
                          {stock.is_new_high === '是' ? (
                            <Badge colorScheme="red">是</Badge>
                          ) : (
                            <Text>-</Text>
                          )}
                        </Td>
                        <Td>{stock.zt_stats}</Td>
                        <Td>
                          <Badge colorScheme="green">{stock.industry}</Badge>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                {ztSubNew.length === 0 && (
                  <Center h="200px">
                    <Text color="gray.500">暂无数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default EastMoneyZtBoardPage;
