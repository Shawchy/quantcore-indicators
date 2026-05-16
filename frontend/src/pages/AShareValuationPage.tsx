/**
 * A 股估值指标页面
 * 包含：百度估值、个股估值、涨跌投票
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Field, Flex, HStack, Heading, Input, InputGroup, NativeSelect, SimpleGrid, Spacer, Stat, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockZhValuationBaidu,
  type StockValueEM,
  type StockZhVoteBaidu,
} from '@/services/akshare/index';

const AShareValuationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("百度估值");
  const [loading, setLoading] = useState(false);
  
  // 输入参数
  const [symbol, setSymbol] = useState('002044');
  const [indicator, setIndicator] = useState('总市值');
  const [period, setPeriod] = useState('近一年');
  const [voteIndicator, setVoteIndicator] = useState('股票');
  
  // 百度估值数据
  const [valuationData, setValuationData] = useState<StockZhValuationBaidu[]>([]);
  
  // 个股估值数据
  const [valueData, setValueData] = useState<StockValueEM[]>([]);
  
  // 涨跌投票数据
  const [voteData, setVoteData] = useState<StockZhVoteBaidu[]>([]);
  
  ;

  const valuationIndicators = ['总市值', '市盈率 (TTM)', '市盈率 (静)', '市净率', '市现率'];
  const periods = ['近一年', '近三年', '近五年', '近十年', '全部'];

  // 获取百度估值数据
  const fetchValuationData = async () => {
    if (!symbol) {
      toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
      return;
    }
    
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockZhValuationBaidu(symbol, indicator, period);
      setValuationData((result as any).data || []);
      toaster.create({ 
        title: `获取成功，共${(result as any).data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取百度估值数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取个股估值数据
  const fetchValueData = async () => {
    if (!symbol) {
      toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
      return;
    }
    
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockValueEM(symbol);
      setValueData((result as any).data || []);
      toaster.create({ 
        title: `获取成功，共${(result as any).data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取个股估值数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取涨跌投票数据
  const fetchVoteData = async () => {
    if (!symbol) {
      toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
      return;
    }
    
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockZhVoteBaidu(symbol, voteIndicator);
      setVoteData((result as any).data || []);
      toaster.create({ 
        title: `获取成功，共${(result as any).data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取涨跌投票数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载数据
    fetchValuationData();
  }, []);

  // 切换 Tab 时加载对应数据
  useEffect(() => {
    if (activeTab === "百度估值" && valuationData.length === 0) {
      fetchValuationData();
    } else if (activeTab === "个股估值" && valueData.length === 0) {
      fetchValueData();
    } else if (activeTab === "涨跌投票" && voteData.length === 0) {
      fetchVoteData();
    }
  }, [activeTab]);

  // 格式化日期显示
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return dateStr;
  };

  // 渲染投票比例
  const renderVoteRatio = (ratio: number | string | null) => {
    if (ratio === null) return '-';
    
    const ratioNum = typeof ratio === 'string' ? parseFloat(ratio.replace('%', '')) : ratio;
    const colorScheme = ratioNum > 50 ? 'green' : 'red';
    
    return (
      <Badge colorPalette={colorScheme}>
        {typeof ratio === 'string' ? ratio : `${ratio}%`}
      </Badge>
    );
  };

  return (
    <Box p={8}>
      <Heading mb={6}>A 股估值指标</Heading>
      
      <Tabs.Root value={activeTab} onValueChange={(e) => setActiveTab(e.value)} mb={6}>
        <Tabs.List>
          <Tabs.Trigger value="百度估值">百度估值</Tabs.Trigger>
          <Tabs.Trigger value="个股估值">个股估值</Tabs.Trigger>
          <Tabs.Trigger value="涨跌投票">涨跌投票</Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>

      <Tabs.ContentGroup>
        {/* 百度估值 */}
        <Tabs.Content value="个股估值">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup w="150px" startAddon="股票代码">
  <Input
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="002044"
                />
