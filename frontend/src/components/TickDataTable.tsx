/**
 * 成交明细组件
 * 显示实时分笔成交数据
 */
import React from 'react'
import { 
  Box,
  Flex,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
} from '@chakra-ui/react'
import type { TickData } from '../types'

interface TickDataProps {
  data: TickData | null
  loading: boolean
  error: string | null
}

const TickDataTable: React.FC<TickDataProps> = ({ data, loading, error }) => {
  // 格式化时间
  const formatTime = (time: string) => {
    return time || '-'
  }

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

  // 获取买卖类型颜色
  const getTypeColor = (type: string) => {
    if (type === '买盘') return 'red'
    if (type === '卖盘') return 'green'
    return 'gray'
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
      <Alert status="error" size="sm" borderRadius="md">
        <AlertIcon boxSize={3} />
        <Text fontSize="xs">{error}</Text>
      </Alert>
    )
  }

  if (!data || data.tick_data.length === 0) {
    return (
      <Text fontSize="sm" color="gray.500" textAlign="center" py={8}>
        暂无成交明细数据
      </Text>
    )
  }

  return (
    <Box>
      {/* 统计信息 */}
      <Flex gap={3} mb={4} flexWrap="wrap">
        <Badge colorScheme="red" fontSize="xs" px={3} py={2} borderRadius="full">
          买盘：{data.stats.buy_count}笔 ({data.stats.buy_ratio}%)
        </Badge>
        <Badge colorScheme="green" fontSize="xs" px={3} py={2} borderRadius="full">
          卖盘：{data.stats.sell_count}笔 ({data.stats.sell_ratio}%)
        </Badge>
        <Badge colorScheme="gray" fontSize="xs" px={3} py={2} borderRadius="full">
          中性：{data.stats.neutral_count}笔
        </Badge>
        <Badge colorScheme="blue" fontSize="xs" px={3} py={2} borderRadius="full">
          总笔数：{data.total_records}
        </Badge>
      </Flex>

      {/* 成交明细表格 */}
      <TableContainer maxH="400px" overflowY="auto">
        <Table size="sm" variant="simple">
          <Thead position="sticky" top={0} bg="white" zIndex={1}>
            <Tr>
              <Th 
                fontSize="xs" 
                color="gray.600" 
                fontWeight="medium"
                py={2}
                px={3}
              >
                时间
              </Th>
              <Th 
                fontSize="xs" 
                color="gray.600" 
                fontWeight="medium"
                isNumeric
                py={2}
                px={3}
              >
                价格
              </Th>
              <Th 
                fontSize="xs" 
                color="gray.600" 
                fontWeight="medium"
                isNumeric
                py={2}
                px={3}
              >
                成交量
              </Th>
              <Th 
                fontSize="xs" 
                color="gray.600" 
                fontWeight="medium"
                isNumeric
                py={2}
                px={3}
              >
                成交额
              </Th>
              <Th 
                fontSize="xs" 
                color="gray.600" 
                fontWeight="medium"
                isNumeric
                py={2}
                px={3}
              >
                类型
              </Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.tick_data.slice(-50).reverse().map((tick, index) => (
              <Tr 
                key={index}
                _hover={{ bg: 'gray.50' }}
              >
                <Td 
                  fontSize="xs" 
                  color="gray.700"
                  fontFamily="mono"
                  py={2}
                  px={3}
                >
                  {formatTime(tick.time)}
                </Td>
                <Td 
                  fontSize="xs" 
                  fontWeight="bold"
                  color={tick.type === '买盘' ? 'red.500' : tick.type === '卖盘' ? 'green.500' : 'gray.500'}
                  fontFamily="mono"
                  isNumeric
                  py={2}
                  px={3}
                >
                  {formatPrice(tick.price)}
                </Td>
                <Td 
                  fontSize="xs" 
                  color="gray.700"
                  fontFamily="mono"
                  isNumeric
                  py={2}
                  px={3}
                >
                  {formatVolume(tick.volume)}
                </Td>
                <Td 
                  fontSize="xs" 
                  color="gray.600"
                  fontFamily="mono"
                  isNumeric
                  py={2}
                  px={3}
                >
                  {tick.amount ? `${(tick.amount / 10000).toFixed(1)}万` : '-'}
                </Td>
                <Td isNumeric py={2} px={3}>
                  <Badge 
                    colorScheme={getTypeColor(tick.type)} 
                    fontSize="xs" 
                    px={2} 
                    py={1}
                    borderRadius="md"
                  >
                    {tick.type}
                  </Badge>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </TableContainer>

      {/* 数据说明 */}
      <Text fontSize="xs" color="gray.500" textAlign="center" mt={3}>
        显示最近 50 条成交记录 | 数据来源：{data.data_source === 'sina' ? '新浪' : '东方财富'}
      </Text>
    </Box>
  )
}

export default TickDataTable
