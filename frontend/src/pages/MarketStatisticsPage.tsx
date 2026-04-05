/**
 * 市场统计页面
 * 包含：创新高/新低统计、破净股统计
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
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockAHighLowStatistics,
  type StockABelowNetAssetStatistics,
} from '@/services/akshare/index';

const MarketStatisticsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0); // 0=创新高/新低，1=破净股
  const [loading, setLoading] = useState(false);
  
  // 输入参数
  const [hlSymbol, setHlSymbol] = useState('all');
  const [bnSymbol, setBnSymbol] = useState('全部 A 股');
  
  // 创新高/新低数据
  const [highLowData, setHighLowData] = useState<StockAHighLowStatistics[]>([]);
  
  // 破净股数据
  const [belowNetAssetData, setBelowNetAssetData] = useState<StockABelowNetAssetStatistics[]>([]);
  
  const toast = useToast();

  const hlSymbols = [
    { value: 'all', label: '全部 A 股' },
    { value: 'sz50', label: '上证 50' },
    { value: 'hs300', label: '沪深 300' },
    { value: 'zz500', label: '中证 500' },
  ];

  const bnSymbols = [
    { value: '全部 A 股', label: '全部 A 股' },
    { value: '沪深 300', label: '沪深 300' },
    { value: '上证 50', label: '上证 50' },
    { value: '中证 500', label: '中证 500' },
  ];

  // 获取创新高/新低数据
  const fetchHighLowData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockAHighLowStatistics(hlSymbol);
      setHighLowData(result.data || []);
      toast({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取创新高/新低数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取破净股数据
  const fetchBelowNetAssetData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockABelowNetAssetStatistics(bnSymbol);
      setBelowNetAssetData(result.data || []);
      toast({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取破净股数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载数据
    fetchHighLowData();
  }, []);

  // 切换 Tab 时加载对应数据
  useEffect(() => {
    if (activeTab === 0 && highLowData.length === 0) {
      fetchHighLowData();
    } else if (activeTab === 1 && belowNetAssetData.length === 0) {
      fetchBelowNetAssetData();
    }
  }, [activeTab]);

  // 格式化日期显示
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return dateStr;
  };

  // 渲染新高/新低数量
  const renderHLNumber = (value: number | null, type: 'high' | 'low') => {
    if (value === null) return '-';
    const colorScheme = type === 'high' ? 'red' : 'green';
    return <Badge colorScheme={colorScheme}>{value}</Badge>;
  };

  return (
    <Box p={8}>
      <Heading mb={6}>市场统计</Heading>
      
      <Tabs index={activeTab} onChange={setActiveTab} mb={6}>
        <TabList>
          <Tab>创新高/新低统计</Tab>
          <Tab>破净股统计</Tab>
        </TabList>
      </Tabs>

      <TabPanels>
        {/* 创新高/新低统计 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <FormControl w="200px">
                <FormLabel mb={1} fontSize="sm">市场类型</FormLabel>
                <Select
                  size="sm"
                  value={hlSymbol}
                  onChange={(e) => setHlSymbol(e.target.value)}
                >
                  {hlSymbols.map((sym) => (
                    <option key={sym.value} value={sym.value}>{sym.label}</option>
                  ))}
                </Select>
              </FormControl>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchHighLowData}
                isLoading={loading && activeTab === 0}
              >
                查询
              </Button>
            </Flex>
            
            {highLowData.length > 0 && (
              <SimpleGrid columns={4} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(highLowData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>最新指数收盘</StatLabel>
                  <StatNumber>{highLowData[0]?.close?.toFixed(2) || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>20 日新高/新低</StatLabel>
                  <StatNumber>
                    <Flex gap={2}>
                      {renderHLNumber(highLowData[0]?.high20, 'high')}
                      {renderHLNumber(highLowData[0]?.low20, 'low')}
                    </Flex>
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>60 日新高/新低</StatLabel>
                  <StatNumber>
                    <Flex gap={2}>
                      {renderHLNumber(highLowData[0]?.high60, 'high')}
                      {renderHLNumber(highLowData[0]?.low60, 'low')}
                    </Flex>
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>120 日新高/新低</StatLabel>
                  <StatNumber>
                    <Flex gap={2}>
                      {renderHLNumber(highLowData[0]?.high120, 'high')}
                      {renderHLNumber(highLowData[0]?.low120, 'low')}
                    </Flex>
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>数据条数</StatLabel>
                  <StatNumber>{highLowData.length}</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th isNumeric>收盘价</Th>
                    <Th isNumeric>20 日新高</Th>
                    <Th isNumeric>20 日新低</Th>
                    <Th isNumeric>60 日新高</Th>
                    <Th isNumeric>60 日新低</Th>
                    <Th isNumeric>120 日新高</Th>
                    <Th isNumeric>120 日新低</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {highLowData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td isNumeric>{item.close?.toFixed(2) || '-'}</Td>
                      <Td isNumeric>{renderHLNumber(item.high20, 'high')}</Td>
                      <Td isNumeric>{renderHLNumber(item.low20, 'low')}</Td>
                      <Td isNumeric>{renderHLNumber(item.high60, 'high')}</Td>
                      <Td isNumeric>{renderHLNumber(item.low60, 'low')}</Td>
                      <Td isNumeric>{renderHLNumber(item.high120, 'high')}</Td>
                      <Td isNumeric>{renderHLNumber(item.low120, 'low')}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {highLowData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {highLowData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>

        {/* 破净股统计 */}
        <TabPanel>
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <FormControl w="200px">
                <FormLabel mb={1} fontSize="sm">市场类型</FormLabel>
                <Select
                  size="sm"
                  value={bnSymbol}
                  onChange={(e) => setBnSymbol(e.target.value)}
                >
                  {bnSymbols.map((sym) => (
                    <option key={sym.value} value={sym.value}>{sym.label}</option>
                  ))}
                </Select>
              </FormControl>
              
              <Spacer />
              <Button
                colorScheme="blue"
                onClick={fetchBelowNetAssetData}
                isLoading={loading && activeTab === 1}
              >
                查询
              </Button>
            </Flex>
            
            {belowNetAssetData.length > 0 && (
              <SimpleGrid columns={3} spacing={4} mb={4}>
                <Stat>
                  <StatLabel>最新日期</StatLabel>
                  <StatNumber>{formatDate(belowNetAssetData[0]?.date)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>破净股家数</StatLabel>
                  <StatNumber>{belowNetAssetData[0]?.below_net_asset?.toLocaleString() || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>总公司数</StatLabel>
                  <StatNumber>{belowNetAssetData[0]?.total_company?.toLocaleString() || '-'}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>破净股比率</StatLabel>
                  <StatNumber>
                    {belowNetAssetData[0]?.below_net_asset_ratio !== null 
                      ? `${(belowNetAssetData[0]!.below_net_asset_ratio! * 100).toFixed(2)}%` 
                      : '-'}
                  </StatNumber>
                  <StatHelpText>
                    {belowNetAssetData[0]?.below_net_asset_ratio !== null 
                      ? belowNetAssetData[0]!.below_net_asset_ratio! > 0.1 ? '偏高' : '正常'
                      : '-'}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>数据条数</StatLabel>
                  <StatNumber>{belowNetAssetData.length}</StatNumber>
                </Stat>
              </SimpleGrid>
            )}

            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>日期</Th>
                    <Th isNumeric>破净股家数</Th>
                    <Th isNumeric>总公司数</Th>
                    <Th isNumeric>破净股比率</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {belowNetAssetData.slice(0, 100).map((item, index) => (
                    <Tr key={index}>
                      <Td>{formatDate(item.date)}</Td>
                      <Td isNumeric>
                        <Badge colorScheme="red">
                          {item.below_net_asset?.toLocaleString() || '-'}
                        </Badge>
                      </Td>
                      <Td isNumeric>{item.total_company?.toLocaleString() || '-'}</Td>
                      <Td isNumeric>
                        {item.below_net_asset_ratio !== null 
                          ? `${(item.below_net_asset_ratio * 100).toFixed(2)}%` 
                          : '-'}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
            
            {belowNetAssetData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {belowNetAssetData.length} 条数据
              </Text>
            )}
          </Box>
        </TabPanel>
      </TabPanels>
    </Box>
  );
};

export default MarketStatisticsPage;
