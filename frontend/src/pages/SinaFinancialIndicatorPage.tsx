/**
 * 新浪财经财务指标页面
 * 展示 86 个财务指标数据
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
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockFinancialIndicator,
} from '@/services/akshare/index';

const SinaFinancialIndicatorPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stockCode, setStockCode] = useState('600004');
  const [startYear, setStartYear] = useState('2020');
  const [indicatorData, setIndicatorData] = useState<StockFinancialIndicator[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  
  const toast = useToast();

  // 获取财务指标数据
  const fetchFinancialIndicator = async (code: string, year: string) => {
    if (!code) {
      toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getFinancialIndicator(code, year);
      setIndicatorData(result);
      toast({ 
        title: `获取成功，共${result.length}条数据`, 
        status: 'success', 
        duration: 2000, 
        isClosable: true 
      });
    } catch (error) {
      console.error('获取财务指标数据失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载南方航空 2020 年数据
    fetchFinancialIndicator('600004', '2020');
  }, []);

  // 处理查询
  const handleSearch = () => {
    fetchFinancialIndicator(stockCode, startYear);
  };

  // 格式化数值
  const formatValue = (value: number | null, suffix: string = '') => {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(2)}${suffix}`;
  };

  // 渲染主要指标卡片
  const renderMainMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    const latestData = data[0];
    
    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
        <Stat>
          <StatLabel>摊薄每股收益</StatLabel>
          <StatNumber>{formatValue(latestData.diluted_eps, '元')}</StatNumber>
          <StatHelpText>最新报告期</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>净资产收益率</StatLabel>
          <StatNumber>{formatValue(latestData.roe, '%')}</StatNumber>
          <StatHelpText>最新报告期</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>销售毛利率</StatLabel>
          <StatNumber>{formatValue(latestData.gross_profit_margin, '%')}</StatNumber>
          <StatHelpText>最新报告期</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>主营业务收入增长率</StatLabel>
          <StatNumber>{formatValue(latestData.revenue_growth_rate, '%')}</StatNumber>
          <StatHelpText>最新报告期</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>净利润增长率</StatLabel>
          <StatNumber>{formatValue(latestData.net_profit_growth_rate, '%')}</StatNumber>
          <StatHelpText>最新报告期</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>资产负债率</StatLabel>
          <StatNumber>{formatValue(latestData.asset_liability_ratio, '%')}</StatNumber>
          <StatHelpText>最新报告期</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>流动比率</StatLabel>
          <StatNumber>{formatValue(latestData.current_ratio)}</StatNumber>
          <StatHelpText>最新报告期</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>应收账款周转率</StatLabel>
          <StatNumber>{formatValue(latestData.accounts_receivable_turnover, '次')}</StatNumber>
          <StatHelpText>最新报告期</StatHelpText>
        </Stat>
      </SimpleGrid>
    );
  };

  // 渲染每股指标表格
  const renderPerShareMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>每股指标</Heading>
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>日期</Th>
              <Th isNumeric>摊薄每股收益</Th>
              <Th isNumeric>加权每股收益</Th>
              <Th isNumeric>调整后每股收益</Th>
              <Th isNumeric>扣非后每股收益</Th>
              <Th isNumeric>每股净资产 (调整前)</Th>
              <Th isNumeric>每股净资产 (调整后)</Th>
              <Th isNumeric>每股经营性现金流</Th>
              <Th isNumeric>每股资本公积金</Th>
              <Th isNumeric>每股未分配利润</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.map((item, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{item.date || '-'}</Td>
                <Td isNumeric>{formatValue(item.diluted_eps)}</Td>
                <Td isNumeric>{formatValue(item.weighted_eps)}</Td>
                <Td isNumeric>{formatValue(item.adjusted_eps)}</Td>
                <Td isNumeric>{formatValue(item.non_recurring_eps)}</Td>
                <Td isNumeric>{formatValue(item.adjusted_net_asset_per_share_before)}</Td>
                <Td isNumeric>{formatValue(item.adjusted_net_asset_per_share_after)}</Td>
                <Td isNumeric>{formatValue(item.operating_cash_flow_per_share)}</Td>
                <Td isNumeric>{formatValue(item.capital_reserve_per_share)}</Td>
                <Td isNumeric>{formatValue(item.undistributed_profit_per_share)}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  // 渲染盈利能力表格
  const renderProfitabilityMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>盈利能力</Heading>
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>日期</Th>
              <Th isNumeric>总资产利润率</Th>
              <Th isNumeric>主营业务利润率</Th>
              <Th isNumeric>总资产净利润率</Th>
              <Th isNumeric>成本费用利润率</Th>
              <Th isNumeric>营业利润率</Th>
              <Th isNumeric>主营业务成本率</Th>
              <Th isNumeric>销售净利率</Th>
              <Th isNumeric>销售毛利率</Th>
              <Th isNumeric>净资产收益率</Th>
              <Th isNumeric>加权净资产收益率</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.map((item, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{item.date || '-'}</Td>
                <Td isNumeric>{formatValue(item.return_on_total_assets, '%')}</Td>
                <Td isNumeric>{formatValue(item.return_on_main_business, '%')}</Td>
                <Td isNumeric>{formatValue(item.return_on_net_assets, '%')}</Td>
                <Td isNumeric>{formatValue(item.return_on_cost_expense, '%')}</Td>
                <Td isNumeric>{formatValue(item.operating_profit_margin, '%')}</Td>
                <Td isNumeric>{formatValue(item.main_business_cost_ratio, '%')}</Td>
                <Td isNumeric>{formatValue(item.net_profit_margin, '%')}</Td>
                <Td isNumeric>{formatValue(item.gross_profit_margin, '%')}</Td>
                <Td isNumeric>{formatValue(item.roe, '%')}</Td>
                <Td isNumeric>{formatValue(item.weighted_roe, '%')}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  // 渲染成长能力表格
  const renderGrowthMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>成长能力</Heading>
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>日期</Th>
              <Th isNumeric>主营业务收入增长率</Th>
              <Th isNumeric>净利润增长率</Th>
              <Th isNumeric>净资产增长率</Th>
              <Th isNumeric>总资产增长率</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.map((item, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{item.date || '-'}</Td>
                <Td isNumeric>{formatValue(item.revenue_growth_rate, '%')}</Td>
                <Td isNumeric>{formatValue(item.net_profit_growth_rate, '%')}</Td>
                <Td isNumeric>{formatValue(item.net_assets_growth_rate, '%')}</Td>
                <Td isNumeric>{formatValue(item.total_assets_growth_rate, '%')}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  // 渲染营运能力表格
  const renderOperationalMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>营运能力</Heading>
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>日期</Th>
              <Th isNumeric>应收账款周转率</Th>
              <Th isNumeric>应收账款周转天数</Th>
              <Th isNumeric>存货周转率</Th>
              <Th isNumeric>存货周转天数</Th>
              <Th isNumeric>总资产周转率</Th>
              <Th isNumeric>总资产周转天数</Th>
              <Th isNumeric>流动资产周转率</Th>
              <Th isNumeric>流动资产周转天数</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.map((item, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{item.date || '-'}</Td>
                <Td isNumeric>{formatValue(item.accounts_receivable_turnover, '次')}</Td>
                <Td isNumeric>{formatValue(item.accounts_receivable_turnover_days, '天')}</Td>
                <Td isNumeric>{formatValue(item.inventory_turnover, '次')}</Td>
                <Td isNumeric>{formatValue(item.inventory_turnover_days, '天')}</Td>
                <Td isNumeric>{formatValue(item.total_assets_turnover, '次')}</Td>
                <Td isNumeric>{formatValue(item.total_assets_turnover_days, '天')}</Td>
                <Td isNumeric>{formatValue(item.current_assets_turnover, '次')}</Td>
                <Td isNumeric>{formatValue(item.current_assets_turnover_days, '天')}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  // 渲染偿债能力表格
  const renderSolvencyMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>偿债能力</Heading>
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>日期</Th>
              <Th isNumeric>流动比率</Th>
              <Th isNumeric>速动比率</Th>
              <Th isNumeric>现金比率</Th>
              <Th isNumeric>资产负债率</Th>
              <Th isNumeric>股东权益比率</Th>
              <Th isNumeric>长期负债比率</Th>
              <Th isNumeric>利息支付倍数</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.map((item, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{item.date || '-'}</Td>
                <Td isNumeric>{formatValue(item.current_ratio)}</Td>
                <Td isNumeric>{formatValue(item.quick_ratio)}</Td>
                <Td isNumeric>{formatValue(item.cash_ratio, '%')}</Td>
                <Td isNumeric>{formatValue(item.asset_liability_ratio, '%')}</Td>
                <Td isNumeric>{formatValue(item.equity_ratio, '%')}</Td>
                <Td isNumeric>{formatValue(item.long_term_debt_ratio, '%')}</Td>
                <Td isNumeric>{formatValue(item.interest_payment_multiple)}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  // 渲染完整数据表格
  const renderFullTable = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto">
        <Table variant="simple" size="xs">
          <Thead>
            <Tr>
              <Th>日期</Th>
              {Object.keys(data[0]).filter(key => key !== 'date' && key !== 'extra_fields').map((field) => (
                <Th key={field} isNumeric>{field}</Th>
              ))}
            </Tr>
          </Thead>
          <Tbody>
            {data.map((item, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{item.date || '-'}</Td>
                {Object.keys(item).filter(key => key !== 'date' && key !== 'extra_fields').map((field) => (
                  <Td key={field} isNumeric>
                    {formatValue(item[field as keyof StockFinancialIndicator] as number)}
                  </Td>
                ))}
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>新浪财经财务指标分析</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center" flexWrap="wrap">
        <InputGroup width={{ base: "100%", md: "250px" }}>
          <InputLeftAddon>股票代码</InputLeftAddon>
          <Input
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value.toUpperCase())}
            placeholder="输入股票代码，如：600004"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
        </InputGroup>
        
        <InputGroup width={{ base: "100%", md: "200px" }}>
          <InputLeftAddon>开始年份</InputLeftAddon>
          <Input
            value={startYear}
            onChange={(e) => setStartYear(e.target.value)}
            placeholder="输入年份，如：2020"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
        </InputGroup>
        
        <Button onClick={handleSearch} colorScheme="blue" isLoading={loading}>
          查询
        </Button>
        <Badge colorScheme="blue" fontSize="0.8em">
          示例：600004（南方航空）
        </Badge>
      </Flex>

      {loading && indicatorData.length === 0 ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <>
          {/* 主要指标卡片 */}
          <Flex justify="space-between" align="center" mb={4}>
            <Heading size="md">主要财务指标</Heading>
            <Text fontSize="sm" color="gray.500">
              共 {indicatorData.length} 条数据
            </Text>
          </Flex>
          {renderMainMetrics(indicatorData)}

          {/* Tab 面板 */}
          <Tabs onChange={setActiveTab} colorScheme="blue" isFitted>
            <TabList mb={4}>
              <Tab>每股指标</Tab>
              <Tab>盈利能力</Tab>
              <Tab>成长能力</Tab>
              <Tab>营运能力</Tab>
              <Tab>偿债能力</Tab>
              <Tab>完整数据</Tab>
            </TabList>

            <TabPanels>
              <TabPanel p={0}>
                {renderPerShareMetrics(indicatorData)}
              </TabPanel>
              
              <TabPanel p={0}>
                {renderProfitabilityMetrics(indicatorData)}
              </TabPanel>
              
              <TabPanel p={0}>
                {renderGrowthMetrics(indicatorData)}
              </TabPanel>
              
              <TabPanel p={0}>
                {renderOperationalMetrics(indicatorData)}
              </TabPanel>
              
              <TabPanel p={0}>
                {renderSolvencyMetrics(indicatorData)}
              </TabPanel>
              
              <TabPanel p={0}>
                <Heading size="md" mb={4}>完整数据（所有字段）</Heading>
                {renderFullTable(indicatorData)}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </>
      )}

      {/* 数据说明 */}
      <Box mt={8} p={4} bg="gray.50" borderRadius="md">
        <Heading size="sm" mb={2}>数据说明</Heading>
        <Text fontSize="sm" color="gray.600">
          1. 数据来源：新浪财经财务分析数据
        </Text>
        <Text fontSize="sm" color="gray.600">
          2. 数据范围：从指定开始年份至今的所有历史数据
        </Text>
        <Text fontSize="sm" color="gray.600">
          3. 指标数量：包含 86 个财务指标
        </Text>
        <Text fontSize="sm" color="gray.600">
          4. 指标分类：每股指标、盈利能力、成长能力、营运能力、偿债能力
        </Text>
        <Text fontSize="sm" color="gray.600">
          5. 更新频率：根据上市公司定期报告更新
        </Text>
      </Box>
    </Box>
  );
};

export default SinaFinancialIndicatorPage;
