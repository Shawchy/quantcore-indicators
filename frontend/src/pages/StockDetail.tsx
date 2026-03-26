import { useParams, useNavigate, useLocation } from 'react-router-dom'
import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatArrow,
  SimpleGrid,
  Spinner,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Flex,
  useToast,
  Button,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Icon,
} from '@chakra-ui/react'
import { FiArrowLeft } from 'react-icons/fi'
import { useQuery } from '@tanstack/react-query'
import { stockApi, realtimeApi, boardApi, capitalFlowApi, shareholderApi } from '../services/api'
import RealtimeQuotePanel from '../components/RealtimeQuote'
import RealtimeQuoteWS from '../components/RealtimeQuoteWS'
import TickDataTable from '../components/TickDataTable'
import { ProKLineChart as KLineChart } from '../components/charts/KLineChart'
import { IndicatorChart } from '../components/KLineChart'
import type { RealtimeQuoteData, TickData, StockBasic, KLineData, TechnicalIndicator, RealtimeQuote } from '../types'
import { useEffect, useState } from 'react'

const queryEnabled = (code: string | undefined, valid: boolean) => Boolean(code && valid)

const StockDetail = () => {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()
  const [wsQuoteData, setWsQuoteData] = useState<RealtimeQuoteData | null>(null)
  
  // 判断是否来自自选股页面
  const isFromWatchlist = location.state?.from === 'watchlist'
  
  const isValidCode = Boolean(code && /^[0-9]{6}$/.test(code))
  const enabled = queryEnabled(code, isValidCode)
  
  const { data: basicData, isLoading: basicLoading } = useQuery({
    queryKey: ['stockBasic', code],
    queryFn: () => stockApi.getBasic(code!),
    enabled,
  })

  const { data: klineData, isLoading: klineLoading } = useQuery({
    queryKey: ['stockKline', code],
    queryFn: () => stockApi.getKline(code!),
    enabled,
  })

  const { data: weeklyKlineData, isLoading: weeklyKlineLoading } = useQuery({
    queryKey: ['stockWeeklyKline', code],
    queryFn: () => stockApi.getWeeklyKline(code!),
    enabled,
  })

  const { data: monthlyKlineData, isLoading: monthlyKlineLoading } = useQuery({
    queryKey: ['stockMonthlyKline', code],
    queryFn: () => stockApi.getMonthlyKline(code!),
    enabled,
  })

  const { data: indicatorData, isLoading: indicatorLoading } = useQuery({
    queryKey: ['stockIndicators', code],
    queryFn: () => stockApi.getIndicators(code!),
    enabled,
  })

  const { data: realtimeData } = useQuery({
    queryKey: ['stockRealtime', code],
    queryFn: () => stockApi.getRealtime(code!),
    enabled,
    refetchInterval: 30000,
  })

  // 使用 WebSocket 实时推送替代 HTTP 轮询
  const { data: realtimeQuoteData, isLoading: quoteLoading, error: quoteError } = useQuery<RealtimeQuoteData>({
    queryKey: ['realtimeQuote', code],
    queryFn: () => realtimeApi.getQuote(code!) as unknown as Promise<RealtimeQuoteData>,
    enabled,
    refetchInterval: false,  // 禁用轮询，使用 WebSocket
    staleTime: 5 * 60 * 1000,  // 5 分钟内有效
  })

  const { data: tickData, isLoading: tickLoading, error: tickError } = useQuery<TickData>({
    queryKey: ['tickData', code],
    queryFn: () => realtimeApi.getTickData(code!, 'dc', 100) as unknown as Promise<TickData>,
    enabled,
    refetchInterval: 60000,  // 降低到 60 秒刷新一次
    retry: 2,  // 失败重试 2 次
    staleTime: 30000,  // 30 秒内认为是新鲜数据
  })

  const { data: boardData } = useQuery({
    queryKey: ['stockBoards', code],
    queryFn: () => boardApi.getStockBoards(code!),
    enabled,
  })

  const { data: capitalFlowData } = useQuery({
    queryKey: ['stockCapitalFlow', code],
    queryFn: () => capitalFlowApi.getStockHistory(code!),
    enabled,
  })

  const { data: shareholderData } = useQuery({
    queryKey: ['stockShareholders', code],
    queryFn: () => shareholderApi.getTop10(code!),
    enabled,
  })
  
  // 显示错误提示
  useEffect(() => {
    if (code && !isValidCode) {
      toast({
        title: '无效的股票代码',
        description: '请输入 6 位数字股票代码',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
      navigate('/')
    }
  }, [code, isValidCode, navigate])

  const stock = (basicData as { data?: StockBasic } | undefined)?.data
  const quote = (realtimeData as { data?: RealtimeQuote } | undefined)?.data
  // 后端返回格式：{status: "complete", data: [...]}
  const klines = ((klineData as { data?: {data?: KLineData[]} } | undefined)?.data?.data) || []
  const weeklyKlines = ((weeklyKlineData as { data?: {data?: KLineData[]} } | undefined)?.data?.data) || []
  const monthlyKlines = ((monthlyKlineData as { data?: {data?: KLineData[]} } | undefined)?.data?.data) || []
  const indicators = ((indicatorData as { data?: TechnicalIndicator[] } | undefined)?.data) || []
  const boards = ((boardData as { data?: any[] } | undefined)?.data) || []
  const capitalFlows = ((capitalFlowData as { data?: any[] } | undefined)?.data) || []
  const shareholders = ((shareholderData as { data?: any[] } | undefined)?.data) || []

  const getKlineOption = () => {
    if (!klines.length) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#a0aec0', fontSize: 14 }
        },
        xAxis: { show: false },
        yAxis: { show: false }
      }
    }

    const dates = klines.map((k: any) => k.date)
    const ohlc = klines.map((k: any) => [k.open, k.close, k.low, k.high])
    const volumes = klines.map((k: any) => k.volume)

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      legend: { data: ['K 线', 'MA5', 'MA20'], bottom: 0, textStyle: { color: '#64748b' } },
      grid: [
        { left: '10%', right: '8%', height: '50%' },
        { left: '10%', right: '8%', top: '65%', height: '20%' },
      ],
      xAxis: [
        { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
        { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
      ],
      yAxis: [
        { scale: true, gridIndex: 0, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } } },
        { scale: true, gridIndex: 1, splitLine: { show: false }, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
        { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: '5%', backgroundColor: '#f1f5f9', fillerColor: 'rgba(59, 130, 246, 0.2)', borderColor: '#e2e8f0', textStyle: { color: '#64748b' } },
      ],
      series: [
        {
          name: 'K 线',
          type: 'candlestick',
          data: ohlc,
          itemStyle: {
            color: '#ef4444',
            color0: '#10b981',
            borderColor: '#ef4444',
            borderColor0: '#10b981',
          },
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          itemStyle: (params: any) => {
            const idx = params.dataIndex
            const open = ohlc[idx][0]
            const close = ohlc[idx][1]
            return { color: close >= open ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)' }
          },
        },
      ],
    }
  }

  const getWeeklyKlineOption = () => {
    if (!weeklyKlines.length) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#a0aec0', fontSize: 14 }
        },
        xAxis: { show: false },
        yAxis: { show: false }
      }
    }

    const dates = weeklyKlines.map((k: any) => k.date)
    const ohlc = weeklyKlines.map((k: any) => [k.open, k.close, k.low, k.high])
    const volumes = weeklyKlines.map((k: any) => k.volume)

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      legend: { data: ['周K线'], bottom: 0, textStyle: { color: '#64748b' } },
      grid: [
        { left: '10%', right: '8%', height: '50%' },
        { left: '10%', right: '8%', top: '65%', height: '20%' },
      ],
      xAxis: [
        { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
        { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
      ],
      yAxis: [
        { scale: true, gridIndex: 0, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } } },
        { scale: true, gridIndex: 1, splitLine: { show: false }, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
        { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: '5%', backgroundColor: '#f1f5f9', fillerColor: 'rgba(59, 130, 246, 0.2)', borderColor: '#e2e8f0', textStyle: { color: '#64748b' } },
      ],
      series: [
        {
          name: '周K线',
          type: 'candlestick',
          data: ohlc,
          itemStyle: {
            color: '#ef4444',
            color0: '#10b981',
            borderColor: '#ef4444',
            borderColor0: '#10b981',
          },
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          itemStyle: (params: any) => {
            const idx = params.dataIndex
            const open = ohlc[idx][0]
            const close = ohlc[idx][1]
            return { color: close >= open ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)' }
          },
        },
      ],
    }
  }

  const getMonthlyKlineOption = () => {
    if (!monthlyKlines.length) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#a0aec0', fontSize: 14 }
        },
        xAxis: { show: false },
        yAxis: { show: false }
      }
    }

    const dates = monthlyKlines.map((k: any) => k.date)
    const ohlc = monthlyKlines.map((k: any) => [k.open, k.close, k.low, k.high])
    const volumes = monthlyKlines.map((k: any) => k.volume)

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      legend: { data: ['月K线'], bottom: 0, textStyle: { color: '#64748b' } },
      grid: [
        { left: '10%', right: '8%', height: '50%' },
        { left: '10%', right: '8%', top: '65%', height: '20%' },
      ],
      xAxis: [
        { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
        { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
      ],
      yAxis: [
        { scale: true, gridIndex: 0, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } } },
        { scale: true, gridIndex: 1, splitLine: { show: false }, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
        { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: '5%', backgroundColor: '#f1f5f9', fillerColor: 'rgba(59, 130, 246, 0.2)', borderColor: '#e2e8f0', textStyle: { color: '#64748b' } },
      ],
      series: [
        {
          name: '月K线',
          type: 'candlestick',
          data: ohlc,
          itemStyle: {
            color: '#ef4444',
            color0: '#10b981',
            borderColor: '#ef4444',
            borderColor0: '#10b981',
          },
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          itemStyle: (params: any) => {
            const idx = params.dataIndex
            const open = ohlc[idx][0]
            const close = ohlc[idx][1]
            return { color: close >= open ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)' }
          },
        },
      ],
    }
  }

  const getIndicatorOption = () => {
    if (!indicators.length) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#a0aec0', fontSize: 14 }
        },
        xAxis: { show: false },
        yAxis: { show: false }
      }
    }

    const dates = indicators.map((i: any) => i.date)
    const macd = indicators.map((i: any) => i.macd)
    const macdSignal = indicators.map((i: any) => i.macd_signal)
    const macdHist = indicators.map((i: any) => i.macd_hist)

    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      legend: { data: ['MACD', 'Signal', 'Hist'], bottom: 0, textStyle: { color: '#64748b' } },
      grid: { left: '10%', right: '8%', bottom: '15%' },
      xAxis: { 
        type: 'category', 
        data: dates,
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b' },
      },
      yAxis: { 
        type: 'value',
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      },
      series: [
        { name: 'MACD', type: 'line', data: macd, lineStyle: { color: 'brand.500' }, itemStyle: { color: 'brand.500' } },
        { name: 'Signal', type: 'line', data: macdSignal, lineStyle: { color: 'brand.600' }, itemStyle: { color: 'brand.600' } },
        { name: 'Hist', type: 'bar', data: macdHist, itemStyle: (params: any) => ({ color: params.value >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)' }) },
      ],
    }
  }

  if (basicLoading) {
    return (
      <Flex justify="center" align="center" h="400px">
        <Spinner size="xl" color="brand.400" />
      </Flex>
    )
  }

  return (
    <VStack spacing={6} align="stretch">
      {/* 面包屑导航和返回按钮 */}
      <HStack justify="space-between" mb={2}>
        <Breadcrumb separator="/">
          <BreadcrumbItem>
            <BreadcrumbLink onClick={() => navigate('/')} color="light.textSecondary" _hover={{ color: 'brand.400' }}>
              首页
            </BreadcrumbLink>
          </BreadcrumbItem>
          {isFromWatchlist && (
            <BreadcrumbItem>
              <BreadcrumbLink onClick={() => navigate('/watchlist')} color="light.textSecondary" _hover={{ color: 'brand.400' }}>
                自选股
              </BreadcrumbLink>
            </BreadcrumbItem>
          )}
          <BreadcrumbItem isCurrentPage>
            <Text color="light.text" fontWeight="medium">{stock?.name || code}</Text>
          </BreadcrumbItem>
        </Breadcrumb>
        
        {isFromWatchlist && (
          <Button
            leftIcon={<Icon as={FiArrowLeft} />}
            size="sm"
            variant="ghost"
            onClick={() => navigate('/watchlist')}
          >
            返回自选股
          </Button>
        )}
      </HStack>

      <HStack justify="space-between" flexWrap="wrap" gap={4}>
        <VStack align="start" spacing={1}>
          <Heading size="lg" color="light.text">
            {stock?.name || code}
            <Text as="span" fontSize="md" color="light.textMuted" ml={2} fontFamily="mono">
              {code}
            </Text>
          </Heading>
          <HStack>
            <Badge 
              bg={stock?.market === 'SH' ? 'rgba(255, 82, 82, 0.15)' : 'rgba(0, 168, 255, 0.15)'}
              color={stock?.market === 'SH' ? 'down.500' : 'brand.400'}
            >
              {stock?.market}
            </Badge>
            {stock?.industry && <Badge colorScheme="purple" variant="subtle">{stock.industry}</Badge>}
          </HStack>
        </VStack>

        {quote && (
          <VStack align="end" spacing={1}>
            <Text 
              fontSize="3xl" 
              fontWeight="bold" 
              color={quote.change_pct >= 0 ? 'up.500' : 'down.500'}
              fontFamily="mono"
            >
              {quote.price?.toFixed(2)}
            </Text>
            <HStack>
              <Stat>
                <StatArrow type={quote.change_pct >= 0 ? 'increase' : 'decrease'} color={quote.change_pct >= 0 ? 'up.500' : 'down.500'} />
              </Stat>
              <Text color={quote.change_pct >= 0 ? 'up.500' : 'down.500'} fontWeight="bold" fontFamily="mono">
                {quote.change_pct >= 0 ? '+' : ''}{quote.change_pct?.toFixed(2)}%
              </Text>
            </HStack>
          </VStack>
        )}
      </HStack>

      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
        {[
          { label: '今开', value: quote?.open?.toFixed(2) || '--' },
          { label: '最高', value: quote?.high?.toFixed(2) || '--', color: 'up.500' },
          { label: '最低', value: quote?.low?.toFixed(2) || '--', color: 'down.500' },
          { label: '成交量', value: quote?.volume ? (quote.volume / 10000).toFixed(0) + '万' : '--' },
        ].map((item) => (
          <Card key={item.label} size="sm">
            <CardBody p={4}>
              <Stat size="sm">
                <StatLabel color="light.textSecondary" fontSize="xs">{item.label}</StatLabel>
                <StatNumber fontSize="md" color={item.color || 'light.text'} fontFamily="mono">{item.value}</StatNumber>
              </Stat>
            </CardBody>
          </Card>
        ))}
      </SimpleGrid>

      <Card>
        <CardBody>
          <Tabs variant="line">
            <TabList borderColor="light.border">
              <Tab color="light.textSecondary">日 K 线</Tab>
              <Tab color="light.textSecondary">周 K 线</Tab>
              <Tab color="light.textSecondary">月 K 线</Tab>
            </TabList>
            <TabPanels>
              <TabPanel p={0} pt={4}>
                <KLineChart
                  data={klines}
                  loading={klineLoading}
                  type="daily"
                  height="400px"
                />
              </TabPanel>
              <TabPanel p={0} pt={4}>
                <KLineChart
                  data={weeklyKlines}
                  loading={weeklyKlineLoading}
                  type="weekly"
                  height="400px"
                />
              </TabPanel>
              <TabPanel p={0} pt={4}>
                <KLineChart
                  data={monthlyKlines}
                  loading={monthlyKlineLoading}
                  type="monthly"
                  height="400px"
                />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </CardBody>
      </Card>

      {/* 实时盘口 - 使用 WebSocket 实时推送 */}
      <Card>
        <CardHeader pb={2}>
          <Flex justify="space-between" align="center">
            <Heading size="sm" color="light.text">
              实时盘口
            </Heading>
            <HStack spacing={2}>
              {wsQuoteData && (
                <Badge fontSize="xs" colorScheme="green">
                  WebSocket 实时更新
                </Badge>
              )}
              {realtimeQuoteData && (
                <Badge fontSize="xs" colorScheme="blue">
                  更新：{realtimeQuoteData.update_time}
                </Badge>
              )}
            </HStack>
          </Flex>
        </CardHeader>
        <CardBody>
          {/* 优先使用 WebSocket 数据，否则降级到 HTTP 数据 */}
          {enabled && wsQuoteData ? (
            <RealtimeQuoteWS code={code!} name={stock?.name} />
          ) : (
            <RealtimeQuotePanel
              data={realtimeQuoteData ?? null}
              loading={quoteLoading}
              error={null}
            />
          )}
        </CardBody>
      </Card>

      {/* 成交明细 */}
      <Card>
        <CardHeader pb={2}>
          <Flex justify="space-between" align="center">
            <Heading size="sm" color="light.text">
              成交明细
            </Heading>
            {tickData && (
              <Badge fontSize="xs" colorScheme="green">
                共 {tickData.total_records} 笔
              </Badge>
            )}
          </Flex>
        </CardHeader>
        <CardBody>
          <TickDataTable
            data={tickData ?? null}
            loading={tickLoading}
            error={null}
          />
        </CardBody>
      </Card>

      {/* 所属板块 */}
      {boards.length > 0 && (
        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">所属板块</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={[1, 2, 3]} gap={4}>
              {boards.map((board: any, index: number) => (
                <Card key={index} size="sm">
                  <CardBody p={4}>
                    <VStack align="start" spacing={2}>
                      <Text fontSize="xs" color="light.textSecondary">{board.board_type}</Text>
                      <Text fontSize="md" fontWeight="bold" color="light.text">{board.name}</Text>
                      <HStack spacing={4}>
                        <Text fontSize="xs" color="light.textSecondary">
                          价格：{board.close_price?.toFixed(2) || '-'}
                        </Text>
                        <Badge colorScheme={board.change_pct && board.change_pct > 0 ? 'red' : 'green'}>
                          {board.change_pct?.toFixed(2) || 0}%
                        </Badge>
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>
      )}

      {/* 资金流向 */}
      {capitalFlows.length > 0 && (
        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">资金流向</Heading>
          </CardHeader>
          <CardBody>
            <TableContainer>
              <Table size="sm" variant="simple">
                <Thead>
                  <Tr>
                    <Th borderColor="light.border" color="light.textSecondary">日期</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>收盘价</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>涨跌幅</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>主力净流入</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>主力净流入率</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>超大单</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>大单</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>中单</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>小单</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {capitalFlows.slice(-10).reverse().map((item: any, index: number) => (
                    <Tr key={index} _hover={{ bg: 'light.bgSecondary' }}>
                      <Td borderColor="light.border" color="light.text">{item.trade_date}</Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        {item.close_price?.toFixed(2) || '-'}
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        <Badge colorScheme={item.change_pct && item.change_pct > 0 ? 'red' : 'green'}>
                          {item.change_pct?.toFixed(2) || 0}%
                        </Badge>
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        <Badge colorScheme={item.main_net_amount && item.main_net_amount > 0 ? 'red' : 'green'}>
                          {(item.main_net_amount / 10000).toFixed(0)}万
                        </Badge>
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        {item.main_net_amount_rate?.toFixed(2) || 0}%
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        {(item.buy_elg_amount / 10000).toFixed(0)}万
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        {(item.buy_lg_amount / 10000).toFixed(0)}万
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        {(item.buy_md_amount / 10000).toFixed(0)}万
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        {(item.buy_sm_amount / 10000).toFixed(0)}万
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          </CardBody>
        </Card>
      )}

      {/* 前十大股东 */}
      {shareholders.length > 0 && (
        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">前十大股东</Heading>
          </CardHeader>
          <CardBody>
            <TableContainer>
              <Table size="sm" variant="simple">
                <Thead>
                  <Tr>
                    <Th borderColor="light.border" color="light.textSecondary">股东名称</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>持股数 (股)</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>持股比例</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>持股变化</Th>
                    <Th borderColor="light.border" color="light.textSecondary">报告期</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {shareholders.map((item: any, index: number) => (
                    <Tr key={index} _hover={{ bg: 'light.bgSecondary' }}>
                      <Td borderColor="light.border" color="light.text">{item.shareholder_name}</Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        {item.hold_amount?.toLocaleString() || '-'}
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        {item.hold_ratio?.toFixed(2) || 0}%
                      </Td>
                      <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">
                        <Badge colorScheme={item.change_amount && item.change_amount > 0 ? 'red' : 'green'}>
                          {item.change_amount?.toLocaleString() || 0}
                        </Badge>
                      </Td>
                      <Td borderColor="light.border" color="light.text">{item.report_date}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">技术指标</Heading>
        </CardHeader>
        <CardBody>
          <IndicatorChart
            data={indicators}
            loading={indicatorLoading}
            height="300px"
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">指标数据</Heading>
        </CardHeader>
        <CardBody>
          <TableContainer>
            <Table size="sm" variant="simple">
              <Thead>
                <Tr>
                  <Th borderColor="light.border" color="light.textSecondary">日期</Th>
                  <Th borderColor="light.border" color="light.textSecondary" isNumeric>MA5</Th>
                  <Th borderColor="light.border" color="light.textSecondary" isNumeric>MA20</Th>
                  <Th borderColor="light.border" color="light.textSecondary" isNumeric>RSI6</Th>
                  <Th borderColor="light.border" color="light.textSecondary" isNumeric>MACD</Th>
                </Tr>
              </Thead>
              <Tbody>
                {indicators.slice(-20).reverse().map((item: any, index: number) => (
                  <Tr key={index} _hover={{ bg: 'light.bgSecondary' }}>
                    <Td borderColor="light.border" color="light.text">{item.date}</Td>
                    <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">{item.ma5?.toFixed(2)}</Td>
                    <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">{item.ma20?.toFixed(2)}</Td>
                    <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">{item.rsi6?.toFixed(2)}</Td>
                    <Td borderColor="light.border" isNumeric fontFamily="mono" color="light.text">{item.macd?.toFixed(4)}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        </CardBody>
      </Card>
    </VStack>
  )
}

export default StockDetail
