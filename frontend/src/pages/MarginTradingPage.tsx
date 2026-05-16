/**
 * 融资融券页面
 * 包含：保证金比例查询、两融账户统计
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Field, Flex, Heading, Input, InputGroup, NativeSelect, SimpleGrid, Spacer, Stat, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockMarginRatioPa,
  type StockMarginAccountInfo,
  type StockMarginSse,
  type StockMarginDetailSse,
  type StockMarginSzse,
  type StockMarginDetailSzse,
} from '@/services/akshare/index';

const MarginTradingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("账户统计"); // 0=保证金比例，1=账户统计，2=上交所汇总，3=上交所明细，4=深交所汇总，5=深交所明细
  const [loading, setLoading] = useState(false);
  
  // 输入参数
  const [symbol, setSymbol] = useState('深市');
  const [date, setDate] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // 保证金比例数据
  const [ratioData, setRatioData] = useState<StockMarginRatioPa[]>([]);
  
  // 账户统计数据
  const [accountInfoData, setAccountInfoData] = useState<StockMarginAccountInfo[]>([]);
  
  // 上交所汇总数据
  const [marginSseData, setMarginSseData] = useState<StockMarginSse[]>([]);
  
  // 上交所明细数据
  const [marginDetailSseData, setMarginDetailSseData] = useState<StockMarginDetailSse[]>([]);
  
  // 深交所汇总数据
  const [marginSzseData, setMarginSzseData] = useState<StockMarginSzse[]>([]);
  
  // 深交所明细数据
  const [marginDetailSzseData, setMarginDetailSzseData] = useState<StockMarginDetailSzse[]>([]);
  
  ;

  const symbols = [
    { value: '深市', label: '深市' },
    { value: '沪市', label: '沪市' },
    { value: '北交所', label: '北交所' },
  ];

  // 获取保证金比例数据
  const fetchRatioData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginRatioPa(symbol, date);
      setRatioData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取保证金比例数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取账户统计数据
  const fetchAccountInfoData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginAccountInfo();
      setAccountInfoData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取账户统计数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取上交所汇总数据
  const fetchMarginSseData = async () => {
    if (!startDate || !endDate) {
      toaster.create({ title: '请选择日期范围', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginSse(startDate, endDate);
      setMarginSseData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取上交所汇总数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取上交所明细数据
  const fetchMarginDetailSseData = async () => {
    if (!date) {
      toaster.create({ title: '请选择交易日期', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginDetailSse(date);
      setMarginDetailSseData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取上交所明细数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取深交所汇总数据
  const fetchMarginSzseData = async () => {
    if (!date) {
      toaster.create({ title: '请选择交易日期', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginSzse(date);
      setMarginSzseData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取深交所汇总数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取深交所明细数据
  const fetchMarginDetailSzseData = async () => {
    if (!date) {
      toaster.create({ title: '请选择交易日期', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginDetailSzse(date);
      setMarginDetailSzseData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取深交所明细数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载数据
    fetchRatioData();
  }, []);

  // 切换 Tab 时加载对应数据
  useEffect(() => {
    if (activeTab === "账户统计" && ratioData.length === 0) {
      fetchRatioData();
    } else if (activeTab === "上交所" && accountInfoData.length === 0) {
      fetchAccountInfoData();
    }
  }, [activeTab]);

  // 格式化日期显示
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return dateStr;
  };

  return (
    <Box p={8}>
      <Heading mb={6}>融资融券</Heading>
      
      <Tabs.Root value={activeTab} onValueChange={(e) => setActiveTab(e.value)} mb={6}>
        <Tabs.List>
          <Tabs.Trigger value="保证金比例查询">保证金比例查询</Tabs.Trigger>
          <Tabs.Trigger value="两融账户统计">两融账户统计</Tabs.Trigger>
          <Tabs.Trigger value="上交所汇总">上交所汇总</Tabs.Trigger>
          <Tabs.Trigger value="上交所明细">上交所明细</Tabs.Trigger>
          <Tabs.Trigger value="深交所汇总">深交所汇总</Tabs.Trigger>
          <Tabs.Trigger value="深交所明细">深交所明细</Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>

      <Tabs.ContentGroup>
        {/* 保证金比例查询 */}
        <Tabs.Content value="两融账户统计">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <Field.Root w="150px">
                <Field.Label mb={1} fontSize="sm">交易所</Field.Label>
                <NativeSelect.Root><NativeSelect.Field
                  
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                >
                  {symbols.map((sym) => (
                    <option key={sym.value} value={sym.value}>{sym.label}</option>
                  ))}
                </NativeSelect.Field></NativeSelect.Root>
              </Field.Root>
              
              <InputGroup w="200px" startAddon="交易日期">
  <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
