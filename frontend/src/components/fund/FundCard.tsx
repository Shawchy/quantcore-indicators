/**
 * 基金卡片组件
 * 
 * 用于展示单个基金的摘要信息，适用于卡片式布局
 */
import React from 'react';
import {
  Card,
  Text,
  HStack,
  VStack,
  Badge,
  Button,
  SimpleGrid,
  Separator,
  Icon,
} from '@chakra-ui/react';
import { useColorModeValue } from '@/components/ui/color-mode';
import { FiStar, FiTrendingUp, FiTrendingDown } from 'react-icons/fi';
import { FundInfo } from '@/services/fund';

interface FundCardProps {
  fund: FundInfo;
  showRank?: boolean;
  showActions?: boolean;
  compact?: boolean;
  isFavorite?: boolean;
  onViewDetail?: (code: string) => void;
  onToggleFavorite?: (code: string) => void;
}

const FundCard: React.FC<FundCardProps> = ({
  fund,
  showRank = true,
  showActions = true,
  compact = false,
  isFavorite = false,
  onViewDetail,
  onToggleFavorite,
}) => {
  // 颜色模式适配
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.400');
  const headingColor = useColorModeValue('gray.900', 'white');

  // 判断涨跌
  const isUp = (fund.change_pct ?? 0) > 0;
  const changeColor = isUp ? 'red.500' : 'green.500';

  return (
    <Card.Root
      bg={cardBg}
      borderColor={borderColor}
      borderWidth="1px"
      borderRadius="xl"
      overflow="hidden"
      _hover={{
        shadow: 'lg',
        transform: 'translateY(-2px)',
        transition: 'all 0.2s',
        borderColor: 'blue.300',
      }}
      transition="all 0.2s"
    >
      {/* 头部：基金信息 */}
      <Card.Body p={compact ? 3 : 4}>
        <HStack justify="space-between" mb={3}>
          <VStack align="start" gap={0.5} flex={1}>
            <HStack gap={2}>
              <Text
                fontWeight="bold"
                fontSize="lg"
                color={headingColor}
                cursor="pointer"
                onClick={() => onViewDetail?.(fund.code)}
                _hover={{ color: 'blue.500' }}
              >
                {fund.name}
              </Text>
              {showRank && fund.rank_3y && (
                <Badge colorPalette="orange" fontSize="xs">
                  近1年: {fund.rank_3y}
                </Badge>
              )}
            </HStack>
            <Text fontSize="sm" color={textColor} cursor="pointer" onClick={() => onViewDetail?.(fund.code)}>
              {fund.code}
            </Text>
          </VStack>
          
          {/* 收藏按钮 */}
          {showActions && onToggleFavorite && (
            <Button
              size="sm"
              variant="ghost"
              colorPalette={isFavorite ? 'yellow' : 'gray'}
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite(fund.code);
              }}
              minW="auto"
              px={2}
            >
              <Icon as={FiStar} fill={isFavorite ? 'currentColor' : 'none'} />
            </Button>
          )}
        </HStack>

        {/* 净值和涨跌幅 */}
        <SimpleGrid columns={2} gap={3} mb={compact ? 2 : 3}>
          <VStack align="start" gap={0}>
            <Text fontSize="xs" color={textColor}>最新净值</Text>
            <Text fontSize="xl" fontWeight="bold" color={headingColor}>
              {fund.net_asset_value?.toFixed(4)}
            </Text>
          </VStack>
          <VStack align="start" gap={0}>
            <Text fontSize="xs" color={textColor}>日涨跌</Text>
            <HStack gap={1}>
              <Icon
                as={isUp ? FiTrendingUp : FiTrendingDown}
                color={changeColor}
                boxSize={4}
              />
              <Text fontSize="lg" fontWeight="bold" color={changeColor}>
                {isUp ? '+' : ''}{fund.change_pct?.toFixed(2)}%
              </Text>
            </HStack>
          </VStack>
        </SimpleGrid>

        {/* 阶段涨幅 */}
        {!compact && (fund.change_1m !== undefined || fund.change_3m !== undefined || fund.change_6m !== undefined || fund.change_1y !== undefined) && (
          <>
            <Separator my={3} />
            <VStack align="start" gap={2}>
              <Text fontSize="xs" fontWeight="medium" color={textColor}>阶段涨幅</Text>
              <SimpleGrid columns={4} gap={2} w="full">
                {fund.change_1m !== undefined && (
                  <VStack align="center" gap={0.5}>
                    <Text fontSize="xs" color={textColor}>近1月</Text>
                    <Text fontSize="sm" fontWeight="bold" color={fund.change_1m > 0 ? 'red.500' : 'green.500'}>
                      {fund.change_1m.toFixed(2)}%
                    </Text>
                  </VStack>
                )}
                {fund.change_3m !== undefined && (
                  <VStack align="center" gap={0.5}>
                    <Text fontSize="xs" color={textColor}>近3月</Text>
                    <Text fontSize="sm" fontWeight="bold" color={fund.change_3m > 0 ? 'red.500' : 'green.500'}>
                      {fund.change_3m.toFixed(2)}%
                    </Text>
                  </VStack>
                )}
                {fund.change_6m !== undefined && (
                  <VStack align="center" gap={0.5}>
                    <Text fontSize="xs" color={textColor}>近6月</Text>
                    <Text fontSize="sm" fontWeight="bold" color={fund.change_6m > 0 ? 'red.500' : 'green.500'}>
                      {fund.change_6m.toFixed(2)}%
                    </Text>
                  </VStack>
                )}
                {fund.change_1y !== undefined && (
                  <VStack align="center" gap={0.5}>
                    <Text fontSize="xs" color={textColor}>近1年</Text>
                    <Text fontSize="sm" fontWeight="bold" color={fund.change_1y > 0 ? 'red.500' : 'green.500'}>
                      {fund.change_1y.toFixed(2)}%
                    </Text>
                  </VStack>
                )}
              </SimpleGrid>
            </VStack>
          </>
        )}

        {/* 操作按钮 */}
        {showActions && (
          <>
            <Separator my={3} />
            <Button
              w="full"
              colorPalette="blue"
              variant="outline"
              size="sm"
              onClick={() => onViewDetail?.(fund.code)}
            >
              查看详情
            </Button>
          </>
        )}
      </Card.Body>
    </Card.Root>
  );
};

export default FundCard;
