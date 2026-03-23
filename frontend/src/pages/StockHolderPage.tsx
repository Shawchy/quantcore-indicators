/**
 * 股东人数及持股集中度页面
 * 展示股东人数变化和持股集中度分析
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
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockHoldNumCNInfo,
} from '../../services/eastmoney';

const StockHolderPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [reportDate, setReportDate] = useState('20210630');
  const [searchTerm, setSearchTerm] = useState('');
  const [holderData, setHolderData] = useState<StockHoldNumCNInfo[]>([]);
  
  const toast = useToast();

  // 获取股东人数数据
  const fetchHolderData = async (date: string) => {
    if (!date) {
      toast({ title: '请选择报告期', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockHoldNumCNInfo(date);
      setHolderData(result);
      toast({ 
        title: `获取成功，共${result.length}条数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取股东人数数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
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
        <Stat>
          <StatLabel>平均股东人数</StatLabel>
          <StatNumber>{formatNumber(stats.avgHolderCount, '人')}</StatNumber>
          <StatHelpText>所有股票平均值</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>平均增幅</StatLabel>
          <StatNumber color={parseFloat(stats.avgGrowth) > 0 ? 'red' : 'green'}>
            {formatPercent(parseFloat(stats.avgGrowth))}
          </StatNumber>
          <StatHelpText>股东人数平均变化</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>股东增加</StatLabel>
          <StatNumber color="red">{formatNumber(stats.increaseCount, '家')}</StatNumber>
          <StatHelpText>股东户数增加的公司</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>股东减少</StatLabel>
          <StatNumber color="green">{formatNumber(stats.decreaseCount, '家')}</StatNumber>
          <StatHelpText>股东户数减少的公司</StatHelpText>
        </Stat>
      </SimpleGrid>
    );
  };

  // 渲染表格
  const renderTable = () => {
    const filteredData = filterData(holderData, searchTerm);

    return (
      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>证券代码</Th>
              <Th>证券简称</Th>
              <Th>变动日期</Th>
              <Th isNumeric>本期股东人数</Th>
              <Th isNumeric>上期股东人数</Th>
              <Th isNumeric>股东人数增幅</Th>
              <Th isNumeric>本期人均持股</Th>
              <Th isNumeric>上期人均持股</Th>
              <Th isNumeric>人均持股增幅</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredData.slice(0, 100).map((item, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{item.security_code}</Td>
                <Td>{item.security_abbr}</Td>
                <Td>{item.change_date}</Td>
                <Td isNumeric>{formatNumber(item.current_holder_count, '人')}</Td>
                <Td isNumeric>{formatNumber(item.previous_holder_count, '人')}</Td>
                <Td isNumeric>
                  <Badge colorScheme={item.holder_count_growth && item.holder_count_growth > 0 ? 'red' : 'green'}>
                    {formatPercent(item.holder_count_growth)}
                  </Badge>
                </Td>
                <Td isNumeric>{formatNumber(item.current_avg_shares, '万股')}</Td>
                <Td isNumeric>{formatNumber(item.previous_avg_shares, '万股')}</Td>
                <Td isNumeric>
                  <Badge colorScheme={item.avg_shares_growth && item.avg_shares_growth > 0 ? 'green' : 'red'}>
                    {formatPercent(item.avg_shares_growth)}
                  </Badge>
                </Td>
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
      <Heading size="lg" mb={6}>股东人数及持股集中度分析</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center" flexWrap="wrap">
        <InputGroup width={{ base: "100%", md: "250px" }}>
          <InputLeftAddon>报告期</InputLeftAddon>
          <Input
            value={reportDate}
            onChange={(e) => setReportDate(e.target.value)}
            placeholder="YYYYMMDD"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
        </InputGroup>
        
        <Button onClick={handleSearch} colorScheme="blue" isLoading={loading}>
          查询
        </Button>
        
        <InputGroup width={{ base: "100%", md: "300px" }}>
          <InputLeftAddon>搜索</InputLeftAddon>
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="输入股票代码或简称搜索"
          />
        </InputGroup>
        
        <Badge colorScheme="blue" fontSize="0.8em">
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
          2. 报告期：可选值 XXXX0331（一季报）、XXXX0630（中报）、XXXX0930（三季报）、XXXX1231（年报）
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
