import React, { useEffect, useState } from 'react'
import { Alert, Badge, Box, Button, HStack, Heading, Input, Spinner, Table, Text, VStack } from '@chakra-ui/react'
import { useColorModeValue } from '../components/ui/color-mode'
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
      <VStack gap={6} align="stretch">
        <Heading size="lg">龙虎榜</Heading>
        
        <HStack>
          <Input
            placeholder="选择交易日期 (YYYY-MM-DD)"
            value={tradeDate}
            onChange={(e) => setTradeDate(e.target.value)}
            maxW="300px"
          />
          <Button colorPalette="blue" onClick={handleSearch}>
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
          <Alert.Root status="error">
            <Alert.Indicator />
            {error}
          </Alert.Root>
        )}

        {!loading && !error && data.length === 0 && (
          <Alert.Root status="info">
            <Alert.Indicator />
            暂无龙虎榜数据
          </Alert.Root>
        )}

        {!loading && data.length > 0 && (
          <Box overflowX="auto">
            <Table.Root  size="sm">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>代码</Table.ColumnHeader>
                  <Table.ColumnHeader>名称</Table.ColumnHeader>
                  <Table.ColumnHeader >收盘价</Table.ColumnHeader>
                  <Table.ColumnHeader >涨跌幅</Table.ColumnHeader>
                  <Table.ColumnHeader >成交额</Table.ColumnHeader>
                  <Table.ColumnHeader >净流入</Table.ColumnHeader>
                  <Table.ColumnHeader >买入额</Table.ColumnHeader>
                  <Table.ColumnHeader >卖出额</Table.ColumnHeader>
                  <Table.ColumnHeader>上榜原因</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {data.map((item, index) => (
                  <Table.Row key={`${item.code}-${index}`} _hover={{ bg: hoverBg }}>
                    <Table.Cell fontWeight="medium">{item.code}</Table.Cell>
                    <Table.Cell>{item.name}</Table.Cell>
                    <Table.Cell >{formatNumber(item.close_price)}</Table.Cell>
                    <Table.Cell >
                      <Badge colorPalette={getChangePctColor(item.change_pct)}>
                        {formatNumber(item.change_pct)}%
                      </Badge>
                    </Table.Cell>
                    <Table.Cell >{formatAmount(item.turnover_amount)}</Table.Cell>
                    <Table.Cell >
                      <Badge colorPalette={item.net_amount && item.net_amount > 0 ? 'red' : 'green'}>
                        {formatAmount(item.net_amount)}
                      </Badge>
                    </Table.Cell>
                    <Table.Cell >{formatAmount(item.buy_amount)}</Table.Cell>
                    <Table.Cell >{formatAmount(item.sell_amount)}</Table.Cell>
                    <Table.Cell maxW="200px" truncate title={item.reason || ''}>
                      <Text fontSize="sm">{item.reason || '-'}</Text>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
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
