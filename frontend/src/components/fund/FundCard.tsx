/**
 * 基金卡片组件
 * 
 * 用于展示单个基金的摘要信息，适用于卡片式布局
 */
import React from 'react';
import {
  Card,
  Typography,
  Space,
  Tag,
  Button,
  Statistic,
  Row,
  Col,
  Divider,
  Tooltip,
} from 'antd';
import {
  StarOutlined,
  StarFilled,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons';
import { FundInfo } from '@/services/fund';

const { Text, Title } = Typography;

interface FundCardProps {
  fund: FundInfo;
  showRank?: boolean;
  showActions?: boolean;
  compact?: boolean;
  isFavorite?: boolean;
  onViewDetail?: (code: string) => void;
  onAddToWatchlist?: (code: string) => void;
}

const FundCard: React.FC<FundCardProps> = ({
  fund,
  showRank = false,
  showActions = true,
  compact = false,
  isFavorite = false,
  onViewDetail,
  onAddToWatchlist,
}) => {
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

  // 获取基金类型标签
  const getFundTypeTag = () => {
    const typeMap: Record<string, { color: string; text: string }> = {
      'stock': { color: 'red', text: '股票型' },
      'bond': { color: 'blue', text: '债券型' },
      'money': { color: 'green', text: '货币型' },
      'index': { color: 'orange', text: '指数型' },
      'mix': { color: 'purple', text: '混合型' },
    };
    const config = fund.type ? typeMap[fund.type] : { color: 'default', text: '未知' };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 卡片内容
  const cardContent = (
    <Space direction="vertical" size="small" style={{ width: '100%' }}>
      {/* 基金基本信息 */}
      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Space direction="vertical" size={0}>
          <Title level={5} style={{ margin: 0 }}>
            {showRank && fund.rank && (
              <Tag color="gold" style={{ marginRight: 8 }}>
                TOP {fund.rank}
              </Tag>
            )}
            {fund.name}
          </Title>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {fund.code}
          </Text>
        </Space>
        <Space>
          {getFundTypeTag()}
          {showActions && (
            <Button
              type="text"
              icon={isFavorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                onAddToWatchlist?.(fund.code);
              }}
            />
          )}
        </Space>
      </Space>

      <Divider style={{ margin: '8px 0' }} />

      {/* 净值和涨跌幅 */}
      <Row gutter={16}>
        <Col flex={1}>
          <Statistic
            title="最新净值"
            value={fund.net_asset_value}
            precision={4}
            valueStyle={{ fontSize: compact ? 16 : 18 }}
          />
        </Col>
        <Col flex={1}>
          <Statistic
            title="日涨跌"
            value={fund.change_pct}
            precision={2}
            suffix="%"
            valueStyle={{
              fontSize: compact ? 16 : 18,
              color: getReturnColor(fund.change_pct),
            }}
            prefix={fund.change_pct && fund.change_pct > 0 ? <RiseOutlined /> : fund.change_pct && fund.change_pct < 0 ? <FallOutlined /> : undefined}
          />
        </Col>
      </Row>

      {/* 阶段涨跌幅 - 非紧凑模式显示 */}
      {!compact && fund.performance && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <Row gutter={[8, 8]}>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>近 1 周</Text>
                <div style={{ color: getReturnColor(fund.performance['1w']) }}>
                  {getReturnText(fund.performance['1w'])}
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>近 1 月</Text>
                <div style={{ color: getReturnColor(fund.performance['1m']) }}>
                  {getReturnText(fund.performance['1m'])}
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>近 3 月</Text>
                <div style={{ color: getReturnColor(fund.performance['3m']) }}>
                  {getReturnText(fund.performance['3m'])}
                </div>
              </div>
            </Col>
          </Row>
          <Row gutter={[8, 8]}>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>近 6 月</Text>
                <div style={{ color: getReturnColor(fund.performance['6m']) }}>
                  {getReturnText(fund.performance['6m'])}
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>近 1 年</Text>
                <div style={{ color: getReturnColor(fund.performance['1y']), fontWeight: 'bold' }}>
                  {getReturnText(fund.performance['1y'])}
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>规模</Text>
                <div>{fund.fund_scale ? `${fund.fund_scale.toFixed(2)}亿` : '--'}</div>
              </div>
            </Col>
          </Row>
        </>
      )}

      {/* 基金公司 */}
      {!compact && fund.fund_company && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>基金公司</Text>
            <div>{fund.fund_company}</div>
          </div>
        </>
      )}

      {/* 操作按钮 */}
      {showActions && (
        <Button
          type="primary"
          block
          onClick={() => onViewDetail?.(fund.code)}
        >
          查看详情
        </Button>
      )}
    </Space>
  );

  return (
    <Card
      hoverable
      onClick={() => onViewDetail?.(fund.code)}
      style={{
        height: '100%',
        cursor: 'pointer',
      }}
    >
      {cardContent}
    </Card>
  );
};

export default FundCard;
