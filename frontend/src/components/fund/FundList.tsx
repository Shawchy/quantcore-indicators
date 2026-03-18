/**
 * 基金列表组件
 * 
 * 用于展示基金列表数据，支持排序、筛选、分页等功能
 */
import React, { useState, useMemo } from 'react';
import {
  Table,
  Tag,
  Space,
  Button,
  Input,
  Select,
  Typography,
  Tooltip,
  Rate,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { SearchOutlined, StarOutlined, StarFilled } from '@ant-design/icons';
import { FundInfo, FundPeriodChangeInfo } from '@/services/fund';

const { Text } = Typography;
const { Option } = Select;

interface FundListProps {
  data: FundInfo[];
  loading?: boolean;
  performanceData?: Record<string, FundPeriodChangeInfo[]>; // 基金代码 -> 阶段涨跌幅数据
  onSort?: (field: string, order: string) => void;
  onFilter?: (filters: FundFilter) => void;
  onViewDetail?: (code: string) => void;
  onAddToWatchlist?: (code: string) => void;
  watchlist?: string[]; // 已在自选中的基金代码
}

interface FundFilter {
  fundType?: string;
  fundCompany?: string;
  minReturn?: number;
  maxReturn?: number;
}

interface FundListTableItem extends FundInfo {
  key: string;
  isFavorite?: boolean;
  performance?: {
    '1w'?: number;
    '1m'?: number;
    '3m'?: number;
    '6m'?: number;
    '1y'?: number;
  };
}

const FundList: React.FC<FundListProps> = ({
  data,
  loading = false,
  performanceData = {},
  onSort,
  onFilter,
  onViewDetail,
  onAddToWatchlist,
  watchlist = [],
}) => {
  const [filters, setFilters] = useState<FundFilter>({});
  const [searchText, setSearchText] = useState('');

  // 处理基金类型
  const getFundTypeTag = (type?: string) => {
    const typeMap: Record<string, { color: string; text: string }> = {
      'stock': { color: 'red', text: '股票型' },
      'bond': { color: 'blue', text: '债券型' },
      'money': { color: 'green', text: '货币型' },
      'index': { color: 'orange', text: '指数型' },
      'mix': { color: 'purple', text: '混合型' },
    };
    const config = type ? typeMap[type] || { color: 'default', text: type } : { color: 'default', text: '未知' };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 处理收益率颜色
  const getReturnColor = (value?: number) => {
    if (value === undefined || value === null) return '#999';
    if (value > 0) return '#ff4d4f';
    if (value < 0) return '#52c41a';
    return '#1890ff';
  };

  // 处理收益率显示
  const getReturnText = (value?: number) => {
    if (value === undefined || value === null) return '--';
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // 转换数据为表格格式
  const tableData: FundListTableItem[] = useMemo(() => {
    return data.map((fund) => {
      const perfData = performanceData[fund.code];
      const getPerfValue = (period: string) => {
        const periodMap: Record<string, string> = {
          '1w': '近一周',
          '1m': '近一月',
          '3m': '近三月',
          '6m': '近六月',
          '1y': '近一年',
        };
        const periodName = periodMap[period];
        const item = perfData?.find(p => p.period === periodName);
        return item?.return_rate;
      };

      return {
        ...fund,
        key: fund.code,
        isFavorite: watchlist.includes(fund.code),
        performance: {
          '1w': getPerfValue('1w'),
          '1m': getPerfValue('1m'),
          '3m': getPerfValue('3m'),
          '6m': getPerfValue('6m'),
          '1y': getPerfValue('1y'),
        },
      };
    });
  }, [data, performanceData, watchlist]);

  // 表格列定义
  const columns: ColumnsType<FundListTableItem> = [
    {
      title: '收藏',
      dataIndex: 'isFavorite',
      key: 'favorite',
      width: 60,
      render: (isFavorite: boolean, record) => (
        <Button
          type="text"
          icon={isFavorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
          onClick={(e) => {
            e.stopPropagation();
            onAddToWatchlist?.(record.code);
          }}
        />
      ),
    },
    {
      title: '基金代码',
      dataIndex: 'code',
      key: 'code',
      width: 100,
      sorter: (a, b) => a.code.localeCompare(b.code),
      render: (code: string) => (
        <Text strong>{code}</Text>
      ),
    },
    {
      title: '基金名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (name: string, record) => (
        <Space direction="vertical" size={0}>
          <Text>{name}</Text>
          {getFundTypeTag(record.type)}
        </Space>
      ),
    },
    {
      title: '最新净值',
      dataIndex: 'net_asset_value',
      key: 'net_asset_value',
      width: 100,
      sorter: (a, b) => (a.net_asset_value || 0) - (b.net_asset_value || 0),
      render: (value?: number) => (
        <Text>{value?.toFixed(4) || '--'}</Text>
      ),
    },
    {
      title: '日涨跌',
      dataIndex: 'change_pct',
      key: 'change_pct',
      width: 100,
      sorter: (a, b) => (a.change_pct || 0) - (b.change_pct || 0),
      render: (value?: number) => (
        <Text style={{ color: getReturnColor(value), fontWeight: 'bold' }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '近 1 周',
      dataIndex: ['performance', '1w'],
      key: 'perf_1w',
      width: 90,
      sorter: (a, b) => (a.performance?.['1w'] || 0) - (b.performance?.['1w'] || 0),
      render: (value?: number) => (
        <Text style={{ color: getReturnColor(value) }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '近 1 月',
      dataIndex: ['performance', '1m'],
      key: 'perf_1m',
      width: 90,
      sorter: (a, b) => (a.performance?.['1m'] || 0) - (b.performance?.['1m'] || 0),
      render: (value?: number) => (
        <Text style={{ color: getReturnColor(value) }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '近 3 月',
      dataIndex: ['performance', '3m'],
      key: 'perf_3m',
      width: 90,
      sorter: (a, b) => (a.performance?.['3m'] || 0) - (b.performance?.['3m'] || 0),
      render: (value?: number) => (
        <Text style={{ color: getReturnColor(value) }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '近 6 月',
      dataIndex: ['performance', '6m'],
      key: 'perf_6m',
      width: 90,
      sorter: (a, b) => (a.performance?.['6m'] || 0) - (b.performance?.['6m'] || 0),
      render: (value?: number) => (
        <Text style={{ color: getReturnColor(value) }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '近 1 年',
      dataIndex: ['performance', '1y'],
      key: 'perf_1y',
      width: 90,
      sorter: (a, b) => (a.performance?.['1y'] || 0) - (b.performance?.['1y'] || 0),
      render: (value?: number) => (
        <Text style={{ color: getReturnColor(value), fontWeight: 'bold' }}>
          {getReturnText(value)}
        </Text>
      ),
    },
    {
      title: '基金规模',
      dataIndex: 'fund_scale',
      key: 'fund_scale',
      width: 110,
      sorter: (a, b) => (a.fund_scale || 0) - (b.fund_scale || 0),
      render: (value?: number) => (
        <Text>{value ? `${value.toFixed(2)}亿` : '--'}</Text>
      ),
    },
    {
      title: '基金公司',
      dataIndex: 'fund_company',
      key: 'fund_company',
      width: 150,
      ellipsis: true,
      render: (company?: string) => (
        <Tooltip title={company}>
          <Text>{company || '--'}</Text>
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          onClick={() => onViewDetail?.(record.code)}
        >
          详情
        </Button>
      ),
    },
  ];

  // 筛选栏
  const FilterBar = () => (
    <Space wrap style={{ marginBottom: 16 }}>
      <Input
        placeholder="搜索基金代码或名称"
        prefix={<SearchOutlined />}
        style={{ width: 300 }}
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        onPressEnter={() => {
          // 可以在这里添加搜索逻辑
        }}
      />
      <Select
        placeholder="基金类型"
        style={{ width: 120 }}
        allowClear
        onChange={(value) => setFilters({ ...filters, fundType: value })}
      >
        <Option value="stock">股票型</Option>
        <Option value="mix">混合型</Option>
        <Option value="bond">债券型</Option>
        <Option value="index">指数型</Option>
        <Option value="money">货币型</Option>
      </Select>
      <Input
        placeholder="最小收益率"
        style={{ width: 120 }}
        type="number"
        onChange={(e) => setFilters({ ...filters, minReturn: parseFloat(e.target.value) || undefined })}
      />
      <Input
        placeholder="最大收益率"
        style={{ width: 120 }}
        type="number"
        onChange={(e) => setFilters({ ...filters, maxReturn: parseFloat(e.target.value) || undefined })}
      />
      <Button
        type="primary"
        onClick={() => onFilter?.(filters)}
      >
        筛选
      </Button>
      <Button
        onClick={() => {
          setFilters({});
          setSearchText('');
        }}
      >
        重置
      </Button>
    </Space>
  );

  return (
    <div>
      <FilterBar />
      <Table
        columns={columns}
        dataSource={tableData}
        loading={loading}
        scroll={{ x: 1500 }}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 只基金`,
        }}
        onRow={(record) => ({
          onClick: () => onViewDetail?.(record.code),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  );
};

export default FundList;
