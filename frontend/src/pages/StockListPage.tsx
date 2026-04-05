/**
 * 股票列表页面
 * 展示沪深京三个交易所的股票列表
 */
import React, { useState, useEffect, useDeferredValue } from 'react';
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
  Badge,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Input,
  InputGroup,
  InputLeftAddon,
  Select,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockInfoA,
  type StockInfoSH,
  type StockInfoSZ,
  type StockInfoBJ,
} from '@/services/akshare/index';

const StockListPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const deferredSearchTerm = useDeferredValue(searchTerm);
  
  // 沪深京 A 股数据
  const [stockInfoA, setStockInfoA] = useState<StockInfoA[]>([]);
  
  // 上海证券交易所数据
  const [stockInfoSH, setStockInfoSH] = useState<StockInfoSH[]>([]);
  const [shBoard, setShBoard] = useState('主板 A 股');
  
  // 深圳证券交易所数据
  const [stockInfoSZ, setStockInfoSZ] = useState<StockInfoSZ[]>([]);
  const [szBoard, setSzBoard] = useState('A 股列表');
  
  // 北京证券交易所数据
  const [stockInfoBJ, setStockInfoBJ] = useState<StockInfoBJ[]>([]);
  
  const toast = useToast();

  // 获取沪深京 A 股列表
  const fetchStockInfoA = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockInfoA();
      setStockInfoA(result.data || []);
      toast({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取沪深京 A 股列表失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取上海证券交易所股票列表
  const fetchStockInfoSH = async (board: string) => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockInfoSH(board);
      setStockInfoSH(result.data || []);
      toast({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取上海证券交易所股票列表失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取深圳证券交易所股票列表
  const fetchStockInfoSZ = async (board: string) => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockInfoSZ(board);
      setStockInfoSZ(result.data || []);
      toast({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取深圳证券交易所股票列表失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取北京证券交易所股票列表
  const fetchStockInfoBJ = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockInfoBJ();
      setStockInfoBJ(result.data || []);
      toast({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取北京证券交易所股票列表失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载沪深京 A 股列表
    fetchStockInfoA();
  }, []);

  // Tab 切换时自动查询
  const handleTabChange = (index: number) => {
    setActiveTab(index);
    setSearchTerm('');
    
    if (index === 1 && stockInfoSH.length === 0) {
      fetchStockInfoSH(shBoard);
    } else if (index === 2 && stockInfoSZ.length === 0) {
      fetchStockInfoSZ(szBoard);
    } else if (index === 3 && stockInfoBJ.length === 0) {
      fetchStockInfoBJ();
    }
  };

  // 板块切换
  const handleSHBoardChange = () => {
    fetchStockInfoSH(shBoard);
  };

  const handleSZBoardChange = () => {
    fetchStockInfoSZ(szBoard);
  };

  // 搜索过滤（使用 deferredSearchTerm 优化性能）
  const filterData = <T extends object>(data: T[], fields: (keyof T)[]): T[] => {
    if (!deferredSearchTerm) return data;
    
    return data.filter(item => {
      return fields.some(field => {
        const value = item[field];
        return value?.toString().toLowerCase().includes(deferredSearchTerm.toLowerCase());
      });
    });
  };

  // 渲染沪深京 A 股表格
  const renderStockInfoATable = () => {
    const filteredData = filterData(stockInfoA, ['code', 'name']);
    
    return (
      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>股票代码</Th>
              <Th>股票简称</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredData.slice(0, 100).map((stock, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{stock.code}</Td>
                <Td>{stock.name}</Td>
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

  // 渲染上海证券交易所表格
  const renderStockInfoSHTable = () => {
    const filteredData = filterData(stockInfoSH, ['security_code', 'security_abbr', 'company_name']);
    
    return (
      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>证券代码</Th>
              <Th>证券简称</Th>
              <Th>公司全称</Th>
              <Th>上市日期</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredData.slice(0, 100).map((stock, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{stock.security_code}</Td>
                <Td>{stock.security_abbr}</Td>
                <Td>{stock.company_name}</Td>
                <Td>{stock.list_date}</Td>
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

  // 渲染深圳证券交易所表格
  const renderStockInfoSZTable = () => {
    const filteredData = filterData(stockInfoSZ, ['stock_code', 'stock_abbr', 'board', 'industry']);
    
    return (
      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>板块</Th>
              <Th>A 股代码</Th>
              <Th>A 股简称</Th>
              <Th>A 股上市日期</Th>
              <Th isNumeric>A 股总股本</Th>
              <Th isNumeric>A 股流通股本</Th>
              <Th>所属行业</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredData.slice(0, 100).map((stock, index) => (
              <Tr key={index}>
                <Td>
                  <Badge colorScheme={stock.board === '主板' ? 'blue' : 'green'}>
                    {stock.board}
                  </Badge>
                </Td>
                <Td fontWeight="bold">{stock.stock_code}</Td>
                <Td>{stock.stock_abbr}</Td>
                <Td>{stock.list_date}</Td>
                <Td isNumeric>{stock.total_shares?.toLocaleString() || '-'}</Td>
                <Td isNumeric>{stock.circulating_shares?.toLocaleString() || '-'}</Td>
                <Td>{stock.industry}</Td>
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

  // 渲染北京证券交易所表格
  const renderStockInfoBJTable = () => {
    const filteredData = filterData(stockInfoBJ, ['security_code', 'security_abbr', 'industry', 'region']);
    
    return (
      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>证券代码</Th>
              <Th>证券简称</Th>
              <Th isNumeric>总股本</Th>
              <Th isNumeric>流通股本</Th>
              <Th>上市日期</Th>
              <Th>所属行业</Th>
              <Th>地区</Th>
              <Th>报告日期</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredData.slice(0, 100).map((stock, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{stock.security_code}</Td>
                <Td>{stock.security_abbr}</Td>
                <Td isNumeric>{stock.total_shares?.toLocaleString() || '-'}</Td>
                <Td isNumeric>{stock.circulating_shares?.toLocaleString() || '-'}</Td>
                <Td>{stock.list_date}</Td>
                <Td>{stock.industry}</Td>
                <Td>{stock.region}</Td>
                <Td>{stock.report_date}</Td>
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
      <Heading size="lg" mb={6}>股票列表 - 沪深京 A 股</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center" flexWrap="wrap">
        <InputGroup width={{ base: "100%", md: "300px" }}>
          <InputLeftAddon>搜索</InputLeftAddon>
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="输入股票代码或简称搜索"
          />
        </InputGroup>
        
        {activeTab === 1 && (
          <>
            <Select width={{ base: "100%", md: "200px" }} value={shBoard} onChange={(e) => setShBoard(e.target.value)}>
              <option value="主板 A 股">主板 A 股</option>
              <option value="主板 B 股">主板 B 股</option>
              <option value="科创板">科创板</option>
            </Select>
            <Button onClick={handleSHBoardChange} colorScheme="blue" isLoading={loading}>
              查询
            </Button>
          </>
        )}
        
        {activeTab === 2 && (
          <>
            <Select width={{ base: "100%", md: "200px" }} value={szBoard} onChange={(e) => setSzBoard(e.target.value)}>
              <option value="A 股列表">A 股列表</option>
              <option value="B 股列表">B 股列表</option>
              <option value="CDR 列表">CDR 列表</option>
              <option value="AB 股列表">AB 股列表</option>
            </Select>
            <Button onClick={handleSZBoardChange} colorScheme="blue" isLoading={loading}>
              查询
            </Button>
          </>
        )}
      </Flex>

      {loading && stockInfoA.length === 0 && stockInfoSH.length === 0 && 
          stockInfoSZ.length === 0 && stockInfoBJ.length === 0 ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <>
          <Tabs onChange={handleTabChange} colorScheme="blue" isFitted>
            <TabList mb={4}>
              <Tab>沪深京 A 股</Tab>
              <Tab>上海证券交易所</Tab>
              <Tab>深圳证券交易所</Tab>
              <Tab>北京证券交易所</Tab>
            </TabList>

            <TabPanels>
              {/* 沪深京 A 股 */}
              <TabPanel p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">沪深京 A 股列表</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {stockInfoA.length} 条数据
                  </Text>
                </Flex>
                {renderStockInfoATable()}
              </TabPanel>
              
              {/* 上海证券交易所 */}
              <TabPanel p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">上海证券交易所股票列表</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {stockInfoSH.length} 条数据
                  </Text>
                </Flex>
                {renderStockInfoSHTable()}
              </TabPanel>
              
              {/* 深圳证券交易所 */}
              <TabPanel p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">深圳证券交易所股票列表</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {stockInfoSZ.length} 条数据
                  </Text>
                </Flex>
                {renderStockInfoSZTable()}
              </TabPanel>
              
              {/* 北京证券交易所 */}
              <TabPanel p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">北京证券交易所股票列表</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {stockInfoBJ.length} 条数据
                  </Text>
                </Flex>
                {renderStockInfoBJTable()}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </>
      )}

      {/* 数据说明 */}
      <Box mt={8} p={4} bg="gray.50" borderRadius="md">
        <Heading size="sm" mb={2}>数据说明</Heading>
        <Text fontSize="sm" color="gray.600">
          1. 数据来源：上海证券交易所、深圳证券交易所、北京证券交易所
        </Text>
        <Text fontSize="sm" color="gray.600">
          2. 沪深京 A 股：包含上海、深圳、北京三个交易所的所有 A 股股票
        </Text>
        <Text fontSize="sm" color="gray.600">
          3. 上海证券交易所：包含主板 A 股、主板 B 股、科创板
        </Text>
        <Text fontSize="sm" color="gray.600">
          4. 深圳证券交易所：包含主板、创业板等
        </Text>
        <Text fontSize="sm" color="gray.600">
          5. 北京证券交易所：包含所有北交所上市公司
        </Text>
        <Text fontSize="sm" color="gray.600">
          6. 数据更新：随交易所公告实时更新
        </Text>
      </Box>
    </Box>
  );
};

export default StockListPage;
