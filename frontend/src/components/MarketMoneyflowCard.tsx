import { Badge, Card, Flex, HStack, Heading, SimpleGrid, Spinner, Text, VStack } from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { moneyflowApi } from '../services/api'
import { FiTrendingUp, FiTrendingDown } from 'react-icons/fi'

interface MarketMoneyflowCardProps {
  showTrend?: boolean
  days?: number
}

const formatAmount = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined) return '--'
  if (Math.abs(amount) >= 1e8) {
    return `${(amount / 1e8).toFixed(2)}亿`
  } else if (Math.abs(amount) >= 1e4) {
    return `${(amount / 1e4).toFixed(2)}万`
  }
  return amount.toFixed(2)
}

const getAmountColor = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined) return 'gray.500'
  return amount >= 0 ? 'up.500' : 'down.500'
}

const MarketMoneyflowCard: React.FC<MarketMoneyflowCardProps> = ({ showTrend = false, days = 5 }) => {
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['marketMoneyflowSummary'],
    queryFn: () => moneyflowApi.getMarketMoneyflowSummary(),
    refetchInterval: 60000,
  })

  // 趋势数据功能预留
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { data: _trendData, isLoading: _trendLoading } = useQuery({
    queryKey: ['marketMoneyflowTrend', days],
    queryFn: () => moneyflowApi.getMarketMoneyflowTrend(days),
    enabled: showTrend,
  })

  if (summaryLoading) {
    return (
      <Card.Root>
        <Card.Body>
          <Flex justify="center" align="center" h="200px">
            <Spinner size="lg" color="brand.400" />
          </Flex>
        </Card.Body>
      </Card.Root>
    )
  }

  const summary = summaryData?.data?.data

  if (!summary) {
    return (
      <Card.Root>
        <Card.Body>
          <Text color="fg.subtle" textAlign="center">暂无资金流向数据</Text>
        </Card.Body>
      </Card.Root>
    )
  }

  const mainNetIn = summary.main_net_in?.amount
  const superLarge = summary.super_large?.amount
  const large = summary.large?.amount
  const medium = summary.medium?.amount
  const small = summary.small?.amount

  return (
    <Card.Root>
      <Card.Header pb={2}>
        <Flex justify="space-between" align="center">
          <Heading size="sm" color="fg">大盘资金流向</Heading>
          {summary.trade_date && (
            <Badge fontSize="xs" colorPalette="blue">
              {summary.trade_date}
            </Badge>
          )}
        </Flex>
      </Card.Header>
      <Card.Body pt={2}>
        <VStack gap={4} align="stretch">
          <Flex justify="center" align="center" direction="column" py={2}>
            <Text fontSize="xs" color="fg.muted" mb={1}>主力净流入</Text>
            <HStack gap={2}>
              {mainNetIn !== null && mainNetIn !== undefined && (
                mainNetIn >= 0 ? (
                  <FiTrendingUp color="var(--chakra-colors-up-500)" size={24} />
                ) : (
                  <FiTrendingDown color="var(--chakra-colors-down-500)" size={24} />
                )
              )}
              <Text
                fontSize="2xl"
                fontWeight="bold"
                color={getAmountColor(mainNetIn)}
                fontFamily="mono"
              >
                {formatAmount(mainNetIn)}
              </Text>
            </HStack>
            {summary.main_net_in?.rate !== null && summary.main_net_in?.rate !== undefined && (
              <Text fontSize="sm" color={getAmountColor(mainNetIn)} fontFamily="mono">
                {mainNetIn! >= 0 ? '+' : ''}{summary.main_net_in.rate.toFixed(2)}%
              </Text>
            )}
          </Flex>

          <SimpleGrid columns={2} gap={3}>
            <VStack gap={1} p={2} bg="bg.subtle" borderRadius="md">
              <Text fontSize="xs" color="fg.muted">超大单</Text>
              <Text fontSize="md" fontWeight="bold" color={getAmountColor(superLarge)} fontFamily="mono">
                {formatAmount(superLarge)}
              </Text>
            </VStack>
            <VStack gap={1} p={2} bg="bg.subtle" borderRadius="md">
              <Text fontSize="xs" color="fg.muted">大单</Text>
              <Text fontSize="md" fontWeight="bold" color={getAmountColor(large)} fontFamily="mono">
                {formatAmount(large)}
              </Text>
            </VStack>
            <VStack gap={1} p={2} bg="bg.subtle" borderRadius="md">
              <Text fontSize="xs" color="fg.muted">中单</Text>
              <Text fontSize="md" fontWeight="bold" color={getAmountColor(medium)} fontFamily="mono">
                {formatAmount(medium)}
              </Text>
            </VStack>
            <VStack gap={1} p={2} bg="bg.subtle" borderRadius="md">
              <Text fontSize="xs" color="fg.muted">小单</Text>
              <Text fontSize="md" fontWeight="bold" color={getAmountColor(small)} fontFamily="mono">
                {formatAmount(small)}
              </Text>
            </VStack>
          </SimpleGrid>

          <HStack justify="center" gap={4} pt={2}>
            {summary.close_sh && (
              <VStack gap={0}>
                <Text fontSize="xs" color="fg.muted">上证</Text>
                <Text fontSize="sm" fontWeight="bold" color="fg" fontFamily="mono">
                  {summary.close_sh.toFixed(2)}
                </Text>
                <Text
                  fontSize="xs"
                  color={summary.pct_change_sh! >= 0 ? 'up.500' : 'down.500'}
                  fontFamily="mono"
                >
                  {summary.pct_change_sh! >= 0 ? '+' : ''}{summary.pct_change_sh?.toFixed(2)}%
                </Text>
              </VStack>
            )}
            {summary.close_sz && (
              <VStack gap={0}>
                <Text fontSize="xs" color="fg.muted">深证</Text>
                <Text fontSize="sm" fontWeight="bold" color="fg" fontFamily="mono">
                  {summary.close_sz.toFixed(2)}
                </Text>
                <Text
                  fontSize="xs"
                  color={summary.pct_change_sz! >= 0 ? 'up.500' : 'down.500'}
                  fontFamily="mono"
                >
                  {summary.pct_change_sz! >= 0 ? '+' : ''}{summary.pct_change_sz?.toFixed(2)}%
                </Text>
              </VStack>
            )}
          </HStack>
        </VStack>
      </Card.Body>
    </Card.Root>
  )
}

export default MarketMoneyflowCard
