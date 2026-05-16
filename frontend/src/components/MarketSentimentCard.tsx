/**
 * 市场情绪卡片组件
 * 显示市场情绪状态和涨跌统计
 */
import React, { useMemo, memo } from 'react'
import { Badge, Box, Flex, Icon, Stat } from '@chakra-ui/react'
import { FiArrowDown, FiArrowUp } from 'react-icons/fi'
import type { MarketStats, MarketSentiment } from '../types'

interface MarketSentimentCardProps {
  stats: MarketStats
  sentiment: MarketSentiment
  totalStocks: number
}

const MarketSentimentCard: React.FC<MarketSentimentCardProps> = memo(({ stats, sentiment, totalStocks }) => {
  // 使用 useMemo 缓存情绪颜色
  const sentimentColor = useMemo(() => {
    const colors = {
      1: 'red',    // 强势下跌
      2: 'orange', // 震荡下跌
      3: 'gray',   // 震荡整理
      4: 'blue',   // 震荡上涨
      5: 'green'   // 强势上涨
    }
    return colors[sentiment.score as keyof typeof colors] || 'gray'
  }, [sentiment.score])

  // 使用 useMemo 缓存情绪文本
  const sentimentEmoji = useMemo(() => {
    const sentimentEmojis = {
      5: '📈📈',
      4: '📈',
      3: '➖',
      2: '📉',
      1: '📉📉'
    }
    return sentimentEmojis[sentiment.score as keyof typeof sentimentEmojis] || '➖'
  }, [sentiment.score])

  return (
    <Box 
      bg="white" 
      borderRadius="lg" 
      boxShadow="md" 
      p={6}
      borderWidth="1px"
      borderColor={`${sentimentColor}.200`}
    >
      <Flex justify="space-between" align="center" mb={4}>
        <Stat.Root>
          <Stat.Label fontSize="lg" fontWeight="bold" color="gray.600">
            市场情绪
          </Stat.Label>
          <Flex align="center" gap={2}>
            <Stat.ValueText fontSize="2xl" fontWeight="bold" color={`${sentimentColor}.500`}>
              {sentimentEmoji} {sentiment.text}
            </Stat.ValueText>
            <Badge colorPalette={sentimentColor} fontSize="sm" px={2} py={1}>
              强弱度：{sentiment.score}/5
            </Badge>
          </Flex>
          <Stat.HelpText mb={0}>
            涨跌比：{sentiment.up_down_ratio.toFixed(2)}
          </Stat.HelpText>
        </Stat.Root>
      </Flex>

      <Flex gap={4} mt={4}>
        <Stat.Root flex={1} bg={`${sentimentColor}.50`} p={3} borderRadius="md">
          <Flex align="center" gap={2}>
            <Icon as={FiArrowUp} color={`${sentimentColor}.500`} />
            <Stat.Label color={`${sentimentColor}.700`} fontWeight="medium">上涨</Stat.Label>
          </Flex>
          <Stat.ValueText fontSize="2xl" fontWeight="bold" color={`${sentimentColor}.600`}>
            {stats.up_count.toLocaleString()}
          </Stat.ValueText>
          <Stat.HelpText mb={0} fontSize="sm" color={`${sentimentColor}.600`}>
            {stats.up_ratio.toFixed(1)}%
          </Stat.HelpText>
        </Stat.Root>

        <Stat.Root flex={1} bg="red.50" p={3} borderRadius="md">
          <Flex align="center" gap={2}>
            <Icon as={FiArrowDown} color="red.500" />
            <Stat.Label color="red.700" fontWeight="medium">下跌</Stat.Label>
          </Flex>
          <Stat.ValueText fontSize="2xl" fontWeight="bold" color="red.600">
            {stats.down_count.toLocaleString()}
          </Stat.ValueText>
          <Stat.HelpText mb={0} fontSize="sm" color="red.600">
            {stats.down_ratio.toFixed(1)}%
          </Stat.HelpText>
        </Stat.Root>

        <Stat.Root flex={1} bg="gray.50" p={3} borderRadius="md">
          <Stat.Label color="gray.700" fontWeight="medium">平盘</Stat.Label>
          <Stat.ValueText fontSize="2xl" fontWeight="bold" color="gray.600">
            {stats.flat_count.toLocaleString()}
          </Stat.ValueText>
          <Stat.HelpText mb={0} fontSize="sm" color="gray.600">
            总计：{totalStocks.toLocaleString()}
          </Stat.HelpText>
        </Stat.Root>
      </Flex>

      <Flex gap={3} mt={4} justify="center">
        <Badge colorPalette="red" fontSize="xs" px={3} py={2} borderRadius="full">
          涨停：{stats.limit_up_count}家
        </Badge>
        <Badge colorPalette="green" fontSize="xs" px={3} py={2} borderRadius="full">
          跌停：{stats.limit_down_count}家
        </Badge>
      </Flex>
    </Box>
  )
})

MarketSentimentCard.displayName = 'MarketSentimentCard'

export default MarketSentimentCard
