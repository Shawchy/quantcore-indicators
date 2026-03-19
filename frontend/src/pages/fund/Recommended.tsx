/**
 * 基金优选页面
 * 
 * 展示精选优质基金推荐
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Tabs,
  Row,
  Col,
  Tag,
  Space,
  Button,
  Rate,
  Tooltip,
} from 'antd';
import {
  TrophyOutlined,
  StarOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import FundCard from '@/components/fund/FundCard';
import { FundInfo } from '@/services/fund';

const { Title, Text } = Typography;

interface RecommendedFund extends FundInfo {
  reason: string;
  rating: number;
  tags: string[];
}

const FundRecommended: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [starFunds, setStarFunds] = useState<RecommendedFund[]>([]);
  const [steadyFunds, setSteadyFunds] = useState<RecommendedFund[]>([]);
  const [highElasticFunds, setHighElasticFunds] = useState<RecommendedFund[]>([]);
  const [valueFunds, setValueFunds] = useState<RecommendedFund[]>([]);

  // 模拟数据（实际应从 API 获取）
  useEffect(() => {
    // 明星基金
    setStarFunds([
      {
        code: '161725',
        name: '招商中证白酒指数 (LOF)A',
        type: 'index',
        net_asset_value: 2.8856,
        change_pct: 0.64,
        fund_scale: 310.21,
        fund_company: '招商基金',
        reason: '近五年收益 519.44%，同类排名第 1，白酒行业龙头基金',
        rating: 5,
        tags: ['行业龙头', '长期优秀', '高收益'],
      },
      {
        code: '005827',
        name: '易方达蓝筹精选混合',
        type: 'mix',
        net_asset_value: 2.3908,
        change_pct: -0.23,
        fund_scale: 310.21,
        fund_company: '易方达基金',
        reason: '张坤管理，专注蓝筹股投资，长期业绩稳定',
        rating: 5,
        tags: ['明星经理', '蓝筹股', '稳健增长'],
      },
    ]);

    // 稳健增长
    setSteadyFunds([
      {
        code: '000001',
        name: '华夏成长混合',
        type: 'mix',
        net_asset_value: 1.5678,
        change_pct: 0.12,
        fund_scale: 156.78,
        fund_company: '华夏基金',
        reason: '成立 20 余年，穿越多轮牛熊，年化收益 15%+',
        rating: 4,
        tags: ['老牌基金', '稳健', '长期投资'],
      },
    ]);

    // 高弹性
    setHighElasticFunds([
      {
        code: '005918',
        name: '天弘中证 500 指数增强 A',
        type: 'index',
        net_asset_value: 1.8765,
        change_pct: 1.23,
        fund_scale: 98.45,
        fund_company: '天弘基金',
        reason: '中证 500 指数增强，弹性大，适合风险偏好较高的投资者',
        rating: 4,
        tags: ['指数增强', '高弹性', '中小盘'],
      },
    ]);

    // 价值投资
    setValueFunds([
      {
        code: '000002',
        name: '嘉实价值优势混合',
        type: 'mix',
        net_asset_value: 1.3456,
        change_pct: -0.45,
        fund_scale: 234.56,
        fund_company: '嘉实基金',
        reason: '专注低估值价值股，安全边际高，适合长期配置',
        rating: 4,
        tags: ['价值投资', '低估值', '安全边际'],
      },
    ]);
  }, []);

  // 渲染基金卡片
  const renderFundCards = (funds: RecommendedFund[]) => (
    <Row gutter={[16, 16]}>
      {funds.map((fund) => (
        <Col xs={24} sm={12} lg={8} xl={6} key={fund.code}>
          <FundCard
            fund={fund}
            showRank={false}
            showActions={true}
            compact={false}
          />
          <Card
            size="small"
            style={{ marginTop: 8, borderTop: '2px solid #1890ff' }}
          >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div>
                <Rate disabled value={fund.rating} />
              </div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {fund.reason}
              </Text>
              <Space wrap>
                {fund.tags.map((tag, idx) => (
                  <Tag key={idx} color="blue">
                    {tag}
                  </Tag>
                ))}
              </Space>
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 标题 */}
        <div>
          <Title level={2} style={{ margin: 0 }}>
            基金优选
          </Title>
          <Text type="secondary">
            专业投研团队精选优质基金，助您轻松投资
          </Text>
        </div>

        {/* 分类说明卡片 */}
        <Row gutter={16}>
          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Space direction="vertical" size="small">
                <Space>
                  <TrophyOutlined style={{ fontSize: 24, color: '#faad14' }} />
                  <Title level={5} style={{ margin: 0 }}>明星基金</Title>
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  长期业绩优秀，市场公认的优质基金
                </Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Space direction="vertical" size="small">
                <Space>
                  <SafetyOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                  <Title level={5} style={{ margin: 0 }}>稳健增长</Title>
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  波动小，稳定增长，适合风险偏好较低的投资者
                </Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Space direction="vertical" size="small">
                <Space>
                  <ThunderboltOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                  <Title level={5} style={{ margin: 0 }}>高弹性</Title>
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  高收益、高波动，适合风险偏好较高的投资者
                </Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Space direction="vertical" size="small">
                <Space>
                  <StarOutlined style={{ fontSize: 24, color: '#722ed1' }} />
                  <Title level={5} style={{ margin: 0 }}>价值投资</Title>
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  专注低估值价值股，安全边际高
                </Text>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Tab 切换 */}
        <Tabs
          items={[
            {
              key: 'star',
              label: (
                <Space>
                  <TrophyOutlined />
                  <span>明星基金</span>
                </Space>
              ),
              children: renderFundCards(starFunds),
            },
            {
              key: 'steady',
              label: (
                <Space>
                  <SafetyOutlined />
                  <span>稳健增长</span>
                </Space>
              ),
              children: renderFundCards(steadyFunds),
            },
            {
              key: 'highElastic',
              label: (
                <Space>
                  <ThunderboltOutlined />
                  <span>高弹性</span>
                </Space>
              ),
              children: renderFundCards(highElasticFunds),
            },
            {
              key: 'value',
              label: (
                <Space>
                  <StarOutlined />
                  <span>价值投资</span>
                </Space>
              ),
              children: renderFundCards(valueFunds),
            },
          ]}
        />
      </Space>
    </div>
  );
};

export default FundRecommended;
