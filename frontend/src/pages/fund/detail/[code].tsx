/**
 * 基金详情页
 * 
 * 展示基金的详细信息，包括基本信息、业绩走势、资产配置等
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Alert, Badge, Box, Button, Card, HStack, Heading, Icon, Progress, Separator, SimpleGrid, Spinner, Stat, Table, Tabs, Text, VStack } from '@chakra-ui/react'
import { toaster } from '../../../components/ui/toaster'
import { FiStar } from 'react-icons/fi'
import {
  fundApi,
  FundInfo,
  FundPeriodChangeInfo,
  FundAssetsAllocationInfo,
  FundPositionInfo,
} from '@/services/fund';

const FundDetail: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  ;

  const [loading, setLoading] = useState(false);
  const [fundInfo, setFundInfo] = useState<FundInfo | null>(null);
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
      toaster.create({
        title: '加载失败',
        description: '加载基金数据失败',
        type: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  }, [code, toaster]);

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
    return <Badge colorPalette={config.color as any}>{config.text}</Badge>;
  };

  // 渲染基本信息
  const renderBasicInfo = () => (
    <Card.Root>
      <Card.Body>
        <VStack gap={4} align="stretch">
          <HStack justify="space-between">
            <VStack align="start" gap={1}>
              <HStack>
                <Heading size="lg">{fundInfo?.name}</Heading>
                {getFundTypeTag()}
              </HStack>
              <Text color="gray.500">基金代码：{code}</Text>
            </VStack>
            <Button
              onClick={() => {
                setIsFavorite(!isFavorite);
                toaster.create({
                  title: isFavorite ? '已取消收藏' : '已加入收藏',
                  type: 'success',
                  duration: 2000,
                });
              }}
            >
              <Icon as={FiStar} fill={isFavorite ? 'yellow.500' : 'none'} color={isFavorite ? 'yellow.500' : 'inherit'} />
              {isFavorite ? '已收藏' : '收藏'}
            </Button>
          </HStack>

          <Separator />

          <SimpleGrid columns={{ base: 1, sm: 2, md: 4 }} gap={4}>
            <Stat.Root>
              <Stat.Label>最新净值</Stat.Label>
              <Stat.ValueText>{fundInfo?.net_asset_value?.toFixed(4) || '--'}</Stat.ValueText>
            </Stat.Root>
            <Stat.Root>
              <Stat.Label>日涨跌幅</Stat.Label>
              <Stat.ValueText color={getReturnColor(fundInfo?.change_pct)}>
                {getReturnText(fundInfo?.change_pct)}
              </Stat.ValueText>
            </Stat.Root>
            <Stat.Root>
              <Stat.Label>基金规模</Stat.Label>
              <Stat.ValueText>{fundInfo?.fund_scale ? `${fundInfo.fund_scale.toFixed(2)}亿` : '--'}</Stat.ValueText>
            </Stat.Root>
            <Stat.Root>
              <Stat.Label>基金公司</Stat.Label>
              <Stat.ValueText fontSize="md">{fundInfo?.fund_company || '--'}</Stat.ValueText>
            </Stat.Root>
          </SimpleGrid>
        </VStack>
      </Card.Body>
    </Card.Root>
  );

  // 渲染阶段涨跌幅
  const renderPeriodChange = () => (
    <Card.Root>
      <Card.Body>
        <Heading size="md" mb={4}>阶段涨跌幅</Heading>
        <SimpleGrid columns={{ base: 2, sm: 3, md: 5 }} gap={4}>
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
      </Card.Body>
    </Card.Root>
  );

  // 渲染资产配置
  const renderAssetsAllocation = () => (
    <Card.Root>
      <Card.Body>
        <Heading size="md" mb={4}>资产配置</Heading>
        <VStack gap={3} align="stretch">
          {assetsAllocation.slice(0, 5).map((item, idx) => (
            <VStack key={idx} align="stretch">
              <HStack justify="space-between">
                <Text>{item.asset_name}</Text>
                <Text fontWeight="bold">{item.ratio?.toFixed(2)}%</Text>
              </HStack>
              <Progress.Root
                value={item.ratio || 0}
                colorPalette={idx === 0 ? 'blue' : 'green'}
                size="sm"
                borderRadius="full"
              />
            </VStack>
          ))}
        </VStack>
      </Card.Body>
    </Card.Root>
  );

  // 渲染持仓占比
  const renderPosition = () => (
    <Card.Root>
      <Card.Body>
        <Heading size="md" mb={4}>持仓占比</Heading>
        <Box>
          <Table.Root  size="sm">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>股票代码</Table.ColumnHeader>
                <Table.ColumnHeader>股票名称</Table.ColumnHeader>
                <Table.ColumnHeader >持仓占比</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {position.slice(0, 10).map((item, idx) => (
                <Table.Row key={idx}>
                  <Table.Cell fontWeight="bold">{item.stock_code}</Table.Cell>
                  <Table.Cell>{item.stock_name}</Table.Cell>
                  <Table.Cell fontWeight="bold" color={getReturnColor(item.ratio)}>
                    {item.ratio?.toFixed(2)}%
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        </Box>
      </Card.Body>
    </Card.Root>
  );

  if (loading) {
    return (
      <Box p={6} textAlign="center">
        <Spinner size="xl" borderWidth="4px"  color="blue.500" />
        <Text mt={4}>加载中...</Text>
      </Box>
    );
  }

  if (!fundInfo) {
    return (
      <Box p={6}>
        <Alert.Root status="error" borderRadius="md">
          <Alert.Indicator />
          <Alert.Title mr={2}>基金不存在</Alert.Title>
          <Alert.Description>未找到该基金的信息</Alert.Description>
        </Alert.Root>
      </Box>
    );
  }

  return (
    <Box p={6}>
      <VStack gap={6} align="stretch">
        {/* 返回按钮 */}
        <HStack>
          <Button
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
        <Tabs.Root variant="enclosed">
          <Tabs.List>
            <Tabs.Trigger value="阶段涨跌幅">阶段涨跌幅</Tabs.Trigger>
            <Tabs.Trigger value="资产配置">资产配置</Tabs.Trigger>
            <Tabs.Trigger value="持仓占比">持仓占比</Tabs.Trigger>
          </Tabs.List>
          <Tabs.ContentGroup>
            <Tabs.Content value="资产配置">{renderPeriodChange()}</Tabs.Content>
            <Tabs.Content value="持仓占比">{renderAssetsAllocation()}</Tabs.Content>
            <Tabs.Content value="阶段涨跌幅">{renderPosition()}</Tabs.Content>
          </Tabs.ContentGroup>
        </Tabs.Root>
      </VStack>
    </Box>
  );
};

export default FundDetail;
