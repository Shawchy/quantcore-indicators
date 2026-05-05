/**
 * A 股估值指标页面
 * 包含：百度估值、个股估值、涨跌投票
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
  Input,
  InputGroup,
  InputLeftAddon,

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
  HStack,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockZhValuationBaidu,
  type StockValueEM,
  type StockZhVoteBaidu,
} from '@/services/akshare/index';

const AShareValuationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0); // 0=百度估值，1=个股估值，2=涨跌投票
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
  
  const toast = useToast();

  const valuationIndicators = ['总市值', '市盈率 (TTM)', '市盈率 (静)', '市净率', '市现率'];
  const periods = ['近一年', '近三年', '近五年', '近十年', '全部'];

  // 获取百度估值数据
  const fetchValuationData = async () => {
    if (!symbol) {
      toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockZhValuationBaidu(symbol, indicator, period);
      setValuationData((result as any).data || []);
      toast({ 
        title: `获取成功，共${(result as any).data?.length || 0}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取百度估值数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取个股估值数据
  const fetchValueData = async () => {
    if (!symbol) {
      toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockValueEM(symbol);
      setValueData((result as any).data || []);
      toast({ 
        title: `获取成功，共${(result as any).data?.length || 0}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取个股估值数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取涨跌投票数据
  const fetchVoteData = async () => {
    if (!symbol) {
      toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockZhVoteBaidu(symbol, voteIndicator);
      setVoteData((result as any).data || []);
      toast({ 
        title: `获取成功，共${(result as any).data?.length || 0}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取涨跌投票数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
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
    if (activeTab === 0 && valuationData.length === 0) {
      fetchValuationData();
    } else if (activeTab === 1 && valueData.length === 0) {
      fetchValueData();
    } else if (activeTab === 2 && voteData.length === 0) {
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
      <Badge colorScheme={colorScheme}>
        {typeof ratio === 'string' ? ratio : `${ratio}%`}
      </Badge>
    );
  };

  return (
    <Box p={8}>
      <Heading mb={6}>A 股估值指标</Heading>
      
      <Tabs index={activeTab} onChange={setActiveTab} mb={6}>
        <TabList>
          <Tab>百度估值</Tab>
          <Tab>个股估值</Tab>
          <Tab>涨跌投票</Tab>
        </TabList>
      </Tabs>

      <TabPanels>
        {/* 百度估值 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup size="sm" w="150px">
                <InputLeftAddon>股票代码</InputLeftAddon>
                <Input
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="002044"
                />
              </InputGroup>
              
              <FormControl w="150px">
                <FormLabel mb={1} fontSize="sm">估值指标</FormLabel>
                <Select
                  size="sm"
                  value={indicator}
                  onChange={(e) => setIndicator(e.target.value)}
                >
                  {valuationIndicators.map((ind) => (
                    <option key={ind} value={ind}>{ind}</option>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl w="150px">
                <FormLabel mb={1} fontSize="sm">时间范围</FormLabel>
                <Select
                  size="sm"
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                >
                  {periods.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </Select>
              </FormControl>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchValuationData}
                isLoading={loading && activeTab === 0}
              >
                查询
              </Button>
            </Flex>
            
            {valuationData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(valuationData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新{indicator}</StatLabel>
                  <StatNumber>
                    {valuationData[0]?.value?.toLocaleString() || '-'}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>数据条数</StatLabel>
                  <StatNumber>{valuationData.length}</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th isNumeric>{indicator}</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {valuationData.slice(0, 100).map((item, index) => (
                    <Tr key={item.code || item.name || index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td isNumeric>{item.value?.toLocaleString() || '-'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {valuationData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {valuationData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 个股估值 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup size="sm" w="150px">
                <InputLeftAddon>股票代码</InputLeftAddon>
                <Input
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="300766"
                />
              </InputGroup>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchValueData}
                isLoading={loading && activeTab === 1}
              >
                查询
              </Button>
            </Flex>
            
            {valueData.length > 0 && (
              <SimpleGrid columns={4} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(valueData[0]?.report_date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新收盘价</StatLabel>
                  <StatNumber>{valueData[0]?.close_price?.toFixed(2) || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>涨跌幅</StatLabel>
                  <StatNumber>
                    {valueData[0]?.change_pct !== null 
                      ? `${valueData[0]!.change_pct!.toFixed(2)}%` 
                      : '-'}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>PE(TTM)</StatLabel>
                  <StatNumber>{valueData[0]?.pe_ttm?.toFixed(2) || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>市净率</StatLabel>
                  <StatNumber>{valueData[0]?.pb?.toFixed(2) || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>总市值</StatLabel>
                  <StatNumber>
                    {valueData[0]?.total_mv 
                      ? `${(valueData[0]!.total_mv! / 100000000).toFixed(2)}亿` 
                      : '-'}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>PEG 值</StatLabel>
                  <StatNumber>{valueData[0]?.peg?.toFixed(2) || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>市销率</StatLabel>
                  <StatNumber>{valueData[0]?.ps?.toFixed(2) || '-'}</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>数据日期</Th>
                    <Th isNumeric>收盘价</Th>
                    <Th isNumeric>涨跌幅</Th>
                    <Th isNumeric>PE(TTM)</Th>
                    <Th isNumeric>PE(静)</Th>
                    <Th isNumeric>市净率</Th>
                    <Th isNumeric>PEG 值</Th>
                    <Th isNumeric>市现率</Th>
                    <Th isNumeric>市销率</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {valueData.slice(0, 100).map((item, index) => (
                    <Tr key={item.code || item.name || index}>
                      <Td>{formatDate(item.report_date)}</Td>
                      <Td isNumeric>{item.close_price?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>
                        {item.change_pct !== null 
                          ? `${item.change_pct.toFixed(2)}%` 
                          : '-'}
                      </Td>
                      <Td isNumeric>{item.pe_ttm?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.pe_static?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.pb?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.peg?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.pc?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.ps?.toFixed(2) || '-'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {valueData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {valueData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 涨跌投票 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <InputGroup size="sm" w="150px">
                <InputLeftAddon>股票/指数代码</InputLeftAddon>
                <Input
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="000001"
                />
              </InputGroup>
              
              <FormControl w="120px">
                <FormLabel mb={1} fontSize="sm">类型</FormLabel>
                <Select
                  size="sm"
                  value={voteIndicator}
                  onChange={(e) => setVoteIndicator(e.target.value)}
                >
                  <option value="股票">股票</option>
                  <option value="指数">指数</option>
                </Select>
              </FormControl>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchVoteData}
                isLoading={loading && activeTab === 2}
              >
                查询
              </Button>
            </Flex>
            
            {voteData.length > 0 && (
              <SimpleGrid columns={4} spacing={4} mb={4}>
                {voteData.map((item, index) => (
                  <Stat key={item.code || item.name || index}>
                    <StatLabel>{item.period}</StatLabel>
                    <StatNumber>
                      <HStack spacing={2}>
                        <Badge colorScheme="green">
                          看涨：{item.vote_up?.toLocaleString() || '-'}
                        </Badge>
                        <Badge colorScheme="red">
                          看跌：{item.vote_down?.toLocaleString() || '-'}
                        </Badge>
                      </HStack>
                    </StatNumber>
                    <StatHelpText>
                      <HStack spacing={2}>
                        {renderVoteRatio(item.vote_up_ratio)}
                        {renderVoteRatio(item.vote_down_ratio)}
                      </HStack>
                    </StatHelpText>
                  </Stat>
                ))}
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>周期</Th>
                    <Th isNumeric>看涨票数</Th>
                    <Th isNumeric>看跌票数</Th>
                    <Th isNumeric>看涨比例</Th>
                    <Th isNumeric>看跌比例</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {voteData.map((item, index) => (
                    <Tr key={item.code || item.name || index}>
                      <Td>{item.period}</Td>
                      <Td isNumeric>
                        <Badge colorScheme="green">
                          {item.vote_up?.toLocaleString() || '-'}
                        </Badge>
                      </Td>
                      <Td isNumeric>
                        <Badge colorScheme="red">
                          {item.vote_down?.toLocaleString() || '-'}
                        </Badge>
                      </Td>
                      <Td isNumeric>{renderVoteRatio(item.vote_up_ratio)}</Td>
                      <Td isNumeric>{renderVoteRatio(item.vote_down_ratio)}</Td>
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

export default AShareValuationPage;
