/**
 * 融资融券页面
 * 包含：保证金比例查询、两融账户统计
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
  TableContainer,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
  Badge,
  Flex,
  Spacer,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  Text,
  Select,
  FormControl,
  FormLabel,
  Input,
  InputGroup,
  InputLeftAddon,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockMarginRatioPa,
  type StockMarginAccountInfo,
  type StockMarginSse,
  type StockMarginDetailSse,
  type StockMarginSzse,
  type StockMarginDetailSzse,
} from '../../services/eastmoney';

const MarginTradingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0); // 0=保证金比例，1=账户统计，2=上交所汇总，3=上交所明细，4=深交所汇总，5=深交所明细
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
  
  const toast = useToast();

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
      setRatioData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取保证金比例数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取账户统计数据
  const fetchAccountInfoData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginAccountInfo();
      setAccountInfoData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取账户统计数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取上交所汇总数据
  const fetchMarginSseData = async () => {
    if (!startDate || !endDate) {
      toast({ title: '请选择日期范围', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginSse(startDate, endDate);
      setMarginSseData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取上交所汇总数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取上交所明细数据
  const fetchMarginDetailSseData = async () => {
    if (!date) {
      toast({ title: '请选择交易日期', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginDetailSse(date);
      setMarginDetailSseData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取上交所明细数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取深交所汇总数据
  const fetchMarginSzseData = async () => {
    if (!date) {
      toast({ title: '请选择交易日期', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginSzse(date);
      setMarginSzseData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取深交所汇总数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取深交所明细数据
  const fetchMarginDetailSzseData = async () => {
    if (!date) {
      toast({ title: '请选择交易日期', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockMarginDetailSzse(date);
      setMarginDetailSzseData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取深交所明细数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
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
    if (activeTab === 0 && ratioData.length === 0) {
      fetchRatioData();
    } else if (activeTab === 1 && accountInfoData.length === 0) {
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
      
      <Tabs index={activeTab} onChange={setActiveTab} mb={6}>
        <TabList>
          <Tab>保证金比例查询</Tab>
          <Tab>两融账户统计</Tab>
          <Tab>上交所汇总</Tab>
          <Tab>上交所明细</Tab>
          <Tab>深交所汇总</Tab>
          <Tab>深交所明细</Tab>
        </TabList>
      </Tabs>

      <TabPanels>
        {/* 保证金比例查询 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <FormControl w="150px">
                <FormLabel mb={1} fontSize="sm">交易所</FormLabel>
                <Select
                  size="sm"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                >
                  {symbols.map((sym) => (
                    <option key={sym.value} value={sym.value}>{sym.label}</option>
                  ))}
                </Select>
              </FormControl>
              
              <InputGroup size="sm" w="200px">
                <InputLeftAddon fontSize="xs">交易日期</InputLeftAddon>
                <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </InputGroup>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchRatioData}
                isLoading={loading && activeTab === 0}
              >
                查询
              </Button>
            </Flex>
            
            {ratioData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>证券数量</StatLabel>
                  <StatNumber>{ratioData.length}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>交易所</StatLabel>
                  <StatNumber>{symbol}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>查询日期</StatLabel>
                  <StatNumber>{date || '最新'}</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>证券代码</Th>
                    <Th>证券简称</Th>
                    <Th isNumeric>融资比例</Th>
                    <Th isNumeric>融券比例</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {ratioData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{item.stock_code}</Td>
                      <Td>{item.stock_name}</Td>
                      <Td isNumeric>
                        {item.margin_ratio !== null ? (
                          <Badge colorScheme={item.margin_ratio < 1 ? 'green' : 'red'}>
                            {item.margin_ratio.toFixed(1)}
                          </Badge>
                        ) : '-'}
                      </Td>
                      <Td isNumeric>
                        {item.short_ratio !== null ? (
                          <Badge colorScheme={item.short_ratio < 1 ? 'green' : 'red'}>
                            {item.short_ratio.toFixed(1)}
                          </Badge>
                        ) : '-'}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {ratioData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {ratioData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 两融账户统计 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchAccountInfoData}
                isLoading={loading && activeTab === 1}
              >
                刷新数据
              </Button>
            </Flex>
            
            {accountInfoData.length > 0 && (
              <SimpleGrid columns={4} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(accountInfoData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>融资余额</StatLabel>
                  <StatNumber>{accountInfoData[0]?.margin_balance?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>融券余额</StatLabel>
                  <StatNumber>{accountInfoData[0]?.short_balance?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>融资买入额</StatLabel>
                  <StatNumber>{accountInfoData[0]?.margin_buy?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>融券卖出额</StatLabel>
                  <StatNumber>{accountInfoData[0]?.short_sell?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>证券公司数量</StatLabel>
                  <StatNumber>{accountInfoData[0]?.broker_count?.toLocaleString() || '-'}家</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>营业部数量</StatLabel>
                  <StatNumber>{accountInfoData[0]?.branch_count?.toLocaleString() || '-'}家</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>个人投资者</StatLabel>
                  <StatNumber>{accountInfoData[0]?.individual_count?.toFixed(2) || '-'}万名</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>机构投资者</StatLabel>
                  <StatNumber>{accountInfoData[0]?.institution_count?.toLocaleString() || '-'}家</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>活跃投资者</StatLabel>
                  <StatNumber>{accountInfoData[0]?.active_count?.toFixed(2) || '-'}万名</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>担保物总价值</StatLabel>
                  <StatNumber>{accountInfoData[0]?.collateral_value?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>平均维持担保比例</StatLabel>
                  <StatNumber>{accountInfoData[0]?.collateral_ratio?.toFixed(1) || '-'}%</StatNumber>
                  <StatHelpText>
                    {accountInfoData[0]?.collateral_ratio !== null 
                      ? accountInfoData[0]!.collateral_ratio! > 250 ? '安全' : '关注'
                      : '-'}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>数据条数</StatLabel>
                  <StatNumber>{accountInfoData.length}</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th isNumeric>融资余额 (亿)</Th>
                    <Th isNumeric>融券余额 (亿)</Th>
                    <Th isNumeric>融资买入 (亿)</Th>
                    <Th isNumeric>融券卖出 (亿)</Th>
                    <Th isNumeric>券商数量</Th>
                    <Th isNumeric>个人投资者 (万)</Th>
                    <Th isNumeric>担保物价值 (亿)</Th>
                    <Th isNumeric>担保比例 (%)</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {accountInfoData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td isNumeric>{item.margin_balance?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.short_balance?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.margin_buy?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.short_sell?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.broker_count?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.individual_count?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.collateral_value?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>
                        {item.collateral_ratio !== null ? (
                          <Badge colorScheme={item.collateral_ratio > 250 ? 'green' : 'yellow'}>
                            {item.collateral_ratio.toFixed(1)}%
                          </Badge>
                        ) : '-'}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {accountInfoData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {accountInfoData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 上交所汇总 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup size="sm" w="200px">
                <InputLeftAddon fontSize="xs">开始日期</InputLeftAddon>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </InputGroup>
              
              <InputGroup size="sm" w="200px">
                <InputLeftAddon fontSize="xs">结束日期</InputLeftAddon>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </InputGroup>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchMarginSseData}
                isLoading={loading && activeTab === 2}
              >
                查询
              </Button>
            </Flex>
            
            {marginSseData.length > 0 && (
              <SimpleGrid columns={4} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>数据条数</StatLabel>
                  <StatNumber>{marginSseData.length}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新融资余额</StatLabel>
                  <StatNumber>{((marginSseData[0]?.margin_balance || 0) / 100000000).toFixed(2)}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新融券余量金额</StatLabel>
                  <StatNumber>{((marginSseData[0]?.short_remaining_amount || 0) / 100000000).toFixed(2)}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新融资融券余额</StatLabel>
                  <StatNumber>{((marginSseData[0]?.total_margin_short_balance || 0) / 100000000).toFixed(2)}亿</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>信用交易日期</Th>
                    <Th isNumeric>融资余额 (元)</Th>
                    <Th isNumeric>融资买入额 (元)</Th>
                    <Th isNumeric>融券余量</Th>
                    <Th isNumeric>融券余量金额 (元)</Th>
                    <Th isNumeric>融券卖出量</Th>
                    <Th isNumeric>融资融券余额 (元)</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {marginSseData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{item.credit_trade_date}</Td>
                      <Td isNumeric>{item.margin_balance?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.margin_buy?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_remaining?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_remaining_amount?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_sell?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.total_margin_short_balance?.toLocaleString() || '-'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {marginSseData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {marginSseData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 上交所明细 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup size="sm" w="200px">
                <InputLeftAddon fontSize="xs">交易日期</InputLeftAddon>
                <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </InputGroup>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchMarginDetailSseData}
                isLoading={loading && activeTab === 3}
              >
                查询
              </Button>
            </Flex>
            
            {marginDetailSseData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>证券数量</StatLabel>
                  <StatNumber>{marginDetailSseData.length}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>交易日期</StatLabel>
                  <StatNumber>{marginDetailSseData[0]?.credit_trade_date || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>总融资余额</StatLabel>
                  <StatNumber>{(marginDetailSseData.reduce((sum, item) => sum + (item.margin_balance || 0), 0) / 100000000).toFixed(2)}亿</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>信用交易日期</Th>
                    <Th>标的证券代码</Th>
                    <Th>标的证券简称</Th>
                    <Th isNumeric>融资余额 (元)</Th>
                    <Th isNumeric>融资买入额 (元)</Th>
                    <Th isNumeric>融资偿还额 (元)</Th>
                    <Th isNumeric>融券余量</Th>
                    <Th isNumeric>融券卖出量</Th>
                    <Th isNumeric>融券偿还量</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {marginDetailSseData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{item.credit_trade_date}</Td>
                      <Td>{item.stock_code}</Td>
                      <Td>{item.stock_name}</Td>
                      <Td isNumeric>{item.margin_balance?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.margin_buy?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.margin_repay?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_remaining?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_sell?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_repay?.toLocaleString() || '-'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {marginDetailSseData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {marginDetailSseData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 深交所汇总 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup size="sm" w="200px">
                <InputLeftAddon fontSize="xs">交易日期</InputLeftAddon>
                <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </InputGroup>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchMarginSzseData}
                isLoading={loading && activeTab === 4}
              >
                查询
              </Button>
            </Flex>
            
            {marginSzseData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>融资买入额</StatLabel>
                  <StatNumber>{marginSzseData[0]?.margin_buy?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>融资余额</StatLabel>
                  <StatNumber>{marginSzseData[0]?.margin_balance?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>融券余量</StatLabel>
                  <StatNumber>{marginSzseData[0]?.short_remaining?.toFixed(2) || '-'}亿股</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>融券余额</StatLabel>
                  <StatNumber>{marginSzseData[0]?.short_balance?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>融资融券余额</StatLabel>
                  <StatNumber>{marginSzseData[0]?.total_margin_short_balance?.toFixed(2) || '-'}亿</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th isNumeric>融资买入额 (亿)</Th>
                    <Th isNumeric>融资余额 (亿)</Th>
                    <Th isNumeric>融券卖出量 (亿股)</Th>
                    <Th isNumeric>融券余量 (亿股)</Th>
                    <Th isNumeric>融券余额 (亿)</Th>
                    <Th isNumeric>融资融券余额 (亿)</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {marginSzseData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td isNumeric>{item.margin_buy?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.margin_balance?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.short_sell?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.short_remaining?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.short_balance?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.total_margin_short_balance?.toFixed(2) || '-'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          </Box>
        </TabPanel>

        {/* 深交所明细 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup size="sm" w="200px">
                <InputLeftAddon fontSize="xs">交易日期</InputLeftAddon>
                <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </InputGroup>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchMarginDetailSzseData}
                isLoading={loading && activeTab === 5}
              >
                查询
              </Button>
            </Flex>
            
            {marginDetailSzseData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>证券数量</StatLabel>
                  <StatNumber>{marginDetailSzseData.length}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>总融资余额</StatLabel>
                  <StatNumber>{(marginDetailSzseData.reduce((sum, item) => sum + (item.margin_balance || 0), 0) / 100000000).toFixed(2)}亿</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>总融券余额</StatLabel>
                  <StatNumber>{(marginDetailSzseData.reduce((sum, item) => sum + (item.short_balance || 0), 0) / 100000000).toFixed(2)}亿</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>证券代码</Th>
                    <Th>证券简称</Th>
                    <Th isNumeric>融资买入额 (元)</Th>
                    <Th isNumeric>融资余额 (元)</Th>
                    <Th isNumeric>融券卖出量</Th>
                    <Th isNumeric>融券余量</Th>
                    <Th isNumeric>融券余额 (元)</Th>
                    <Th isNumeric>融资融券余额 (元)</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {marginDetailSzseData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{item.stock_code}</Td>
                      <Td>{item.stock_name}</Td>
                      <Td isNumeric>{item.margin_buy?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.margin_balance?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_sell?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_remaining?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.short_balance?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>{item.total_margin_short_balance?.toLocaleString() || '-'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          </Box>
        </TabPanel>
      </TabPanels>
    </Box>
  );
};

export default MarginTradingPage;