</InputGroup>
              
              <Field.Root w="150px">
                <Field.Label mb={1} fontSize="sm">估值指标</Field.Label>
                <NativeSelect.Root><NativeSelect.Field
                  
                  value={indicator}
                  onChange={(e) => setIndicator(e.target.value)}
                >
                  {valuationIndicators.map((ind) => (
                    <option key={ind} value={ind}>{ind}</option>
                  ))}
                </NativeSelect.Field></NativeSelect.Root>
              </Field.Root>
              
              <Field.Root w="150px">
                <Field.Label mb={1} fontSize="sm">时间范围</Field.Label>
                <NativeSelect.Root><NativeSelect.Field
                  
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                >
                  {periods.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </NativeSelect.Field></NativeSelect.Root>
              </Field.Root>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchValuationData}
                loading={loading && activeTab === "百度估值"}
              >
                查询
              </Button>
            </Flex>
            
            {valuationData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(valuationData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新{indicator}</Stat.Label>
                  <Stat.ValueText>
                    {valuationData[0]?.value?.toLocaleString() || '-'}
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>数据条数</Stat.Label>
                  <Stat.ValueText>{valuationData.length}</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader >{indicator}</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {valuationData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.name || index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell >{item.value?.toLocaleString() || '-'}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {valuationData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {valuationData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 个股估值 */}
        <Tabs.Content value="涨跌投票">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup w="150px" startAddon="股票代码">
  <Input
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="300766"
                />
</InputGroup>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchValueData}
                loading={loading && activeTab === "个股估值"}
              >
                查询
              </Button>
            </Flex>
            
            {valueData.length > 0 && (
              <SimpleGrid columns={4} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(valueData[0]?.report_date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新收盘价</Stat.Label>
                  <Stat.ValueText>{valueData[0]?.close_price?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>涨跌幅</Stat.Label>
                  <Stat.ValueText>
                    {valueData[0]?.change_pct !== null 
                      ? `${valueData[0]!.change_pct!.toFixed(2)}%` 
                      : '-'}
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>PE(TTM)</Stat.Label>
                  <Stat.ValueText>{valueData[0]?.pe_ttm?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>市净率</Stat.Label>
                  <Stat.ValueText>{valueData[0]?.pb?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>总市值</Stat.Label>
                  <Stat.ValueText>
                    {valueData[0]?.total_mv 
                      ? `${(valueData[0]!.total_mv! / 100000000).toFixed(2)}亿` 
                      : '-'}
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>PEG 值</Stat.Label>
                  <Stat.ValueText>{valueData[0]?.peg?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>市销率</Stat.Label>
                  <Stat.ValueText>{valueData[0]?.ps?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>数据日期</Table.ColumnHeader>
                    <Table.ColumnHeader >收盘价</Table.ColumnHeader>
                    <Table.ColumnHeader >涨跌幅</Table.ColumnHeader>
                    <Table.ColumnHeader >PE(TTM)</Table.ColumnHeader>
                    <Table.ColumnHeader >PE(静)</Table.ColumnHeader>
                    <Table.ColumnHeader >市净率</Table.ColumnHeader>
                    <Table.ColumnHeader >PEG 值</Table.ColumnHeader>
                    <Table.ColumnHeader >市现率</Table.ColumnHeader>
                    <Table.ColumnHeader >市销率</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {valueData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.name || index}>
                      <Table.Cell>{formatDate(item.report_date)}</Table.Cell>
                      <Table.Cell >{item.close_price?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >
                        {item.change_pct !== null 
                          ? `${item.change_pct.toFixed(2)}%` 
                          : '-'}
                      </Table.Cell>
                      <Table.Cell >{item.pe_ttm?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.pe_static?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.pb?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.peg?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.pc?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.ps?.toFixed(2) || '-'}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {valueData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {valueData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 涨跌投票 */}
        <Tabs.Content value="百度估值">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup w="150px" startAddon="股票/指数代码">
  <Input
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="000001"
                />
</InputGroup>
              
              <Field.Root w="120px">
                <Field.Label mb={1} fontSize="sm">类型</Field.Label>
                <NativeSelect.Root><NativeSelect.Field
                  
                  value={voteIndicator}
                  onChange={(e) => setVoteIndicator(e.target.value)}
                >
                  <option value="股票">股票</option>
                  <option value="指数">指数</option>
                </NativeSelect.Field></NativeSelect.Root>
              </Field.Root>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchVoteData}
                loading={loading && activeTab === "涨跌投票"}
              >
                查询
              </Button>
            </Flex>
            
            {voteData.length > 0 && (
              <SimpleGrid columns={4} gap={4} mb={4}>
                {voteData.map((item, index) => (
                  <Stat.Root key={item.code || item.name || index}>
                    <Stat.Label>{item.period}</Stat.Label>
                    <Stat.ValueText>
                      <HStack gap={2}>
                        <Badge colorPalette="green">
                          看涨：{item.vote_up?.toLocaleString() || '-'}
                        </Badge>
                        <Badge colorPalette="red">
                          看跌：{item.vote_down?.toLocaleString() || '-'}
                        </Badge>
                      </HStack>
                    </Stat.ValueText>
                    <Stat.HelpText>
                      <HStack gap={2}>
                        {renderVoteRatio(item.vote_up_ratio)}
                        {renderVoteRatio(item.vote_down_ratio)}
                      </HStack>
                    </Stat.HelpText>
                  </Stat.Root>
                ))}
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>周期</Table.ColumnHeader>
                    <Table.ColumnHeader >看涨票数</Table.ColumnHeader>
                    <Table.ColumnHeader >看跌票数</Table.ColumnHeader>
                    <Table.ColumnHeader >看涨比例</Table.ColumnHeader>
                    <Table.ColumnHeader >看跌比例</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {voteData.map((item, index) => (
                    <Table.Row key={item.code || item.name || index}>
                      <Table.Cell>{item.period}</Table.Cell>
                      <Table.Cell >
                        <Badge colorPalette="green">
                          {item.vote_up?.toLocaleString() || '-'}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell >
                        <Badge colorPalette="red">
                          {item.vote_down?.toLocaleString() || '-'}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell >{renderVoteRatio(item.vote_up_ratio)}</Table.Cell>
                      <Table.Cell >{renderVoteRatio(item.vote_down_ratio)}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          </Box>
        </Tabs.Content>
      </Tabs.ContentGroup>
    </Box>
  );
};

export default AShareValuationPage;
