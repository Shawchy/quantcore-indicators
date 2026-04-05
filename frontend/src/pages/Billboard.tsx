import React, { useEffect, useState } from 'react'
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  Badge,
  Input,
  Button,
  HStack,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
} from '@chakra-ui/react'
import { billboardApi } from '../services/api'

interface BillboardEntry {
  code: string
  name: string
  close_price: number | null
  change_pct: number | null
  turnover_amount: number | null
  net_amount: number | null
  buy_amount: number | null
  sell_amount: number | null
  reason: string | null
  trade_date: string
}

const Billboard: React.FC = () => {
  const [data, setData] = useState<BillboardEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tradeDate, setTradeDate] = useState<string>('')
  
  const bgColor = useColorModeValue('white', 'gray.800')
  const hoverBg = useColorModeValue('gray.50', 'gray.700')

  const fetchBillboard = async (date?: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await billboardApi.getDaily(date)
      if ((res as any).success && (res as any).data) {
        setData((res as any).data)
      } else {
        setData([])
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '获取龙虎榜数据失败'
      setError(errorMessage)
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBillboard()
  }, [])

  const handleSearch = () => {
    fetchBillboard(tradeDate || undefined)
  }

  const formatNumber = (num: number | null, decimals: number = 2) => {
    if (num === null || num === undefined) return '-'
    return num.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  const formatAmount = (amount: number | null) => {
    if (amount === null || amount === undefined) return '-'
    if (Math.abs(amount) >= 100000000) {
      return `${(amount / 100000000).toFixed(2)}亿`
    } else if (Math.abs(amount) >= 10000) {
      return `${(amount / 10000).toFixed(2)}万`
    }
    return amount.toFixed(2)
  }

  const getChangePctColor = (pct: number | null) => {
    if (pct === null) return 'gray'
    if (pct > 0) return 'red'
    if (pct < 0) return 'green'
    return 'gray'
  }

  return (
    <Box p={6} bg={bgColor} borderRadius="lg" shadow="md">
      <VStack spacing={6} align="stretch">
        <Heading size="lg">龙虎榜</Heading>
        
        <HStack>
          <Input
            placeholder="选择交易日期 (YYYY-MM-DD)"
            value={tradeDate}
            onChange={(e) => setTradeDate(e.target.value)}
            maxW="300px"
          />
          <Button colorScheme="blue" onClick={handleSearch}>
            查询
          </Button>
          <Button onClick={() => { setTradeDate(''); fetchBillboard() }}>
            重置
          </Button>
        </HStack>

        {loading && (
          <Box display="flex" justifyContent="center" py={10}>
            <Spinner size="xl" />
          </Box>
        )}

        {error && (
          <Alert status="error">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {!loading && !error && data.length === 0 && (
          <Alert status="info">
            <AlertIcon />
            暂无龙虎榜数据
          </Alert>
        )}

        {!loading && data.length > 0 && (
          <Box overflowX="auto">
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>代码</Th>
                  <Th>名称</Th>
                  <Th isNumeric>收盘价</Th>
                  <Th isNumeric>涨跌幅</Th>
                  <Th isNumeric>成交额</Th>
                  <Th isNumeric>净流入</Th>
                  <Th isNumeric>买入额</Th>
                  <Th isNumeric>卖出额</Th>
                  <Th>上榜原因</Th>
                </Tr>
              </Thead>
              <Tbody>
                {data.map((item, index) => (
                  <Tr key={`${item.code}-${index}`} _hover={{ bg: hoverBg }}>
                    <Td fontWeight="medium">{item.code}</Td>
                    <Td>{item.name}</Td>
                    <Td isNumeric>{formatNumber(item.close_price)}</Td>
                    <Td isNumeric>
                      <Badge colorScheme={getChangePctColor(item.change_pct)}>
                        {formatNumber(item.change_pct)}%
                      </Badge>
                    </Td>
                    <Td isNumeric>{formatAmount(item.turnover_amount)}</Td>
                    <Td isNumeric>
                      <Badge colorScheme={item.net_amount && item.net_amount > 0 ? 'red' : 'green'}>
                        {formatAmount(item.net_amount)}
                      </Badge>
                    </Td>
                    <Td isNumeric>{formatAmount(item.buy_amount)}</Td>
                    <Td isNumeric>{formatAmount(item.sell_amount)}</Td>
                    <Td maxW="200px" isTruncated title={item.reason || ''}>
                      <Text fontSize="sm">{item.reason || '-'}</Text>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        )}

        {!loading && data.length > 0 && (
          <Text fontSize="sm" color="gray.500">
            共 {data.length} 条数据
          </Text>
        )}
      </VStack>
    </Box>
  )
}

export default Billboard
