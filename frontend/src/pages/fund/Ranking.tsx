/**
 * 基金排行榜页面
 * 
 * 展示按不同维度排序的基金排行榜
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Typography,
  Tabs,
  Select,
  Space,
  message,
} from 'antd';
import { fundApi, FundInfo, FundPeriodChangeInfo } from '@/services/fund';
import FundList from '@/components/fund/FundList';

const { Title } = Typography;
const { Option } = Select;

type RankType = 'return' | 'scale' | 'rank';
type PeriodType = '1w' | '1m' | '3m' | '6m' | '1y' | '3y' | '5y';

const FundRanking: React.FC = () => {
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
        const batch = allCodes.slice(i, i + batchSize);
        const infoRes = await fundApi.getFundBaseInfo(batch);
        const batchInfo = Array.isArray(infoRes.data) ? infoRes.data : [infoRes.data];
        fundInfoList.push(...batchInfo);
      }

      // 3. 筛选基金类型
      let filtered = fundInfoList;
      if (fundType !== 'all') {
        filtered = fundInfoList.filter(f => f.type === fundType);
      }

      // 4. 批量获取阶段涨跌幅（用于排序）
      const topFunds = filtered.slice(0, 100); // 只获取前 100 只的业绩数据
      const periodMap: Record<PeriodType, string> = {
        '1w': '近一周',
        '1m': '近一月',
        '3m': '近三月',
        '6m': '近六月',
        '1y': '近一年',
        '3y': '近三年',
        '5y': '近五年',
      };

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

      message.success(`加载成功，共 ${filtered.length} 只基金`);
    } catch (error: any) {
      console.error('加载基金数据失败:', error);
      message.error('加载基金数据失败');
    } finally {
      setLoading(false);
    }
  }, [fundType]);

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
    message.success(`已将 ${code} 添加到自选`);
    // TODO: 实际添加到自选列表
  };

  // 处理查看详情
  const handleViewDetail = (code: string) => {
    window.location.href = `/fund/detail/${code}`;
  };

  // Tab 配置
  const rankTypeTabs = [
    { key: 'return', label: '收益排行' },
    { key: 'scale', label: '规模排行' },
    { key: 'rank', label: '同类排行' },
  ];

  const periodTabs = [
    { key: '1w', label: '近 1 周' },
    { key: '1m', label: '近 1 月' },
    { key: '3m', label: '近 3 月' },
    { key: '6m', label: '近 6 月' },
    { key: '1y', label: '近 1 年' },
    { key: '3y', label: '近 3 年' },
    { key: '5y', label: '近 5 年' },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 标题 */}
        <div>
          <Title level={2} style={{ margin: 0 }}>
            基金排行榜
          </Title>
          <Text type="secondary">
            按收益、规模、同类排名等维度查看基金排行
          </Text>
        </div>

        {/* 筛选条件 */}
        <Card>
          <Space wrap>
            <span>排行类型:</span>
            <Tabs
              activeKey={rankType}
              onChange={(key) => setRankType(key as RankType)}
              items={rankTypeTabs}
              size="small"
              style={{ margin: 0 }}
            />
          </Space>

          {rankType === 'return' || rankType === 'rank' ? (
            <Space wrap style={{ marginTop: 16 }}>
              <span>时间段:</span>
              <Tabs
                activeKey={period}
                onChange={(key) => setPeriod(key as PeriodType)}
                items={periodTabs}
                size="small"
                style={{ margin: 0 }}
              />
            </Space>
          ) : null}

          <Space wrap style={{ marginTop: 16 }}>
            <span>基金类型:</span>
            <Select
              value={fundType}
              onChange={setFundType}
              style={{ width: 150 }}
            >
              <Option value="all">全部</Option>
              <Option value="stock">股票型</Option>
              <Option value="mix">混合型</Option>
              <Option value="bond">债券型</Option>
              <Option value="index">指数型</Option>
              <Option value="money">货币型</Option>
            </Select>
            <span>共 {fundData.length} 只基金</span>
          </Space>
        </Card>

        {/* 基金列表 */}
        <Card>
          <FundList
            data={getSortedData()}
            loading={loading}
            performanceData={performanceData}
            onAddToWatchlist={handleAddToWatchlist}
            onViewDetail={handleViewDetail}
          />
        </Card>
      </Space>
    </div>
  );
};

export default FundRanking;
