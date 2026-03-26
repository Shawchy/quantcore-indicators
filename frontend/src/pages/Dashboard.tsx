import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  SimpleGrid,
  Text,
  VStack,
  HStack,
  Badge,
  Spinner,
  Flex,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useColorModeValue,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { screenerApi, sectorApi, marketIndexApi } from '../services/api'
import { useWebSocket } from '../hooks/useWebSocket'
import { INDEX_CODES } from '../constants'
import { getKlineOption } from '../utils/chartConfig'
import { getMarketColor } from '../utils/marketColors'
import { StatCard } from '../components/StatCard'
import { RankBadge } from '../components/RankBadge'
import { SmartDateSelector } from '../components/SmartDateSelector'
import MarketMoneyflowCard from '../components/MarketMoneyflowCard'
import { FiTrendingUp, FiActivity, FiPieChart, FiBarChart } from 'react-icons/fi'

const Dashboard = () => {
  const [selectedDate, setSelectedDate] = useState<string>('')
  const cardBg = useColorModeValue('white', 'gray.800')
  
  // WebSocket 连接 - 用于实时推送
  const { isConnected } = useWebSocket({
    autoConnect: true,
    subscriptions: [
      'market:quotes',      // 市场行情
      'moneyflow:market',   // 资金流向
    ],
    onMessage: (event, data) => {
      console.log('[Dashboard] 收到 WebSocket 消息:', event, data)
      // 可以在这里处理 WebSocket 数据更新
    },
  })

  // 获取市场统计数据
  const { data: marketStats, isLoading: statsLoading } = useQuery({
    queryKey: ['marketStats', selectedDate],
    queryFn: () => screenerApi.getMarketStats(selectedDate),
  })

  // 获取板块排行
  const { data: sectorRanking, isLoading: sectorLoading } = useQuery({
    queryKey: ['sectorRanking', selectedDate],
    queryFn: () => sectorApi.getRanking('industry', 'change_pct', 10, selectedDate),
  })

  // 获取大盘指数实时数据
  const { data: realtimeData, isLoading: realtimeLoading } = useQuery({
    queryKey: ['indexRealtime'],
    queryFn: () => marketIndexApi.getRealtime(`${INDEX_CODES.SHANGHAI},${INDEX_CODES.SHENZHEN},${INDEX_CODES.GEM}`),
    refetchInterval: false, // 禁用轮询，使用 WebSocket 推送
    staleTime: 5 * 60 * 1000,       // 5 分钟内使用缓存
    gcTime: 10 * 60 * 1000,          // 缓存 10 分钟
  })

  // 获取上证指数 K 线数据
  const { data: indexData, isLoading: indexLoading } = useQuery({
    queryKey: ['indexData', selectedDate],
    queryFn: async () => {
      const endDate = selectedDate || new Date().toISOString().split('T')[0].replace(/-/g, '')
      const startDateObj = new Date()
      startDateObj.setDate(startDateObj.getDate() - 30)
      const startDate = startDateObj.toISOString().split('T')[0].replace(/-/g, '')
      const result = await marketIndexApi.getKline('000001', startDate, endDate)
      return result.data
    },
    enabled: true,
  })

  const handleDateChange = (newDate: string) => {
    setSelectedDate(newDate)
  }

  // 获取上证指数实时数据
  const getShIndexRealtime = () => {
    if (!realtimeData?.data) return null
    return realtimeData.data.find((item: any) => item.code === INDEX_CODES.SHANGHAI)
  }

  // K 线图配置（使用 useMemo 优化）
  const klineChartOption = useMemo(() => {
    const klineData = indexData?.data?.klines || []
    const dates = klineData.map((item: any) => {
      const dateStr = item.date || ''
      if (dateStr.length >= 10) {
        return dateStr.slice(5)
      }
      return dateStr
    })
    const closes = klineData.map((item: any) => item.close || 0)
    const volumes = klineData.map((item: any) => item.volume || 0)
    
    return getKlineOption(dates, closes, volumes)
  }, [indexData])

  // 行业分布饼图配置（使用 useMemo 优化）
  const industryPieOption = useMemo(() => {
    const topIndustries = marketStats?.data?.top_industries || []
    const colors = ['#3b82f6', '#2563eb', '#10b981', '#f59e0b', '#6b7280', '#8b5cf6', '#ec4899', '#14b8a6']
    
    const data = topIndustries.slice(0, 8).map((item: any, index: number) => ({
      value: item[1],
      name: item[0],
      itemStyle: { color: colors[index % colors.length] }
    }))
    
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#64748b', fontSize: 11 },
      },
      series: [
        {
          name: '行业分布',
          type: 'pie',
          radius: ['50%', '70%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: { show: false },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              color: '#1e293b',
            },
          },
          data: data.length > 0 ? data : [],
        },
      ],
    }
  }, [marketStats])

  const shIndex = getShIndexRealtime()

  return (
    <VStack spacing={6} align="stretch">
      {/* 标题栏 */}
      <Flex justify="space-between" align="center" wrap="wrap" gap={3}>
        <Box>
          <Heading size="lg" color="light.text">
            市场概览
          </Heading>
          <Text color="light.textSecondary" fontSize="sm" mt={1}>
            实时数据 · 智能日期选择 · 自动刷新
          </Text>
        </Box>
        <Box w={{ base: '100%', md: '400px' }}>
          <SmartDateSelector 
            onDateChange={handleDateChange}
            enableAutoRefresh={true}
            showSlider={true}
          />
        </Box>
      </Flex>

      {/* 统计卡片 */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
        <StatCard
          label="市场股票数"
          value={statsLoading ? <Spinner size="sm" /> : (marketStats?.data?.total_stocks || 0)}
          helpText="A 股市场"
          icon={FiActivity}
          accentColor="blue"
        />
        <StatCard
          label="行业板块数"
          value={marketStats?.data?.industry_distribution ? Object.keys(marketStats.data.industry_distribution).length : 0}
          helpText="申万一级行业"
          icon={FiPieChart}
          accentColor="purple"
        />
        <StatCard
          label="上证指数"
          value={realtimeLoading ? <Spinner size="sm" /> : (shIndex ? shIndex.price.toFixed(2) : '-')}
          helpText={shIndex ? `${shIndex.change >= 0 ? '+' : ''}${shIndex.change?.toFixed(2)} (${shIndex.change_pct?.toFixed(2)}%)` : ''}
          icon={FiBarChart}
          accentColor={shIndex?.change >= 0 ? 'red' : 'green'}
        />
        <StatCard
          label="市场成交额"
          value={statsLoading ? <Spinner size="sm" /> : (marketStats?.data?.turnover ? `${(marketStats.data.turnover / 100000000).toFixed(2)}亿` : '-')}
          helpText="全市场"
          icon={FiTrendingUp}
          accentColor="orange"
        />
      </SimpleGrid>

      {/* 大盘走势和实时行情 */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        {/* K 线图 */}
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Flex justify="space-between" align="center">
              <Heading size="sm" color="light.text">
                大盘走势（上证指数）
              </Heading>
              <Badge colorScheme="blue" variant="subtle" fontSize="xs">
                30 日 K 线
              </Badge>
            </Flex>
          </CardHeader>
          <CardBody pt={2}>
            {indexLoading ? (
              <Flex justify="center" align="center" h="300px">
                <Spinner color="brand.500" />
              </Flex>
            ) : (
              <ReactECharts option={klineChartOption} style={{ height: '320px' }} />
            )}
          </CardBody>
        </Card>

        {/* 实时行情 - 使用 WebSocket 推送 */}
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Flex justify="space-between" align="center">
              <Heading size="sm" color="light.text">
                大盘实时行情
              </Heading>
              <HStack spacing={2}>
                {isConnected && (
                  <Badge colorScheme="green" variant="subtle" fontSize="xs">
                    WebSocket 推送
                  </Badge>
                )}
                <Badge colorScheme="blue" variant="subtle" fontSize="xs">
                  实时更新
                </Badge>
              </HStack>
            </Flex>
          </CardHeader>
          <CardBody pt={2}>
            {realtimeLoading ? (
              <Flex justify="center" align="center" h="300px">
                <Spinner color="brand.500" />
              </Flex>
            ) : (
              <VStack spacing={4} align="stretch">
                {realtimeData?.data?.map((item: any) => (
                  <HStack key={item.code} justify="space-between" p={3} bg="gray.50" borderRadius="md">
                    <VStack align="start" spacing={1}>
                      <Text fontWeight="bold" fontSize="sm" color="light.text">
                        {item.name}
                      </Text>
                      <Text fontSize="xs" color="light.textSecondary">
                        {item.code}
                      </Text>
                    </VStack>
                    <VStack align="end" spacing={1}>
                      <Text fontSize="lg" fontWeight="bold" color={getMarketColor(item.change)}>
                        {item.price?.toFixed(2)}
                      </Text>
                      <Text fontSize="xs" color={getMarketColor(item.change)}>
                        {item.change >= 0 ? '+' : ''}{item.change?.toFixed(2)} ({item.change_pct?.toFixed(2)}%)
                      </Text>
                    </VStack>
                  </HStack>
                ))}
              </VStack>
            )}
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* 行业分布和板块排行 */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        {/* 行业分布 */}
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">
              行业分布
            </Heading>
          </CardHeader>
          <CardBody pt={2}>
            <ReactECharts option={industryPieOption} style={{ height: '300px' }} />
          </CardBody>
        </Card>

        {/* 板块排行 */}
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Flex justify="space-between" align="center">
              <Heading size="sm" color="light.text">
                板块排行 TOP10
              </Heading>
              <Badge colorScheme="blue" variant="subtle" fontSize="xs">
                行业板块
              </Badge>
            </Flex>
          </CardHeader>
          <CardBody pt={2}>
            {sectorLoading ? (
              <Flex justify="center" align="center" h="300px">
                <Spinner color="brand.500" />
              </Flex>
            ) : (
              <VStack spacing={2} align="stretch">
                {sectorRanking?.data?.slice(0, 10).map((sector: any, index: number) => (
                  <HStack key={index} justify="space-between" p={2} borderRadius="md" bg={index % 2 === 0 ? 'gray.50' : 'white'} _dark={{ bg: index % 2 === 0 ? 'gray.700' : 'gray.800' }}>
                    <HStack spacing={3}>
                      <RankBadge rank={index + 1} />
                      <Text fontWeight="medium" fontSize="sm">{sector.name}</Text>
                    </HStack>
                    <HStack spacing={4}>
                      <Text fontSize="sm" color={getMarketColor(sector.change_pct)}>
                        {sector.change_pct >= 0 ? '+' : ''}{(sector.change_pct || 0).toFixed(2)}%
                      </Text>
                    </HStack>
                  </HStack>
                ))}
              </VStack>
            )}
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* 大盘资金流向 */}
      <SimpleGrid columns={{ base: 1, lg: 3 }} spacing={4}>
        <MarketMoneyflowCard />
      </SimpleGrid>
    </VStack>
  )
}

export default Dashboard
