/**
 * 股票列表页面
 * 展示沪深京三个交易所的股票列表
 */
import React, { useState, useEffect, useDeferredValue } from 'react';
import { Badge, Box, Button, Center, Flex, Heading, Input, InputGroup, NativeSelect, Spinner, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockInfoA,
  type StockInfoSH,
  type StockInfoSZ,
  type StockInfoBJ,
} from '@/services/akshare/index';

const StockListPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("A股列表");
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
  
  ;

  // 获取沪深京 A 股列表
  const fetchStockInfoA = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockInfoA();
      setStockInfoA(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取沪深京 A 股列表失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
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
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取上海证券交易所股票列表失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
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
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取深圳证券交易所股票列表失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
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
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取北京证券交易所股票列表失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载沪深京 A 股列表
    fetchStockInfoA();
  }, []);

  // Tab 切换时自动查询
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    setSearchTerm('');
    
    if (value === "新股列表" && stockInfoSH.length === 0) {
      fetchStockInfoSH(shBoard);
    } else if (value === "深市新股" && stockInfoSZ.length === 0) {
      fetchStockInfoSZ(szBoard);
    } else if (value === "京市新股" && stockInfoBJ.length === 0) {
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
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>股票代码</Table.ColumnHeader>
              <Table.ColumnHeader>股票简称</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredData.slice(0, 100).map((stock, index) => (
              <Table.Row key={stock.code || index}>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
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
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>证券代码</Table.ColumnHeader>
              <Table.ColumnHeader>证券简称</Table.ColumnHeader>
              <Table.ColumnHeader>公司全称</Table.ColumnHeader>
              <Table.ColumnHeader>上市日期</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredData.slice(0, 100).map((stock, index) => (
              <Table.Row key={stock.security_code || index}>
                <Table.Cell fontWeight="bold">{stock.security_code}</Table.Cell>
                <Table.Cell>{stock.security_abbr}</Table.Cell>
                <Table.Cell>{stock.company_name}</Table.Cell>
                <Table.Cell>{stock.list_date}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
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
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>板块</Table.ColumnHeader>
              <Table.ColumnHeader>A 股代码</Table.ColumnHeader>
              <Table.ColumnHeader>A 股简称</Table.ColumnHeader>
              <Table.ColumnHeader>A 股上市日期</Table.ColumnHeader>
              <Table.ColumnHeader >A 股总股本</Table.ColumnHeader>
              <Table.ColumnHeader >A 股流通股本</Table.ColumnHeader>
              <Table.ColumnHeader>所属行业</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredData.slice(0, 100).map((stock, index) => (
              <Table.Row key={stock.stock_code || index}>
                <Table.Cell>
                  <Badge colorPalette={stock.board === '主板' ? 'blue' : 'green'}>
                    {stock.board}
                  </Badge>
                </Table.Cell>
                <Table.Cell fontWeight="bold">{stock.stock_code}</Table.Cell>
                <Table.Cell>{stock.stock_abbr}</Table.Cell>
                <Table.Cell>{stock.list_date}</Table.Cell>
                <Table.Cell >{stock.total_shares?.toLocaleString() || '-'}</Table.Cell>
                <Table.Cell >{stock.circulating_shares?.toLocaleString() || '-'}</Table.Cell>
                <Table.Cell>{stock.industry}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
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
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>证券代码</Table.ColumnHeader>
              <Table.ColumnHeader>证券简称</Table.ColumnHeader>
              <Table.ColumnHeader >总股本</Table.ColumnHeader>
              <Table.ColumnHeader >流通股本</Table.ColumnHeader>
              <Table.ColumnHeader>上市日期</Table.ColumnHeader>
              <Table.ColumnHeader>所属行业</Table.ColumnHeader>
              <Table.ColumnHeader>地区</Table.ColumnHeader>
              <Table.ColumnHeader>报告日期</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredData.slice(0, 100).map((stock, index) => (
              <Table.Row key={stock.security_code || index}>
                <Table.Cell>{stock.security_abbr}</Table.Cell>
                <Table.Cell >{stock.total_shares?.toLocaleString() || '-'}</Table.Cell>
                <Table.Cell >{stock.circulating_shares?.toLocaleString() || '-'}</Table.Cell>
                <Table.Cell>{stock.list_date}</Table.Cell>
                <Table.Cell>{stock.industry}</Table.Cell>
                <Table.Cell>{stock.region}</Table.Cell>
                <Table.Cell>{stock.report_date}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
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
        <InputGroup width={{ base: "100%", md: "300px" }} startAddon="搜索">
  <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="输入股票代码或简称搜索"
          />
</InputGroup>
        
        {activeTab === "新股列表" && (
          <>
            <NativeSelect.Root size="sm"><NativeSelect.Field width={{ base: "100%", md: "200px" }} value={shBoard} onChange={(e) => setShBoard(e.target.value)}>
              <option value="主板 A 股">主板 A 股</option>
              <option value="主板 B 股">主板 B 股</option>
              <option value="科创板">科创板</option>
            </NativeSelect.Field></NativeSelect.Root>
            <Button onClick={handleSHBoardChange} colorPalette="blue" loading={loading}>
              查询
            </Button>
          </>
        )}
        
        {activeTab === "深市新股" && (
          <>
            <NativeSelect.Root size="sm"><NativeSelect.Field width={{ base: "100%", md: "200px" }} value={szBoard} onChange={(e) => setSzBoard(e.target.value)}>
              <option value="A 股列表">A 股列表</option>
              <option value="B 股列表">B 股列表</option>
              <option value="CDR 列表">CDR 列表</option>
              <option value="AB 股列表">AB 股列表</option>
            </NativeSelect.Field></NativeSelect.Root>
            <Button onClick={handleSZBoardChange} colorPalette="blue" loading={loading}>
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
          <Tabs.Root onValueChange={(e) => handleTabChange(e.value)} colorPalette="blue">
            <Tabs.List mb={4}>
              <Tabs.Trigger value="沪深京_a_股">沪深京 A 股</Tabs.Trigger>
              <Tabs.Trigger value="上海证券交易所">上海证券交易所</Tabs.Trigger>
              <Tabs.Trigger value="深圳证券交易所">深圳证券交易所</Tabs.Trigger>
              <Tabs.Trigger value="北京证券交易所">北京证券交易所</Tabs.Trigger>
            </Tabs.List>

            <Tabs.ContentGroup>
              {/* 沪深京 A 股 */}
              <Tabs.Content value="上海证券交易所" p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">沪深京 A 股列表</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {stockInfoA.length} 条数据
                  </Text>
                </Flex>
                {renderStockInfoATable()}
              </Tabs.Content>
              
              {/* 上海证券交易所 */}
              <Tabs.Content value="深圳证券交易所" p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">上海证券交易所股票列表</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {stockInfoSH.length} 条数据
                  </Text>
                </Flex>
                {renderStockInfoSHTable()}
              </Tabs.Content>
              
              {/* 深圳证券交易所 */}
              <Tabs.Content value="北京证券交易所" p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">深圳证券交易所股票列表</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {stockInfoSZ.length} 条数据
                  </Text>
                </Flex>
                {renderStockInfoSZTable()}
              </Tabs.Content>
              
              {/* 北京证券交易所 */}
              <Tabs.Content value="北京证券交易所" p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">北京证券交易所股票列表</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {stockInfoBJ.length} 条数据
                  </Text>
                </Flex>
                {renderStockInfoBJTable()}
              </Tabs.Content>
            </Tabs.ContentGroup>
          </Tabs.Root>
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
