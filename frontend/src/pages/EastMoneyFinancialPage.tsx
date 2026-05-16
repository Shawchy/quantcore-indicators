/**
 * 东方财富财务分析页面
 * 包含：资产负债表、利润表
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Flex, Heading, Input, InputGroup, Spinner, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockBalanceSheet,
  type StockProfitSheet,
} from '@/services/akshare/index';

const EastMoneyFinancialPage: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState("概览") // 0=报告期，1=年度
  const [loading, setLoading] = useState(false)
  const [stockCode, setStockCode] = useState('SH600519')

  // 资产负债表数据
  const [balanceReportData, setBalanceReportData] = useState<StockBalanceSheet[]>([])
  const [balanceYearlyData, setBalanceYearlyData] = useState<StockBalanceSheet[]>([])

  // 利润表数据 - 目前仅使用 report 数据
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_profitReportData, setProfitReportData] = useState<StockProfitSheet[]>([])
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_profitYearlyData, setProfitYearlyData] = useState<StockProfitSheet[]>([])
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_profitQuarterlyData] = useState<StockProfitSheet[]>([])

  

  // 获取资产负债表 - 按报告期
  const fetchBalanceReport = async (code: string) => {
    if (!code) {
      toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getBalanceSheetReport(code);
      setBalanceReportData(result.data || []);
      toaster.create({ title: `获取成功，共${result.data?.length || 0}条报告期数据`, type: 'success', duration: 2000, closable: true });
    } catch (error) {
      console.error('获取资产负债表（报告期）失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取资产负债表 - 按年度
  const fetchBalanceYearly = async (code: string) => {
    if (!code) {
      toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getBalanceSheetYearly(code);
      setBalanceYearlyData(result.data || []);
      toaster.create({ title: `获取成功，共${result.data?.length || 0}条年度数据`, type: 'success', duration: 2000, closable: true });
    } catch (error) {
      console.error('获取资产负债表（年度）失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取利润表 - 按报告期
  const fetchProfitReport = async (code: string) => {
    if (!code) {
      toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getProfitSheetReport(code);
      setProfitReportData(result.data || []);
      toaster.create({ title: `获取成功，共${result.data?.length || 0}条报告期数据`, type: 'success', duration: 2000, closable: true });
    } catch (error) {
      console.error('获取利润表（报告期）失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取利润表 - 按年度
  const fetchProfitYearly = async (code: string) => {
    if (!code) {
      toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getProfitSheetYearly(code);
      setProfitYearlyData(result.data || []);
      toaster.create({ title: `获取成功，共${result.data?.length || 0}条年度数据`, type: 'success', duration: 2000, closable: true });
    } catch (error) {
      console.error('获取利润表（年度）失败:', error);
      toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取利润表 - 按单季度
  // const fetchProfitQuarterly = async (code: string) => {
  //   if (!code) {
  //     toaster.create({ title: '请输入股票代码', type: 'warning', duration: 2000, closable: true });
  //     return;
  //   }
  //   setLoading(true);
  //   try {
  //     const result = await eastMoneyApi.getProfitSheetQuarterly(code);
  //     setProfitQuarterlyData(result.data || []);
  //     toaster.create({ title: `获取成功，共${result.data?.length || 0}条单季度数据`, type: 'success', duration: 2000, closable: true });
  //   } catch (error) {
  //     console.error('获取利润表（单季度）失败:', error);
  //     toaster.create({ title: '获取数据失败', type: 'error', duration: 2000, closable: true });
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  useEffect(() => {
    // 初始加载贵州茅台数据
    fetchBalanceReport('SH600519');
    fetchBalanceYearly('SH600519');
  }, []);

  // 处理查询
  const handleSearch = () => {
    if (activeSubTab === "概览") {
      fetchBalanceReport(stockCode);
      fetchProfitReport(stockCode);
    } else {
      fetchBalanceYearly(stockCode);
      fetchProfitYearly(stockCode);
    }
  };

  // Tab 切换时自动查询
  const handleTabChange = (value: string) => {
    setActiveSubTab(value);
    if (stockCode) {
      if (value === "概览") {
        fetchBalanceReport(stockCode);
        fetchProfitReport(stockCode);
      } else {
        fetchBalanceYearly(stockCode);
        fetchProfitYearly(stockCode);
      }
    }
  };

  // 格式化金额（万元）
  const formatAmount = (value: number | null) => {
    if (value === null || value === undefined) return '-';
    return (value / 10000).toFixed(2);
  };

  // 渲染资产负债表主要指标表格
  const renderBalanceMainMetrics = (data: StockBalanceSheet[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto" mb={6}>
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>报告期</Table.ColumnHeader>
              <Table.ColumnHeader >资产总计</Table.ColumnHeader>
              <Table.ColumnHeader >负债合计</Table.ColumnHeader>
              <Table.ColumnHeader >所有者权益</Table.ColumnHeader>
              <Table.ColumnHeader >货币资金</Table.ColumnHeader>
              <Table.ColumnHeader >应收账款</Table.ColumnHeader>
              <Table.ColumnHeader >存货</Table.ColumnHeader>
              <Table.ColumnHeader >固定资产</Table.ColumnHeader>
              <Table.ColumnHeader >短期借款</Table.ColumnHeader>
              <Table.ColumnHeader >应付账款</Table.ColumnHeader>
              <Table.ColumnHeader >长期借款</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.slice(0, 20).map((sheet, index) => (
              <Table.Row key={index}>
                <Table.Cell fontWeight="bold">{sheet.end_date || '-'}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.total_assets)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.total_liabilities)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.total_equity)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.cash_equivalents)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.accounts_receivable)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.inventory)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.fixed_assets)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.short_term_borrowings)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.accounts_payable)}</Table.Cell>
                <Table.Cell >{formatAmount(sheet.long_term_borrowings)}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    );
  };

  // 渲染利润表主要指标表格
  // const renderProfitMainMetrics = (data: StockProfitSheet[]) => {
  //   if (data.length === 0) return null;

  //   return (
  //     <Box overflowX="auto" mb={6}>
  //       <Table.Root  size="sm">
  //         <Table.Header>
  //           <Table.Row>
  //             <Table.ColumnHeader>报告期</Table.ColumnHeader>
  //             <Table.ColumnHeader >营业收入</Table.ColumnHeader>
  //             <Table.ColumnHeader >营业成本</Table.ColumnHeader>
  //             <Table.ColumnHeader >营业利润</Table.ColumnHeader>
  //             <Table.ColumnHeader >利润总额</Table.ColumnHeader>
  //             <Table.ColumnHeader >净利润</Table.ColumnHeader>
  //           </Table.Row>
  //         </Table.Header>
  //         <Table.Body>
  //           {data.slice(0, 20).map((sheet, index) => (
  //             <Table.Row key={index}>
  //               <Table.Cell fontWeight="bold">{sheet.end_date || '-'}</Table.Cell>
  //               <Table.Cell >{formatAmount(sheet.total_revenue)}</Table.Cell>
  //               <Table.Cell >{formatAmount(sheet.operating_cost)}</Table.Cell>
  //               <Table.Cell >{formatAmount(sheet.operating_profit)}</Table.Cell>
  //               <Table.Cell >{formatAmount(sheet.total_profit)}</Table.Cell>
  //               <Table.Cell >{formatAmount(sheet.net_profit)}</Table.Cell>
  //             </Table.Row>
  //           ))}
  //         </Table.Body>
  //       </Table.Root>
  //     </Box>
  //   );
  // };

  // 渲染资产负债表完整数据表格
  const renderBalanceFullTable = (data: StockBalanceSheet[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto">
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>报告期</Table.ColumnHeader>
              <Table.ColumnHeader>公告日期</Table.ColumnHeader>
              {Object.keys(data[0].extra_fields || {}).slice(0, 50).map((field) => (
                <Table.ColumnHeader key={field} >{field}</Table.ColumnHeader>
              ))}
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.slice(0, 10).map((sheet, index) => (
              <Table.Row key={index}>
                <Table.Cell fontWeight="bold">{sheet.end_date || '-'}</Table.Cell>
                <Table.Cell>{sheet.report_date || '-'}</Table.Cell>
                {Object.keys(sheet.extra_fields || {}).slice(0, 50).map((field) => (
                  <Table.Cell key={field} >
                    {formatAmount((sheet.extra_fields || {})[field] as number)}
                  </Table.Cell>
                ))}
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    );
  };

  // const currentBalanceData = activeSubTab === "概览" ? balanceReportData : balanceYearlyData;

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>东方财富财务分析 - 资产负债表</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center">
        <InputGroup width="300px" startAddon="股票代码">
  <Input
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value.toUpperCase())}
            placeholder="输入股票代码，如：SH600519"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
</InputGroup>
        <Button onClick={handleSearch} colorPalette="blue" loading={loading}>
          查询
        </Button>
        <Badge colorPalette="blue" fontSize="0.8em" ml={2}>
          示例：SH600519（贵州茅台）
        </Badge>
      </Flex>

      <Tabs.Root onValueChange={(e) => handleTabChange(e.value)} colorPalette="blue">
        <Tabs.List>
          <Tabs.Trigger value="按报告期">按报告期</Tabs.Trigger>
          <Tabs.Trigger value="按年度">按年度</Tabs.Trigger>
        </Tabs.List>

        <Tabs.ContentGroup>
          {/* 按报告期 */}
          <Tabs.Content value="按年度">
            {loading && balanceReportData.length === 0 ? (
              <Center h="400px">
                <Spinner size="xl" />
              </Center>
            ) : (
              <>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">主要财务指标</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {balanceReportData.length} 条数据（单位：万元）
                  </Text>
                </Flex>
                {renderBalanceMainMetrics(balanceReportData)}

                <Heading size="md" mt={8} mb={4}>完整数据（前 50 个字段）</Heading>
                {renderBalanceFullTable(balanceReportData)}
              </>
            )}
          </Tabs.Content>

          {/* 按年度 */}
          <Tabs.Content value="按报告期">
            {loading && balanceYearlyData.length === 0 ? (
              <Center h="400px">
                <Spinner size="xl" />
              </Center>
            ) : (
              <>
                <Flex justify="space-between" align="center" mb={4}>
                  <Heading size="md">主要财务指标</Heading>
                  <Text fontSize="sm" color="gray.500">
                    共 {balanceYearlyData.length} 条数据（单位：万元）
                  </Text>
                </Flex>
                {renderBalanceMainMetrics(balanceYearlyData)}

                <Heading size="md" mt={8} mb={4}>完整数据（前 50 个字段）</Heading>
                {renderBalanceFullTable(balanceYearlyData)}
              </>
            )}
          </Tabs.Content>
        </Tabs.ContentGroup>
      </Tabs.Root>

      {/* 数据说明 */}
      <Box mt={8} p={4} bg="gray.50" borderRadius="md">
        <Heading size="sm" mb={2}>数据说明</Heading>
        <Text fontSize="sm" color="gray.600">
          1. 数据来源：东方财富网财务分析数据
        </Text>
        <Text fontSize="sm" color="gray.600">
          2. 金额单位：万元
        </Text>
        <Text fontSize="sm" color="gray.600">
          3. 按报告期：包含季报、半年报、年报
        </Text>
        <Text fontSize="sm" color="gray.600">
          4. 按年度：仅包含年度数据
        </Text>
        <Text fontSize="sm" color="gray.600">
          5. 完整数据包含 319 个财务指标字段，此处仅展示前 50 个
        </Text>
      </Box>
    </Box>
  );
};

export default EastMoneyFinancialPage;
