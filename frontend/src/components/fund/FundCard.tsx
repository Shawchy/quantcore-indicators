/**
 * 基金卡片组件
 * 
 * 用于展示单个基金的摘要信息，适用于卡片式布局
 */
import React from 'react';
import { Badge, Button, Card, HStack, Heading, Icon, Separator, SimpleGrid, Stat, Text, VStack } from '@chakra-ui/react'
import { useColorModeValue } from '../ui/color-mode'
import { FiStar } from 'react-icons/fi'
import { FiTrendingUp, FiTrendingDown } from 'react-icons/fi';
import { FundInfo } from '@/services/fund';

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
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

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
    const typeMap: Record<string, { color: string; text: string }> = {
      'stock': { color: 'red', text: '股票型' },
      'bond': { color: 'blue', text: '债券型' },
      'money': { color: 'green', text: '货币型' },
      'index': { color: 'orange', text: '指数型' },
      'mix': { color: 'purple', text: '混合型' },
    };
    const config = fund.type ? typeMap[fund.type] : { color: 'gray', text: '未知' };
    return <Badge colorPalette={config.color as any}>{config.text}</Badge>;
  };

  return (
    <Card.Root
      _hover={{ bg: hoverBg }}
      cursor="pointer"
      onClick={() => onViewDetail?.(fund.code)}
      height="100%"
    >
      <Card.Body>
        <VStack gap={3} align="stretch">
          {/* 基金基本信息 */}
          <HStack justify="space-between">
            <VStack align="start" gap={0}>
              <HStack>
                {showRank && fund.rank && (
                  <Badge colorPalette="yellow">TOP {fund.rank}</Badge>
                )}
                <Heading size="md">{fund.name}</Heading>
              </HStack>
              <Text fontSize="sm" color="gray.500">{fund.code}</Text>
            </VStack>
            <HStack>
              {getFundTypeTag()}
              {showActions && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    onAddToWatchlist?.(fund.code);
                  }}
                >
                  <Icon
                    as={FiStar}
                    color={isFavorite ? 'yellow.500' : 'inherit'}
                    fill={isFavorite ? 'yellow.500' : 'none'}
                  />
                </Button>
              )}
            </HStack>
          </HStack>

          <Separator />

          {/* 净值和涨跌幅 */}
          <SimpleGrid columns={2} gap={4}>
            <Stat.Root>
              <Stat.Label fontSize="sm">最新净值</Stat.Label>
              <Stat.ValueText fontSize={compact ? 'lg' : 'xl'}>
                {fund.net_asset_value?.toFixed(4) || '--'}
              </Stat.ValueText>
            </Stat.Root>
            <Stat.Root>
              <Stat.Label fontSize="sm">日涨跌</Stat.Label>
              <Stat.ValueText
                fontSize={compact ? 'lg' : 'xl'}
                color={getReturnColor(fund.change_pct)}
              >
                <HStack>
                  {fund.change_pct && fund.change_pct > 0 && <FiTrendingUp />}
                  {fund.change_pct && fund.change_pct < 0 && <FiTrendingDown />}
                  <span>{getReturnText(fund.change_pct)}</span>
                </HStack>
              </Stat.ValueText>
            </Stat.Root>
          </SimpleGrid>

          {/* 阶段涨跌幅 - 非紧凑模式显示 */}
          {!compact && fund.performance && (
            <>
              <Separator />
              <SimpleGrid columns={3} gap={2}>
                <VStack>
                  <Text fontSize="xs" color="gray.500">近 1 周</Text>
                  <Text fontSize="sm" color={getReturnColor(fund.performance['1w'])}>
                    {getReturnText(fund.performance['1w'])}
                  </Text>
                </VStack>
                <VStack>
                  <Text fontSize="xs" color="gray.500">近 1 月</Text>
                  <Text fontSize="sm" color={getReturnColor(fund.performance['1m'])}>
                    {getReturnText(fund.performance['1m'])}
                  </Text>
                </VStack>
                <VStack>
                  <Text fontSize="xs" color="gray.500">近 3 月</Text>
                  <Text fontSize="sm" color={getReturnColor(fund.performance['3m'])}>
                    {getReturnText(fund.performance['3m'])}
                  </Text>
                </VStack>
              </SimpleGrid>
              <SimpleGrid columns={3} gap={2}>
                <VStack>
                  <Text fontSize="xs" color="gray.500">近 6 月</Text>
                  <Text fontSize="sm" color={getReturnColor(fund.performance['6m'])}>
                    {getReturnText(fund.performance['6m'])}
                  </Text>
                </VStack>
                <VStack>
                  <Text fontSize="xs" color="gray.500">近 1 年</Text>
                  <Text fontSize="sm" fontWeight="bold" color={getReturnColor(fund.performance['1y'])}>
                    {getReturnText(fund.performance['1y'])}
                  </Text>
                </VStack>
                <VStack>
                  <Text fontSize="xs" color="gray.500">规模</Text>
                  <Text fontSize="sm">
                    {fund.fund_scale ? `${fund.fund_scale.toFixed(2)}亿` : '--'}
                  </Text>
                </VStack>
              </SimpleGrid>
            </>
          )}

          {/* 基金公司 */}
          {!compact && fund.fund_company && (
            <>
              <Separator />
              <VStack align="start" gap={1}>
                <Text fontSize="xs" color="gray.500">基金公司</Text>
                <Text fontSize="sm">{fund.fund_company}</Text>
              </VStack>
            </>
          )}

          {/* 操作按钮 */}
          {showActions && (
            <Button colorPalette="blue" width="full" onClick={() => onViewDetail?.(fund.code)}>
              查看详情
            </Button>
          )}
        </VStack>
      </Card.Body>
    </Card.Root>
  );
};

export default React.memo(FundCard);
