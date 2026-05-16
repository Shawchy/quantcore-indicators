/**
 * 东方财富综合涨停板行情页面
 * 包含：涨停股池、昨日涨停、强势股、次新股
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Flex, Grid, Heading, Input, InputGroup, Spinner, Stat, Table, Tabs, Text } from '@chakra-ui/react'
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
  const [, setActiveTab] = useState("涨停股池");

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
          <InputGroup width="200px" endAddon="日期">
            <Input
              type="date"
              value={date.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}
              onChange={handleDateChange}
            />
          </InputGroup>
          <Button onClick={handleRefresh} colorPalette="blue" loading={loading}>
            刷新
          </Button>
        </Flex>
      </Flex>

      <Tabs.Root onValueChange={(e) => setActiveTab(e.value)} colorPalette="blue">
        <Tabs.List>
          <Tabs.Trigger value="涨停股池">涨停股池</Tabs.Trigger>
          <Tabs.Trigger value="昨日涨停">昨日涨停</Tabs.Trigger>
          <Tabs.Trigger value="强势股">强势股</Tabs.Trigger>
          <Tabs.Trigger value="次新股">次新股</Tabs.Trigger>
        </Tabs.List>

        <Tabs.ContentGroup>
          {/* 涨停股池 */}
          <Tabs.Content value="昨日涨停">
            <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
              <Stat.Root>
                <Stat.Label>涨停总数</Stat.Label>
                <Stat.ValueText color="red.500">{ztPoolStats.total}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>首板</Stat.Label>
                <Stat.ValueText>{ztPoolStats.firstBoard}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>连板</Stat.Label>
                <Stat.ValueText color="orange.500">{ztPoolStats.continuous}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>最高连板</Stat.Label>
                <Stat.ValueText color="purple.500">{ztPoolStats.maxContinuous}</Stat.ValueText>
              </Stat.Root>
            </Grid>

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
                    {ztPool.map((stock) => (
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
                {ztPool.length === 0 && (
                  <Center h="200px">
                    <Text color="gray.500">暂无数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </Tabs.Content>

          {/* 昨日涨停 */}
          <Tabs.Content value="强势股">
            <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
              <Stat.Root>
                <Stat.Label>股票总数</Stat.Label>
                <Stat.ValueText color="blue.500">{ztPreviousStats.total}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>上涨</Stat.Label>
                <Stat.ValueText color="red.500">{ztPreviousStats.up}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>下跌</Stat.Label>
                <Stat.ValueText color="green.500">{ztPreviousStats.down}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>平均涨幅</Stat.Label>
                <Stat.ValueText color={ztPreviousStats.avgChange > 0 ? 'red.500' : 'green.500'}>
                  {ztPreviousStats.avgChange.toFixed(2)}%
                </Stat.ValueText>
              </Stat.Root>
            </Grid>

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
                      <Table.ColumnHeader>涨停价</Table.ColumnHeader>
                      <Table.ColumnHeader>换手率</Table.ColumnHeader>
                      <Table.ColumnHeader>涨速</Table.ColumnHeader>
                      <Table.ColumnHeader>振幅</Table.ColumnHeader>
                      <Table.ColumnHeader>昨日封板</Table.ColumnHeader>
                      <Table.ColumnHeader>昨日连板</Table.ColumnHeader>
                      <Table.ColumnHeader>涨停统计</Table.ColumnHeader>
                      <Table.ColumnHeader>所属行业</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {ztPrevious.map((stock) => (
                      <Table.Row key={stock.serial_no}>
                        <Table.Cell>{stock.serial_no}</Table.Cell>
                        <Table.Cell>
                          <Text fontWeight="bold">{stock.code}</Text>
                        </Table.Cell>
                        <Table.Cell>{stock.name}</Table.Cell>
                        <Table.Cell color={stock.change_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.change_pct.toFixed(2)}%
                        </Table.Cell>
                        <Table.Cell>{stock.latest_price.toFixed(2)}</Table.Cell>
                        <Table.Cell>{stock.limit_up_price.toFixed(2)}</Table.Cell>
                        <Table.Cell>{stock.turnover_rate.toFixed(2)}%</Table.Cell>
                        <Table.Cell color={stock.speed_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.speed_pct.toFixed(2)}%
                        </Table.Cell>
                        <Table.Cell>{stock.amplitude.toFixed(2)}%</Table.Cell>
                        <Table.Cell>{stock.yesterday_seal_time}</Table.Cell>
                        <Table.Cell>
                          <Badge colorPalette={stock.yesterday_continuous > 1 ? 'purple' : 'blue'}>
                            {stock.yesterday_continuous}连板
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
                {ztPrevious.length === 0 && (
                  <Center h="200px">
                    <Text color="gray.500">暂无数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </Tabs.Content>

          {/* 强势股 */}
          <Tabs.Content value="次新股">
            <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
              <Stat.Root>
                <Stat.Label>股票总数</Stat.Label>
                <Stat.ValueText color="blue.500">{ztStrongStats.total}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>创新高</Stat.Label>
                <Stat.ValueText color="red.500">{ztStrongStats.newHigh}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>上涨</Stat.Label>
                <Stat.ValueText color="red.500">{ztStrongStats.positive}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>平均量比</Stat.Label>
                <Stat.ValueText color="orange.500">{ztStrongStats.avgVolumeRatio.toFixed(2)}</Stat.ValueText>
              </Stat.Root>
            </Grid>

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
                      <Table.ColumnHeader>涨停价</Table.ColumnHeader>
                      <Table.ColumnHeader>换手率</Table.ColumnHeader>
                      <Table.ColumnHeader>涨速</Table.ColumnHeader>
                      <Table.ColumnHeader>量比</Table.ColumnHeader>
                      <Table.ColumnHeader>是否新高</Table.ColumnHeader>
                      <Table.ColumnHeader>涨停统计</Table.ColumnHeader>
                      <Table.ColumnHeader>入选理由</Table.ColumnHeader>
                      <Table.ColumnHeader>所属行业</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {ztStrong.map((stock) => (
                      <Table.Row key={stock.serial_no}>
                        <Table.Cell>{stock.serial_no}</Table.Cell>
                        <Table.Cell>
                          <Text fontWeight="bold">{stock.code}</Text>
                        </Table.Cell>
                        <Table.Cell>{stock.name}</Table.Cell>
                        <Table.Cell color={stock.change_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.change_pct.toFixed(2)}%
                        </Table.Cell>
                        <Table.Cell>{stock.latest_price.toFixed(2)}</Table.Cell>
                        <Table.Cell>{stock.limit_up_price.toFixed(2)}</Table.Cell>
                        <Table.Cell>{stock.turnover_rate.toFixed(2)}%</Table.Cell>
                        <Table.Cell color={stock.speed_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.speed_pct.toFixed(2)}%
                        </Table.Cell>
                        <Table.Cell color={stock.volume_ratio > 1 ? 'red.500' : 'green.500'}>
                          {stock.volume_ratio.toFixed(2)}
                        </Table.Cell>
                        <Table.Cell>
                          {stock.is_new_high === '是' ? (
                            <Badge colorPalette="red">是</Badge>
                          ) : (
                            <Text>-</Text>
                          )}
                        </Table.Cell>
                        <Table.Cell>{stock.zt_stats}</Table.Cell>
                        <Table.Cell>
                          <Badge colorPalette="purple">{stock.reason}</Badge>
                        </Table.Cell>
                        <Table.Cell>
                          <Badge colorPalette="green">{stock.industry}</Badge>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
                {ztStrong.length === 0 && (
                  <Center h="200px">
                    <Text color="gray.500">暂无数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </Tabs.Content>

          {/* 次新股 */}
          <Tabs.Content value="涨停股池">
            <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
              <Stat.Root>
                <Stat.Label>股票总数</Stat.Label>
                <Stat.ValueText color="blue.500">{ztSubNewStats.total}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>上涨</Stat.Label>
                <Stat.ValueText color="red.500">{ztSubNewStats.positive}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>下跌</Stat.Label>
                <Stat.ValueText color="green.500">{ztSubNewStats.negative}</Stat.ValueText>
              </Stat.Root>
              <Stat.Root>
                <Stat.Label>平均换手</Stat.Label>
                <Stat.ValueText color="orange.500">{ztSubNewStats.avgTurnover.toFixed(2)}%</Stat.ValueText>
              </Stat.Root>
            </Grid>

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
                      <Table.ColumnHeader>涨停价</Table.ColumnHeader>
                      <Table.ColumnHeader>换手率</Table.ColumnHeader>
                      <Table.ColumnHeader>开板几日</Table.ColumnHeader>
                      <Table.ColumnHeader>开板日期</Table.ColumnHeader>
                      <Table.ColumnHeader>上市日期</Table.ColumnHeader>
                      <Table.ColumnHeader>是否新高</Table.ColumnHeader>
                      <Table.ColumnHeader>涨停统计</Table.ColumnHeader>
                      <Table.ColumnHeader>所属行业</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {ztSubNew.map((stock) => (
                      <Table.Row key={stock.serial_no}>
                        <Table.Cell>{stock.serial_no}</Table.Cell>
                        <Table.Cell>
                          <Text fontWeight="bold">{stock.code}</Text>
                        </Table.Cell>
                        <Table.Cell>{stock.name}</Table.Cell>
                        <Table.Cell color={stock.change_pct > 0 ? 'red.500' : 'green.500'}>
                          {stock.change_pct.toFixed(2)}%
                        </Table.Cell>
                        <Table.Cell>{stock.latest_price.toFixed(2)}</Table.Cell>
                        <Table.Cell>{stock.limit_up_price.toFixed(2)}</Table.Cell>
                        <Table.Cell color={stock.turnover_rate > 10 ? 'red.500' : 'green.500'}>
                          {stock.turnover_rate.toFixed(2)}%
                        </Table.Cell>
                        <Table.Cell>{stock.open_days}天</Table.Cell>
                        <Table.Cell>{stock.open_date}</Table.Cell>
                        <Table.Cell>{stock.list_date}</Table.Cell>
                        <Table.Cell>
                          {stock.is_new_high === '是' ? (
                            <Badge colorPalette="red">是</Badge>
                          ) : (
                            <Text>-</Text>
                          )}
                        </Table.Cell>
                        <Table.Cell>{stock.zt_stats}</Table.Cell>
                        <Table.Cell>
                          <Badge colorPalette="green">{stock.industry}</Badge>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
                {ztSubNew.length === 0 && (
                  <Center h="200px">
                    <Text color="gray.500">暂无数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </Tabs.Content>
        </Tabs.ContentGroup>
      </Tabs.Root>
    </Box>
  );
};

export default EastMoneyZtBoardPage;
