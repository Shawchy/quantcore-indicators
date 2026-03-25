/**
 * 基金列表组件
 * 
 * 用于展示基金列表数据，支持排序、筛选、分页等功能
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Badge,
  HStack,
  VStack,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Text,
  Tooltip,
  useColorModeValue,
  Icon,
} from '@chakra-ui/react';
import { StarIcon, SearchIcon, ChevronUpIcon, ChevronDownIcon } from '@chakra-ui/icons';
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
    return <Badge colorScheme={config.color as any}>{config.text}</Badge>;
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
      <InputGroup w="300px">
        <InputLeftElement pointerEvents="none">
          <SearchIcon color="gray.300" />
        </InputLeftElement>
        <Input
          placeholder="搜索基金代码或名称"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
      </InputGroup>
      
      <Select
        placeholder="基金类型"
        w="120px"
        onChange={(e) => setFilters({ ...filters, fundType: e.target.value })}
      >
        <option value="stock">股票型</option>
        <option value="mix">混合型</option>
        <option value="bond">债券型</option>
        <option value="index">指数型</option>
        <option value="money">货币型</option>
      </Select>
      
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
      
      <Button colorScheme="blue" onClick={() => onFilter?.(filters)}>
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
      <TableContainer>
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th w="60px">收藏</Th>
              <Th w="100px">基金代码</Th>
              <Th w="200px">基金名称</Th>
              <Th w="100px">最新净值</Th>
              <Th w="100px">日涨跌</Th>
              <Th w="90px">近 1 周</Th>
              <Th w="90px">近 1 月</Th>
              <Th w="90px">近 3 月</Th>
              <Th w="90px">近 6 月</Th>
              <Th w="90px">近 1 年</Th>
              <Th w="110px">基金规模</Th>
              <Th w="150px">基金公司</Th>
              <Th w="100px">操作</Th>
            </Tr>
          </Thead>
          <Tbody>
            {tableData.map((item) => (
              <Tr
                key={item.code}
                _hover={{ bg: hoverBg }}
                cursor="pointer"
                onClick={() => onViewDetail?.(item.code)}
              >
                <Td>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAddToWatchlist?.(item.code);
                    }}
                  >
                    <Icon
                      as={StarIcon}
                      color={item.isFavorite ? 'yellow.500' : 'inherit'}
                      fill={item.isFavorite ? 'yellow.500' : 'none'}
                    />
                  </Button>
                </Td>
                <Td fontWeight="bold">{item.code}</Td>
                <Td>
                  <VStack align="start" spacing={1}>
                    <Text>{item.name}</Text>
                    {getFundTypeTag(item.type)}
                  </VStack>
                </Td>
                <Td>{item.net_asset_value?.toFixed(4) || '--'}</Td>
                <Td>
                  <Text fontWeight="bold" color={getReturnColor(item.change_pct)}>
                    {getReturnText(item.change_pct)}
                  </Text>
                </Td>
                <Td color={getReturnColor(item.performance?.['1w'])}>
                  {getReturnText(item.performance?.['1w'])}
                </Td>
                <Td color={getReturnColor(item.performance?.['1m'])}>
                  {getReturnText(item.performance?.['1m'])}
                </Td>
                <Td color={getReturnColor(item.performance?.['3m'])}>
                  {getReturnText(item.performance?.['3m'])}
                </Td>
                <Td color={getReturnColor(item.performance?.['6m'])}>
                  {getReturnText(item.performance?.['6m'])}
                </Td>
                <Td fontWeight="bold" color={getReturnColor(item.performance?.['1y'])}>
                  {getReturnText(item.performance?.['1y'])}
                </Td>
                <Td>{item.fund_scale ? `${item.fund_scale.toFixed(2)}亿` : '--'}</Td>
                <Td>
                  <Tooltip label={item.fund_company}>
                    <Text noOfLines={1}>{item.fund_company || '--'}</Text>
                  </Tooltip>
                </Td>
                <Td>
                  <Button size="sm" variant="link" colorScheme="blue">
                    详情
                  </Button>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default FundList;
