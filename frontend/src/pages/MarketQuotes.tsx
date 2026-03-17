import React, { useState } from 'react'
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
  Button,
  HStack,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
  Flex,
  Icon,
  SimpleGrid,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react'
import { SearchIcon, RepeatIcon } from '@chakra-ui/icons'
import { useQuery } from '@tanstack/react-query'
import { marketQuotesApi } from '../services/api'

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
  } = useQuery({
    queryKey: ['marketQuotes', selectedType],
    queryFn: async () => {
      const response = await marketQuotesApi.getMarketQuotes(selectedType || undefined)
      if (response.success && response.data) {
        return response.data as MarketQuote[]
      }
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
      <VStack spacing={6} align="stretch">
        {/* 标题和刷新按钮 */}
        <Flex justify="space-between" align="center" w="100%">
          <Heading size="lg">📊 市场实时行情</Heading>
          <Button
            size="sm"
            colorScheme="blue"
            leftIcon={<RepeatIcon />}
            onClick={handleRefresh}
            isLoading={loading}
          >
            刷新
          </Button>
        </Flex>

        {/* 市场统计卡片 */}
        {stats && (
          <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel fontSize="sm" color="gray.600">股票总数</StatLabel>
                  <StatNumber fontSize="2xl" fontWeight="bold">{stats.total}</StatNumber>
                  <StatHelpText mb={0} fontSize="xs" color="gray.500">
                    {currentTypeName}
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel fontSize="sm" color="gray.600">上涨家数</StatLabel>
                  <StatNumber fontSize="2xl" fontWeight="bold" color="red.500">
                    {stats.up}
                  </StatNumber>
                  <StatHelpText mb={0} fontSize="xs" color="gray.500">
                    占比 {stats.upRatio}%
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel fontSize="sm" color="gray.600">下跌家数</StatLabel>
                  <StatNumber fontSize="2xl" fontWeight="bold" color="green.500">
                    {stats.down}
                  </StatNumber>
                  <StatHelpText mb={0} fontSize="xs" color="gray.500">
                    占比 {stats.downRatio}%
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel fontSize="sm" color="gray.600">平均涨跌幅</StatLabel>
                  <StatNumber 
                    fontSize="2xl" 
                    fontWeight="bold"
                    color={parseFloat(stats.avgPct) > 0 ? 'red.500' : 'green.500'}
                  >
                    {parseFloat(stats.avgPct) > 0 ? '+' : ''}{stats.avgPct}%
                  </StatNumber>
                  <StatHelpText mb={0} fontSize="xs" color="gray.500">
                    平盘 {stats.flat}家
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>
        )}

        {/* 市场类型选择和搜索 */}
        <HStack spacing={4} wrap="wrap">
          {/* 市场类型下拉框 */}
          <Box>
            <Text fontSize="sm" fontWeight="bold" mb={2} color="gray.600">
              市场类型：
            </Text>
            <Select
              value={selectedType}
              onChange={handleTypeChange}
              w="200px"
              size="md"
              colorScheme="blue"
            >
              {MARKET_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                  {type.stability === 5 && ' ⭐⭐⭐⭐⭐'}
                  {type.stability === 4 && ' ⭐⭐⭐⭐'}
                  {type.stability === 3 && ' ⭐⭐⭐'}
                </option>
              ))}
            </Select>
          </Box>

          {/* 显示数量选择 */}
          <Box>
            <Text fontSize="sm" fontWeight="bold" mb={2} color="gray.600">
              显示数量：
            </Text>
            <Select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              w="120px"
              size="md"
            >
              <option value={50}>50 条</option>
              <option value={100}>100 条</option>
              <option value={200}>200 条</option>
              <option value={500}>500 条</option>
              <option value={1000}>1000 条</option>
            </Select>
          </Box>

          {/* 搜索框 */}
          <Box flex={1} minW="200px">
            <Text fontSize="sm" fontWeight="bold" mb={2} color="gray.600">
              搜索：
            </Text>
            <InputGroup>
              <InputLeftElement pointerEvents="none">
                <SearchIcon color="gray.400" />
              </InputLeftElement>
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
            <Spinner size="xl" thickness="4px" speed="0.65s" color="blue.500" />
          </Box>
        )}

        {/* 错误提示 */}
        {queryError && (
          <Alert status="error" borderRadius="lg">
            <AlertIcon />
            获取数据失败：{(queryError as Error).message}
            <Button
              size="sm"
              colorScheme="red"
              ml={4}
              onClick={handleRefresh}
            >
              重试
            </Button>
          </Alert>
        )}

        {/* 空数据提示 */}
        {!loading && !queryError && (!marketData || marketData.length === 0) && (
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            暂无市场实时行情数据，请尝试切换市场类型或刷新
          </Alert>
        )}

        {/* 数据表格 */}
        {!loading && filteredData.length > 0 && (
          <Box overflowX="auto" borderRadius="lg" boxShadow="md">
            <Table variant="simple" size="sm">
              <Thead bg="gray.50">
                <Tr>
                  <Th>代码</Th>
                  <Th>名称</Th>
                  <Th isNumeric>最新价</Th>
                  <Th isNumeric>涨跌幅</Th>
                  <Th isNumeric>涨跌额</Th>
                  <Th isNumeric>最高</Th>
                  <Th isNumeric>最低</Th>
                  <Th isNumeric>今开</Th>
                  <Th isNumeric>昨收</Th>
                  <Th isNumeric>成交量</Th>
                  <Th isNumeric>成交额</Th>
                  <Th isNumeric>换手率</Th>
                  <Th isNumeric>量比</Th>
                  <Th isNumeric>市盈率</Th>
                  <Th isNumeric>总市值</Th>
                  <Th isNumeric>流通市值</Th>
                  <Th>市场类型</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredData.map((item, index) => (
                  <Tr key={`${item.code}-${index}`} _hover={{ bg: hoverBg }}>
                    <Td fontWeight="medium">{item.code}</Td>
                    <Td>{item.name}</Td>
                    <Td isNumeric>{formatNumber(item.price)}</Td>
                    <Td isNumeric>
                      <Badge 
                        colorScheme={getChangePctColor(item.change_pct)} 
                        fontSize="xs"
                        px={2}
                        py={1}
                      >
                        {formatNumber(item.change_pct)}%
                      </Badge>
                    </Td>
                    <Td isNumeric>
                      <Badge 
                        colorScheme={item.change && item.change > 0 ? 'red' : 'green'}
                        fontSize="xs"
                        px={2}
                        py={1}
                      >
                        {formatNumber(item.change)}
                      </Badge>
                    </Td>
                    <Td isNumeric>{formatNumber(item.high)}</Td>
                    <Td isNumeric>{formatNumber(item.low)}</Td>
                    <Td isNumeric>{formatNumber(item.open)}</Td>
                    <Td isNumeric>{formatNumber(item.prev_close)}</Td>
                    <Td isNumeric>{formatAmount(item.volume)}</Td>
                    <Td isNumeric>{formatAmount(item.amount)}</Td>
                    <Td isNumeric>{formatNumber(item.turnover_rate)}%</Td>
                    <Td isNumeric>{formatNumber(item.volume_ratio)}</Td>
                    <Td isNumeric>{formatNumber(item.pe_ratio)}</Td>
                    <Td isNumeric>{formatMarketCap(item.total_market_cap)}</Td>
                    <Td isNumeric>{formatMarketCap(item.float_market_cap)}</Td>
                    <Td>
                      <Badge colorScheme="blue" fontSize="xs">
                        {item.market_type || '-'}
                      </Badge>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
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
