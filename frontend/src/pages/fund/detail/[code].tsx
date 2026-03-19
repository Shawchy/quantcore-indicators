/**
 * 基金详情页
 * 
 * 展示基金的详细信息，包括基本信息、业绩走势、资产配置等
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Typography,
  Space,
  Row,
  Col,
  Statistic,
  Tag,
  Table,
  Tabs,
  Spin,
  Alert,
  Button,
  Descriptions,
  Progress,
} from 'antd';
import {
  ArrowLeftOutlined,
  StarOutlined,
  StarFilled,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons';
import {
  fundApi,
  FundInfo,
  FundRealtimeRateInfo,
  FundPeriodChangeInfo,
  FundAssetsAllocationInfo,
  FundPositionInfo,
} from '@/services/fund';

const { Title, Text } = Typography;

const FundDetail: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [fundInfo, setFundInfo] = useState<FundInfo | null>(null);
  const [realtimeRate, setRealtimeRate] = useState<FundRealtimeRateInfo | null>(null);
  const [periodChange, setPeriodChange] = useState<FundPeriodChangeInfo[]>([]);
  const [assetsAllocation, setAssetsAllocation] = useState<FundAssetsAllocationInfo[]>([]);
  const [position, setPosition] = useState<FundPositionInfo[]>([]);
  const [isFavorite, setIsFavorite] = useState(false);

  // 加载基金数据
  const loadFundData = useCallback(async () => {
    if (!code) return;

    setLoading(true);
    try {
      // 1. 获取基金基本信息
      const infoRes = await fundApi.getFundBaseInfo(code);
      const info = Array.isArray(infoRes.data) ? infoRes.data[0] : infoRes.data;
      setFundInfo(info);

      // 2. 获取实时估算涨跌幅
      try {
        const rateRes = await fundApi.getFundRealtimeRate(code);
        const rate = Array.isArray(rateRes.data) ? rateRes.data[0] : rateRes.data;
        setRealtimeRate(rate);
      } catch (e) {
        console.log('获取实时估算失败');
      }

      // 3. 获取阶段涨跌幅
      try {
        const periodRes = await fundApi.getFundPeriodChange(code);
        setPeriodChange(periodRes.data);
      } catch (e) {
        console.log('获取阶段涨跌幅失败');
      }

      // 4. 获取资产配置
      try {
        const assetsRes = await fundApi.getFundAssetsAllocation(code);
        setAssetsAllocation(assetsRes.data);
      } catch (e) {
        console.log('获取资产配置失败');
      }

      // 5. 获取持仓占比
      try {
        const positionRes = await fundApi.getFundPosition(code);
        setPosition(Array.isArray(positionRes.data) ? positionRes.data : [positionRes.data]);
      } catch (e) {
        console.log('获取持仓占比失败');
      }
    } catch (error: any) {
      console.error('加载基金数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [code]);

  useEffect(() => {
    loadFundData();
  }, [loadFundData]);

  // 处理添加到自选
  const handleAddToWatchlist = () => {
    setIsFavorite(!isFavorite);
    // TODO: 实际添加到自选列表
  };

  // 获取收益率颜色
  const getReturnColor = (value?: number) => {
    if (value === undefined || value === null) return '#999';
    if (value > 0) return '#ff4d4f';
    if (value < 0) return '#52c41a';
    return '#1890ff';
  };

  // 获取收益率文本
  const getReturnText = (value?: number) => {
    if (value === undefined || value === null) return '--';
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  if (loading) {
    return (
      <div style={{ padding: 48, textAlign: 'center' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (!fundInfo) {
    return (
      <div style={{ padding: 48 }}>
        <Alert
          message="基金不存在"
          description="未找到该基金的信息"
          type="error"
          showIcon
        />
      </div>
    );
  }

  // 基本信息表格列
  const periodColumns = [
    {
      title: '时间段',
      dataIndex: 'period',
      key: 'period',
      width: 100,
    },
    {
      title: '收益率',
      dataIndex: 'return_rate',
      key: 'return_rate',
      width: 120,
      render: (value?: number) => (
        <Text strong style={{ color: getReturnColor(value) }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '同类平均',
      dataIndex: 'avg_return',
      key: 'avg_return',
      width: 120,
      render: (value?: number) => (
        <Text style={{ color: getReturnColor(value) }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '同类排行',
      key: 'rank',
      width: 150,
      render: (_: any, record: FundPeriodChangeInfo) => {
        if (!record.rank || !record.total_count) return '--';
        const rankRate = record.rank_rate || 0;
        let color = rankRate < 0.1 ? 'gold' : rankRate < 0.3 ? 'lime' : rankRate < 0.5 ? 'orange' : 'default';
        return (
          <Tag color={color}>
            {record.rank}/{record.total_count} (前{(rankRate * 100).toFixed(1)}%)
          </Tag>
        );
      },
    },
  ];

  // 资产配置表格列
  const assetsColumns = [
    {
      title: '报告期',
      dataIndex: 'report_date',
      key: 'report_date',
      width: 120,
    },
    {
      title: '股票比重',
      dataIndex: 'stock_ratio',
      key: 'stock_ratio',
      width: 150,
      render: (value?: number) => (
        <Space>
          <Progress
            percent={value || 0}
            size="small"
            strokeColor={getReturnColor(value)}
            format={(val?: number) => `${val?.toFixed(2)}%`}
          />
        </Space>
      ),
    },
    {
      title: '债券比重',
      dataIndex: 'bond_ratio',
      key: 'bond_ratio',
      width: 150,
      render: (value?: number) => (
        <Progress
          percent={value || 0}
          size="small"
          strokeColor="#1890ff"
          format={(val?: number) => `${val?.toFixed(2)}%`}
        />
      ),
    },
    {
      title: '现金比重',
      dataIndex: 'cash_ratio',
      key: 'cash_ratio',
      width: 150,
      render: (value?: number) => (
        <Progress
          percent={value || 0}
          size="small"
          strokeColor="#52c41a"
          format={(val?: number) => `${val?.toFixed(2)}%`}
        />
      ),
    },
    {
      title: '总规模 (亿)',
      dataIndex: 'total_scale',
      key: 'total_scale',
      width: 120,
      render: (value?: number) => `${value?.toFixed(2) || '--'}`,
    },
  ];

  // 持仓占比表格列
  const positionColumns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 120,
    },
    {
      title: '持仓占比',
      dataIndex: 'position_ratio',
      key: 'position_ratio',
      width: 120,
      render: (value?: number) => `${value?.toFixed(2) || '--'}%`,
    },
    {
      title: '较上期变化',
      dataIndex: 'change',
      key: 'change',
      width: 120,
      render: (value?: number) => (
        <Text style={{ color: getReturnColor(value) }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '报告期',
      dataIndex: 'report_date',
      key: 'report_date',
      width: 120,
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 返回按钮 */}
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/fund/ranking')}>
          返回排行榜
        </Button>

        {/* 基本信息卡片 */}
        <Card>
          <Row gutter={16}>
            <Col flex={1}>
              <Space direction="vertical" size="small">
                <Space>
                  <Title level={3} style={{ margin: 0 }}>
                    {fundInfo.name}
                  </Title>
                  <Tag color="blue">{fundInfo.code}</Tag>
                  <Tag>{fundInfo.type === 'stock' ? '股票型' : fundInfo.type === 'bond' ? '债券型' : '混合型'}</Tag>
                </Space>
                <Text type="secondary">{fundInfo.fund_company}</Text>
              </Space>
            </Col>
            <Col flex={1}>
              <Row gutter={16} justify="end">
                <Col>
                  <Statistic
                    title="最新净值"
                    value={fundInfo.net_asset_value}
                    precision={4}
                    valueStyle={{ fontSize: 24 }}
                  />
                </Col>
                <Col>
                  <Statistic
                    title="日涨跌"
                    value={fundInfo.change_pct}
                    precision={2}
                    suffix="%"
                    valueStyle={{
                      fontSize: 24,
                      color: getReturnColor(fundInfo.change_pct),
                    }}
                    prefix={fundInfo.change_pct && fundInfo.change_pct > 0 ? <RiseOutlined /> : fundInfo.change_pct && fundInfo.change_pct < 0 ? <FallOutlined /> : undefined}
                  />
                </Col>
                <Col>
                  <Button
                    type={isFavorite ? 'primary' : 'default'}
                    icon={isFavorite ? <StarFilled /> : <StarOutlined />}
                    onClick={handleAddToWatchlist}
                  >
                    {isFavorite ? '已收藏' : '收藏'}
                  </Button>
                </Col>
              </Row>
            </Col>
          </Row>

          {/* 实时估算 */}
          {realtimeRate && (
            <Alert
              message={`估算时间：${realtimeRate.estimate_time}`}
              description={`估算涨跌幅：${getReturnText(realtimeRate.estimate_change_pct)}`}
              type={realtimeRate.estimate_change_pct && realtimeRate.estimate_change_pct > 0 ? 'success' : 'warning'}
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </Card>

        {/* Tab 切换 */}
        <Tabs
          items={[
            {
              key: 'period',
              label: '阶段涨跌幅',
              children: (
                <Card>
                  <Table
                    columns={periodColumns}
                    dataSource={periodChange}
                    pagination={false}
                    rowKey="period"
                  />
                </Card>
              ),
            },
            {
              key: 'assets',
              label: '资产配置',
              children: (
                <Card>
                  <Table
                    columns={assetsColumns}
                    dataSource={assetsAllocation}
                    pagination={false}
                    rowKey="report_date"
                  />
                </Card>
              ),
            },
            {
              key: 'position',
              label: '持仓详情',
              children: (
                <Card>
                  <Table
                    columns={positionColumns}
                    dataSource={position}
                    pagination={false}
                    rowKey="stock_code"
                  />
                </Card>
              ),
            },
          ]}
        />
      </Space>
    </div>
  );
};

export default FundDetail;