</InputGroup>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchRatioData}
                loading={loading && activeTab === "账户统计"}
              >
                查询
              </Button>
            </Flex>
            
            {ratioData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>证券数量</Stat.Label>
                  <Stat.ValueText>{ratioData.length}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>交易所</Stat.Label>
                  <Stat.ValueText>{symbol}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>查询日期</Stat.Label>
                  <Stat.ValueText>{date || '最新'}</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>证券代码</Table.ColumnHeader>
                    <Table.ColumnHeader>证券简称</Table.ColumnHeader>
                    <Table.ColumnHeader >融资比例</Table.ColumnHeader>
                    <Table.ColumnHeader >融券比例</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {ratioData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.trade_date || index}>
                      <Table.Cell>{item.stock_code}</Table.Cell>
                      <Table.Cell>{item.stock_name}</Table.Cell>
                      <Table.Cell >
                        {item.margin_ratio !== null ? (
                          <Badge colorPalette={item.margin_ratio < 1 ? 'green' : 'red'}>
                            {item.margin_ratio.toFixed(1)}
                          </Badge>
                        ) : '-'}
                      </Table.Cell>
                      <Table.Cell >
                        {item.short_ratio !== null ? (
                          <Badge colorPalette={item.short_ratio < 1 ? 'green' : 'red'}>
                            {item.short_ratio.toFixed(1)}
                          </Badge>
                        ) : '-'}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {ratioData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {ratioData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 两融账户统计 */}
        <Tabs.Content value="上交所汇总">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchAccountInfoData}
                loading={loading && activeTab === "上交所"}
              >
                刷新数据
              </Button>
            </Flex>
            
            {accountInfoData.length > 0 && (
              <SimpleGrid columns={4} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(accountInfoData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>融资余额</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.margin_balance?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>融券余额</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.short_balance?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>融资买入额</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.margin_buy?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>融券卖出额</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.short_sell?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>证券公司数量</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.broker_count?.toLocaleString() || '-'}家</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>营业部数量</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.branch_count?.toLocaleString() || '-'}家</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>个人投资者</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.individual_count?.toFixed(2) || '-'}万名</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>机构投资者</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.institution_count?.toLocaleString() || '-'}家</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>活跃投资者</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.active_count?.toFixed(2) || '-'}万名</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>担保物总价值</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.collateral_value?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>平均维持担保比例</Stat.Label>
                  <Stat.ValueText>{accountInfoData[0]?.collateral_ratio?.toFixed(1) || '-'}%</Stat.ValueText>
                  <Stat.HelpText>
                    {accountInfoData[0]?.collateral_ratio !== null 
                      ? accountInfoData[0]!.collateral_ratio! > 250 ? '安全' : '关注'
                      : '-'}
                  </Stat.HelpText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>数据条数</Stat.Label>
                  <Stat.ValueText>{accountInfoData.length}</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader >融资余额 (亿)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券余额 (亿)</Table.ColumnHeader>
                    <Table.ColumnHeader >融资买入 (亿)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券卖出 (亿)</Table.ColumnHeader>
                    <Table.ColumnHeader >券商数量</Table.ColumnHeader>
                    <Table.ColumnHeader >个人投资者 (万)</Table.ColumnHeader>
                    <Table.ColumnHeader >担保物价值 (亿)</Table.ColumnHeader>
                    <Table.ColumnHeader >担保比例 (%)</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {accountInfoData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.trade_date || index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell >{item.margin_balance?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.short_balance?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.margin_buy?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.short_sell?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.broker_count?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.individual_count?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.collateral_value?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >
                        {item.collateral_ratio !== null ? (
                          <Badge colorPalette={item.collateral_ratio > 250 ? 'green' : 'yellow'}>
                            {item.collateral_ratio.toFixed(1)}%
                          </Badge>
                        ) : '-'}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {accountInfoData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {accountInfoData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 上交所汇总 */}
        <Tabs.Content value="上交所明细">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup w="200px" startAddon="开始日期">
  <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
</InputGroup>
              
              <InputGroup w="200px" startAddon="结束日期">
  <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
</InputGroup>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchMarginSseData}
                loading={loading && activeTab === "深交所"}
              >
                查询
              </Button>
            </Flex>
            
            {marginSseData.length > 0 && (
              <SimpleGrid columns={4} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>数据条数</Stat.Label>
                  <Stat.ValueText>{marginSseData.length}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新融资余额</Stat.Label>
                  <Stat.ValueText>{((marginSseData[0]?.margin_balance || 0) / 100000000).toFixed(2)}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新融券余量金额</Stat.Label>
                  <Stat.ValueText>{((marginSseData[0]?.short_remaining_amount || 0) / 100000000).toFixed(2)}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新融资融券余额</Stat.Label>
                  <Stat.ValueText>{((marginSseData[0]?.total_margin_short_balance || 0) / 100000000).toFixed(2)}亿</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>信用交易日期</Table.ColumnHeader>
                    <Table.ColumnHeader >融资余额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融资买入额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券余量</Table.ColumnHeader>
                    <Table.ColumnHeader >融券余量金额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券卖出量</Table.ColumnHeader>
                    <Table.ColumnHeader >融资融券余额 (元)</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {marginSseData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.trade_date || index}>
                      <Table.Cell>{item.credit_trade_date}</Table.Cell>
                      <Table.Cell >{item.margin_balance?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.margin_buy?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_remaining?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_remaining_amount?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_sell?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.total_margin_short_balance?.toLocaleString() || '-'}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {marginSseData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {marginSseData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 上交所明细 */}
        <Tabs.Content value="深交所汇总">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup w="200px" startAddon="交易日期">
  <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
</InputGroup>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchMarginDetailSseData}
                loading={loading && activeTab === "上交所明细"}
              >
                查询
              </Button>
            </Flex>
            
            {marginDetailSseData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>证券数量</Stat.Label>
                  <Stat.ValueText>{marginDetailSseData.length}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>交易日期</Stat.Label>
                  <Stat.ValueText>{marginDetailSseData[0]?.credit_trade_date || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>总融资余额</Stat.Label>
                  <Stat.ValueText>{(marginDetailSseData.reduce((sum, item) => sum + (item.margin_balance || 0), 0) / 100000000).toFixed(2)}亿</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>信用交易日期</Table.ColumnHeader>
                    <Table.ColumnHeader>标的证券代码</Table.ColumnHeader>
                    <Table.ColumnHeader>标的证券简称</Table.ColumnHeader>
                    <Table.ColumnHeader >融资余额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融资买入额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融资偿还额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券余量</Table.ColumnHeader>
                    <Table.ColumnHeader >融券卖出量</Table.ColumnHeader>
                    <Table.ColumnHeader >融券偿还量</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {marginDetailSseData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.trade_date || index}>
                      <Table.Cell>{item.credit_trade_date}</Table.Cell>
                      <Table.Cell>{item.stock_code}</Table.Cell>
                      <Table.Cell>{item.stock_name}</Table.Cell>
                      <Table.Cell >{item.margin_balance?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.margin_buy?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.margin_repay?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_remaining?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_sell?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_repay?.toLocaleString() || '-'}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {marginDetailSseData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {marginDetailSseData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 深交所汇总 */}
        <Tabs.Content value="深交所明细">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup w="200px" startAddon="交易日期">
  <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
</InputGroup>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchMarginSzseData}
                loading={loading && activeTab === "深交所汇总"}
              >
                查询
              </Button>
            </Flex>
            
            {marginSzseData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>融资买入额</Stat.Label>
                  <Stat.ValueText>{marginSzseData[0]?.margin_buy?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>融资余额</Stat.Label>
                  <Stat.ValueText>{marginSzseData[0]?.margin_balance?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>融券余量</Stat.Label>
                  <Stat.ValueText>{marginSzseData[0]?.short_remaining?.toFixed(2) || '-'}亿股</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>融券余额</Stat.Label>
                  <Stat.ValueText>{marginSzseData[0]?.short_balance?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>融资融券余额</Stat.Label>
                  <Stat.ValueText>{marginSzseData[0]?.total_margin_short_balance?.toFixed(2) || '-'}亿</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader >融资买入额 (亿)</Table.ColumnHeader>
                    <Table.ColumnHeader >融资余额 (亿)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券卖出量 (亿股)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券余量 (亿股)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券余额 (亿)</Table.ColumnHeader>
                    <Table.ColumnHeader >融资融券余额 (亿)</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {marginSzseData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.trade_date || index}>
                      <Table.Cell >{item.margin_buy?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.margin_balance?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.short_sell?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.short_remaining?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.short_balance?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.total_margin_short_balance?.toFixed(2) || '-'}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          </Box>
        </Tabs.Content>

        {/* 深交所明细 */}
        <Tabs.Content value="保证金比例查询">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup w="200px" startAddon="交易日期">
  <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
</InputGroup>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchMarginDetailSzseData}
                loading={loading && activeTab === "深交所明细"}
              >
                查询
              </Button>
            </Flex>
            
            {marginDetailSzseData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>证券数量</Stat.Label>
                  <Stat.ValueText>{marginDetailSzseData.length}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>总融资余额</Stat.Label>
                  <Stat.ValueText>{(marginDetailSzseData.reduce((sum, item) => sum + (item.margin_balance || 0), 0) / 100000000).toFixed(2)}亿</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>总融券余额</Stat.Label>
                  <Stat.ValueText>{(marginDetailSzseData.reduce((sum, item) => sum + (item.short_balance || 0), 0) / 100000000).toFixed(2)}亿</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>证券代码</Table.ColumnHeader>
                    <Table.ColumnHeader>证券简称</Table.ColumnHeader>
                    <Table.ColumnHeader >融资买入额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融资余额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融券卖出量</Table.ColumnHeader>
                    <Table.ColumnHeader >融券余量</Table.ColumnHeader>
                    <Table.ColumnHeader >融券余额 (元)</Table.ColumnHeader>
                    <Table.ColumnHeader >融资融券余额 (元)</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {marginDetailSzseData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.trade_date || index}>
                      <Table.Cell>{item.stock_code}</Table.Cell>
                      <Table.Cell>{item.stock_name}</Table.Cell>
                      <Table.Cell >{item.margin_buy?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.margin_balance?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_sell?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_remaining?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.short_balance?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >{item.total_margin_short_balance?.toLocaleString() || '-'}</Table.Cell>
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

export default MarginTradingPage;
