/**
 * 东方财富财务分析页面
 * 包含：资产负债表、利润表
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
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
  Badge,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockBalanceSheet,
  type StockProfitSheet,
} from '@/services/akshare/index';

const EastMoneyFinancialPage: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState(0) // 0=报告期，1=年度
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

  const toast = useToast()

  // 获取资产负债表 - 按报告期
  const fetchBalanceReport = async (code: string) => {
    if (!code) {
      toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getBalanceSheetReport(code);
      setBalanceReportData(result.data || []);
      toast({ title: `获取成功，共${result.data?.length || 0}条报告期数据`, status: 'success', duration: 2000, isClosable: true });
    } catch (error) {
      console.error('获取资产负债表（报告期）失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取资产负债表 - 按年度
  const fetchBalanceYearly = async (code: string) => {
    if (!code) {
      toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getBalanceSheetYearly(code);
      setBalanceYearlyData(result.data || []);
      toast({ title: `获取成功，共${result.data?.length || 0}条年度数据`, status: 'success', duration: 2000, isClosable: true });
    } catch (error) {
      console.error('获取资产负债表（年度）失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取利润表 - 按报告期
  const fetchProfitReport = async (code: string) => {
    if (!code) {
      toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getProfitSheetReport(code);
      setProfitReportData(result.data || []);
      toast({ title: `获取成功，共${result.data?.length || 0}条报告期数据`, status: 'success', duration: 2000, isClosable: true });
    } catch (error) {
      console.error('获取利润表（报告期）失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取利润表 - 按年度
  const fetchProfitYearly = async (code: string) => {
    if (!code) {
      toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
      return;
    }
    setLoading(true);
    try {
      const result = await eastMoneyApi.getProfitSheetYearly(code);
      setProfitYearlyData(result.data || []);
      toast({ title: `获取成功，共${result.data?.length || 0}条年度数据`, status: 'success', duration: 2000, isClosable: true });
    } catch (error) {
      console.error('获取利润表（年度）失败:', error);
      toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  // 获取利润表 - 按单季度
  // const fetchProfitQuarterly = async (code: string) => {
  //   if (!code) {
  //     toast({ title: '请输入股票代码', status: 'warning', duration: 2000, isClosable: true });
  //     return;
  //   }
  //   setLoading(true);
  //   try {
  //     const result = await eastMoneyApi.getProfitSheetQuarterly(code);
  //     setProfitQuarterlyData(result.data || []);
  //     toast({ title: `获取成功，共${result.data?.length || 0}条单季度数据`, status: 'success', duration: 2000, isClosable: true });
  //   } catch (error) {
  //     console.error('获取利润表（单季度）失败:', error);
  //     toast({ title: '获取数据失败', status: 'error', duration: 2000, isClosable: true });
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
    if (activeSubTab === 0) {
      fetchBalanceReport(stockCode);
      fetchProfitReport(stockCode);
    } else {
      fetchBalanceYearly(stockCode);
      fetchProfitYearly(stockCode);
    }
  };

  // Tab 切换时自动查询
  const handleTabChange = (index: number) => {
    setActiveSubTab(index);
    if (stockCode) {
      if (index === 0) {
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
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>报告期</Th>
              <Th isNumeric>资产总计</Th>
              <Th isNumeric>负债合计</Th>
              <Th isNumeric>所有者权益</Th>
              <Th isNumeric>货币资金</Th>
              <Th isNumeric>应收账款</Th>
              <Th isNumeric>存货</Th>
              <Th isNumeric>固定资产</Th>
              <Th isNumeric>短期借款</Th>
              <Th isNumeric>应付账款</Th>
              <Th isNumeric>长期借款</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.slice(0, 20).map((sheet, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{sheet.end_date || '-'}</Td>
                <Td isNumeric>{formatAmount(sheet.total_assets)}</Td>
                <Td isNumeric>{formatAmount(sheet.total_liabilities)}</Td>
                <Td isNumeric>{formatAmount(sheet.total_equity)}</Td>
                <Td isNumeric>{formatAmount(sheet.cash_equivalents)}</Td>
                <Td isNumeric>{formatAmount(sheet.accounts_receivable)}</Td>
                <Td isNumeric>{formatAmount(sheet.inventory)}</Td>
                <Td isNumeric>{formatAmount(sheet.fixed_assets)}</Td>
                <Td isNumeric>{formatAmount(sheet.short_term_borrowings)}</Td>
                <Td isNumeric>{formatAmount(sheet.accounts_payable)}</Td>
                <Td isNumeric>{formatAmount(sheet.long_term_borrowings)}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  // 渲染利润表主要指标表格
  // const renderProfitMainMetrics = (data: StockProfitSheet[]) => {
  //   if (data.length === 0) return null;

  //   return (
  //     <Box overflowX="auto" mb={6}>
  //       <Table variant="simple" size="sm">
  //         <Thead>
  //           <Tr>
  //             <Th>报告期</Th>
  //             <Th isNumeric>营业收入</Th>
  //             <Th isNumeric>营业成本</Th>
  //             <Th isNumeric>营业利润</Th>
  //             <Th isNumeric>利润总额</Th>
  //             <Th isNumeric>净利润</Th>
  //           </Tr>
  //         </Thead>
  //         <Tbody>
  //           {data.slice(0, 20).map((sheet, index) => (
  //             <Tr key={index}>
  //               <Td fontWeight="bold">{sheet.end_date || '-'}</Td>
  //               <Td isNumeric>{formatAmount(sheet.total_revenue)}</Td>
  //               <Td isNumeric>{formatAmount(sheet.operating_cost)}</Td>
  //               <Td isNumeric>{formatAmount(sheet.operating_profit)}</Td>
  //               <Td isNumeric>{formatAmount(sheet.total_profit)}</Td>
  //               <Td isNumeric>{formatAmount(sheet.net_profit)}</Td>
  //             </Tr>
  //           ))}
  //         </Tbody>
  //       </Table>
  //     </Box>
  //   );
  // };

  // 渲染资产负债表完整数据表格
  const renderBalanceFullTable = (data: StockBalanceSheet[]) => {
    if (data.length === 0) return null;

    return (
      <Box overflowX="auto">
        <Table variant="simple" size="xs">
          <Thead>
            <Tr>
              <Th>报告期</Th>
              <Th>公告日期</Th>
              {Object.keys(data[0].extra_fields || {}).slice(0, 50).map((field) => (
                <Th key={field} isNumeric>{field}</Th>
              ))}
            </Tr>
          </Thead>
          <Tbody>
            {data.slice(0, 10).map((sheet, index) => (
              <Tr key={index}>
                <Td fontWeight="bold">{sheet.end_date || '-'}</Td>
                <Td>{sheet.report_date || '-'}</Td>
                {Object.keys(sheet.extra_fields || {}).slice(0, 50).map((field) => (
                  <Td key={field} isNumeric>
                    {formatAmount((sheet.extra_fields || {})[field] as number)}
                  </Td>
                ))}
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  // const currentBalanceData = activeSubTab === 0 ? balanceReportData : balanceYearlyData;

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>东方财富财务分析 - 资产负债表</Heading>

      {/* 搜索栏 */}
      <Flex gap={4} mb={6} align="center">
        <InputGroup width="300px">
          <InputLeftAddon>股票代码</InputLeftAddon>
          <Input
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value.toUpperCase())}
            placeholder="输入股票代码，如：SH600519"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
        </InputGroup>
        <Button onClick={handleSearch} colorScheme="blue" isLoading={loading}>
          查询
        </Button>
        <Badge colorScheme="blue" fontSize="0.8em" ml={2}>
          示例：SH600519（贵州茅台）
        </Badge>
      </Flex>

      <Tabs onChange={handleTabChange} colorScheme="blue">
        <TabList>
          <Tab>按报告期</Tab>
          <Tab>按年度</Tab>
        </TabList>

        <TabPanels>
          {/* 按报告期 */}
          <TabPanel>
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
          </TabPanel>

          {/* 按年度 */}
          <TabPanel>
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
          </TabPanel>
        </TabPanels>
      </Tabs>

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
