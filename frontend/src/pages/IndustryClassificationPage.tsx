/**
 * 行业分类页面
 * 包含：申万行业分类变动历史、行业市盈率
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
  Flex,
  Text,
  Spinner,
  Center,
  Button,
  Input,
  InputGroup,
  InputLeftAddon,
  Badge,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Select,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockIndustryClfHistSW,
  type StockIndustryPERatio,
} from '../../services/eastmoney';

const IndustryClassificationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // 申万行业分类数据
  const [industryClfData, setIndustryClfData] = useState<StockIndustryClfHistSW[]>([]);
  
  // 行业市盈率数据
  const [peRatioData, setPeRatioData] = useState<StockIndustryPERatio[]>([]);
  const [peClassType, setPeClassType] = useState('国证行业分类');
  const [peDate, setPeDate] = useState('');
  
  const toast = useToast();

  // 获取申万行业分类变动历史
  const fetchIndustryClfHist = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockIndustryClfHistSW();
      setIndustryClfData(result);
      toast({ 
        title: `获取成功，共${result.length}条数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取申万行业分类变动历史失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取行业市盈率
  const fetchIndustryPERatio = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockIndustryPERatio(peClassType, peDate || undefined);
      setPeRatioData(result);
      toast({ 
        title: `获取成功，共${result.length}条数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取行业市盈率失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载申万行业分类数据
    fetchIndustryClfHist();
  }, []);

  // Tab 切换
  const handleTabChange = (index: number) => {
    setActiveTab(index);
    setSearchTerm('');
    if (index === 1 && peRatioData.length === 0) {
      fetchIndustryPERatio();
    }
  };

  // 搜索过滤
  const filterData = <T extends object>(data: T[], fields: (keyof T)[]): T[] => {
    if (!searchTerm) return data;
    
    return data.filter(item => {
      return fields.some(field => {
        const value = item[field];
        return value?.toString().toLowerCase().includes(searchTerm.toLowerCase());
      });
    });
  };

  // 渲染申万行业分类表格
  const renderIndustryClfTable = () => {
    const filteredData = filterData(industryClfData, ['symbol', 'industry_code', 'start_date']);
    
    return (
      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>股票代码</Th>
              <Th>计入日期</Th>
              <Th>申万行业代码</Th>
              <Th>更新日期</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredData.slice(0, 100).map((item, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{item.symbol}</Td>
                <Td>{item.start_date}</Td>
                <Td>
                  <Badge colorScheme="blue">{item.industry_code}</Badge>
                </Td>
                <Td>{item.update_time}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
        {filteredData.length > 100 && (
          <Text mt={4} fontSize="sm" color="gray.500">
            仅显示前 100 条，共 {filteredData.length} 条数据
          </Text>
        )}
      </Box>
    );
  };

  // 渲染行业市盈率表格
  const renderIndustryPERatioTable = () => {
    const filteredData = filterData(peRatioData, ['industry_name', 'industry_code', 'change_date']);
    
    return (
      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>变动日期</Th>
              <Th>行业名称</Th>
              <Th>行业编码</Th>
              <Th isNumeric>行业层级</Th>
              <Th isNumeric>公司数量</Th>
              <Th isNumeric>纳入计算公司数量</Th>
              <Th isNumeric>总市值 (亿元)</Th>
              <Th isNumeric>净利润 (亿元)</Th>
              <Th isNumeric>静态市盈率 - 加权平均</Th>
              <Th isNumeric>静态市盈率 - 中位数</Th>
              <Th isNumeric>静态市盈率 - 算术平均</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredData.slice(0, 100).map((item, index) => (
              <Tr key={index}>
                <Td>{item.change_date}</Td>
                <Td fontWeight="bold">{item.industry_name}</Td>
                <Td>
                  <Badge colorScheme="green">{item.industry_code}</Badge>
                </Td>
                <Td isNumeric>{item.industry_level}</Td>
                <Td isNumeric>{item.company_count?.toFixed(0) || '-'}</Td>
                <Td isNumeric>{item.calc_company_count?.toFixed(0) || '-'}</Td>
                <Td isNumeric>{item.total_market_cap?.toFixed(2) || '-'}</Td>
                <Td isNumeric>{item.net_profit?.toFixed(2) || '-'}</Td>
                <Td isNumeric>{item.pe_static_weighted?.toFixed(2) || '-'}</Td>
                <Td isNumeric>{item.pe_static_median?.toFixed(2) || '-'}</Td>
                <Td isNumeric>{item.pe_static_arithmetic?.toFixed(2) || '-'}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
        {filteredData.length > 100 && (
          <Text mt={4} fontSize="sm" color="gray.500">
            仅显示前 100 条，共 {filteredData.length} 条数据
          </Text>
        )}
      </Box>
    );
  };

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>行业分类与市盈率分析</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center" flexWrap="wrap">
        <InputGroup width={{ base: "100%", md: "300px" }}>
          <InputLeftAddon>搜索</InputLeftAddon>
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="输入股票代码、行业名称或代码搜索"
          />
        </InputGroup>
        
        {activeTab === 1 && (
          <>
            <Select 
              width={{ base: "100%", md: "200px" }} 
              value={peClassType} 
              onChange={(e) => setPeClassType(e.target.value)}
            >
              <option value="证监会行业分类">证监会行业分类</option>
              <option value="国证行业分类">国证行业分类</option>
            </Select>
            
            <InputGroup width={{ base: "100%", md: "200px" }}>
              <InputLeftAddon>日期</InputLeftAddon>
              <Input
                value={peDate}
                onChange={(e) => setPeDate(e.target.value)}
                placeholder="YYYYMMDD"
              />
            </InputGroup>
            
            <Button onClick={fetchIndustryPERatio} colorScheme="blue" isLoading={loading}>
              查询
            </Button>
          </>
        )}
      </Flex>

      {loading && industryClfData.length === 0 && peRatioData.length === 0 ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <>
          <Tabs onChange={handleTabChange} colorScheme="blue" isFitted>
            <TabList mb={4}>
              <Tab>申万行业分类变动历史</Tab>
              <Tab>行业市盈率</Tab>
            </TabList>

            <TabPanels>
              {/* 申万行业分类变动历史 */}
              <TabPanel p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">申万行业分类变动历史</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {industryClfData.length} 条数据
                  </Text>
                </Flex>
                {renderIndustryClfTable()}
              </TabPanel>
              
              {/* 行业市盈率 */}
              <TabPanel p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">行业市盈率</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {peRatioData.length} 条数据
                  </Text>
                </Flex>
                {renderIndustryPERatioTable()}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </>
      )}

      {/* 数据说明 */}
      <Box mt={8} p={4} bg="gray.50" borderRadius="md">
        <Heading size="sm" mb={2}>数据说明</Heading>
        <Text fontSize="sm" color="gray.600">
          1. 申万行业分类变动历史：申万宏源研究发布的行业分类数据，记录个股行业分类的变动历史
        </Text>
        <Text fontSize="sm" color="gray.600">
          2. 行业市盈率：巨潮资讯数据中心提供的行业市盈率数据，包含不同行业分类标准
        </Text>
        <Text fontSize="sm" color="gray.600">
          3. 行业分类类型：支持证监会行业分类和国证行业分类两种标准
        </Text>
        <Text fontSize="sm" color="gray.600">
          4. 市盈率类型：包含静态市盈率（加权平均、中位数、算术平均）
        </Text>
        <Text fontSize="sm" color="gray.600">
          5. 数据单位：总市值和净利润单位为亿元，市盈率为倍数
        </Text>
        <Text fontSize="sm" color="gray.600">
          6. 更新频率：行业分类随申万宏源研究更新，市盈率数据随交易日更新
        </Text>
      </Box>
    </Box>
  );
};

export default IndustryClassificationPage;
