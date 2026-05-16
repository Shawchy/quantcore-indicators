/**
 * 乐咕乐股市场指标页面
 * 包含：大盘拥挤度、股债利差、巴菲特指标
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Flex, Heading, SimpleGrid, Spacer, Stat, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockAConestionLG,
  type StockEBSLG,
  type StockBuffettIndexLG,
} from '@/services/akshare/index';

const LeguleGuMarketIndicatorsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("大盘拥挤度"); // 0=大盘拥挤度，1=股债利差，2=巴菲特指标
  const [loading, setLoading] = useState(false);
  
  // 大盘拥挤度数据
  const [congestionData, setCongestionData] = useState<StockAConestionLG[]>([]);
  
  // 股债利差数据
  const [ebsData, setEbsData] = useState<StockEBSLG[]>([]);
  
  // 巴菲特指标数据
  const [buffettData, setBuffettData] = useState<StockBuffettIndexLG[]>([]);
  
  ;

  // 获取大盘拥挤度
  const fetchCongestionData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockAConestionLG();
      setCongestionData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取大盘拥挤度失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取股债利差
  const fetchEBSData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockEBSLG();
      setEbsData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取股债利差失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取巴菲特指标
  const fetchBuffettData = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockBuffettIndexLG();
      setBuffettData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取巴菲特指标失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
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
    if (activeTab === "大盘拥挤度" && congestionData.length === 0) {
      fetchCongestionData();
    } else if (activeTab === "股债利差" && ebsData.length === 0) {
      fetchEBSData();
    } else if (activeTab === "巴菲特指标" && buffettData.length === 0) {
      fetchBuffettData();
    }
  }, [activeTab]);

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
      <Badge colorPalette={colorScheme}>
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
      <Badge colorPalette={colorScheme}>
        {(decile * 100).toFixed(2)}% ({description})
      </Badge>
    );
  };

  return (
    <Box p={8}>
      <Heading mb={6}>乐咕乐股市场指标</Heading>
      
      <Tabs.Root value={activeTab} onValueChange={(e) => setActiveTab(e.value)} mb={6}>
        <Tabs.List>
          <Tabs.Trigger value="大盘拥挤度">大盘拥挤度</Tabs.Trigger>
          <Tabs.Trigger value="股债利差">股债利差</Tabs.Trigger>
          <Tabs.Trigger value="巴菲特指标">巴菲特指标</Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>

      <Tabs.ContentGroup>
        {/* 大盘拥挤度 */}
        <Tabs.Content value="股债利差">
          <Box>
            <Flex mb={4} align="center">
              <Heading size="md">大盘拥挤度</Heading>
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchCongestionData}
                loading={loading && activeTab === "大盘拥挤度"}
              >
                刷新数据
              </Button>
            </Flex>
            
            {congestionData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(congestionData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新收盘价</Stat.Label>
                  <Stat.ValueText>{congestionData[0]?.close?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新拥挤度</Stat.Label>
                  <Stat.ValueText>
                    {congestionData[0]?.congestion !== null 
                      ? (congestionData[0]!.congestion! * 100).toFixed(2) + '%' 
                      : '-'}
                  </Stat.ValueText>
                  <Stat.HelpText>
                    {congestionData[0]?.congestion !== null 
                      ? congestionData[0]!.congestion! > 0.5 ? '偏高' : '偏低'
                      : '-'}
                  </Stat.HelpText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader >收盘价</Table.ColumnHeader>
                    <Table.ColumnHeader >拥挤度</Table.ColumnHeader>
                    <Table.ColumnHeader>拥挤度级别</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {congestionData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.name || index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell >{item.close?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >
                        {item.congestion !== null 
                          ? (item.congestion * 100).toFixed(2) + '%' 
                          : '-'}
                      </Table.Cell>
                      <Table.Cell>{renderCongestionLevel(item.congestion)}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {congestionData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {congestionData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 股债利差 */}
        <Tabs.Content value="巴菲特指标">
          <Box>
            <Flex mb={4} align="center">
              <Heading size="md">股债利差</Heading>
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchEBSData}
                loading={loading && activeTab === "股债利差"}
              >
                刷新数据
              </Button>
            </Flex>
            
            {ebsData.length > 0 && (
              <SimpleGrid columns={4} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(ebsData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>沪深 300 指数</Stat.Label>
                  <Stat.ValueText>{ebsData[0]?.hs300_index?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>股债利差</Stat.Label>
                  <Stat.ValueText>
                    {ebsData[0]?.ebs !== null 
                      ? (ebsData[0]!.ebs! * 100).toFixed(2) + '%' 
                      : '-'}
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>股债利差均线</Stat.Label>
                  <Stat.ValueText>
                    {ebsData[0]?.ebs_ma !== null 
                      ? (ebsData[0]!.ebs_ma! * 100).toFixed(2) + '%' 
                      : '-'}
                  </Stat.ValueText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader >沪深 300 指数</Table.ColumnHeader>
                    <Table.ColumnHeader >股债利差</Table.ColumnHeader>
                    <Table.ColumnHeader >股债利差均线</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {ebsData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.name || index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell >{item.hs300_index?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >
                        {item.ebs !== null 
                          ? (item.ebs * 100).toFixed(2) + '%' 
                          : '-'}
                      </Table.Cell>
                      <Table.Cell >
                        {item.ebs_ma !== null 
                          ? (item.ebs_ma * 100).toFixed(2) + '%' 
                          : '-'}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {ebsData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {ebsData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>

        {/* 巴菲特指标 */}
        <Tabs.Content value="大盘拥挤度">
          <Box>
            <Flex mb={4} align="center">
              <Heading size="md">巴菲特指标</Heading>
              <Spacer />
              <Button
                colorPalette="blue"
                onClick={fetchBuffettData}
                loading={loading && activeTab === "巴菲特指标"}
              >
                刷新数据
              </Button>
            </Flex>
            
            {buffettData.length > 0 && (
              <SimpleGrid columns={3} gap={4} mb={4}>
                <Stat.Root>
                  <Stat.Label>最新日期</Stat.Label>
                  <Stat.ValueText>{formatDate(buffettData[0]?.date)}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>最新收盘价</Stat.Label>
                  <Stat.ValueText>{buffettData[0]?.close?.toFixed(2) || '-'}</Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>总市值/GDP</Stat.Label>
                  <Stat.ValueText>
                    {buffettData[0]?.total_market_cap !== null && buffettData[0]?.gdp !== null
                      ? ((buffettData[0]!.total_market_cap! / buffettData[0]!.gdp!) * 100).toFixed(2) + '%'
                      : '-'}
                  </Stat.ValueText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>近十年分位数</Stat.Label>
                  <Stat.ValueText>
                    {buffettData[0]?.decile_10y !== null 
                      ? (buffettData[0]!.decile_10y! * 100).toFixed(2) + '%' 
                      : '-'}
                  </Stat.ValueText>
                  <Stat.HelpText>
                    {buffettData[0]?.decile_10y !== null
                      ? buffettData[0]!.decile_10y! > 0.5 ? '偏高' : '偏低'
                      : '-'}
                  </Stat.HelpText>
                </Stat.Root>
                <Stat.Root>
                  <Stat.Label>总历史分位数</Stat.Label>
                  <Stat.ValueText>
                    {buffettData[0]?.decile_all !== null 
                      ? (buffettData[0]!.decile_all! * 100).toFixed(2) + '%' 
                      : '-'}
                  </Stat.ValueText>
                  <Stat.HelpText>
                    {buffettData[0]?.decile_all !== null
                      ? buffettData[0]!.decile_all! > 0.5 ? '偏高' : '偏低'
                      : '-'}
                  </Stat.HelpText>
                </Stat.Root>
              </SimpleGrid>
            )}

            <Box>
              <Table.Root  size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>日期</Table.ColumnHeader>
                    <Table.ColumnHeader >收盘价</Table.ColumnHeader>
                    <Table.ColumnHeader >总市值 (亿元)</Table.ColumnHeader>
                    <Table.ColumnHeader >GDP(亿元)</Table.ColumnHeader>
                    <Table.ColumnHeader >近十年分位数</Table.ColumnHeader>
                    <Table.ColumnHeader >总历史分位数</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {buffettData.slice(0, 100).map((item, index) => (
                    <Table.Row key={item.code || item.name || index}>
                      <Table.Cell>{formatDate(item.date)}</Table.Cell>
                      <Table.Cell >{item.close?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.total_market_cap?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >{item.gdp?.toFixed(2) || '-'}</Table.Cell>
                      <Table.Cell >
                        {item.decile_10y !== null 
                          ? renderDecile(item.decile_10y)
                          : '-'}
                      </Table.Cell>
                      <Table.Cell >
                        {item.decile_all !== null 
                          ? renderDecile(item.decile_all)
                          : '-'}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
            
            {buffettData.length > 100 && (
              <Text mt={2} color="gray.500" fontSize="sm">
                仅显示前 100 条，共 {buffettData.length} 条数据
              </Text>
            )}
          </Box>
        </Tabs.Content>
      </Tabs.ContentGroup>
    </Box>
  );
};

export default LeguleGuMarketIndicatorsPage;
