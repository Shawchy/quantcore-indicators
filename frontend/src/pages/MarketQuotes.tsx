import React, { useState } from 'react'
import { Alert, Badge, Box, Button, Card, Flex, HStack, Heading, Input, InputGroup, NativeSelect, SimpleGrid, Spinner, Stat, Table, Text, VStack } from '@chakra-ui/react'
import { useColorModeValue } from '../components/ui/color-mode'
import { FiSearch } from 'react-icons/fi'
import { useQuery } from '@tanstack/react-query'

interface MarketQuote {
  code: string
  name: string
  change_pct: number | null
  price: number | null
  high: number | null
  low: number | null
  open: number | null
  change: number | null
  turnover_rate: number | null
  volume_ratio: number | null
  pe_ratio: number | null
  volume: number | null
  amount: number | null
  prev_close: number | null
  total_market_cap: number | null
  float_market_cap: number | null
  market_type: string | null
}

// 市场类型定义（带稳定性评级）
const MARKET_TYPES = [
  { value: '', label: '沪深 A 股（默认）', stability: 5 },
  { value: 'ETF', label: 'ETF 基金', stability: 5 },
  { value: 'LOF', label: 'LOF 基金', stability: 5 },
  { value: '创业板', label: '创业板', stability: 4 },
  { value: '科创板', label: '科创板', stability: 4 },
  { value: '沪深系列指数', label: '沪深系列指数', stability: 4 },
  { value: '上证系列指数', label: '上证系列指数', stability: 4 },
  { value: '深证系列指数', label: '深证系列指数', stability: 4 },
  { value: '行业板块', label: '行业板块', stability: 4 },
  { value: '概念板块', label: '概念板块', stability: 4 },
  { value: '可转债', label: '可转债', stability: 4 },
  { value: '沪 A', label: '沪 A', stability: 4 },
  { value: '深 A', label: '深 A', stability: 4 },
  { value: '北 A', label: '北 A', stability: 3 },
  { value: '港股', label: '港股', stability: 3 },
  { value: '美股', label: '美股', stability: 3 },
]

