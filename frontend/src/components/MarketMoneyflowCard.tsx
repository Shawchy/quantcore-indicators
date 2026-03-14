import { Card, CardBody, CardHeader, Heading, VStack, HStack, Text, Flex, Badge, Spinner, SimpleGrid } from '@chakra-ui/react'
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
      <Card>
        <CardBody>
          <Flex justify="center" align="center" h="200px">
            <Spinner size="lg" color="brand.400" />
          </Flex>
        </CardBody>
      </Card>
    )
  }

  const summary = summaryData?.data?.data

  if (!summary) {
    return (
      <Card>
        <CardBody>
          <Text color="light.textMuted" textAlign="center">暂无资金流向数据</Text>
        </CardBody>
      </Card>
    )
  }

  const mainNetIn = summary.main_net_in?.amount
  const superLarge = summary.super_large?.amount
  const large = summary.large?.amount
  const medium = summary.medium?.amount
  const small = summary.small?.amount

  return (
    <Card>
      <CardHeader pb={2}>
        <Flex justify="space-between" align="center">
          <Heading size="sm" color="light.text">大盘资金流向</Heading>
          {summary.trade_date && (
            <Badge fontSize="xs" colorScheme="blue">
              {summary.trade_date}
            </Badge>
          )}
        </Flex>
      </CardHeader>
      <CardBody pt={2}>
        <VStack spacing={4} align="stretch">
          <Flex justify="center" align="center" direction="column" py={2}>
            <Text fontSize="xs" color="light.textSecondary" mb={1}>主力净流入</Text>
            <HStack spacing={2}>
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

          <SimpleGrid columns={2} spacing={3}>
            <VStack spacing={1} p={2} bg="light.bgSecondary" borderRadius="md">
              <Text fontSize="xs" color="light.textSecondary">超大单</Text>
              <Text fontSize="md" fontWeight="bold" color={getAmountColor(superLarge)} fontFamily="mono">
                {formatAmount(superLarge)}
              </Text>
            </VStack>
            <VStack spacing={1} p={2} bg="light.bgSecondary" borderRadius="md">
              <Text fontSize="xs" color="light.textSecondary">大单</Text>
              <Text fontSize="md" fontWeight="bold" color={getAmountColor(large)} fontFamily="mono">
                {formatAmount(large)}
              </Text>
            </VStack>
            <VStack spacing={1} p={2} bg="light.bgSecondary" borderRadius="md">
              <Text fontSize="xs" color="light.textSecondary">中单</Text>
              <Text fontSize="md" fontWeight="bold" color={getAmountColor(medium)} fontFamily="mono">
                {formatAmount(medium)}
              </Text>
            </VStack>
            <VStack spacing={1} p={2} bg="light.bgSecondary" borderRadius="md">
              <Text fontSize="xs" color="light.textSecondary">小单</Text>
              <Text fontSize="md" fontWeight="bold" color={getAmountColor(small)} fontFamily="mono">
                {formatAmount(small)}
              </Text>
            </VStack>
          </SimpleGrid>

          <HStack justify="center" spacing={4} pt={2}>
            {summary.close_sh && (
              <VStack spacing={0}>
                <Text fontSize="xs" color="light.textSecondary">上证</Text>
                <Text fontSize="sm" fontWeight="bold" color="light.text" fontFamily="mono">
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
              <VStack spacing={0}>
                <Text fontSize="xs" color="light.textSecondary">深证</Text>
                <Text fontSize="sm" fontWeight="bold" color="light.text" fontFamily="mono">
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
      </CardBody>
    </Card>
  )
}

export default MarketMoneyflowCard
