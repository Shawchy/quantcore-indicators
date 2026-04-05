/**
 * 基金排行榜页面
 * 
 * 展示按不同维度排序的基金排行榜
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardBody,
  Heading,
  Text,
  Tabs,
  TabList,
  Tab,
  Select,
  HStack,
  VStack,
  Badge,
  useToast,
} from '@chakra-ui/react';
import { fundApi, FundInfo, FundPeriodChangeInfo } from '@/services/fund';
import FundList from '@/components/fund/FundList';

type RankType = 'return' | 'scale' | 'rank';
type PeriodType = '1w' | '1m' | '3m' | '6m' | '1y' | '3y' | '5y';

const FundRanking: React.FC = () => {
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [fundData, setFundData] = useState<FundInfo[]>([]);
  const [performanceData, setPerformanceData] = useState<Record<string, FundPeriodChangeInfo[]>>({});
  const [rankType, setRankType] = useState<RankType>('return');
  const [period, setPeriod] = useState<PeriodType>('1y');
  const [fundType, setFundType] = useState<string>('all');

  // 加载基金数据
  const loadFundData = useCallback(async () => {
    setLoading(true);
    try {
      // 1. 获取基金代码列表
      const codesRes = await fundApi.getFundCodes();
      const allCodes = codesRes.data;

      // 2. 分批获取基金基本信息（每次 100 只）
      const batchSize = 100;
      const fundInfoList: FundInfo[] = [];
      
      for (let i = 0; i < allCodes.length; i += batchSize) {
        const batch = allCodes.slice(i, i + batchSize)
        const infoRes = await fundApi.getFundBaseInfo(batch[0].code)
        const batchInfo = Array.isArray(infoRes.data) ? infoRes.data : [infoRes.data]
        fundInfoList.push(...batchInfo)
      }

      // 3. 筛选基金类型
      let filtered = fundInfoList;
      if (fundType !== 'all') {
        filtered = fundInfoList.filter(f => f.type === fundType);
      }

      // 4. 批量获取阶段涨跌幅（用于排序）
      const topFunds = filtered.slice(0, 100) // 只获取前 100 只的业绩数据
      // const periodMap: Record<PeriodType, string> = {
      //   '1w': '近一周',
      //   '1m': '近一月',
      //   '3m': '近三月',
      //   '6m': '近六月',
      //   '1y': '近一年',
      //   '3y': '近三年',
      //   '5y': '近五年',
      // }

      const perfDataMap: Record<string, FundPeriodChangeInfo[]> = {};
      for (const fund of topFunds) {
        try {
          const perfRes = await fundApi.getFundPeriodChange(fund.code);
          perfDataMap[fund.code] = perfRes.data;
        } catch (e) {
          // 忽略单个基金的失败
        }
      }

      setFundData(filtered);
      setPerformanceData(perfDataMap);

      toast({
        title: '加载成功',
        description: `共 ${filtered.length} 只基金`,
        status: 'success',
        duration: 3000,
      });
    } catch (error: any) {
      console.error('加载基金数据失败:', error);
      toast({
        title: '加载失败',
        description: '加载基金数据失败',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  }, [fundType, toast]);

  useEffect(() => {
    loadFundData();
  }, [loadFundData]);

  // 获取排序后的数据
  const getSortedData = () => {
    let sorted = [...fundData];

    if (rankType === 'return') {
      // 按收益率排序
      const periodName = {
        '1w': '近一周',
        '1m': '近一月',
        '3m': '近三月',
        '6m': '近六月',
        '1y': '近一年',
        '3y': '近三年',
        '5y': '近五年',
      }[period];

      sorted.sort((a, b) => {
        const aPerf = performanceData[a.code]?.find(p => p.period === periodName);
        const bPerf = performanceData[b.code]?.find(p => p.period === periodName);
        return (bPerf?.return_rate || 0) - (aPerf?.return_rate || 0);
      });

      // 添加排名
      sorted = sorted.slice(0, 100).map((fund, index) => ({
        ...fund,
        rank: index + 1,
      }));
    } else if (rankType === 'scale') {
      // 按规模排序
      sorted.sort((a, b) => (b.fund_scale || 0) - (a.fund_scale || 0));
      sorted = sorted.slice(0, 100).map((fund, index) => ({
        ...fund,
        rank: index + 1,
      }));
    } else if (rankType === 'rank') {
      // 按同类排名排序
      const periodName = {
        '1w': '近一周',
        '1m': '近一月',
        '3m': '近三月',
        '6m': '近六月',
        '1y': '近一年',
        '3y': '近三年',
        '5y': '近五年',
      }[period];

      sorted.sort((a, b) => {
        const aPerf = performanceData[a.code]?.find(p => p.period === periodName);
        const bPerf = performanceData[b.code]?.find(p => p.period === periodName);
        return (aPerf?.rank || 9999) - (bPerf?.rank || 9999);
      });

      sorted = sorted.slice(0, 100).map((fund, index) => ({
        ...fund,
        rank: index + 1,
      }));
    }

    return sorted;
  };

  // 处理添加到自选
  const handleAddToWatchlist = (code: string) => {
    toast({
      title: '添加成功',
      description: `已将 ${code} 添加到自选`,
      status: 'success',
      duration: 2000,
    });
  };

  // 处理查看详情
  const handleViewDetail = (code: string) => {
    window.location.href = `/fund/detail/${code}`;
  };

  return (
    <Box p={6}>
      <VStack spacing={8} align="stretch">
        {/* 标题 */}
        <Box>
          <Heading size="xl" mb={2}>
            基金排行榜
          </Heading>
          <Text color="gray.500">
            按收益、规模、同类排名等维度查看基金排行
          </Text>
        </Box>

        {/* 筛选条件 */}
        <Card>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {/* 排行类型 Tabs */}
              <HStack>
                <Text fontWeight="bold">排行类型:</Text>
                <Tabs
                  variant="enclosed"
                  index={['return', 'scale', 'rank'].indexOf(rankType)}
                  onChange={(index) => setRankType(['return', 'scale', 'rank'][index] as RankType)}
                  size="sm"
                >
                  <TabList>
                    <Tab>收益排行</Tab>
                    <Tab>规模排行</Tab>
                    <Tab>同类排行</Tab>
                  </TabList>
                </Tabs>
              </HStack>

              {/* 时间段 Tabs（仅收益排行和同类排行显示） */}
              {(rankType === 'return' || rankType === 'rank') && (
                <HStack>
                  <Text fontWeight="bold">时间段:</Text>
                  <Tabs
                    variant="enclosed"
                    index={['1w', '1m', '3m', '6m', '1y', '3y', '5y'].indexOf(period)}
                    onChange={(index) => setPeriod(['1w', '1m', '3m', '6m', '1y', '3y', '5y'][index] as PeriodType)}
                    size="sm"
                  >
                    <TabList>
                      <Tab>近 1 周</Tab>
                      <Tab>近 1 月</Tab>
                      <Tab>近 3 月</Tab>
                      <Tab>近 6 月</Tab>
                      <Tab>近 1 年</Tab>
                      <Tab>近 3 年</Tab>
                      <Tab>近 5 年</Tab>
                    </TabList>
                  </Tabs>
                </HStack>
              )}

              {/* 基金类型选择 */}
              <HStack wrap="wrap">
                <Text fontWeight="bold">基金类型:</Text>
                <Select
                  value={fundType}
                  onChange={(e) => setFundType(e.target.value)}
                  width="150px"
                >
                  <option value="all">全部</option>
                  <option value="stock">股票型</option>
                  <option value="mix">混合型</option>
                  <option value="bond">债券型</option>
                  <option value="index">指数型</option>
                  <option value="money">货币型</option>
                </Select>
                <Badge colorScheme="blue" fontSize="sm">
                  共 {fundData.length} 只基金
                </Badge>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* 基金列表 */}
        <Card>
          <CardBody>
            <FundList
              data={getSortedData()}
              loading={loading}
              performanceData={performanceData}
              onAddToWatchlist={handleAddToWatchlist}
              onViewDetail={handleViewDetail}
            />
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
};

export default FundRanking;
