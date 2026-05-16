/**
 * 美港目标价页面
 * 展示美股和港股的机构目标价评级
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Center, Flex, Heading, Spinner, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockPriceJS,
} from '@/services/akshare/index';

const StockPriceTargetPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [, setActiveTab] = useState("目标价");
  const [usData, setUsData] = useState<StockPriceJS[]>([]);
  const [hkData, setHkData] = useState<StockPriceJS[]>([]);
  
  ;

  // 获取美股目标价
  const fetchUsData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockPriceJS('us');
      setUsData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条美股数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取美股目标价失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取港股目标价
  const fetchHkData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockPriceJS('hk');
      setHkData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条港股数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取港股目标价失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载美股数据
    fetchUsData();
  }, []);

  // Tab 切换
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    if (value === "机构评级" && hkData.length === 0) {
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
    
    return <Badge colorPalette={colorScheme}>{rating}</Badge>;
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
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>日期</Table.ColumnHeader>
              <Table.ColumnHeader>个股名称</Table.ColumnHeader>
              <Table.ColumnHeader>评级</Table.ColumnHeader>
              <Table.ColumnHeader >先前目标价</Table.ColumnHeader>
              <Table.ColumnHeader >最新目标价</Table.ColumnHeader>
              <Table.ColumnHeader >变动幅度</Table.ColumnHeader>
              <Table.ColumnHeader>机构名称</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.slice(0, 100).map((item, index) => {
              const change = calculateChange(item.previous_target, item.latest_target);
              return (
                <Table.Row key={index}>
                  <Table.Cell>{item.date}</Table.Cell>
                  <Table.Cell fontWeight="bold">{item.stock_name}</Table.Cell>
                  <Table.Cell>{formatRating(item.rating)}</Table.Cell>
                  <Table.Cell >{formatTarget(item.previous_target)}</Table.Cell>
                  <Table.Cell >{formatTarget(item.latest_target)}</Table.Cell>
                  <Table.Cell >
                    {change !== null ? (
                      <Badge colorPalette={change > 0 ? 'red' : 'green'}>
                        {change > 0 ? '+' : ''}{change.toFixed(2)}%
                      </Badge>
                    ) : (
                      '-'
                    )}
                  </Table.Cell>
                  <Table.Cell>{item.institution}</Table.Cell>
                </Table.Row>
              );
            })}
          </Table.Body>
        </Table.Root>
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
          <Tabs.Root onValueChange={(e) => handleTabChange(e.value)} colorPalette="blue" >
            <Tabs.List mb={4}>
              <Tabs.Trigger value="美股目标价">美股目标价</Tabs.Trigger>
              <Tabs.Trigger value="港股目标价">港股目标价</Tabs.Trigger>
            </Tabs.List>

            <Tabs.ContentGroup>
              {/* 美股 */}
              <Tabs.Content value="港股目标价" p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">美股机构目标价</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {usData.length} 条数据
                  </Text>
                </Flex>
                {renderTable(usData)}
              </Tabs.Content>
              
              {/* 港股 */}
              <Tabs.Content value="港股" p={0}>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">港股机构目标价</Heading>
                    <Text fontSize="sm" color="gray.500">
                    共 {hkData.length} 条数据
                  </Text>
                </Flex>
                {renderTable(hkData)}
              </Tabs.Content>
            </Tabs.ContentGroup>
          </Tabs.Root>
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
