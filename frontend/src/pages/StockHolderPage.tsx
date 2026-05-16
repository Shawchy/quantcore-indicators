/**
 * 股东人数及持股集中度页面
 * 展示股东人数变化和持股集中度分析
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Flex, Heading, Input, InputGroup, SimpleGrid, Spinner, Stat, Table, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockHoldNumCNInfo,
} from '@/services/akshare/index';

const StockHolderPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [reportDate, setReportDate] = useState('20210630');
  const [searchTerm, setSearchTerm] = useState('');
  const [holderData, setHolderData] = useState<StockHoldNumCNInfo[]>([]);
  
  ;

  // 获取股东人数数据
  const fetchHolderData = async (date: string) => {
    if (!date) {
      toaster.create({ title: '请选择报告期', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockHoldNumCNInfo(date);
      setHolderData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取股东人数数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载 2021 年中报数据
    fetchHolderData('20210630');
  }, []);

  // 处理查询
  const handleSearch = () => {
    fetchHolderData(reportDate);
  };

  // 搜索过滤
  const filterData = (data: StockHoldNumCNInfo[], term: string) => {
    if (!term) return data;
    
    return data.filter(item => {
      const code = item.security_code.toLowerCase();
      const name = item.security_abbr.toLowerCase();
      const searchLower = term.toLowerCase();
      return code.includes(searchLower) || name.includes(searchLower);
    });
  };

  // 格式化数值
  const formatNumber = (value: number | null, suffix: string = '') => {
    if (value === null || value === undefined) return '-';
    return `${value.toLocaleString()}${suffix}`;
  };

  const formatPercent = (value: number | null) => {
    if (value === null || value === undefined) return '-';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  // 计算统计数据
  const calculateStats = () => {
    if (holderData.length === 0) return null;

    const avgHolderCount = holderData.reduce((sum, item) => sum + (item.current_holder_count || 0), 0) / holderData.length;
    const avgGrowth = holderData.reduce((sum, item) => sum + (item.holder_count_growth || 0), 0) / holderData.length;
    const increaseCount = holderData.filter(item => (item.holder_count_growth || 0) > 0).length;
    const decreaseCount = holderData.filter(item => (item.holder_count_growth || 0) < 0).length;

    return {
      avgHolderCount: Math.round(avgHolderCount),
      avgGrowth: avgGrowth.toFixed(2),
      increaseCount,
      decreaseCount,
    };
  };

  const stats = calculateStats();

  // 渲染统计数据
  const renderStats = () => {
    if (!stats) return null;

    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
        <Stat.Root>
          <Stat.Label>平均股东人数</Stat.Label>
          <Stat.ValueText>{formatNumber(stats.avgHolderCount, '人')}</Stat.ValueText>
          <Stat.HelpText>所有股票平均值</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>平均增幅</Stat.Label>
          <Stat.ValueText color={parseFloat(stats.avgGrowth) > 0 ? 'red' : 'green'}>
            {formatPercent(parseFloat(stats.avgGrowth))}
          </Stat.ValueText>
          <Stat.HelpText>股东人数平均变化</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>股东增加</Stat.Label>
          <Stat.ValueText color="red">{formatNumber(stats.increaseCount, '家')}</Stat.ValueText>
          <Stat.HelpText>股东户数增加的公司</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>股东减少</Stat.Label>
          <Stat.ValueText color="green">{formatNumber(stats.decreaseCount, '家')}</Stat.ValueText>
          <Stat.HelpText>股东户数减少的公司</Stat.HelpText>
        </Stat.Root>
      </SimpleGrid>
    );
  };

  // 渲染表格
  const renderTable = () => {
    const filteredData = filterData(holderData, searchTerm);

    return (
      <Box overflowX="auto">
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>证券代码</Table.ColumnHeader>
              <Table.ColumnHeader>证券简称</Table.ColumnHeader>
              <Table.ColumnHeader>变动日期</Table.ColumnHeader>
              <Table.ColumnHeader >本期股东人数</Table.ColumnHeader>
              <Table.ColumnHeader >上期股东人数</Table.ColumnHeader>
              <Table.ColumnHeader >股东人数增幅</Table.ColumnHeader>
              <Table.ColumnHeader >本期人均持股</Table.ColumnHeader>
              <Table.ColumnHeader >上期人均持股</Table.ColumnHeader>
              <Table.ColumnHeader >人均持股增幅</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredData.slice(0, 100).map((item, index) => (
              <Table.Row key={index}>
                <Table.Cell fontWeight="bold">{item.security_code}</Table.Cell>
                <Table.Cell>{item.security_abbr}</Table.Cell>
                <Table.Cell>{item.change_date}</Table.Cell>
                <Table.Cell >{formatNumber(item.current_holder_count, '人')}</Table.Cell>
                <Table.Cell >{formatNumber(item.previous_holder_count, '人')}</Table.Cell>
                <Table.Cell >
                  <Badge colorPalette={item.holder_count_growth && item.holder_count_growth > 0 ? 'red' : 'green'}>
                    {formatPercent(item.holder_count_growth)}
                  </Badge>
                </Table.Cell>
                <Table.Cell >{formatNumber(item.current_avg_shares, '万股')}</Table.Cell>
                <Table.Cell >{formatNumber(item.previous_avg_shares, '万股')}</Table.Cell>
                <Table.Cell >
                  <Badge colorPalette={item.avg_shares_growth && item.avg_shares_growth > 0 ? 'green' : 'red'}>
                    {formatPercent(item.avg_shares_growth)}
                  </Badge>
                </Table.Cell>
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
      <Heading size="lg" mb={6}>股东人数及持股集中度分析</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center" flexWrap="wrap">
        <InputGroup width={{ base: "100%", md: "250px" }} startAddon="报告期">
  <Input
            value={reportDate}
            onChange={(e) => setReportDate(e.target.value)}
            placeholder="YYYYMMDD"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
</InputGroup>
        
        <Button onClick={handleSearch} colorPalette="blue" loading={loading}>
          查询
        </Button>
        
        <InputGroup width={{ base: "100%", md: "300px" }} startAddon="搜索">
  <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="输入股票代码或简称搜索"
          />
</InputGroup>
        
        <Badge colorPalette="blue" fontSize="0.8em">
          示例：20210630（2021 年中报）
        </Badge>
      </Flex>

      {loading && holderData.length === 0 ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <>
          {/* 统计数据 */}
          <Flex justify="space-between" align="center" mb={4}>
            <Heading size="md">统计摘要</Heading>
            <Text fontSize="sm" color="gray.500">
              共 {holderData.length} 条数据
            </Text>
          </Flex>
          {renderStats()}

          {/* 数据表格 */}
          <Heading size="md" mb={4}>详细数据</Heading>
          {renderTable()}
        </>
      )}

      {/* 数据说明 */}
      <Box mt={8} p={4} bg="gray.50" borderRadius="md">
        <Heading size="sm" mb={2}>数据说明</Heading>
        <Text fontSize="sm" color="gray.600">
          1. 数据来源：巨潮资讯 - 数据中心 - 专题统计 - 股东股本
        </Text>
        <Text fontSize="sm" color="gray.600">
          2. 报告期：可选值 YYYY0331（一季报）、YYYY0630（中报）、YYYY0930（三季报）、YYYY1231（年报），其中 YYYY 代表年份
        </Text>
        <Text fontSize="sm" color="gray.600">
          3. 数据范围：从 20170331 开始至今
        </Text>
        <Text fontSize="sm" color="gray.600">
          4. 股东人数增幅：（本期股东人数 - 上期股东人数）/ 上期股东人数 × 100%
        </Text>
        <Text fontSize="sm" color="gray.600">
          5. 人均持股数量：人均持有流通股数量，单位：万股
        </Text>
        <Text fontSize="sm" color="gray.600">
          6. 分析意义：
            - 股东人数增加，筹码分散，通常利空
            - 股东人数减少，筹码集中，通常利好
            - 人均持股增加，说明筹码趋向集中
        </Text>
      </Box>
    </Box>
  );
};

export default StockHolderPage;
