/**
 * 大宗交易页面
 * 包含：市场统计、每日明细
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
  type StockDzjySctj,
  type StockDzjyMrmx,
} from '../../services/eastmoney';

const BlockTradePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0); // 0=市场统计，1=每日明细
  const [loading, setLoading] = useState(false);
  
  // 输入参数
  const [symbol, setSymbol] = useState('A 股');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // 市场统计数据
  const [sctjData, setSctjData] = useState<StockDzjySctj[]>([]);
  
  // 每日明细数据
  const [mrmxData, setMrmxData] = useState<StockDzjyMrmx[]>([]);
  
  const toast = useToast();

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
      setSctjData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取大宗交易市场统计数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取每日明细数据
  const fetchMrmxData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockDzjyMrmx(symbol, startDate, endDate);
      setMrmxData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取大宗交易每日明细数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
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
    if (activeTab === 0 && sctjData.length === 0) {
      fetchSctjData();
    } else if (activeTab === 1 && mrmxData.length === 0) {
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
      <Badge colorScheme={colorScheme}>
        {ratio.toFixed(2)}%
      </Badge>
    );
  };

  // 渲染涨跌幅
  const renderChangePct = (pct: number | null) => {
    if (pct === null) return '-';
    const colorScheme = pct > 0 ? 'red' : pct < 0 ? 'green' : 'gray';
    return (
      <Badge colorScheme={colorScheme}>
        {pct.toFixed(2)}%
      </Badge>
    );
  };

  return (
    <Box p={8}>
      <Heading mb={6}>大宗交易</Heading>
      
      <Tabs index={activeTab} onChange={setActiveTab} mb={6}>
        <TabList>
          <Tab>市场统计</Tab>
          <Tab>每日明细</Tab>
        </TabList>
      </Tabs>

      <TabPanels>
        {/* 市场统计 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchSctjData}
                isLoading={loading && activeTab === 0}
              >
                刷新数据
              </Button>
            </Flex>
            
            {sctjData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(sctjData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>上证指数</StatLabel>
                  <StatNumber>{sctjData[0]?.sh_index?.toFixed(2) || '-'}</StatNumber>
                  <StatHelpText>
                    {sctjData[0]?.sh_change_pct !== null 
                      ? `${sctjData[0]!.sh_change_pct! > 0 ? '+' : ''}${sctjData[0]!.sh_change_pct!.toFixed(2)}%`
                      : '-'}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>成交总额</StatLabel>
                  <StatNumber>{formatAmount(sctjData[0]?.total_amount, '亿')}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>溢价成交额</StatLabel>
                  <StatNumber>{formatAmount(sctjData[0]?.premium_amount, '亿')}</StatNumber>
                  <StatHelpText>
                    占比{sctjData[0]?.premium_ratio?.toFixed(2)}%
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>折价成交额</StatLabel>
                  <StatNumber>{formatAmount(sctjData[0]?.discount_amount, '亿')}</StatNumber>
                  <StatHelpText>
                    占比{sctjData[0]?.discount_ratio?.toFixed(2)}%
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>数据条数</StatLabel>
                  <StatNumber>{sctjData.length}</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th isNumeric>上证指数</Th>
                    <Th isNumeric>涨跌幅</Th>
                    <Th isNumeric>成交总额</Th>
                    <Th isNumeric>溢价成交额</Th>
                    <Th isNumeric>溢价占比</Th>
                    <Th isNumeric>折价成交额</Th>
                    <Th isNumeric>折价占比</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {sctjData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td isNumeric>{item.sh_index?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>
                        {item.sh_change_pct !== null 
                          ? (
                            <Badge colorScheme={item.sh_change_pct > 0 ? 'red' : 'green'}>
                              {item.sh_change_pct.toFixed(2)}%
                            </Badge>
                          )
                          : '-'}
                      </Td>
                      <Td isNumeric>{formatAmount(item.total_amount, '亿')}</Td>
                      <Td isNumeric>{formatAmount(item.premium_amount, '万')}</Td>
                      <Td isNumeric>{item.premium_ratio?.toFixed(2)}%</Td>
                      <Td isNumeric>{formatAmount(item.discount_amount, '万')}</Td>
                      <Td isNumeric>{item.discount_ratio?.toFixed(2)}%</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {sctjData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {sctjData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 每日明细 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <FormControl w="150px">
                <FormLabel mb={1} fontSize="sm">证券类型</FormLabel>
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
              
              <InputGroup size="sm" w="180px">
                <InputLeftAddon fontSize="xs">开始日期</InputLeftAddon>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </InputGroup>
              
              <InputGroup size="sm" w="180px">
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
                onClick={fetchMrmxData}
                isLoading={loading && activeTab === 1}
              >
                查询
              </Button>
            </Flex>
            
            {mrmxData.length > 0 && (
              <SimpleGrid columns={4} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(mrmxData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>交易笔数</StatLabel>
                  <StatNumber>{mrmxData.length}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>成交总额</StatLabel>
                  <StatNumber>
                    {formatAmount(mrmxData.reduce((sum, item) => sum + (item.amount || 0), 0), '亿')}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>平均折溢率</StatLabel>
                  <StatNumber>
                    {mrmxData.reduce((sum, item) => sum + (item.premium_ratio || 0), 0) / mrmxData.length}%
                  </StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th>代码</Th>
                    <Th>名称</Th>
                    <Th isNumeric>涨跌幅</Th>
                    <Th isNumeric>收盘价</Th>
                    <Th isNumeric>成交价</Th>
                    <Th isNumeric>折溢率</Th>
                    <Th isNumeric>成交量 (万股)</Th>
                    <Th isNumeric>成交额 (万元)</Th>
                    <Th>买方营业部</Th>
                    <Th>卖方营业部</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {mrmxData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td>{item.stock_code}</Td>
                      <Td>{item.stock_name}</Td>
                      <Td isNumeric>{renderChangePct(item.change_pct)}</Td>
                      <Td isNumeric>{item.close_price?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.deal_price?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{renderPremiumRatio(item.premium_ratio)}</Td>
                      <Td isNumeric>{(item.volume || 0) / 10000}%</Td>
                      <Td isNumeric>{formatAmount(item.amount, '万')}</Td>
                      <Td>{item.buyer_dept || '-'}</Td>
                      <Td>{item.seller_dept || '-'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {mrmxData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {mrmxData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>
      </TabPanels>
    </Box>
  );
};

export default BlockTradePage;
