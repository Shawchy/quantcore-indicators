/**
 * 基金首页
 * 
 * 基金模块的入口页面，展示基金市场概览
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Typography,
  Row,
  Col,
  Statistic,
  Space,
  Button,
} from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  DollarOutlined,
  LineChartOutlined,
  StarOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

const FundHome: React.FC = () => {
  const navigate = useNavigate();

  // 模拟市场概览数据
  const marketOverview = {
    totalFunds: 24708,
    riseCount: 12345,
    fallCount: 11234,
    avgReturn: 2.34,
    topSector: '白酒',
    topSectorReturn: 5.67,
  };

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 标题 */}
        <div>
          <Title level={2} style={{ margin: 0 }}>
            基金中心
          </Title>
          <Text type="secondary">
            全面的基金数据，专业的分析工具，助您做出明智的投资决策
          </Text>
        </div>

        {/* 市场概览 */}
        <Card title="市场概览">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="基金总数"
                value={marketOverview.totalFunds}
                suffix="只"
                valueStyle={{ fontSize: 24 }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="上涨基金"
                value={marketOverview.riseCount}
                suffix="只"
                valueStyle={{ color: '#ff4d4f', fontSize: 24 }}
                prefix={<RiseOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="下跌基金"
                value={marketOverview.fallCount}
                suffix="只"
                valueStyle={{ color: '#52c41a', fontSize: 24 }}
                prefix={<FallOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="平均收益"
                value={marketOverview.avgReturn}
                precision={2}
                suffix="%"
                valueStyle={{ color: '#ff4d4f', fontSize: 24 }}
              />
            </Col>
          </Row>
        </Card>

        {/* 功能入口 */}
        <Row gutter={16}>
          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              onClick={() => navigate('/fund/ranking')}
              style={{ textAlign: 'center', cursor: 'pointer' }}
            >
              <Space direction="vertical" size="small">
                <TrophyOutlined style={{ fontSize: 48, color: '#faad14' }} />
                <Title level={5} style={{ margin: 0 }}>基金排行榜</Title>
                <Text type="secondary">
                  按收益、规模、同类排名查看基金排行
                </Text>
                <Button type="primary">进入</Button>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              onClick={() => navigate('/fund/hot-sectors')}
              style={{ textAlign: 'center', cursor: 'pointer' }}
            >
              <Space direction="vertical" size="small">
                <DollarOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                <Title level={5} style={{ margin: 0 }}>热门板块</Title>
                <Text type="secondary">
                  追踪市场热门板块，把握投资热点
                </Text>
                <Button type="primary">进入</Button>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              onClick={() => navigate('/fund/recommended')}
              style={{ textAlign: 'center', cursor: 'pointer' }}
            >
              <Space direction="vertical" size="small">
                <StarOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                <Title level={5} style={{ margin: 0 }}>基金优选</Title>
                <Text type="secondary">
                  专业投研团队精选优质基金
                </Text>
                <Button type="primary">进入</Button>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              onClick={() => navigate('/watchlist')}
              style={{ textAlign: 'center', cursor: 'pointer' }}
            >
              <Space direction="vertical" size="small">
                <LineChartOutlined style={{ fontSize: 48, color: '#722ed1' }} />
                <Title level={5} style={{ margin: 0 }}>我的自选</Title>
                <Text type="secondary">
                  管理您的自选基金，实时跟踪行情
                </Text>
                <Button type="primary">进入</Button>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* 投资小贴士 */}
        <Card title="投资小贴士">
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div>
              <Text strong>💡 分散投资：</Text>
              <Text>不要把所有资金投入到单只基金，分散投资可以降低风险。</Text>
            </div>
            <div>
              <Text strong>📈 长期持有：</Text>
              <Text>基金投资适合长期持有，短期波动不必过于担心。</Text>
            </div>
            <div>
              <Text strong>🎯 定投策略：</Text>
              <Text>定期定额投资可以平摊成本，降低择时风险。</Text>
            </div>
            <div>
              <Text strong>📊 关注业绩：</Text>
              <Text>关注基金的长期业绩，而不仅仅是短期表现。</Text>
            </div>
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default FundHome;
