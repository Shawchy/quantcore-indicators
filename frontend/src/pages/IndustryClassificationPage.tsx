/**
 * 行业分类页面
 * 包含：申万行业分类变动历史、行业市盈率
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Flex, Heading, Input, InputGroup, NativeSelect, Spinner, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockIndustryClfHistSW,
  type StockIndustryPERatio,
} from '@/services/akshare/index';

const IndustryClassificationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("行业市盈率");
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // 申万行业分类数据
  const [industryClfData, setIndustryClfData] = useState<StockIndustryClfHistSW[]>([]);
  
  // 行业市盈率数据
  const [peRatioData, setPeRatioData] = useState<StockIndustryPERatio[]>([]);
  const [peClassType, setPeClassType] = useState('国证行业分类');
  const [peDate, setPeDate] = useState('');
  
  ;

  // 获取申万行业分类变动历史
  const fetchIndustryClfHist = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockIndustryClfHistSW();
      setIndustryClfData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取申万行业分类变动历史失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取行业市盈率
  const fetchIndustryPERatio = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockIndustryPERatio(peClassType, peDate || undefined);
      setPeRatioData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取行业市盈率失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载申万行业分类数据
    fetchIndustryClfHist();
  }, []);

  // Tab 切换
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    setSearchTerm('');
    if (value === "行业市净率" && peRatioData.length === 0) {
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
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>股票代码</Table.ColumnHeader>
              <Table.ColumnHeader>计入日期</Table.ColumnHeader>
              <Table.ColumnHeader>申万行业代码</Table.ColumnHeader>
              <Table.ColumnHeader>更新日期</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredData.slice(0, 100).map((item, index) => (
              <Table.Row key={index}>
                <Table.Cell fontWeight="bold">{item.symbol}</Table.Cell>
                <Table.Cell>{item.start_date}</Table.Cell>
                <Table.Cell>
                  <Badge colorPalette="blue">{item.industry_code}</Badge>
                </Table.Cell>
                <Table.Cell>{item.update_time}</Table.Cell>
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

  // 渲染行业市盈率表格
  const renderIndustryPERatioTable = () => {
    const filteredData = filterData(peRatioData, ['industry_name', 'industry_code', 'change_date']);
    
    return (
      <Box overflowX="auto">
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>变动日期</Table.ColumnHeader>
              <Table.ColumnHeader>行业名称</Table.ColumnHeader>
              <Table.ColumnHeader>行业编码</Table.ColumnHeader>
              <Table.ColumnHeader >行业层级</Table.ColumnHeader>
              <Table.ColumnHeader >公司数量</Table.ColumnHeader>
              <Table.ColumnHeader >纳入计算公司数量</Table.ColumnHeader>
              <Table.ColumnHeader >总市值 (亿元)</Table.ColumnHeader>
              <Table.ColumnHeader >净利润 (亿元)</Table.ColumnHeader>
              <Table.ColumnHeader >静态市盈率 - 加权平均</Table.ColumnHeader>
              <Table.ColumnHeader >静态市盈率 - 中位数</Table.ColumnHeader>
              <Table.ColumnHeader >静态市盈率 - 算术平均</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredData.slice(0, 100).map((item, index) => (
              <Table.Row key={index}>
                <Table.Cell>{item.change_date}</Table.Cell>
                <Table.Cell fontWeight="bold">{item.industry_name}</Table.Cell>
                <Table.Cell>
                  <Badge colorPalette="green">{item.industry_code}</Badge>
                </Table.Cell>
                <Table.Cell >{item.industry_level}</Table.Cell>
                <Table.Cell >{item.company_count?.toFixed(0) || '-'}</Table.Cell>
                <Table.Cell >{item.calc_company_count?.toFixed(0) || '-'}</Table.Cell>
                <Table.Cell >{item.total_market_cap?.toFixed(2) || '-'}</Table.Cell>
                <Table.Cell >{item.net_profit?.toFixed(2) || '-'}</Table.Cell>
                <Table.Cell >{item.pe_static_weighted?.toFixed(2) || '-'}</Table.Cell>
                <Table.Cell >{item.pe_static_median?.toFixed(2) || '-'}</Table.Cell>
                <Table.Cell >{item.pe_static_arithmetic?.toFixed(2) || '-'}</Table.Cell>
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
      <Heading size="lg" mb={6}>行业分类与市盈率分析</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center" flexWrap="wrap">
        <InputGroup width={{ base: "100%", md: "300px" }} startAddon="搜索">
  <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="输入股票代码、行业名称或代码搜索"
          />
</InputGroup>
        
        {activeTab === "行业市净率" && (
          <>
            <NativeSelect.Root size="sm"><NativeSelect.Field 
              width={{ base: "100%", md: "200px" }} 
              value={peClassType} 
              onChange={(e) => setPeClassType(e.target.value)}
            >
              <option value="证监会行业分类">证监会行业分类</option>
              <option value="国证行业分类">国证行业分类</option>
            </NativeSelect.Field></NativeSelect.Root>
            
            <InputGroup width={{ base: "100%", md: "200px" }} startAddon="日期">
  <Input
                value={peDate}
                onChange={(e) => setPeDate(e.target.value)}
                placeholder="YYYYMMDD"
              />
</InputGroup>
            
            <Button onClick={fetchIndustryPERatio} colorPalette="blue" loading={loading}>
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
          <Tabs.Root onValueChange={(e) => handleTabChange(e.value)} colorPalette="blue">
            <Tabs.List mb={4}>
              <Tabs.Trigger value="申万行业分类变动历史">申万行业分类变动历史</Tabs.Trigger>
              <Tabs.Trigger value="行业市盈率">行业市盈率</Tabs.Trigger>
            </Tabs.List>

            <Tabs.ContentGroup>
              {/* 申万行业分类变动历史 */}
              <Tabs.Content value="行业市盈率" p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">申万行业分类变动历史</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {industryClfData.length} 条数据
                  </Text>
                </Flex>
                {renderIndustryClfTable()}
              </Tabs.Content>
              
              {/* 行业市盈率 */}
              <Tabs.Content value="行业市盈率" p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">行业市盈率</Heading>
                    <Text fontSize="sm" color="gray.500">
                    共 {peRatioData.length} 条数据
                  </Text>
                </Flex>
                {renderIndustryPERatioTable()}
              </Tabs.Content>
            </Tabs.ContentGroup>
          </Tabs.Root>
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
