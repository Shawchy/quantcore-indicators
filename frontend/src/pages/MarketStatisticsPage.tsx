/**
 * 市场统计页面
 * 包含：创新高/新低统计、破净股统计
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Field, Flex, Heading, NativeSelect, SimpleGrid, Spacer, Stat, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockAHighLowStatistics,
  type StockABelowNetAssetStatistics,
} from '@/services/akshare/index';

const MarketStatisticsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("市场估值"); // 0=创新高/新低，1=破净股
  const [loading, setLoading] = useState(false);
  
  // 输入参数
  const [hlSymbol, setHlSymbol] = useState('all');
  const [bnSymbol, setBnSymbol] = useState('全部 A 股');
  
  // 创新高/新低数据
  const [highLowData, setHighLowData] = useState<StockAHighLowStatistics[]>([]);
  
  // 破净股数据
  const [belowNetAssetData, setBelowNetAssetData] = useState<StockABelowNetAssetStatistics[]>([]);
  
  ;

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
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取创新高/新低数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
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
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取破净股数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
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
    if (activeTab === "市场估值" && highLowData.length === 0) {
      fetchHighLowData();
    } else if (activeTab === "市场情绪" && belowNetAssetData.length === 0) {
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
    return <Badge colorPalette={colorScheme}>{value}</Badge>;
  };

  return (
    <Box p={8}>
      <Heading mb={6}>市场统计</Heading>
      
      <Tabs.Root value={activeTab} onValueChange={(e) => setActiveTab(e.value)} mb={6}>
        <Tabs.List>
          <Tabs.Trigger value="创新高_新低统计">创新高/新低统计</Tabs.Trigger>
          <Tabs.Trigger value="破净股统计">破净股统计</Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>

      <Tabs.ContentGroup>
        {/* 创新高/新低统计 */}
        <Tabs.Content value="破净股统计">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <Field.Root w="200px">
                <Field.Label mb={1} fontSize="sm">市场类型</Field.Label>
                <NativeSelect.Root><NativeSelect.Field
                  
                  value={hlSymbol}
                  onChange={(e) => setHlSymbol(e.target.value)}
                >
                  {hlSymbols.map((sym) => (
                    <option key={sym.value} value={sym.value}>{sym.label}</option>
                  ))}
                </NativeSelect.Field></NativeSelect.Root>
              </Field.Root>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchHighLowData}
                loading={loading && activeTab === "市场估值"}
              >
                查询
              </Button>
            </Flex>
            
            {highLowData.length > 0 && (
              <SimpleGrid columns={4} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(highLowData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新指数收盘</Stat.Label>
                  <Stat.ValueText>{highLowData[0]?.close?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>20 日新高/新低</Stat.Label>
                  <Stat.ValueText>
                    <Flex gap={2}>
                      {renderHLNumber(highLowData[0]?.high20, 'high')}
                      {renderHLNumber(highLowData[0]?.low20, 'low')}
                    </Flex>
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>60 日新高/新低</Stat.Label>
                  <Stat.ValueText>
                    <Flex gap={2}>
                      {renderHLNumber(highLowData[0]?.high60, 'high')}
                      {renderHLNumber(highLowData[0]?.low60, 'low')}
                    </Flex>
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>120 日新高/新低</Stat.Label>
                  <Stat.ValueText>
                    <Flex gap={2}>
                      {renderHLNumber(highLowData[0]?.high120, 'high')}
                      {renderHLNumber(highLowData[0]?.low120, 'low')}
                    </Flex>
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>数据条数</Stat.Label>
                  <Stat.ValueText>{highLowData.length}</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader >收盘价</Table.ColumnHeader>
                    <Table.ColumnHeader >20 日新高</Table.ColumnHeader>
                    <Table.ColumnHeader >20 日新低</Table.ColumnHeader>
                    <Table.ColumnHeader >60 日新高</Table.ColumnHeader>
                    <Table.ColumnHeader >60 日新低</Table.ColumnHeader>
                    <Table.ColumnHeader >120 日新高</Table.ColumnHeader>
                    <Table.ColumnHeader >120 日新低</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {highLowData.slice(0, 100).map((item, index) => (
                    <Table.Row key={index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell >{item.close?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{renderHLNumber(item.high20, 'high')}</Table.Cell>
                      <Table.Cell >{renderHLNumber(item.low20, 'low')}</Table.Cell>
                      <Table.Cell >{renderHLNumber(item.high60, 'high')}</Table.Cell>
                      <Table.Cell >{renderHLNumber(item.low60, 'low')}</Table.Cell>
                      <Table.Cell >{renderHLNumber(item.high120, 'high')}</Table.Cell>
                      <Table.Cell >{renderHLNumber(item.low120, 'low')}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {highLowData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {highLowData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 破净股统计 */}
        <Tabs.Content value="创新高_新低统计">
          <Box>
            <Flex mb={4} align="center" gap={4}>
              <Field.Root w="200px">
                <Field.Label mb={1} fontSize="sm">市场类型</Field.Label>
                <NativeSelect.Root><NativeSelect.Field
                  
                  value={bnSymbol}
                  onChange={(e) => setBnSymbol(e.target.value)}
                >
                  {bnSymbols.map((sym) => (
                    <option key={sym.value} value={sym.value}>{sym.label}</option>
                  ))}
                </NativeSelect.Field></NativeSelect.Root>
              </Field.Root>
              
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchBelowNetAssetData}
                loading={loading && activeTab === "市场情绪"}
              >
                查询
              </Button>
            </Flex>
            
            {belowNetAssetData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(belowNetAssetData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>破净股家数</Stat.Label>
                  <Stat.ValueText>{belowNetAssetData[0]?.below_net_asset?.toLocaleString() || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>总公司数</Stat.Label>
                  <Stat.ValueText>{belowNetAssetData[0]?.total_company?.toLocaleString() || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>破净股比率</Stat.Label>
                  <Stat.ValueText>
                    {belowNetAssetData[0]?.below_net_asset_ratio !== null 
                      ? `${(belowNetAssetData[0]!.below_net_asset_ratio! * 100).toFixed(2)}%` 
                      : '-'}
                  </Stat.ValueText>
                  <Stat.HelpText>
                    {belowNetAssetData[0]?.below_net_asset_ratio !== null 
                      ? belowNetAssetData[0]!.below_net_asset_ratio! > 0.1 ? '偏高' : '正常'
                      : '-'}
                  </Stat.HelpText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>数据条数</Stat.Label>
                  <Stat.ValueText>{belowNetAssetData.length}</Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader >破净股家数</Table.ColumnHeader>
                    <Table.ColumnHeader >总公司数</Table.ColumnHeader>
                    <Table.ColumnHeader >破净股比率</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {belowNetAssetData.slice(0, 100).map((item, index) => (
                    <Table.Row key={index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell >
                        <Badge colorPalette="red">
                          {item.below_net_asset?.toLocaleString() || '-'}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell >{item.total_company?.toLocaleString() || '-'}</Table.Cell>
                      <Table.Cell >
                        {item.below_net_asset_ratio !== null 
                          ? `${(item.below_net_asset_ratio * 100).toFixed(2)}%` 
                          : '-'}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {belowNetAssetData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {belowNetAssetData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>
      </Tabs.ContentGroup>
    </Box>
  );
};

export default MarketStatisticsPage;
