/**
 * 基金详情页
 * 
 * 展示基金的详细信息，包括基本信息、业绩走势、资产配置等
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardBody,
  Heading,
  Text,
  HStack,
  VStack,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Button,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  Divider,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Progress,
  Icon,
  useToast,
} from '@chakra-ui/react';
import {
  ArrowBackIcon,
  StarIcon,
} from '@chakra-ui/icons';
import { FiTrendingUp, FiTrendingDown } from 'react-icons/fi';
import {
  fundApi,
  FundInfo,
  FundRealtimeRateInfo,
  FundPeriodChangeInfo,
  FundAssetsAllocationInfo,
  FundPositionInfo,
} from '@/services/fund';

const FundDetail: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const toast = useToast();

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
      toast({
        title: '加载失败',
        description: '加载基金数据失败',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  }, [code, toast]);

  useEffect(() => {
    loadFundData();
  }, [loadFundData]);

  // 获取收益率颜色
  const getReturnColor = (value?: number) => {
    if (value === undefined || value === null) return 'gray.500';
    if (value > 0) return 'red.500';
    if (value < 0) return 'green.500';
    return 'blue.500';
  };

  // 获取收益率文本
  const getReturnText = (value?: number) => {
    if (value === undefined || value === null) return '--';
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // 获取基金类型标签
  const getFundTypeTag = () => {
    if (!fundInfo?.type) return null;
    const typeMap: Record<string, { color: string; text: string }> = {
      'stock': { color: 'red', text: '股票型' },
      'bond': { color: 'blue', text: '债券型' },
      'money': { color: 'green', text: '货币型' },
      'index': { color: 'orange', text: '指数型' },
      'mix': { color: 'purple', text: '混合型' },
    };
    const config = typeMap[fundInfo.type] || { color: 'gray', text: '未知' };
    return <Badge colorScheme={config.color as any}>{config.text}</Badge>;
  };

  // 渲染基本信息
  const renderBasicInfo = () => (
    <Card>
      <CardBody>
        <VStack spacing={4} align="stretch">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <HStack>
                <Heading size="lg">{fundInfo?.name}</Heading>
                {getFundTypeTag()}
              </HStack>
              <Text color="gray.500">基金代码：{code}</Text>
            </VStack>
            <Button
              leftIcon={<Icon as={StarIcon} fill={isFavorite ? 'yellow.500' : 'none'} color={isFavorite ? 'yellow.500' : 'inherit'} />}
              onClick={() => {
                setIsFavorite(!isFavorite);
                toast({
                  title: isFavorite ? '已取消收藏' : '已加入收藏',
                  status: 'success',
                  duration: 2000,
                });
              }}
            >
              {isFavorite ? '已收藏' : '收藏'}
            </Button>
          </HStack>

          <Divider />

          <SimpleGrid columns={{ base: 1, sm: 2, md: 4 }} spacing={4}>
            <Stat>
              <StatLabel>最新净值</StatLabel>
              <StatNumber>{fundInfo?.net_asset_value?.toFixed(4) || '--'}</StatNumber>
            </Stat>
            <Stat>
              <StatLabel>日涨跌幅</StatLabel>
              <StatNumber color={getReturnColor(fundInfo?.change_pct)}>
                {getReturnText(fundInfo?.change_pct)}
              </StatNumber>
            </Stat>
            <Stat>
              <StatLabel>基金规模</StatLabel>
              <StatNumber>{fundInfo?.fund_scale ? `${fundInfo.fund_scale.toFixed(2)}亿` : '--'}</StatNumber>
            </Stat>
            <Stat>
              <StatLabel>基金公司</StatLabel>
              <StatNumber fontSize="md">{fundInfo?.fund_company || '--'}</StatNumber>
            </Stat>
          </SimpleGrid>
        </VStack>
      </CardBody>
    </Card>
  );

  // 渲染阶段涨跌幅
  const renderPeriodChange = () => (
    <Card>
      <CardBody>
        <Heading size="md" mb={4}>阶段涨跌幅</Heading>
        <SimpleGrid columns={{ base: 2, sm: 3, md: 5 }} spacing={4}>
          {periodChange.map((item, idx) => (
            <VStack key={idx} p={3} borderWidth="1px" borderRadius="md">
              <Text fontSize="sm" color="gray.500">{item.period}</Text>
              <Text fontWeight="bold" color={getReturnColor(item.return_rate)} fontSize="lg">
                {getReturnText(item.return_rate)}
              </Text>
              <Text fontSize="xs" color="gray.500">排名：{item.rank}</Text>
            </VStack>
          ))}
        </SimpleGrid>
      </CardBody>
    </Card>
  );

  // 渲染资产配置
  const renderAssetsAllocation = () => (
    <Card>
      <CardBody>
        <Heading size="md" mb={4}>资产配置</Heading>
        <VStack spacing={3} align="stretch">
          {assetsAllocation.slice(0, 5).map((item, idx) => (
            <VStack key={idx} align="stretch">
              <HStack justify="space-between">
                <Text>{item.asset_name}</Text>
                <Text fontWeight="bold">{item.ratio?.toFixed(2)}%</Text>
              </HStack>
              <Progress
                value={item.ratio || 0}
                colorScheme={idx === 0 ? 'blue' : 'green'}
                size="sm"
                borderRadius="full"
              />
            </VStack>
          ))}
        </VStack>
      </CardBody>
    </Card>
  );

  // 渲染持仓占比
  const renderPosition = () => (
    <Card>
      <CardBody>
        <Heading size="md" mb={4}>持仓占比</Heading>
        <TableContainer>
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>股票代码</Th>
                <Th>股票名称</Th>
                <Th isNumeric>持仓占比</Th>
              </Tr>
            </Thead>
            <Tbody>
              {position.slice(0, 10).map((item, idx) => (
                <Tr key={idx}>
                  <Td fontWeight="bold">{item.stock_code}</Td>
                  <Td>{item.stock_name}</Td>
                  <Td isNumeric fontWeight="bold" color={getReturnColor(item.ratio)}>
                    {item.ratio?.toFixed(2)}%
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );

  if (loading) {
    return (
      <Box p={6} textAlign="center">
        <Spinner size="xl" thickness="4px" speed="0.65s" color="blue.500" />
        <Text mt={4}>加载中...</Text>
      </Box>
    );
  }

  if (!fundInfo) {
    return (
      <Box p={6}>
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          <AlertTitle mr={2}>基金不存在</AlertTitle>
          <AlertDescription>未找到该基金的信息</AlertDescription>
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={6}>
      <VStack spacing={6} align="stretch">
        {/* 返回按钮 */}
        <HStack>
          <Button
            leftIcon={<ArrowBackIcon />}
            variant="ghost"
            onClick={() => navigate('/fund')}
          >
            返回
          </Button>
          <Heading size="lg">基金详情</Heading>
        </HStack>

        {/* 基本信息 */}
        {renderBasicInfo()}

        {/* Tab 切换 */}
        <Tabs variant="enclosed">
          <TabList>
            <Tab>阶段涨跌幅</Tab>
            <Tab>资产配置</Tab>
            <Tab>持仓占比</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>{renderPeriodChange()}</TabPanel>
            <TabPanel>{renderAssetsAllocation()}</TabPanel>
            <TabPanel>{renderPosition()}</TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
};

export default FundDetail;
