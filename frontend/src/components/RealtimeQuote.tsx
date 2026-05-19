/**
 * 实时盘口组件
 * 显示买一卖一、五档盘口等实时数据
 */
import React from 'react'
import { 
  Box, Flex, Text, Table, Stat, Spinner, Alert as ChakraAlert
} from '@chakra-ui/react'
import type { RealtimeQuoteData } from '../types'

interface RealtimeQuoteProps {
  data: RealtimeQuoteData | null
  loading: boolean
  error: string | null
}

const RealtimeQuote: React.FC<RealtimeQuoteProps> = ({ data, loading, error }) => {
  // 格式化价格
  const formatPrice = (price: number) => {
    if (!price || price === 0) return '-'
    return price.toFixed(2)
  }

  // 格式化成交量
  const formatVolume = (volume: number) => {
    if (!volume || volume === 0) return '-'
    if (volume >= 10000) {
      return `${(volume / 10000).toFixed(1)}万`
    }
    return volume.toFixed(0)
  }

  // 渲染五档盘口行
  const renderBidAskRow = (item: { price: number; volume: number } | null, index: number, type: 'bid' | 'ask') => {
    const color = type === 'bid' ? 'red.500' : 'green.500'
    const bgColor = type === 'bid' ? 'red.50' : 'green.50'
    
    return (
      <Table.Row key={`${type}-${index}`} bg={bgColor}>
        <Table.Cell 
          color={color} 
          fontWeight="bold" 
          fontFamily="mono"
          textAlign="right"
          py={2}
          px={3}
        >
          {item && formatPrice(item.price)}
        </Table.Cell>
        <Table.Cell 
          color="gray.600" 
          fontFamily="mono"
          textAlign="right"
          py={2}
          px={3}
        >
          {item && formatVolume(item.volume)}
        </Table.Cell>
      </Table.Row>
    )
  }

  if (loading) {
    return (
      <Flex justify="center" align="center" h="200px">
        <Spinner size="md" />
      </Flex>
    )
  }

  if (error) {
    return (
      <ChakraAlert.Root status="error" size="sm" borderRadius="md">
        <ChakraAlert.Indicator />
        <Text fontSize="xs">{error}</Text>
      </ChakraAlert.Root>
    )
  }

  if (!data) {
    return (
      <Text fontSize="sm" color="gray.500" textAlign="center" py={8}>
        暂无实时盘口数据
      </Text>
    )
  }

  const { quote, bid_ask } = data

  return (
    <Box>
      {/* 实时价格 */}
      <Flex justify="space-between" align="center" mb={4} pb={4} borderBottom="1px" borderColor="gray.200">
        <Box>
          <Text fontSize="xs" color="gray.600" mb={1}>实时价格</Text>
          <Stat.Root>
            <Stat.ValueText 
              fontSize="3xl" 
              fontWeight="bold" 
              color={quote?.change_pct >= 0 ? 'red.500' : 'green.500'}
              fontFamily="mono"
            >
              {formatPrice(quote?.price)}
            </Stat.ValueText>
            <Stat.HelpText 
              mb={0} 
              fontSize="sm" 
              fontWeight="bold"
              color={quote?.change_pct >= 0 ? 'red.500' : 'green.500'}
            >
              {quote?.change_pct != null ? (quote.change_pct >= 0 ? '+' : '') : ''}
              {quote?.change_pct != null ? quote.change_pct.toFixed(2) : '-'}% 
              ({quote?.change != null ? (quote.change >= 0 ? '+' : '') : ''}
              {quote?.change != null ? quote.change.toFixed(2) : '-'})
            </Stat.HelpText>
          </Stat.Root>
        </Box>

        <Box textAlign="right">
          <Text fontSize="xs" color="gray.600" mb={1}>更新时间</Text>
          <Text fontSize="sm" fontWeight="medium" color="gray.700">
            {data?.update_time || '-'}
          </Text>
        </Box>
      </Flex>

      {/* 基本行情 */}
      <Flex gap={3} mb={4} flexWrap="wrap">
        {[
          { label: '今开', value: formatPrice(quote?.open) },
          { label: '最高', value: formatPrice(quote?.high), color: 'red.500' },
          { label: '最低', value: formatPrice(quote?.low), color: 'green.500' },
          { label: '昨收', value: formatPrice(quote?.close) },
          { label: '成交量', value: formatVolume(quote?.volume) },
          { label: '成交额', value: quote?.amount != null ? (quote.amount >= 100000000 ? `${(quote.amount / 100000000).toFixed(2)}亿` : `${(quote.amount / 10000).toFixed(0)}万`) : '-' },
        ].map((item, index) => (
          <Box 
            key={item.label || index} 
            flex="1" 
            minW="80px"
            bg="gray.50" 
            p={2} 
            borderRadius="md"
            textAlign="center"
          >
            <Text fontSize="xs" color="gray.600" mb={1}>{item.label}</Text>
            <Text 
              fontSize="sm" 
              fontWeight="bold" 
              color={item.color || 'gray.700'}
              fontFamily="mono"
            >
              {item.value}
            </Text>
          </Box>
        ))}
      </Flex>

      {/* 五档盘口 */}
      {bid_ask && bid_ask.bid.length > 0 && (
        <Flex gap={4}>
          {/* 买盘 */}
          <Box flex={1} bg="gray.50" borderRadius="md" p={3}>
            <Text fontSize="xs" fontWeight="bold" color="red.600" mb={2} textAlign="center">
              买盘
            </Text>
            <Table.Root size="sm">
              <Table.Body>
                {bid_ask.bid.slice(0, 5).map((item, index) => (
                  renderBidAskRow(item, index, 'bid')
                ))}
              </Table.Body>
            </Table.Root>
          </Box>

          {/* 卖盘 */}
          <Box flex={1} bg="gray.50" borderRadius="md" p={3}>
            <Text fontSize="xs" fontWeight="bold" color="green.600" mb={2} textAlign="center">
              卖盘
            </Text>
            <Table.Root size="sm">
              <Table.Body>
                {bid_ask.ask.slice(0, 5).map((item, index) => (
                  renderBidAskRow(item, index, 'ask')
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
        </Flex>
      )}

      {/* 数据说明 */}
      <Text fontSize="xs" color="gray.500" textAlign="center" mt={3}>
        数据来源：{data?.data_source === 'sina' ? '新浪' : '东方财富'} | 
        获取耗时：{data?.fetch_time || '-'}秒
      </Text>
    </Box>
  )
}

export default React.memo(RealtimeQuote)
