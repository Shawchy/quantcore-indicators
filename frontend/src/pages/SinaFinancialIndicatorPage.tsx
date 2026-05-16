/**
 * 新浪财经财务指标页面
 * 展示 86 个财务指标数据
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Flex, Heading, Input, InputGroup, SimpleGrid, Spinner, Stat, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockFinancialIndicator,
} from '@/services/akshare/index';

const SinaFinancialIndicatorPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stockCode, setStockCode] = useState('600004');
  const [startYear, setStartYear] = useState('2020');
  const [indicatorData, setIndicatorData] = useState<StockFinancialIndicator[]>([]);
  const [, setActiveTab] = useState("盈利能力");
  
  ;

  // 获取财务指标数据
  const fetchFinancialIndicator = async (code: string, year: string) => {
    if (!code) {
      toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getFinancialIndicator(code, year);
      setIndicatorData(result.data || []);
      toaster.create({ 
        title: `获取成功，共${result.data?.length || 0}条数据`, 
        type: 'success', 
        duration: 2000, 
        closable: true 
      });
    } catch (error) {
      console.error('获取财务指标数据失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
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
        <Stat.Root>
          <Stat.Label>摊薄每股收益</Stat.Label>
          <Stat.ValueText>{formatValue(latestData.diluted_eps, '元')}</Stat.ValueText>
          <Stat.HelpText>最新报告期</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>净资产收益率</Stat.Label>
          <Stat.ValueText>{formatValue(latestData.roe, '%')}</Stat.ValueText>
          <Stat.HelpText>最新报告期</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>销售毛利率</Stat.Label>
          <Stat.ValueText>{formatValue(latestData.gross_profit_margin, '%')}</Stat.ValueText>
          <Stat.HelpText>最新报告期</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>主营业务收入增长率</Stat.Label>
          <Stat.ValueText>{formatValue(latestData.revenue_growth_rate, '%')}</Stat.ValueText>
          <Stat.HelpText>最新报告期</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>净利润增长率</Stat.Label>
          <Stat.ValueText>{formatValue(latestData.net_profit_growth_rate, '%')}</Stat.ValueText>
          <Stat.HelpText>最新报告期</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>资产负债率</Stat.Label>
          <Stat.ValueText>{formatValue(latestData.asset_liability_ratio, '%')}</Stat.ValueText>
          <Stat.HelpText>最新报告期</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>流动比率</Stat.Label>
          <Stat.ValueText>{formatValue(latestData.current_ratio)}</Stat.ValueText>
          <Stat.HelpText>最新报告期</Stat.HelpText>
        </Stat.Root>
        
        <Stat.Root>
          <Stat.Label>应收账款周转率</Stat.Label>
          <Stat.ValueText>{formatValue(latestData.accounts_receivable_turnover, '次')}</Stat.ValueText>
          <Stat.HelpText>最新报告期</Stat.HelpText>
        </Stat.Root>
      </SimpleGrid>
    );
  };

  // 渲染每股指标表格
  const renderPerShareMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>每股指标</Heading>
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>日期</Table.ColumnHeader>
              <Table.ColumnHeader >摊薄每股收益</Table.ColumnHeader>
              <Table.ColumnHeader >加权每股收益</Table.ColumnHeader>
              <Table.ColumnHeader >调整后每股收益</Table.ColumnHeader>
              <Table.ColumnHeader >扣非后每股收益</Table.ColumnHeader>
              <Table.ColumnHeader >每股净资产 (调整前)</Table.ColumnHeader>
              <Table.ColumnHeader >每股净资产 (调整后)</Table.ColumnHeader>
              <Table.ColumnHeader >每股经营性现金流</Table.ColumnHeader>
              <Table.ColumnHeader >每股资本公积金</Table.ColumnHeader>
              <Table.ColumnHeader >每股未分配利润</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.map((item, index) => (
              <Table.Row key={item.code || item.date || index}>
                <Table.Cell fontWeight="bold">{item.date || '-'}</Table.Cell>
                <Table.Cell >{formatValue(item.diluted_eps)}</Table.Cell>
                <Table.Cell >{formatValue(item.weighted_eps)}</Table.Cell>
                <Table.Cell >{formatValue(item.adjusted_eps)}</Table.Cell>
                <Table.Cell >{formatValue(item.non_recurring_eps)}</Table.Cell>
                <Table.Cell >{formatValue(item.adjusted_net_asset_per_share_before)}</Table.Cell>
                <Table.Cell >{formatValue(item.adjusted_net_asset_per_share_after)}</Table.Cell>
                <Table.Cell >{formatValue(item.operating_cash_flow_per_share)}</Table.Cell>
                <Table.Cell >{formatValue(item.capital_reserve_per_share)}</Table.Cell>
                <Table.Cell >{formatValue(item.undistributed_profit_per_share)}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    );
  };

  // 渲染盈利能力表格
  const renderProfitabilityMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>盈利能力</Heading>
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>日期</Table.ColumnHeader>
              <Table.ColumnHeader >总资产利润率</Table.ColumnHeader>
              <Table.ColumnHeader >主营业务利润率</Table.ColumnHeader>
              <Table.ColumnHeader >总资产净利润率</Table.ColumnHeader>
              <Table.ColumnHeader >成本费用利润率</Table.ColumnHeader>
              <Table.ColumnHeader >营业利润率</Table.ColumnHeader>
              <Table.ColumnHeader >主营业务成本率</Table.ColumnHeader>
              <Table.ColumnHeader >销售净利率</Table.ColumnHeader>
              <Table.ColumnHeader >销售毛利率</Table.ColumnHeader>
              <Table.ColumnHeader >净资产收益率</Table.ColumnHeader>
              <Table.ColumnHeader >加权净资产收益率</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.map((item, index) => (
              <Table.Row key={item.code || item.date || index}>
                <Table.Cell fontWeight="bold">{item.date || '-'}</Table.Cell>
                <Table.Cell >{formatValue(item.return_on_total_assets, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.return_on_main_business, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.return_on_net_assets, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.return_on_cost_expense, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.operating_profit_margin, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.main_business_cost_ratio, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.net_profit_margin, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.gross_profit_margin, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.roe, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.weighted_roe, '%')}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    );
  };

  // 渲染成长能力表格
  const renderGrowthMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>成长能力</Heading>
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>日期</Table.ColumnHeader>
              <Table.ColumnHeader >主营业务收入增长率</Table.ColumnHeader>
              <Table.ColumnHeader >净利润增长率</Table.ColumnHeader>
              <Table.ColumnHeader >净资产增长率</Table.ColumnHeader>
              <Table.ColumnHeader >总资产增长率</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.map((item, index) => (
              <Table.Row key={item.code || item.date || index}>
                <Table.Cell fontWeight="bold">{item.date || '-'}</Table.Cell>
                <Table.Cell >{formatValue(item.revenue_growth_rate, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.net_profit_growth_rate, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.net_assets_growth_rate, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.total_assets_growth_rate, '%')}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    );
  };

  // 渲染营运能力表格
  const renderOperationalMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>营运能力</Heading>
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>日期</Table.ColumnHeader>
              <Table.ColumnHeader >应收账款周转率</Table.ColumnHeader>
              <Table.ColumnHeader >应收账款周转天数</Table.ColumnHeader>
              <Table.ColumnHeader >存货周转率</Table.ColumnHeader>
              <Table.ColumnHeader >存货周转天数</Table.ColumnHeader>
              <Table.ColumnHeader >总资产周转率</Table.ColumnHeader>
              <Table.ColumnHeader >总资产周转天数</Table.ColumnHeader>
              <Table.ColumnHeader >流动资产周转率</Table.ColumnHeader>
              <Table.ColumnHeader >流动资产周转天数</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.map((item, index) => (
              <Table.Row key={item.code || item.date || index}>
                <Table.Cell fontWeight="bold">{item.date || '-'}</Table.Cell>
                <Table.Cell >{formatValue(item.accounts_receivable_turnover, '次')}</Table.Cell>
                <Table.Cell >{formatValue(item.accounts_receivable_turnover_days, '天')}</Table.Cell>
                <Table.Cell >{formatValue(item.inventory_turnover, '次')}</Table.Cell>
                <Table.Cell >{formatValue(item.inventory_turnover_days, '天')}</Table.Cell>
                <Table.Cell >{formatValue(item.total_assets_turnover, '次')}</Table.Cell>
                <Table.Cell >{formatValue(item.total_assets_turnover_days, '天')}</Table.Cell>
                <Table.Cell >{formatValue(item.current_assets_turnover, '次')}</Table.Cell>
                <Table.Cell >{formatValue(item.current_assets_turnover_days, '天')}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    );
  };

  // 渲染偿债能力表格
  const renderSolvencyMetrics = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Heading size="md" mb={4}>偿债能力</Heading>
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>日期</Table.ColumnHeader>
              <Table.ColumnHeader >流动比率</Table.ColumnHeader>
              <Table.ColumnHeader >速动比率</Table.ColumnHeader>
              <Table.ColumnHeader >现金比率</Table.ColumnHeader>
              <Table.ColumnHeader >资产负债率</Table.ColumnHeader>
              <Table.ColumnHeader >股东权益比率</Table.ColumnHeader>
              <Table.ColumnHeader >长期负债比率</Table.ColumnHeader>
              <Table.ColumnHeader >利息支付倍数</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.map((item, index) => (
              <Table.Row key={item.code || item.date || index}>
                <Table.Cell fontWeight="bold">{item.date || '-'}</Table.Cell>
                <Table.Cell >{formatValue(item.current_ratio)}</Table.Cell>
                <Table.Cell >{formatValue(item.quick_ratio)}</Table.Cell>
                <Table.Cell >{formatValue(item.cash_ratio, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.asset_liability_ratio, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.equity_ratio, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.long_term_debt_ratio, '%')}</Table.Cell>
                <Table.Cell >{formatValue(item.interest_payment_multiple)}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    );
  };

  // 渲染完整数据表格
  const renderFullTable = (data: StockFinancialIndicator[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto">
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>日期</Table.ColumnHeader>
              {Object.keys(data[0]).filter(key => key !== 'date' && key !== 'extra_fields').map((field) => (
                <Table.ColumnHeader key={field} >{field}</Table.ColumnHeader>
              ))}
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.map((item, index) => (
              <Table.Row key={item.code || item.date || index}>
                <Table.Cell fontWeight="bold">{item.date || '-'}</Table.Cell>
                {Object.keys(item).filter(key => key !== 'date' && key !== 'extra_fields').map((field) => (
                  <Table.Cell key={field} >
                    {formatValue(item[field as keyof StockFinancialIndicator] as number)}
                  </Table.Cell>
                ))}
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    );
  };

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>新浪财经财务指标分析</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center" flexWrap="wrap">
        <InputGroup width={{ base: "100%", md: "250px" }} startAddon="股票代码">
  <Input
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value.toUpperCase())}
            placeholder="输入股票代码，如：600004"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
</InputGroup>
        
        <InputGroup width={{ base: "100%", md: "200px" }} startAddon="开始年份">
  <Input
            value={startYear}
            onChange={(e) => setStartYear(e.target.value)}
            placeholder="输入年份，如：2020"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
</InputGroup>
        
        <Button onClick={handleSearch} colorPalette="blue" loading={loading}>
          查询
        </Button>
        <Badge colorPalette="blue" fontSize="0.8em">
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
          <Tabs.Root onValueChange={(e) => setActiveTab(e.value)} colorPalette="blue">
            <Tabs.List mb={4}>
              <Tabs.Trigger value="每股指标">每股指标</Tabs.Trigger>
              <Tabs.Trigger value="盈利能力">盈利能力</Tabs.Trigger>
              <Tabs.Trigger value="成长能力">成长能力</Tabs.Trigger>
              <Tabs.Trigger value="营运能力">营运能力</Tabs.Trigger>
              <Tabs.Trigger value="偿债能力">偿债能力</Tabs.Trigger>
              <Tabs.Trigger value="完整数据">完整数据</Tabs.Trigger>
            </Tabs.List>

            <Tabs.ContentGroup>
              <Tabs.Content value="盈利能力" p={0}>
                {renderPerShareMetrics(indicatorData)}
              </Tabs.Content>
              
              <Tabs.Content value="成长能力" p={0}>
                {renderProfitabilityMetrics(indicatorData)}
              </Tabs.Content>
              
              <Tabs.Content value="营运能力" p={0}>
                {renderGrowthMetrics(indicatorData)}
              </Tabs.Content>
              
              <Tabs.Content value="偿债能力" p={0}>
                {renderOperationalMetrics(indicatorData)}
              </Tabs.Content>
              
              <Tabs.Content value="完整数据" p={0}>
                {renderSolvencyMetrics(indicatorData)}
              </Tabs.Content>
              
              <Tabs.Content value="完整数据" p={0}>
                <Heading size="md" mb={4}>完整数据（所有字段）</Heading>
                {renderFullTable(indicatorData)}
              </Tabs.Content>
            </Tabs.ContentGroup>
          </Tabs.Root>
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
