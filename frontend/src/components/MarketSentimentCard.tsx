/**
 * 市场情绪卡片组件
 * 显示市场情绪状态和涨跌统计
 */
import React from 'react'
import { Box, Stat, StatLabel, StatNumber, StatHelpText, Flex, Badge, Icon } from '@chakra-ui/react'
import { ArrowUpIcon, ArrowDownIcon } from '@chakra-ui/icons'
import type { MarketStats, MarketSentiment } from '../types'

interface MarketSentimentCardProps {
  stats: MarketStats
  sentiment: MarketSentiment
  totalStocks: number
}

const MarketSentimentCard: React.FC<MarketSentimentCardProps> = ({ stats, sentiment, totalStocks }) => {
  // 根据情绪分数设置颜色
  const getSentimentColor = (score: number) => {
    const colors = {
      1: 'red',    // 强势下跌
      2: 'orange', // 震荡下跌
      3: 'gray',   // 震荡整理
      4: 'blue',   // 震荡上涨
      5: 'green'   // 强势上涨
    }
    return colors[score as keyof typeof colors] || 'gray'
  }

  const sentimentColor = getSentimentColor(sentiment.score)

  // 格式化情绪文本
  const sentimentEmojis = {
    5: '📈📈',
    4: '📈',
    3: '➖',
    2: '📉',
    1: '📉📉'
  }

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
        <Stat>
          <StatLabel fontSize="lg" fontWeight="bold" color="gray.600">
            市场情绪
          </StatLabel>
          <Flex align="center" gap={2}>
            <StatNumber fontSize="2xl" fontWeight="bold" color={`${sentimentColor}.500`}>
              {sentimentEmojis[sentiment.score as keyof typeof sentimentEmojis] || '➖'} {sentiment.text}
            </StatNumber>
            <Badge colorScheme={sentimentColor} fontSize="sm" px={2} py={1}>
              强弱度：{sentiment.score}/5
            </Badge>
          </Flex>
          <StatHelpText mb={0}>
            涨跌比：{sentiment.up_down_ratio.toFixed(2)}
          </StatHelpText>
        </Stat>
      </Flex>

      <Flex gap={4} mt={4}>
        <Stat flex={1} bg={`${sentimentColor}.50`} p={3} borderRadius="md">
          <Flex align="center" gap={2}>
            <Icon as={ArrowUpIcon} color={`${sentimentColor}.500`} />
            <StatLabel color={`${sentimentColor}.700`} fontWeight="medium">上涨</StatLabel>
          </Flex>
          <StatNumber fontSize="2xl" fontWeight="bold" color={`${sentimentColor}.600`}>
            {stats.up_count.toLocaleString()}
          </StatNumber>
          <StatHelpText mb={0} fontSize="sm" color={`${sentimentColor}.600`}>
            {stats.up_ratio.toFixed(1)}%
          </StatHelpText>
        </Stat>

        <Stat flex={1} bg="red.50" p={3} borderRadius="md">
          <Flex align="center" gap={2}>
            <Icon as={ArrowDownIcon} color="red.500" />
            <StatLabel color="red.700" fontWeight="medium">下跌</StatLabel>
          </Flex>
          <StatNumber fontSize="2xl" fontWeight="bold" color="red.600">
            {stats.down_count.toLocaleString()}
          </StatNumber>
          <StatHelpText mb={0} fontSize="sm" color="red.600">
            {stats.down_ratio.toFixed(1)}%
          </StatHelpText>
        </Stat>

        <Stat flex={1} bg="gray.50" p={3} borderRadius="md">
          <StatLabel color="gray.700" fontWeight="medium">平盘</StatLabel>
          <StatNumber fontSize="2xl" fontWeight="bold" color="gray.600">
            {stats.flat_count.toLocaleString()}
          </StatNumber>
          <StatHelpText mb={0} fontSize="sm" color="gray.600">
            总计：{totalStocks.toLocaleString()}
          </StatHelpText>
        </Stat>
      </Flex>

      <Flex gap={3} mt={4} justify="center">
        <Badge colorScheme="red" fontSize="xs" px={3} py={2} borderRadius="full">
          涨停：{stats.limit_up_count}家
        </Badge>
        <Badge colorScheme="green" fontSize="xs" px={3} py={2} borderRadius="full">
          跌停：{stats.limit_down_count}家
        </Badge>
      </Flex>
    </Box>
  )
}

export default MarketSentimentCard
