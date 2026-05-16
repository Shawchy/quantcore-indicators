/**
 * 东方财富千股千评页面
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Dialog, Flex, Grid, Heading, Input, InputGroup, Spinner, Stat, Table, Tabs, Text, useDisclosure } from '@chakra-ui/react'
import {
  eastMoneyApi,
  type StockComment,
  type StockCommentDetailInstitution,
  type StockCommentDetailScore,
} from '@/services/akshare/index';
import EChartsReactCore from 'echarts-for-react/lib/core'
import echarts from '@/lib/echarts'

const EastMoneyStockCommentPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [comments, setComments] = useState<StockComment[]>([]);
  const [searchCode, setSearchCode] = useState('');
  const [selectedStock, setSelectedStock] = useState<StockComment | null>(null);
  const [institutionData, setInstitutionData] = useState<StockCommentDetailInstitution[]>([]);
  const [scoreData, setScoreData] = useState<StockCommentDetailScore[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  
  const { open, onOpen, setOpen } = useDisclosure();

  // 获取千股千评数据
  const fetchComments = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockComment();
      setComments(result.data || []);
    } catch (error) {
      console.error('获取千股千评数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取个股详情
  const fetchStockDetail = async (code: string) => {
    setDetailLoading(true);
    try {
      const [institutionRes, scoreRes] = await Promise.all([
        eastMoneyApi.getStockCommentDetailInstitution(code),
        eastMoneyApi.getStockCommentDetailScore(code),
      ]);
      setInstitutionData(institutionRes.data || []);
      setScoreData(scoreRes.data || []);
    } catch (error) {
      console.error('获取个股详情失败:', error);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, []);

  // 刷新数据
  const handleRefresh = () => {
    fetchComments();
  };

  // 查看详情
  const handleViewDetail = (stock: StockComment) => {
    setSelectedStock(stock);
    fetchStockDetail(stock.code);
    onOpen();
  };

  // 搜索股票
  const handleSearch = () => {
    if (!searchCode) {
      fetchComments();
      return;
    }
    const filtered = comments.filter(c => c.code.includes(searchCode) || c.name.includes(searchCode));
    setComments(filtered);
  };

  // 统计数据
  const stats = {
    total: comments.length,
    positive: comments.filter(c => c.change_pct > 0).length,
    negative: comments.filter(c => c.change_pct < 0).length,
    avgScore: comments.length > 0 
      ? comments.reduce((sum, c) => sum + c.comprehensive_score, 0) / comments.length 
      : 0,
  };

  return (
    <Box p={6}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">东方财富千股千评</Heading>
        <Flex gap={4} align="center">
          <InputGroup width="300px" startAddon="股票代码/名称">
  <Input
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              placeholder="输入股票代码或名称"
            />
</InputGroup>
          <Button onClick={handleSearch} colorPalette="blue">
            搜索
          </Button>
          <Button onClick={handleRefresh} colorPalette="green" loading={loading}>
            刷新
          </Button>
        </Flex>
      </Flex>

      {/* 统计信息 */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
        <Stat.Root>
          <Stat.Label>股票总数</Stat.Label>
          <Stat.ValueText color="blue.500">{stats.total}</Stat.ValueText>
        </Stat.Root>
        <Stat.Root>
          <Stat.Label>上涨</Stat.Label>
          <Stat.ValueText color="red.500">{stats.positive}</Stat.ValueText>
        </Stat.Root>
        <Stat.Root>
          <Stat.Label>下跌</Stat.Label>
          <Stat.ValueText color="green.500">{stats.negative}</Stat.ValueText>
        </Stat.Root>
        <Stat.Root>
          <Stat.Label>平均综合得分</Stat.Label>
          <Stat.ValueText color="purple.500">{stats.avgScore.toFixed(2)}</Stat.ValueText>
        </Stat.Root>
      </Grid>

      {/* 千股千评表格 */}
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
                <Table.ColumnHeader>最新价</Table.ColumnHeader>
                <Table.ColumnHeader>涨跌幅</Table.ColumnHeader>
                <Table.ColumnHeader>换手率</Table.ColumnHeader>
                <Table.ColumnHeader>市盈率</Table.ColumnHeader>
                <Table.ColumnHeader>主力成本</Table.ColumnHeader>
                <Table.ColumnHeader>机构参与度</Table.ColumnHeader>
                <Table.ColumnHeader>综合得分</Table.ColumnHeader>
                <Table.ColumnHeader>上升</Table.ColumnHeader>
                <Table.ColumnHeader>目前排名</Table.ColumnHeader>
                <Table.ColumnHeader>关注指数</Table.ColumnHeader>
                <Table.ColumnHeader>操作</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {comments.map((stock) => (
                <Table.Row key={stock.serial_no}>
                  <Table.Cell>{stock.serial_no}</Table.Cell>
                  <Table.Cell>
                    <Text fontWeight="bold">{stock.code}</Text>
                  </Table.Cell>
                  <Table.Cell>{stock.name}</Table.Cell>
                  <Table.Cell>{stock.latest_price.toFixed(2)}</Table.Cell>
                  <Table.Cell color={stock.change_pct > 0 ? 'red.500' : 'green.500'}>
                    {stock.change_pct.toFixed(2)}%
                  </Table.Cell>
                  <Table.Cell>{stock.turnover_rate.toFixed(2)}%</Table.Cell>
                  <Table.Cell>{stock.pe_ratio.toFixed(2)}</Table.Cell>
                  <Table.Cell>{stock.main_force_cost.toFixed(2)}</Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette={stock.institution_participation > 30 ? 'red' : 'blue'}>
                      {stock.institution_participation.toFixed(2)}%
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette={stock.comprehensive_score > 60 ? 'green' : 'orange'}>
                      {stock.comprehensive_score.toFixed(2)}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette={stock.rise > 0 ? 'red' : 'green'}>
                      {stock.rise > 0 ? '+' : ''}{stock.rise}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>{stock.current_rank}</Table.Cell>
                  <Table.Cell>{stock.attention_index.toFixed(1)}</Table.Cell>
                  <Table.Cell>
                    <Button 
                      size="sm" 
                      colorPalette="blue"
                      onClick={() => handleViewDetail(stock)}
                    >
                      详情
                    </Button>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
          {comments.length === 0 && (
            <Center h="200px">
              <Text color="gray.500">暂无数据</Text>
            </Center>
          )}
        </Box>
      )}

      {/* 详情弹窗 */}
      <Dialog.Root open={open} onOpenChange={(details) => setOpen(details.open)} size="full">
        <Dialog.Backdrop />
        <Dialog.Content>
          <Dialog.Header>
            {selectedStock?.code} - {selectedStock?.name} 详情
          </Dialog.Header>
          <Dialog.CloseTrigger />
          <Dialog.Body>
            {detailLoading ? (
              <Center h="400px">
                <Spinner size="xl" />
              </Center>
            ) : (
              <Tabs.Root colorPalette="blue">
                <Tabs.List>
                  <Tabs.Trigger value="机构参与度">机构参与度</Tabs.Trigger>
                  <Tabs.Trigger value="历史评分">历史评分</Tabs.Trigger>
                </Tabs.List>
                <Tabs.ContentGroup>
                  {/* 机构参与度 */}
                  <Tabs.Content value="历史评分">
                    <Box h="400px">
                      <EChartsReactCore echarts={echarts}
                        option={{
                          grid: { left: 60, right: 20, top: 30, bottom: 40 },
                          xAxis: { type: 'category', data: institutionData.map(d => d.trading_day), axisLabel: { color: '#64748b' } },
                          yAxis: { type: 'value', axisLabel: { color: '#64748b' } },
                          tooltip: { trigger: 'axis' },
                          series: [{
                            name: '机构参与度',
                            type: 'line',
                            data: institutionData.map(d => d.institution_participation),
                            lineStyle: { color: '#8884d8', width: 2 },
                            itemStyle: { color: '#8884d8' },
                            symbol: 'circle',
                            symbolSize: 6,
                          }]
                        }}
                        style={{ height: '100%', width: '100%' }}
                      />
                    </Box>
                  </Tabs.Content>

                  {/* 历史评分 */}
                  <Tabs.Content value="机构参与度">
                    <Box h="400px">
                      <EChartsReactCore echarts={echarts}
                        option={{
                          grid: { left: 60, right: 20, top: 30, bottom: 40 },
                          xAxis: { type: 'category', data: scoreData.map(d => d.trading_day), axisLabel: { color: '#64748b' } },
                          yAxis: { type: 'value', min: 0, max: 100, axisLabel: { color: '#64748b' } },
                          tooltip: { trigger: 'axis' },
                          series: [{
                            name: '综合评分',
                            type: 'line',
                            data: scoreData.map(d => d.score),
                            lineStyle: { color: '#82ca9d', width: 2 },
                            itemStyle: { color: '#82ca9d' },
                            symbol: 'circle',
                            symbolSize: 6,
                          }]
                        }}
                        style={{ height: '100%', width: '100%' }}
                      />
                    </Box>
                  </Tabs.Content>
                </Tabs.ContentGroup>
              </Tabs.Root>
            )}
          </Dialog.Body>
          <Dialog.Footer>
            <Button onClick={() => setOpen(false)}>关闭</Button>
          </Dialog.Footer>
        </Dialog.Content>
      </Dialog.Root>
    </Box>
  );
};

export default EastMoneyStockCommentPage;