const MarketQuotes: React.FC = () => {
  const [selectedType, setSelectedType] = useState<string>('') // 默认为空（沪深 A 股）
  const [searchTerm, setSearchTerm] = useState('')
  const [limit, setLimit] = useState<number>(100) // 默认显示 100 条
  
  const bgColor = useColorModeValue('white', 'gray.800')
  const hoverBg = useColorModeValue('gray.50', 'gray.700')
  const cardBg = useColorModeValue('gray.50', 'gray.700')

  // 使用 React Query 获取市场数据
  const { 
    data: marketData, 
    isLoading: loading, 
    error: queryError,
    refetch 
  } = useQuery<MarketQuote[]>({
    queryKey: ['marketQuotes', selectedType],
    queryFn: async () => {
      // 暂时返回空数组，等待 API 实现
      console.log('获取市场报价:', selectedType)
      return []
    },
    staleTime: 30000, // 30 秒内使用缓存
    gcTime: 120000,   // 缓存 2 分钟
    refetchOnWindowFocus: false,
  })

  const handleRefresh = () => {
    refetch()
  }

  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedType(e.target.value)
  }

  const formatNumber = (num: number | null, decimals: number = 2) => {
    if (num === null || num === undefined || isNaN(num)) return '-'
    return num.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  const formatAmount = (amount: number | null) => {
    if (amount === null || amount === undefined || isNaN(amount)) return '-'
    if (Math.abs(amount) >= 100000000) {
      return `${(amount / 100000000).toFixed(2)}亿`
    } else if (Math.abs(amount) >= 10000) {
      return `${(amount / 10000).toFixed(2)}万`
    }
    return amount.toFixed(2)
  }

  const formatMarketCap = (cap: number | null) => {
    if (cap === null || cap === undefined || isNaN(cap)) return '-'
    if (Math.abs(cap) >= 100000000) {
      return `${(cap / 100000000).toFixed(2)}亿`
    } else if (Math.abs(cap) >= 10000) {
      return `${(cap / 10000).toFixed(2)}万`
    }
    return cap.toFixed(2)
  }

  const getChangePctColor = (pct: number | null) => {
    if (pct === null || isNaN(pct)) return 'gray'
    if (pct > 0) return 'red'
    if (pct < 0) return 'green'
    return 'gray'
  }

  // 计算市场统计数据
  const calculateStats = (quotes: MarketQuote[]) => {
    if (!quotes || quotes.length === 0) return null
    
    const up = quotes.filter(q => q.change_pct && q.change_pct > 0).length
    const down = quotes.filter(q => q.change_pct && q.change_pct < 0).length
    const flat = quotes.filter(q => q.change_pct && q.change_pct === 0).length
    const total = quotes.length
    const avgPct = quotes.reduce((sum, q) => sum + (q.change_pct || 0), 0) / total
    
    return {
      total,
      up,
      down,
      flat,
      upRatio: ((up / total) * 100).toFixed(2),
      downRatio: ((down / total) * 100).toFixed(2),
      avgPct: avgPct.toFixed(2),
    }
  }

  // 过滤和限制数据
  const filteredData = (marketData || []).filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.code.includes(searchTerm)
  ).slice(0, limit)

  const stats = calculateStats(marketData || [])
  const currentTypeName = MARKET_TYPES.find(t => t.value === selectedType)?.label || '沪深 A 股（默认）'

  return (
    <Box p={6} bg={bgColor} borderRadius="lg" shadow="md">
      <VStack gap={6} align="stretch">
        {/* 标题和刷新按钮 */}
        <Flex justify="space-between" align="center" w="100%">
          <Heading size="lg">📊 市场实时行情</Heading>
          <Button
            size="sm"
            colorPalette="blue"
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Flex>

        {/* 市场统计卡片 */}
        {stats && (
          <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
            <Card.Root bg={cardBg}>
              <Card.Body>
                <Stat.Root>
                  <Stat.Label fontSize="sm" color="gray.600">股票总数</Stat.Label>
                  <Stat.ValueText fontSize="2xl" fontWeight="bold">{stats.total}</Stat.ValueText>
                  <Stat.HelpText mb={0} fontSize="xs" color="gray.500">
                    {currentTypeName}
                  </Stat.HelpText>
                </Stat.Root>
              </Card.Body>
            </Card.Root>
            
            <Card.Root bg={cardBg}>
              <Card.Body>
                <Stat.Root>
                  <Stat.Label fontSize="sm" color="gray.600">上涨家数</Stat.Label>
                  <Stat.ValueText fontSize="2xl" fontWeight="bold" color="red.500">
                    {stats.up}
                  </Stat.ValueText>
                  <Stat.HelpText mb={0} fontSize="xs" color="gray.500">
                    占比 {stats.upRatio}%
                  </Stat.HelpText>
                </Stat.Root>
              </Card.Body>
            </Card.Root>
            
            <Card.Root bg={cardBg}>
              <Card.Body>
                <Stat.Root>
                  <Stat.Label fontSize="sm" color="gray.600">下跌家数</Stat.Label>
                  <Stat.ValueText fontSize="2xl" fontWeight="bold" color="green.500">
                    {stats.down}
                  </Stat.ValueText>
                  <Stat.HelpText mb={0} fontSize="xs" color="gray.500">
                    占比 {stats.downRatio}%
                  </Stat.HelpText>
                </Stat.Root>
              </Card.Body>
            </Card.Root>
            
            <Card.Root bg={cardBg}>
              <Card.Body>
                <Stat.Root>
                  <Stat.Label fontSize="sm" color="gray.600">平均涨跌幅</Stat.Label>
                  <Stat.ValueText 
                    fontSize="2xl" 
                    fontWeight="bold"
                    color={parseFloat(stats.avgPct) > 0 ? 'red.500' : 'green.500'}
                  >
                    {parseFloat(stats.avgPct) > 0 ? '+' : ''}{stats.avgPct}%
                  </Stat.ValueText>
                  <Stat.HelpText mb={0} fontSize="xs" color="gray.500">
                    平盘 {stats.flat}家
                  </Stat.HelpText>
                </Stat.Root>
              </Card.Body>
            </Card.Root>
          </SimpleGrid>
        )}

        {/* 市场类型选择和搜索 */}
        <HStack gap={4} wrap="wrap">
          {/* 市场类型下拉框 */}
          <Box>
            <Text fontSize="sm" fontWeight="bold" mb={2} color="gray.600">
              市场类型：
            </Text>
            <NativeSelect.Root><NativeSelect.Field
              value={selectedType}
              onChange={handleTypeChange}
              
              colorPalette="blue"
            >
              {MARKET_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                  {type.stability === 5 && ' ⭐⭐⭐⭐⭐'}
                  {type.stability === 4 && ' ⭐⭐⭐⭐'}
                  {type.stability === 3 && ' ⭐⭐⭐'}
                </option>
              ))}
            </NativeSelect.Field></NativeSelect.Root>
          </Box>

          {/* 显示数量选择 */}
          <Box>
            <Text fontSize="sm" fontWeight="bold" mb={2} color="gray.600">
              显示数量：
            </Text>
            <NativeSelect.Root size="md"><NativeSelect.Field
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            >
              <option value={50}>50 条</option>
              <option value={100}>100 条</option>
              <option value={200}>200 条</option>
              <option value={500}>500 条</option>
              <option value={1000}>1000 条</option>
            </NativeSelect.Field></NativeSelect.Root>
          </Box>

          {/* 搜索框 */}
          <Box flex={1} minW="200px">
            <Text fontSize="sm" fontWeight="bold" mb={2} color="gray.600">
              搜索：
            </Text>
            <InputGroup startElement={<FiSearch color="gray.400" />}>
              <Input
                placeholder="输入代码或名称"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                size="md"
              />
            </InputGroup>
          </Box>
        </HStack>

        {/* 加载状态 */}
        {loading && (
          <Box display="flex" justifyContent="center" py={10}>
            <Spinner size="xl" borderWidth="4px"  color="blue.500" />
          </Box>
        )}

        {/* 错误提示 */}
        {queryError && (
          <Alert.Root status="error" borderRadius="lg">
            <Alert.Indicator />
            获取数据失败：{(queryError as Error).message}
            <Button
              size="sm"
              colorPalette="red"
              ml={4}
              onClick={handleRefresh}
            >
              重试
            </Button>
          </Alert.Root>
        )}

        {/* 空数据提示 */}
        {!loading && !queryError && (!marketData || marketData.length === 0) && (
          <Alert.Root status="info" borderRadius="lg">
            <Alert.Indicator />
            暂无市场实时行情数据，请尝试切换市场类型或刷新
          </Alert.Root>
        )}

        {/* 数据表格 */}
        {!loading && filteredData.length > 0 && (
          <Box overflowX="auto" borderRadius="lg" boxShadow="md">
            <Table.Root  size="sm">
              <Table.Header bg="gray.50">
                <Table.Row>
                  <Table.ColumnHeader>代码</Table.ColumnHeader>
                  <Table.ColumnHeader>名称</Table.ColumnHeader>
                  <Table.ColumnHeader >最新价</Table.ColumnHeader>
                  <Table.ColumnHeader >涨跌幅</Table.ColumnHeader>
                  <Table.ColumnHeader >涨跌额</Table.ColumnHeader>
                  <Table.ColumnHeader >最高</Table.ColumnHeader>
                  <Table.ColumnHeader >最低</Table.ColumnHeader>
                  <Table.ColumnHeader >今开</Table.ColumnHeader>
                  <Table.ColumnHeader >昨收</Table.ColumnHeader>
                  <Table.ColumnHeader >成交量</Table.ColumnHeader>
                  <Table.ColumnHeader >成交额</Table.ColumnHeader>
                  <Table.ColumnHeader >换手率</Table.ColumnHeader>
                  <Table.ColumnHeader >量比</Table.ColumnHeader>
                  <Table.ColumnHeader >市盈率</Table.ColumnHeader>
                  <Table.ColumnHeader >总市值</Table.ColumnHeader>
                  <Table.ColumnHeader >流通市值</Table.ColumnHeader>
                  <Table.ColumnHeader>市场类型</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {filteredData.map((item, index) => (
                  <Table.Row key={`${item.code}-${index}`} _hover={{ bg: hoverBg }}>
                    <Table.Cell fontWeight="medium">{item.code}</Table.Cell>
                    <Table.Cell>{item.name}</Table.Cell>
                    <Table.Cell >{formatNumber(item.price)}</Table.Cell>
                    <Table.Cell >
                      <Badge 
                        colorPalette={getChangePctColor(item.change_pct)} 
                        fontSize="xs"
                        px={2}
                        py={1}
                      >
                        {formatNumber(item.change_pct)}%
                      </Badge>
                    </Table.Cell>
                    <Table.Cell >
                      <Badge 
                        colorPalette={item.change && item.change > 0 ? 'red' : 'green'}
                        fontSize="xs"
                        px={2}
                        py={1}
                      >
                        {formatNumber(item.change)}
                      </Badge>
                    </Table.Cell>
                    <Table.Cell >{formatNumber(item.high)}</Table.Cell>
                    <Table.Cell >{formatNumber(item.low)}</Table.Cell>
                    <Table.Cell >{formatNumber(item.open)}</Table.Cell>
                    <Table.Cell >{formatNumber(item.prev_close)}</Table.Cell>
                    <Table.Cell >{formatAmount(item.volume)}</Table.Cell>
                    <Table.Cell >{formatAmount(item.amount)}</Table.Cell>
                    <Table.Cell >{formatNumber(item.turnover_rate)}%</Table.Cell>
                    <Table.Cell >{formatNumber(item.volume_ratio)}</Table.Cell>
                    <Table.Cell >{formatNumber(item.pe_ratio)}</Table.Cell>
                    <Table.Cell >{formatMarketCap(item.total_market_cap)}</Table.Cell>
                    <Table.Cell >{formatMarketCap(item.float_market_cap)}</Table.Cell>
                    <Table.Cell>
                      <Badge colorPalette="blue" fontSize="xs">
                        {item.market_type || '-'}
                      </Badge>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
        )}

        {/* 数据条数提示 */}
        {!loading && filteredData.length > 0 && (
          <Flex justify="space-between" align="center">
            <Text fontSize="sm" color="gray.500">
              显示 {filteredData.length} 条数据（共 {marketData?.length || 0} 条）
            </Text>
            <Text fontSize="xs" color="gray.400">
              数据更新：{new Date().toLocaleTimeString()}
            </Text>
          </Flex>
        )}
      </VStack>
    </Box>
  )
}

export default MarketQuotes
