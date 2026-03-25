/**
 * 美港目标价页面
 * 展示美股和港股的机构目标价评级
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
  Badge,
  useToast,
  Select,
  Tab,
  Tabs,
  TabList,
  TabPanels,
  TabPanel,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockPriceJS,
} from '@/services/akshare/index';

const StockPriceTargetPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [usData, setUsData] = useState<StockPriceJS[]>([]);
  const [hkData, setHkData] = useState<StockPriceJS[]>([]);
  
  const toast = useToast();

  // 获取美股目标价
  const fetchUsData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockPriceJS('us');
      setUsData(result);
      toast({ 
        title: `获取成功，共${result.length}条美股数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取美股目标价失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取港股目标价
  const fetchHkData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockPriceJS('hk');
      setHkData(result);
      toast({ 
        title: `获取成功，共${result.length}条港股数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取港股目标价失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载美股数据
    fetchUsData();
  }, []);

  // Tab 切换
  const handleTabChange = (index: number) => {
    setActiveTab(index);
    if (index === 1 && hkData.length === 0) {
      fetchHkData();
    }
  };

  // 格式化评级
  const formatRating = (rating: string | null) => {
    if (!rating || rating === 'None') return '-';
    
    // 根据评级显示不同颜色
    const bullishRatings = ['买入', '增持', '跑赢大市', 'Outperform', 'Overweight', 'Buy'];
    const bearishRatings = ['卖出', '减持', '跑输大市', 'Underperform', 'Underweight', 'Sell'];
    const neutralRatings = ['中性', '持有', '与大市持平', 'Hold', 'Neutral', 'None'];
    
    let colorScheme = 'gray';
    if (bullishRatings.some(r => rating.includes(r))) {
      colorScheme = 'green';
    } else if (bearishRatings.some(r => rating.includes(r))) {
      colorScheme = 'red';
    } else if (neutralRatings.some(r => rating.includes(r))) {
      colorScheme = 'yellow';
    }
    
    return <Badge colorScheme={colorScheme}>{rating}</Badge>;
  };

  // 格式化目标价
  const formatTarget = (value: number | null) => {
    if (value === null || value === undefined) return '-';
    return `$${value.toFixed(2)}`;
  };

  // 计算目标价变动
  const calculateChange = (previous: number | null, latest: number | null) => {
    if (previous === null || previous === undefined || latest === null || latest === undefined) {
      return null;
    }
    const change = ((latest - previous) / previous) * 100;
    return change;
  };

  // 渲染表格
  const renderTable = (data: StockPriceJS[]) => {
    return (
      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>日期</Th>
              <Th>个股名称</Th>
              <Th>评级</Th>
              <Th isNumeric>先前目标价</Th>
              <Th isNumeric>最新目标价</Th>
              <Th isNumeric>变动幅度</Th>
              <Th>机构名称</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.slice(0, 100).map((item, index) => {
              const change = calculateChange(item.previous_target, item.latest_target);
              return (
                <Tr key={index}>
                  <Td>{item.date}</Td>
                  <Td fontWeight="bold">{item.stock_name}</Td>
                  <Td>{formatRating(item.rating)}</Td>
                  <Td isNumeric>{formatTarget(item.previous_target)}</Td>
                  <Td isNumeric>{formatTarget(item.latest_target)}</Td>
                  <Td isNumeric>
                    {change !== null ? (
                      <Badge colorScheme={change > 0 ? 'green' : 'red'}>
                        {change > 0 ? '+' : ''}{change.toFixed(2)}%
                      </Badge>
                    ) : (
                      '-'
                    )}
                  </Td>
                  <Td>{item.institution}</Td>
                </Tr>
              );
            })}
          </Tbody>
        </Table>
        {data.length > 100 && (
          <Text mt={4} fontSize="sm" color="gray.500">
            仅显示前 100 条，共 {data.length} 条数据
          </Text>
        )}
      </Box>
    );
  };

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>美港目标价 - 机构评级</Heading>

      {loading && usData.length === 0 && hkData.length === 0 ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <>
          <Tabs onChange={handleTabChange} colorScheme="blue" isFitted>
            <TabList mb={4}>
              <Tab>美股目标价</Tab>
              <Tab>港股目标价</Tab>
            </TabList>

            <TabPanels>
              {/* 美股 */}
              <TabPanel p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">美股机构目标价</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {usData.length} 条数据
                  </Text>
                </Flex>
                {renderTable(usData)}
              </TabPanel>
              
              {/* 港股 */}
              <TabPanel p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">港股机构目标价</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {hkData.length} 条数据
                  </Text>
                </Flex>
                {renderTable(hkData)}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </>
      )}

      {/* 数据说明 */}
      <Box mt={8} p={4} bg="gray.50" borderRadius="md">
        <Heading size="sm" mb={2}>数据说明</Heading>
        <Text fontSize="sm" color="gray.600">
          1. 数据来源：美港电讯 - 投行报告
        </Text>
        <Text fontSize="sm" color="gray.600">
          2. 数据范围：2019 年至今
        </Text>
        <Text fontSize="sm" color="gray.600">
          3. 评级说明：
            - 绿色：买入、增持、跑赢大市等看多评级
            - 红色：卖出、减持、跑输大市等看空评级
            - 黄色：中性、持有等中性评级
        </Text>
        <Text fontSize="sm" color="gray.600">
          4. 变动幅度：（最新目标价 - 先前目标价）/ 先前目标价 × 100%
        </Text>
        <Text fontSize="sm" color="gray.600">
          5. 数据更新：实时获取最新机构评级和目标价
        </Text>
        <Text fontSize="sm" color="gray.600">
          6. 注意事项：该接口暂时不能使用，数据可能不完整
        </Text>
      </Box>
    </Box>
  );
};

export default StockPriceTargetPage;
