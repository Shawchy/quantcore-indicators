/**
 * 热门板块页面
 * 
 * 展示涨幅领先、资金流入、估值低位等热门板块
 */
import React, { useState } from 'react';
import {
  Alert,
  Card,
  Typography,
  Tabs,
  Table,
  Tag,
  Space,
} from 'antd';
import { RiseOutlined, DollarOutlined, LineChartOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface SectorInfo {
  key: string;
  name: string;
  change_pct: number;
  fund_count: number;
  avg_scale: number;
  top_funds: Array<{ code: string; name: string; return_rate: number }>;
}

const HotSectors: React.FC = () => {
  const [loading, setLoading] = useState(false);

  // 模拟数据（实际应从 API 获取）
  const riseLeadingSectors: SectorInfo[] = [
    {
      key: '1',
      name: '白酒',
      change_pct: 5.67,
      fund_count: 45,
      avg_scale: 125.5,
      top_funds: [
        { code: '161725', name: '招商中证白酒', return_rate: 6.45 },
        { code: '005827', name: '易方达蓝筹精选', return_rate: 5.89 },
      ],
    },
    {
      key: '2',
      name: '新能源',
      change_pct: 4.32,
      fund_count: 78,
      avg_scale: 98.3,
      top_funds: [
        { code: '005918', name: '天弘中证 500', return_rate: 5.12 },
      ],
    },
    {
      key: '3',
      name: '医药',
      change_pct: 3.21,
      fund_count: 92,
      avg_scale: 67.8,
      top_funds: [],
    },
  ];

  const capitalInflowSectors: SectorInfo[] = [
    {
      key: '1',
      name: '科技',
      change_pct: 2.15,
      fund_count: 156,
      avg_scale: 234.5,
      top_funds: [],
    },
    {
      key: '2',
      name: '消费',
      change_pct: 1.87,
      fund_count: 123,
      avg_scale: 189.2,
      top_funds: [],
    },
  ];

  const lowValuationSectors: SectorInfo[] = [
    {
      key: '1',
      name: '银行',
      change_pct: -0.45,
      fund_count: 34,
      avg_scale: 456.7,
      top_funds: [],
    },
    {
      key: '2',
      name: '地产',
      change_pct: -1.23,
      fund_count: 28,
      avg_scale: 234.1,
      top_funds: [],
    },
  ];

  // 获取涨跌幅颜色
  const getReturnColor = (value: number) => {
    if (value > 0) return '#ff4d4f';
    if (value < 0) return '#52c41a';
    return '#1890ff';
  };

  // 获取涨跌幅文本
  const getReturnText = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // 板块表格列
  const sectorColumns = [
    {
      title: '板块名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: '涨跌幅',
      dataIndex: 'change_pct',
      key: 'change_pct',
      width: 120,
      render: (value: number) => (
        <Text strong style={{ color: getReturnColor(value) }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '基金数量',
      dataIndex: 'fund_count',
      key: 'fund_count',
      width: 100,
      render: (count: number) => `${count}只`,
    },
    {
      title: '平均规模 (亿)',
      dataIndex: 'avg_scale',
      key: 'avg_scale',
      width: 120,
      render: (scale: number) => `${scale.toFixed(2)}`,
    },
    {
      title: '代表基金',
      key: 'top_funds',
      render: (_: any, record: SectorInfo) => (
        <Space direction="vertical" size={0}>
          {record.top_funds.slice(0, 2).map((fund, idx) => (
            <div key={idx}>
              <Tag color="blue">{fund.code}</Tag>
              <Text>{fund.name}</Text>
              <Text style={{ color: getReturnColor(fund.return_rate), marginLeft: 8 }}>
                {getReturnText(fund.return_rate)}
              </Text>
            </div>
          ))}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 标题 */}
        <div>
          <Title level={2} style={{ margin: 0 }}>
            热门板块
          </Title>
          <Text type="secondary">
            追踪市场热门板块，把握投资热点
          </Text>
        </div>

        {/* Tab 切换 */}
        <Tabs
          items={[
            {
              key: 'rise',
              label: (
                <Space>
                  <RiseOutlined />
                  <span>涨幅领先</span>
                </Space>
              ),
              children: (
                <Card>
                  <Alert
                    message="涨幅领先板块"
                    description="展示近期涨幅最大的行业板块"
                    type="success"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  <Table
                    columns={sectorColumns}
                    dataSource={riseLeadingSectors}
                    pagination={false}
                    rowKey="key"
                  />
                </Card>
              ),
            },
            {
              key: 'capital',
              label: (
                <Space>
                  <DollarOutlined />
                  <span>资金流入</span>
                </Space>
              ),
              children: (
                <Card>
                  <Alert
                    message="资金流入板块"
                    description="展示主力资金净流入的行业板块"
                    type="default"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  <Table
                    columns={sectorColumns}
                    dataSource={capitalInflowSectors}
                    pagination={false}
                    rowKey="key"
                  />
                </Card>
              ),
            },
            {
              key: 'valuation',
              label: (
                <Space>
                  <LineChartOutlined />
                  <span>估值低位</span>
                </Space>
              ),
              children: (
                <Card>
                  <Alert
                    message="估值低位板块"
                    description="展示估值处于历史低位的行业板块"
                    type="warning"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  <Table
                    columns={sectorColumns}
                    dataSource={lowValuationSectors}
                    pagination={false}
                    rowKey="key"
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

export default HotSectors;
