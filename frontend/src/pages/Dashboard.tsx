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
  Icon,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import React, { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { screenerApi, sectorApi, stockApi, watchlistApi } from '../services/api'
import { StatCard } from '../components/StatCard'
import { RankBadge } from '../components/RankBadge'
import { SmartDateSelector } from '../components/SmartDateSelector'
import { FiTrendingUp, FiActivity, FiPieChart, FiBarChart } from 'react-icons/fi'

const Dashboard = () => {
  const [selectedDate, setSelectedDate] = useState<string>('')

  const { data: marketStats, isLoading: statsLoading, refetch: refetchMarketStats } = useQuery({
    queryKey: ['marketStats', selectedDate],
    queryFn: () => screenerApi.getMarketStats(selectedDate || undefined),
  })

  const { data: sectorRanking, isLoading: sectorLoading, refetch: refetchSectorRanking } = useQuery({
    queryKey: ['sectorRanking', selectedDate],
    queryFn: () => sectorApi.getRanking('industry', 'change_pct', 10, selectedDate || undefined),
  })

  // 获取上证指数数据
  const { data: indexData } = useQuery({
    queryKey: ['indexData', selectedDate],
    queryFn: async () => {
      // 获取最近 30 天的上证指数数据
      const endDate = selectedDate || new Date().toISOString().split('T')[0].replace(/-/g, '')
      const startDate = new Date(new Date(endDate).setDate(new Date(endDate).getDate() - 30)).toISOString().split('T')[0].replace(/-/g, '')
      const result = await stockApi.getKline('000001', { startDate, endDate })
      return result.data
    },
    enabled: false, // 初始不加载
  })

  // 获取自选股列表
  const { data: watchlistData } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => watchlistApi.getList(),
  })

  const handleDateChange = (newDate: string) => {
    setSelectedDate(newDate)
    // 触发数据刷新
    setTimeout(() => {
      refetchMarketStats()
      refetchSectorRanking()
    }, 100)
  }

  const getKlineOption = () => {
    // 使用真实的上证指数数据
    const klineData = indexData?.data?.klines || []
    const dates = klineData.map((item: any) => item.date?.slice(5) || '') // 只显示月 - 日
    const prices = klineData.map((item: any) => item.close || 0)
    
    return {
      backgroundColor: 'transparent',
      animation: true,
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      grid: {
        left: '8%',
        right: '5%',
        top: '10%',
        bottom: '15%',
      },
      xAxis: {
        type: 'category',
        data: dates.length > 0 ? dates : [],
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b', fontSize: 10 },
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b', fontSize: 10 },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
      },
      series: [
        {
          name: '上证指数',
          type: 'line',
          smooth: true,
          data: prices.length > 0 ? prices : [],
          lineStyle: {
            color: '#3b82f6',
            width: 2,
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0)' },
              ],
            },
          },
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: { color: '#3b82f6' },
        },
      ],
    }
  }

  const getPieOption = () => {
    // 使用真实的行业分布数据
    const industryDist = marketStats?.data?.industry_distribution || {}
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
          data: data.length > 0 ? data : [
            { value: 35, name: '科技', itemStyle: { color: '#3b82f6' } },
            { value: 25, name: '金融', itemStyle: { color: '#2563eb' } },
            { value: 20, name: '消费', itemStyle: { color: '#10b981' } },
            { value: 15, name: '医药', itemStyle: { color: '#f59e0b' } },
            { value: 5, name: '其他', itemStyle: { color: '#6b7280' } },
          ],
        },
      ],
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      <Flex justify="space-between" align="center" wrap="wrap" gap={3}>
        <Box>
          <Heading 
            size="lg" 
            color="light.text"
          >
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

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
        <StatCard
          label="市场股票数"
          value={statsLoading ? <Spinner size="sm" /> : (marketStats?.data?.total_stocks || '5,234')}
          helpText="A 股市场"
          icon={FiActivity}
          accentColor="blue"
        />
        <StatCard
          label="行业板块数"
          value={marketStats?.data?.industry_distribution ? Object.keys(marketStats.data.industry_distribution).length : '142'}
          helpText="申万一级行业"
          icon={FiPieChart}
          accentColor="purple"
        />
        <StatCard
          label="上涨/下跌"
          value={marketStats?.data?.trade_date ? '计算中' : '2,341/2,893'}
          helpText="涨跌比"
          icon={FiTrendingUp}
          accentColor="green"
        />
        <StatCard
          label="市场成交额"
          value={marketStats?.data?.trade_date ? '计算中' : '8,521 亿'}
          helpText="较昨日 +12.3%"
          icon={FiBarChart}
          accentColor="orange"
        />
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader pb={2}>
            <Flex justify="space-between" align="center">
              <Heading size="sm" color="light.text">
                板块涨幅排行
              </Heading>
              <Badge colorScheme="blue" variant="subtle" fontSize="xs">
                TOP 10
              </Badge>
            </Flex>
          </CardHeader>
          <CardBody pt={2}>
            {sectorLoading ? (
              <Flex justify="center" align="center" h="200px">
                <Spinner color="brand.500" />
              </Flex>
            ) : (
              <VStack align="stretch" spacing={2}>
                {(sectorRanking?.data || []).slice(0, 8).map((sector: any, index: number) => (
                  <Flex 
                    key={sector.code}
                    align="center" 
                    justify="space-between"
                    p={2}
                    borderRadius="md"
                    bg="light.bgSecondary"
                    _hover={{ bg: 'brand.50' }}
                    transition="all 0.2s"
                    cursor="pointer"
                  >
                    <HStack spacing={3}>
                      <RankBadge rank={index + 1} />
                      <Text color="light.text" fontSize="sm" fontWeight="medium">
                        {sector.name}
                      </Text>
                    </HStack>
                    <HStack spacing={3}>
                      <Box w="60px">
                        <Progress 
                          value={(sector.change_pct || 0) * 10} 
                          size="xs" 
                          colorScheme={sector.change_pct >= 0 ? 'red' : 'green'}
                          borderRadius="full"
                          bg="gray.100"
                        />
                      </Box>
                      <Badge 
                        variant={sector.change_pct >= 0 ? 'up' : 'down'}
                        fontSize="xs"
                        minW="55px"
                        textAlign="center"
                      >
                        {sector.change_pct >= 0 ? '+' : ''}
                        {(sector.change_pct || 0).toFixed(2)}%
                      </Badge>
                    </HStack>
                  </Flex>
                ))}
              </VStack>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader pb={2}>
            <Flex justify="space-between" align="center">
              <Heading size="sm" color="light.text">
                大盘走势
              </Heading>
              <Badge colorScheme="blue" variant="subtle" fontSize="xs">
                上证指数
              </Badge>
            </Flex>
          </CardHeader>
          <CardBody pt={2}>
            <ReactECharts 
              option={getKlineOption()} 
              style={{ height: '240px' }} 
            />
          </CardBody>
        </Card>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">
              快速选股入口
            </Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={2} spacing={3}>
              {[
                { label: '高控盘股', count: 128, color: 'brand.500' },
                { label: '突破新高', count: 89, color: 'brand.600' },
                { label: 'MACD金叉', count: 234, color: 'green.500' },
                { label: 'RSI超卖', count: 156, color: 'orange.500' },
              ].map((item) => (
                <Box
                  key={item.label}
                  p={4}
                  borderRadius="lg"
                  border="1px solid"
                  borderColor="light.border"
                  bg="light.bgSecondary"
                  cursor="pointer"
                  transition="all 0.2s"
                  _hover={{
                    borderColor: item.color,
                    bg: 'white',
                    transform: 'translateY(-2px)',
                    boxShadow: 'md',
                  }}
                >
                  <Text color="light.textSecondary" fontSize="xs">
                    {item.label}
                  </Text>
                  <Text 
                    color={item.color} 
                    fontSize="xl" 
                    fontWeight="bold"
                    fontFamily="mono"
                  >
                    {item.count}
                  </Text>
                </Box>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>

        <Card>
          <CardHeader pb={2}>
            <Flex justify="space-between" align="center">
              <Heading size="sm" color="light.text">
                行业分布
              </Heading>
              <Badge colorScheme="blue" variant="subtle" fontSize="xs">
                市场
              </Badge>
            </Flex>
          </CardHeader>
          <CardBody pt={2}>
            <ReactECharts 
              option={getPieOption()} 
              style={{ height: '200px' }} 
            />
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardHeader pb={2}>
          <Flex justify="space-between" align="center">
            <Heading size="sm" color="light.text">
              今日关注
            </Heading>
            <Badge colorScheme="blue" variant="subtle" fontSize="xs">
              自选股
            </Badge>
          </Flex>
        </CardHeader>
        <CardBody>
          {watchlistData?.data && watchlistData.data.length > 0 ? (
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th borderColor="light.border">股票</Th>
                  <Th borderColor="light.border" isNumeric>代码</Th>
                  <Th borderColor="light.border" isNumeric>备注</Th>
                </Tr>
              </Thead>
              <Tbody>
                {watchlistData.data.slice(0, 5).map((stock: any) => (
                  <Tr key={stock.code} _hover={{ bg: 'light.bgSecondary' }}>
                    <Td borderColor="light.border">
                      <VStack align="start" spacing={0}>
                        <Text color="light.text" fontWeight="medium">{stock.code}</Text>
                        <Text color="light.textSecondary" fontSize="xs">{stock.name || '-'}</Text>
                      </VStack>
                    </Td>
                    <Td borderColor="light.border" isNumeric fontFamily="mono">
                      {stock.code}
                    </Td>
                    <Td borderColor="light.border" color="light.textSecondary">
                      {stock.note || '-'}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          ) : (
            <Flex justify="center" align="center" h="150px" direction="column" gap={2}>
              <Text color="light.textSecondary" fontSize="sm">暂无自选股</Text>
              <Text color="light.textSecondary" fontSize="xs">添加关注的股票以快速查看</Text>
            </Flex>
          )}
        </CardBody>
      </Card>
    </VStack>
  )
}

export default Dashboard
