/**
 * 基金列表组件
 * 
 * 用于展示基金列表数据，支持排序、筛选、分页等功能
 */
import React, { useState, useMemo } from 'react';
import { Badge, Box, Button, HStack, Icon, Input, InputGroup, NativeSelect, Table, Text, Tooltip, VStack } from '@chakra-ui/react'
import { useColorModeValue } from '../ui/color-mode'
import { FiSearch, FiStar } from 'react-icons/fi'
import { FundInfo, FundPeriodChangeInfo } from '@/services/fund';

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
  performanceData = {},
  onFilter,
  onViewDetail,
  onAddToWatchlist,
  watchlist = [],
}) => {
  const [filters, setFilters] = useState<FundFilter>({});
  const [searchText, setSearchText] = useState('');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  // 处理基金类型
  const getFundTypeTag = (type?: string) => {
    const typeMap: Record<string, { color: string; text: string }> = {
      'stock': { color: 'red', text: '股票型' },
      'bond': { color: 'blue', text: '债券型' },
      'money': { color: 'green', text: '货币型' },
      'index': { color: 'orange', text: '指数型' },
      'mix': { color: 'purple', text: '混合型' },
    };
    const config = type ? typeMap[type] || { color: 'gray', text: type } : { color: 'gray', text: '未知' };
    return <Badge colorPalette={config.color as any}>{config.text}</Badge>;
  };

  // 处理收益率颜色
  const getReturnColor = (value?: number) => {
    if (value === undefined || value === null) return 'gray.500';
    if (value > 0) return 'red.500';
    if (value < 0) return 'green.500';
    return 'blue.500';
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

  // 筛选栏
  const FilterBar = () => (
    <HStack wrap="wrap" mb={4} gap={2}>
      <InputGroup w="300px" startElement={<FiSearch color="gray.300" />}>
        <Input
          placeholder="搜索基金代码或名称"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
      </InputGroup>
      
      <NativeSelect.Root><NativeSelect.Field
        placeholder="基金类型"
        onChange={(e) => setFilters({ ...filters, fundType: e.target.value })}
      >
        <option value="stock">股票型</option>
        <option value="mix">混合型</option>
        <option value="bond">债券型</option>
        <option value="index">指数型</option>
        <option value="money">货币型</option>
      </NativeSelect.Field></NativeSelect.Root>
      
      <Input
        placeholder="最小收益率"
        w="120px"
        type="number"
        onChange={(e) => setFilters({ ...filters, minReturn: parseFloat(e.target.value) || undefined })}
      />
      
      <Input
        placeholder="最大收益率"
        w="120px"
        type="number"
        onChange={(e) => setFilters({ ...filters, maxReturn: parseFloat(e.target.value) || undefined })}
      />
      
      <Button colorPalette="blue" onClick={() => onFilter?.(filters)}>
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
    </HStack>
  );

  return (
    <Box>
      <FilterBar />
      <Box>
        <Table.Root  size="sm">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader w="60px">收藏</Table.ColumnHeader>
              <Table.ColumnHeader w="100px">基金代码</Table.ColumnHeader>
              <Table.ColumnHeader w="200px">基金名称</Table.ColumnHeader>
              <Table.ColumnHeader w="100px">最新净值</Table.ColumnHeader>
              <Table.ColumnHeader w="100px">日涨跌</Table.ColumnHeader>
              <Table.ColumnHeader w="90px">近 1 周</Table.ColumnHeader>
              <Table.ColumnHeader w="90px">近 1 月</Table.ColumnHeader>
              <Table.ColumnHeader w="90px">近 3 月</Table.ColumnHeader>
              <Table.ColumnHeader w="90px">近 6 月</Table.ColumnHeader>
              <Table.ColumnHeader w="90px">近 1 年</Table.ColumnHeader>
              <Table.ColumnHeader w="110px">基金规模</Table.ColumnHeader>
              <Table.ColumnHeader w="150px">基金公司</Table.ColumnHeader>
              <Table.ColumnHeader w="100px">操作</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {tableData.map((item) => (
              <Table.Row
                key={item.code}
                _hover={{ bg: hoverBg }}
                cursor="pointer"
                onClick={() => onViewDetail?.(item.code)}
              >
                <Table.Cell>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAddToWatchlist?.(item.code);
                    }}
                  >
                    <Icon
                      as={FiStar}
                      color={item.isFavorite ? 'yellow.500' : 'inherit'}
                      fill={item.isFavorite ? 'yellow.500' : 'none'}
                    />
                  </Button>
                </Table.Cell>
                <Table.Cell fontWeight="bold">{item.code}</Table.Cell>
                <Table.Cell>
                  <VStack align="start" gap={1}>
                    <Text>{item.name}</Text>
                    {getFundTypeTag(item.type)}
                  </VStack>
                </Table.Cell>
                <Table.Cell>{item.net_asset_value?.toFixed(4) || '--'}</Table.Cell>
                <Table.Cell>
                  <Text fontWeight="bold" color={getReturnColor(item.change_pct)}>
                    {getReturnText(item.change_pct)}
                  </Text>
                </Table.Cell>
                <Table.Cell color={getReturnColor(item.performance?.['1w'])}>
                  {getReturnText(item.performance?.['1w'])}
                </Table.Cell>
                <Table.Cell color={getReturnColor(item.performance?.['1m'])}>
                  {getReturnText(item.performance?.['1m'])}
                </Table.Cell>
                <Table.Cell color={getReturnColor(item.performance?.['3m'])}>
                  {getReturnText(item.performance?.['3m'])}
                </Table.Cell>
                <Table.Cell color={getReturnColor(item.performance?.['6m'])}>
                  {getReturnText(item.performance?.['6m'])}
                </Table.Cell>
                <Table.Cell fontWeight="bold" color={getReturnColor(item.performance?.['1y'])}>
                  {getReturnText(item.performance?.['1y'])}
                </Table.Cell>
                <Table.Cell>{item.fund_scale ? `${item.fund_scale.toFixed(2)}亿` : '--'}</Table.Cell>
                <Table.Cell>
                  <Tooltip.Root>
                    <Tooltip.Trigger>
                      <Text lineClamp={1}>{item.fund_company || '--'}</Text>
                    </Tooltip.Trigger>
                    <Tooltip.Content>{item.fund_company || '--'}</Tooltip.Content>
                  </Tooltip.Root>
                </Table.Cell>
                <Table.Cell>
                  <Button size="sm" variant="plain" colorPalette="blue">
                    详情
                  </Button>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    </Box>
  );
};

export default FundList;
