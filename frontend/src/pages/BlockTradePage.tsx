/**
 * 大宗交易页面
 * 包含：市场统计、每日明细
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Field, Flex, Heading, Input, InputGroup, NativeSelect, SimpleGrid, Spacer, Stat, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockDzjySctj,
  type StockDzjyMrmx,
} from '@/services/akshare/index';

const BlockTradePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("市场统计");
  const [loading, setLoading] = useState(false);
  
  // 输入参数
  const [symbol, setSymbol] = useState('A 股');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // 市场统计数据
  const [sctjData, setSctjData] = useState<StockDzjySctj[]>([]);
  
  // 每日明细数据
  const [mrmxData, setMrmxData] = useState<StockDzjyMrmx[]>([]);
  
  ;

  const symbols = [
    { value: 'A 股', label: 'A 股' },
    { value: 'B 股', label: 'B 股' },
    { value: '基金', label: '基金' },
    { value: '债券', label: '债券' },
  ];

  // 获取市场统计数据
  const fetchSctjData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockDzjySctj();
      setSctjData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取大宗交易市场统计数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取每日明细数据
  const fetchMrmxData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockDzjyMrmx(symbol, startDate, endDate);
      setMrmxData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取大宗交易每日明细数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载数据
    fetchSctjData();
  }, []);

  // 切换 Tab 时加载对应数据
  useEffect(() => {
    if (activeTab === "市场统计" && sctjData.length === 0) {
      fetchSctjData();
    } else if (activeTab === "每日明细" && mrmxData.length === 0) {
      fetchMrmxData();
    }
  }, [activeTab]);

  // 格式化日期显示
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return dateStr;
  };

  // 格式化金额显示
  const formatAmount = (amount: number | null, unit: '万' | '亿' = '万') => {
    if (amount === null) return '-';
    if (unit === '万') {
      return `${(amount / 10000).toFixed(2)}万`;
    } else {
      return `${(amount / 100000000).toFixed(2)}亿`;
    }
  };

  // 渲染折溢率
  const renderPremiumRatio = (ratio: number | null) => {
    if (ratio === null) return '-';
    const colorScheme = ratio > 0 ? 'red' : ratio < 0 ? 'green' : 'gray';
    return (
      <Badge colorPalette={colorScheme}>
        {ratio.toFixed(2)}%
      </Badge>
    );
  };

  // 渲染涨跌幅
  const renderChangePct = (pct: number | null) => {
    if (pct === null) return '-';
    const colorScheme = pct > 0 ? 'red' : pct < 0 ? 'green' : 'gray';
    return (
      <Badge colorPalette={colorScheme}>
        {pct.toFixed(2)}%
      </Badge>
    );
  };

  return (
    <Box p={8}>
      <Heading mb={6}>大宗交易</Heading>
      
      <Tabs.Root value={activeTab} onValueChange={(e) => setActiveTab(e.value)} mb={6}>
        <Tabs.List>
          <Tabs.Trigger value="市场统计">市场统计</Tabs.Trigger>
          <Tabs.Trigger value="每日明细">每日明细</Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>

      <Tabs.ContentGroup>
        {/* 市场统计 */}
        <Tabs.Content value="每日明细">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchSctjData}
                loading={loading && activeTab === "市场统计"}
              >
                刷新数据
              </Button>
            </Flex>
            
            {sctjData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(sctjData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>上证指数</Stat.Label>
                  <Stat.ValueText>{sctjData[0]?.sh_index?.toFixed(2) || '-'}</Stat.ValueText>
                  <Stat.HelpText>
                    {sctjData[0]?.sh_change_pct !== null 
                      ? `${sctjData[0]!.sh_change_pct! > 0 ? '+' : ''}${sctjData[0]!.sh_change_pct!.toFixed(2)}%`
                      : '-'}
                  </Stat.HelpText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>成交总额</Stat.Label>
                  <Stat.ValueText>{formatAmount(sctjData[0]?.total_amount, '亿')}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>溢价成交额</Stat.Label>
                  <Stat.ValueText>{formatAmount(sctjData[0]?.premium_amount, '亿')}</Stat.ValueText>
                  <Stat.HelpText>
                    占比{sctjData[0]?.premium_ratio?.toFixed(2)}%
                  </Stat.HelpText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>折价成交额</Stat.Label>
                  <Stat.ValueText>{formatAmount(sctjData[0]?.discount_amount, '亿')}</Stat.ValueText>
                  <Stat.HelpText>
                    占比{sctjData[0]?.discount_ratio?.toFixed(2)}%
                  </Stat.HelpText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>数据条数</Stat.Label>
                  <Stat.ValueText>{sctjData.length}</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader >上证指数</Table.ColumnHeader>
                    <Table.ColumnHeader >涨跌幅</Table.ColumnHeader>
                    <Table.ColumnHeader >成交总额</Table.ColumnHeader>
                    <Table.ColumnHeader >溢价成交额</Table.ColumnHeader>
                    <Table.ColumnHeader >溢价占比</Table.ColumnHeader>
                    <Table.ColumnHeader >折价成交额</Table.ColumnHeader>
                    <Table.ColumnHeader >折价占比</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {sctjData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.trade_date || index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell >{item.sh_index?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >
                        {item.sh_change_pct !== null 
                          ? (
                            <Badge colorPalette={item.sh_change_pct > 0 ? 'red' : 'green'}>
                              {item.sh_change_pct.toFixed(2)}%
                            </Badge>
                          )
                          : '-'}
                      </Table.Cell>
                      <Table.Cell >{formatAmount(item.total_amount, '亿')}</Table.Cell>
                      <Table.Cell >{formatAmount(item.premium_amount, '万')}</Table.Cell>
                      <Table.Cell >{item.premium_ratio?.toFixed(2)}%</Table.Cell>
                      <Table.Cell >{formatAmount(item.discount_amount, '万')}</Table.Cell>
                      <Table.Cell >{item.discount_ratio?.toFixed(2)}%</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {sctjData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {sctjData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 每日明细 */}
        <Tabs.Content value="市场统计">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <Field.Root w="150px">
                <Field.Label mb={1} fontSize="sm">证券类型</Field.Label>
                <NativeSelect.Root><NativeSelect.Field
                  
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                >
                  {symbols.map((sym) => (
                    <option key={sym.value} value={sym.value}>{sym.label}</option>
                  ))}
                </NativeSelect.Field></NativeSelect.Root>
              </Field.Root>
              
              <InputGroup w="180px" startAddon="开始日期">
  <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
</InputGroup>
              
              <InputGroup w="180px" startAddon="结束日期">
  <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
</InputGroup>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchMrmxData}
                loading={loading && activeTab === "每日明细"}
              >
                查询
              </Button>
            </Flex>
            
            {mrmxData.length > 0 && (
              <SimpleGrid columns={4} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(mrmxData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>交易笔数</Stat.Label>
                  <Stat.ValueText>{mrmxData.length}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>成交总额</Stat.Label>
                  <Stat.ValueText>
                    {formatAmount(mrmxData.reduce((sum, item) => sum + (item.amount || 0), 0), '亿')}
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>平均折溢率</Stat.Label>
                  <Stat.ValueText>
                    {mrmxData.reduce((sum, item) => sum + (item.premium_ratio || 0), 0) / mrmxData.length}%
                  </Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader>代码</Table.ColumnHeader>
                    <Table.ColumnHeader>名称</Table.ColumnHeader>
                    <Table.ColumnHeader >涨跌幅</Table.ColumnHeader>
                    <Table.ColumnHeader >收盘价</Table.ColumnHeader>
                    <Table.ColumnHeader >成交价</Table.ColumnHeader>
                    <Table.ColumnHeader >折溢率</Table.ColumnHeader>
                    <Table.ColumnHeader >成交量 (万股)</Table.ColumnHeader>
                    <Table.ColumnHeader >成交额 (万元)</Table.ColumnHeader>
                    <Table.ColumnHeader>买方营业部</Table.ColumnHeader>
                    <Table.ColumnHeader>卖方营业部</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {mrmxData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.trade_date || index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell>{item.stock_code}</Table.Cell>
                      <Table.Cell>{item.stock_name}</Table.Cell>
                      <Table.Cell >{renderChangePct(item.change_pct)}</Table.Cell>
                      <Table.Cell >{item.close_price?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.deal_price?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{renderPremiumRatio(item.premium_ratio)}</Table.Cell>
                      <Table.Cell >{(item.volume || 0) / 10000}%</Table.Cell>
                      <Table.Cell >{formatAmount(item.amount, '万')}</Table.Cell>
                      <Table.Cell>{item.buyer_dept || '-'}</Table.Cell>
                      <Table.Cell>{item.seller_dept || '-'}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {mrmxData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {mrmxData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>
      </Tabs.ContentGroup>
    </Box>
  );
};

export default BlockTradePage;
