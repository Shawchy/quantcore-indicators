/**
 * 乐咕乐股市场指标页面
 * 包含：大盘拥挤度、股债利差、巴菲特指标
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
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockAConestionLG,
  type StockEBSLG,
  type StockBuffettIndexLG,
} from '../../services/eastmoney';

const LeguleGuMarketIndicatorsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0); // 0=大盘拥挤度，1=股债利差，2=巴菲特指标
  const [loading, setLoading] = useState(false);
  
  // 大盘拥挤度数据
  const [congestionData, setCongestionData] = useState<StockAConestionLG[]>([]);
  
  // 股债利差数据
  const [ebsData, setEbsData] = useState<StockEBSLG[]>([]);
  
  // 巴菲特指标数据
  const [buffettData, setBuffettData] = useState<StockBuffettIndexLG[]>([]);
  
  const toast = useToast();

  // 获取大盘拥挤度
  const fetchCongestionData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockAConestionLG();
      setCongestionData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取大盘拥挤度失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取股债利差
  const fetchEBSData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockEBSLG();
      setEbsData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取股债利差失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取巴菲特指标
  const fetchBuffettData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockBuffettIndexLG();
      setBuffettData(result);
      toast({ 
        title: `获取成功，共${result.length}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取巴菲特指标失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载数据
    fetchCongestionData();
  }, []);

  // 切换 Tab 时加载对应数据
  useEffect(() => {
    if (activeTab === 0 && congestionData.length === 0) {
      fetchCongestionData();
    } else if (activeTab === 1 && ebsData.length === 0) {
      fetchEBSData();
    } else if (activeTab === 2 && buffettData.length === 0) {
      fetchBuffettData();
    }
  }, [activeTab]);

  // 获取最新数据
  const getLatestData = (data: any[]) => {
    if (data.length === 0) return null;
    return data[0];
  };

  // 格式化日期显示
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return dateStr;
  };

  // 渲染拥挤度级别
  const renderCongestionLevel = (congestion: number | null) => {
    if (congestion === null) return '-';
    
    let colorScheme = 'green';
    let level = '低';
    
    if (congestion > 0.7) {
      colorScheme = 'red';
      level = '极高';
    } else if (congestion > 0.5) {
      colorScheme = 'orange';
      level = '高';
    } else if (congestion > 0.3) {
      colorScheme = 'yellow';
      level = '中';
    }
    
    return (
      <Badge colorScheme={colorScheme}>
        {congestion.toFixed(4)} ({level})
      </Badge>
    );
  };

  // 渲染巴菲特指标分位数
  const renderDecile = (decile: number | null) => {
    if (decile === null) return '-';
    
    let colorScheme = 'green';
    let description = '低估区域';
    
    if (decile > 0.8) {
      colorScheme = 'red';
      description = '高估区域';
    } else if (decile > 0.6) {
      colorScheme = 'yellow';
      description = '合理区域';
    } else if (decile > 0.3) {
      colorScheme = 'blue';
      description = '偏低区域';
    }
    
    return (
      <Badge colorScheme={colorScheme}>
        {(decile * 100).toFixed(2)}% ({description})
      </Badge>
    );
  };

  return (
    <Box p={8}>
      <Heading mb={6}>乐咕乐股市场指标</Heading>
      
      <Tabs index={activeTab} onChange={setActiveTab} mb={6}>
        <TabList>
          <Tab>大盘拥挤度</Tab>
          <Tab>股债利差</Tab>
          <Tab>巴菲特指标</Tab>
        </TabList>
      </Tabs>

      <TabPanels>
        {/* 大盘拥挤度 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center">
              <Heading size="md">大盘拥挤度</Heading>
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchCongestionData}
                isLoading={loading && activeTab === 0}
              >
                刷新数据
              </Button>
            </Flex>
            
            {congestionData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(congestionData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新收盘价</StatLabel>
                  <StatNumber>{congestionData[0]?.close?.toFixed(2) || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新拥挤度</StatLabel>
                  <StatNumber>
                    {congestionData[0]?.congestion !== null 
                      ? (congestionData[0]!.congestion! * 100).toFixed(2) + '%' 
                      : '-'}
                  </StatNumber>
                  <StatHelpText>
                    {congestionData[0]?.congestion !== null 
                      ? congestionData[0]!.congestion! > 0.5 ? '偏高' : '偏低'
                      : '-'}
                  </StatHelpText>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th isNumeric>收盘价</Th>
                    <Th isNumeric>拥挤度</Th>
                    <Th>拥挤度级别</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {congestionData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td isNumeric>{item.close?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>
                        {item.congestion !== null 
                          ? (item.congestion * 100).toFixed(2) + '%' 
                          : '-'}
                      </Td>
                      <Td>{renderCongestionLevel(item.congestion)}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {congestionData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {congestionData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 股债利差 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center">
              <Heading size="md">股债利差</Heading>
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchEBSData}
                isLoading={loading && activeTab === 1}
              >
                刷新数据
              </Button>
            </Flex>
            
            {ebsData.length > 0 && (
              <SimpleGrid columns={4} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(ebsData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>沪深 300 指数</StatLabel>
                  <StatNumber>{ebsData[0]?.hs300_index?.toFixed(2) || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>股债利差</StatLabel>
                  <StatNumber>
                    {ebsData[0]?.ebs !== null 
                      ? (ebsData[0]!.ebs! * 100).toFixed(2) + '%' 
                      : '-'}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>股债利差均线</StatLabel>
                  <StatNumber>
                    {ebsData[0]?.ebs_ma !== null 
                      ? (ebsData[0]!.ebs_ma! * 100).toFixed(2) + '%' 
                      : '-'}
                  </StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th isNumeric>沪深 300 指数</Th>
                    <Th isNumeric>股债利差</Th>
                    <Th isNumeric>股债利差均线</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {ebsData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td isNumeric>{item.hs300_index?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>
                        {item.ebs !== null 
                          ? (item.ebs * 100).toFixed(2) + '%' 
                          : '-'}
                      </Td>
                      <Td isNumeric>
                        {item.ebs_ma !== null 
                          ? (item.ebs_ma * 100).toFixed(2) + '%' 
                          : '-'}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {ebsData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {ebsData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 巴菲特指标 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center">
              <Heading size="md">巴菲特指标</Heading>
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchBuffettData}
                isLoading={loading && activeTab === 2}
              >
                刷新数据
              </Button>
            </Flex>
            
            {buffettData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(buffettData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新收盘价</StatLabel>
                  <StatNumber>{buffettData[0]?.close?.toFixed(2) || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>总市值/GDP</StatLabel>
                  <StatNumber>
                    {buffettData[0]?.total_market_cap !== null && buffettData[0]?.gdp !== null
                      ? ((buffettData[0]!.total_market_cap! / buffettData[0]!.gdp!) * 100).toFixed(2) + '%'
                      : '-'}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>近十年分位数</StatLabel>
                  <StatNumber>
                    {buffettData[0]?.decile_10y !== null 
                      ? (buffettData[0]!.decile_10y! * 100).toFixed(2) + '%' 
                      : '-'}
                  </StatNumber>
                  <StatHelpText>
                    {buffettData[0]?.decile_10y !== null
                      ? buffettData[0]!.decile_10y! > 0.5 ? '偏高' : '偏低'
                      : '-'}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>总历史分位数</StatLabel>
                  <StatNumber>
                    {buffettData[0]?.decile_all !== null 
                      ? (buffettData[0]!.decile_all! * 100).toFixed(2) + '%' 
                      : '-'}
                  </StatNumber>
                  <StatHelpText>
                    {buffettData[0]?.decile_all !== null
                      ? buffettData[0]!.decile_all! > 0.5 ? '偏高' : '偏低'
                      : '-'}
                  </StatHelpText>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th isNumeric>收盘价</Th>
                    <Th isNumeric>总市值 (亿元)</Th>
                    <Th isNumeric>GDP(亿元)</Th>
                    <Th isNumeric>近十年分位数</Th>
                    <Th isNumeric>总历史分位数</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {buffettData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td isNumeric>{item.close?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.total_market_cap?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{item.gdp?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>
                        {item.decile_10y !== null 
                          ? renderDecile(item.decile_10y)
                          : '-'}
                      </Td>
                      <Td isNumeric>
                        {item.decile_all !== null 
                          ? renderDecile(item.decile_all)
                          : '-'}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {buffettData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {buffettData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>
      </TabPanels>
    </Box>
  );
};

export default LeguleGuMarketIndicatorsPage;
