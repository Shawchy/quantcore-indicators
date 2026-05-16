/* eslint-disable @typescript-eslint/no-unused-vars */
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { Badge, Box, Breadcrumb, Button, Card, Flex, HStack, Heading, Icon, SimpleGrid, Spinner, Stat, Table, Tabs, Text, VStack } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import { FiArrowLeft } from 'react-icons/fi'
import { useQuery } from '@tanstack/react-query'
import { stockApi, realtimeApi, boardApi } from '../services/api'
import RealtimeQuotePanel from '../components/RealtimeQuote'
import TickDataTable from '../components/TickDataTable'
import { ProKLineChart as KLineChart } from '../components/charts/KLineChart'
import type { RealtimeQuoteData, TickData, StockBasic, RealtimeQuote, KLineData, TechnicalIndicator, ApiResponse, BoardInfo, CapitalFlow, Shareholder, ChartItemStyleParams } from '../types'
import { useEffect } from 'react'

const queryEnabled = (code: string | undefined, valid: boolean) => Boolean(code && valid)

const StockDetail = () => {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  
  
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

  const { data: indicatorData } = useQuery({
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

  // 实时行情数据
  const { data: realtimeQuoteData, isLoading: quoteLoading } = useQuery<RealtimeQuoteData>({
    queryKey: ['realtimeQuote', code],
    queryFn: () => realtimeApi.getQuote(code!) as unknown as Promise<RealtimeQuoteData>,
    enabled,
    refetchInterval: 30000,  // 30 秒轮询一次
    staleTime: 5 * 60 * 1000,  // 5 分钟内有效
  })

  const { data: tickData, isLoading: tickLoading } = useQuery<TickData>({
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
  
  // 显示错误提示
  useEffect(() => {
    if (code && !isValidCode) {
      toaster.create({
        title: '无效的股票代码',
        description: '请输入 6 位数字股票代码',
        type: 'error',
        duration: 5000,
        closable: true,
      })
      navigate('/')
    }
  }, [code, isValidCode, navigate])

  const stock = (basicData as { data?: StockBasic } | undefined)?.data
  const quote = (realtimeData as { data?: RealtimeQuote } | undefined)?.data
  
  // 后端返回格式：{success: true, data: {code, name, klines: [...]}}
  const klines = (() => {
    if (!klineData) return []
    
    const resp = klineData as unknown as ApiResponse<{ klines?: KLineData[]; data?: KLineData[] } | KLineData[]>
    if (resp.success && resp.data) {
      const innerData = resp.data
      
      if ('klines' in innerData && Array.isArray(innerData.klines)) {
        return innerData.klines
      }
      
      if ('data' in innerData && Array.isArray(innerData.data)) {
        return innerData.data
      }
      
      if (Array.isArray(innerData)) {
        return innerData
      }
    }
    
    if ('data' in resp && resp.data) {
      const innerData = resp.data
      if ('klines' in innerData && Array.isArray(innerData.klines)) {
        return innerData.klines
      }
      if (Array.isArray(innerData)) {
        return innerData
      }
    }
    
    return []
  })()
  
  const weeklyKlines = (() => {
    if (!weeklyKlineData) return []
    const innerData = (weeklyKlineData as unknown as ApiResponse<KLineData[] | { data: KLineData[] }>)?.data
    if (Array.isArray(innerData)) return innerData
    if (innerData && 'data' in innerData && Array.isArray(innerData.data)) return innerData.data
    return []
  })()
  
  const monthlyKlines = (() => {
    if (!monthlyKlineData) return []
    const innerData = (monthlyKlineData as unknown as ApiResponse<KLineData[] | { data: KLineData[] }>)?.data
    if (Array.isArray(innerData)) return innerData
    if (innerData && 'data' in innerData && Array.isArray(innerData.data)) return innerData.data
    return []
  })()
  
  const indicators = ((indicatorData as unknown as ApiResponse<TechnicalIndicator[]> | undefined)?.data) || []
  const boards = ((boardData as unknown as ApiResponse<BoardInfo[]> | undefined)?.data) || []
  const capitalFlows: CapitalFlow[] = []
  const shareholders: Shareholder[] = []

  // 调试日志
  useEffect(() => {
    // K线数据加载状态
  }, [klines])

  // @ts-expect-error reserved for future use
  const _getKlineOption = () => {
  //   if (!klines.length) {
  //     return {
  //       title: {
  //         text: '暂无数据',
  //         left: 'center',
  //         top: 'center',
  //         textStyle: { color: '#a0aec0', fontSize: 14 }
  //       },
  //       xAxis: { show: false },
  //       yAxis: { show: false }
  //     }
  //   }

    const dates = klines.map((k: KLineData) => k.date)
    const ohlc = klines.map((k: KLineData) => [k.open, k.close, k.low, k.high])
    const volumes = klines.map((k: KLineData) => k.volume)

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
          itemStyle: (params: ChartItemStyleParams) => {
            const idx = params.dataIndex
            const open = ohlc[idx][0]
            const close = ohlc[idx][1]
            return { color: close >= open ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)' }
          },
        },
      ],
    }
  }

  // @ts-expect-error reserved for future use
  const _getWeeklyKlineOption = () => {
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

    const dates = weeklyKlines.map((k: KLineData) => k.date)
    const ohlc = weeklyKlines.map((k: KLineData) => [k.open, k.close, k.low, k.high])
    const volumes = weeklyKlines.map((k: KLineData) => k.volume)

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
          itemStyle: (params: ChartItemStyleParams) => {
            const idx = params.dataIndex
            const open = ohlc[idx][0]
            const close = ohlc[idx][1]
            return { color: close >= open ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)' }
          },
        },
      ],
    }
  }

  // @ts-expect-error reserved for future use
  const _getMonthlyKlineOption = () => {
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

    const dates = monthlyKlines.map((k: KLineData) => k.date)
    const ohlc = monthlyKlines.map((k: KLineData) => [k.open, k.close, k.low, k.high])
    const volumes = monthlyKlines.map((k: KLineData) => k.volume)

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
          itemStyle: (params: ChartItemStyleParams) => {
            const idx = params.dataIndex
            const open = ohlc[idx][0]
            const close = ohlc[idx][1]
            return { color: close >= open ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)' }
          },
        },
      ],
    }
  }

  // @ts-expect-error reserved for future use
  const _getIndicatorOption = () => {
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

    const dates = indicators.map((i: TechnicalIndicator) => i.date)
    const macd = indicators.map((i: TechnicalIndicator) => i.macd)
    const macdSignal = indicators.map((i: TechnicalIndicator) => i.macd_signal)
    const macdHist = indicators.map((i: TechnicalIndicator) => i.macd_hist)

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
        { name: 'Hist', type: 'bar', data: macdHist, itemStyle: (params: ChartItemStyleParams) => ({ color: params.value >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)' }) },
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
    <VStack gap={6} align="stretch">
      {/* 面包屑导航和返回按钮 */}
      <HStack justify="space-between" mb={2}>
        <Breadcrumb.Root>
          <Breadcrumb.Item>
            <Breadcrumb.Link onClick={() => navigate('/')} color="light.textSecondary" _hover={{ color: 'brand.400' }}>
              首页
            </Breadcrumb.Link>
          </Breadcrumb.Item>
          {isFromWatchlist && (
            <Breadcrumb.Item>
              <Breadcrumb.Link onClick={() => navigate('/watchlist')} color="light.textSecondary" _hover={{ color: 'brand.400' }}>
                自选股
              </Breadcrumb.Link>
            </Breadcrumb.Item>
          )}
          <Breadcrumb.Item >
            <Text color="light.text" fontWeight="medium">{stock?.name || code}</Text>
          </Breadcrumb.Item>
        </Breadcrumb.Root>
        
        {isFromWatchlist && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate('/watchlist')}
          >
            <Icon as={FiArrowLeft} />
            返回自选股
          </Button>
        )}
      </HStack>

      <HStack justify="space-between" flexWrap="wrap" gap={4}>
        <VStack align="start" gap={1}>
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
            {stock?.industry && <Badge colorPalette="purple" variant="subtle">{stock.industry}</Badge>}
          </HStack>
        </VStack>

        {quote && (
          <VStack align="end" gap={1}>
            <Text 
              fontSize="3xl" 
              fontWeight="bold" 
              color={quote.change_pct >= 0 ? 'up.500' : 'down.500'}
              fontFamily="mono"
            >
              {quote.price?.toFixed(2)}
            </Text>
            <HStack>
              <Stat.Root>
                {quote.change_pct >= 0 ? <Stat.UpIndicator color="up.500" /> : <Stat.DownIndicator color="down.500" />}
              </Stat.Root>
              <Text color={quote.change_pct >= 0 ? 'up.500' : 'down.500'} fontWeight="bold" fontFamily="mono">
                {quote.change_pct >= 0 ? '+' : ''}{quote.change_pct?.toFixed(2)}%
              </Text>
            </HStack>
          </VStack>
        )}
      </HStack>

      <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
        {[
          { label: '今开', value: quote?.open?.toFixed(2) || '--' },
          { label: '最高', value: quote?.high?.toFixed(2) || '--', color: 'up.500' },
          { label: '最低', value: quote?.low?.toFixed(2) || '--', color: 'down.500' },
          { label: '成交量', value: quote?.volume ? (quote.volume / 10000).toFixed(0) + '万' : '--' },
        ].map((item) => (
          <Card.Root key={item.label} size="sm">
            <Card.Body p={4}>
              <Stat.Root size="sm">
                <Stat.Label color="light.textSecondary" fontSize="xs">{item.label}</Stat.Label>
                <Stat.ValueText fontSize="md" color={item.color || 'light.text'} fontFamily="mono">{item.value}</Stat.ValueText>
              </Stat.Root>
            </Card.Body>
          </Card.Root>
        ))}
      </SimpleGrid>

      <Card.Root>
        <Card.Body>
          <Tabs.Root variant="line">
            <Tabs.List borderColor="light.border">
              <Tabs.Trigger value="日_k_线">日 K 线</Tabs.Trigger>
              <Tabs.Trigger value="周_k_线">周 K 线</Tabs.Trigger>
              <Tabs.Trigger value="月_k_线">月 K 线</Tabs.Trigger>
            </Tabs.List>
            <Tabs.ContentGroup>
              <Tabs.Content value="周_k_线" p={0} pt={4}>
                <KLineChart
                  data={klines}
                  loading={klineLoading}
                  type="daily"
                  height="400px"
                />
              </Tabs.Content>
              <Tabs.Content value="月_k_线" p={0} pt={4}>
                <KLineChart
                  data={weeklyKlines}
                  loading={weeklyKlineLoading}
                  type="weekly"
                  height="400px"
                />
              </Tabs.Content>
              <Tabs.Content value="月K" p={0} pt={4}>
                <KLineChart
                  data={monthlyKlines}
                  loading={monthlyKlineLoading}
                  type="monthly"
                  height="400px"
                />
              </Tabs.Content>
            </Tabs.ContentGroup>
          </Tabs.Root>
        </Card.Body>
      </Card.Root>

      {/* 实时盘口 */}
      <Card.Root>
        <Card.Header pb={2}>
          <Flex justify="space-between" align="center">
            <Heading size="sm" color="light.text">
              实时盘口
            </Heading>
            {realtimeQuoteData && (
              <Badge fontSize="xs" colorPalette="blue">
                更新：{realtimeQuoteData.update_time}
              </Badge>
            )}
          </Flex>
        </Card.Header>
        <Card.Body>
          <RealtimeQuotePanel
            data={realtimeQuoteData ?? null}
            loading={quoteLoading}
            error={null}
          />
        </Card.Body>
      </Card.Root>

      {/* 成交明细 */}
      <Card.Root>
        <Card.Header pb={2}>
          <Flex justify="space-between" align="center">
            <Heading size="sm" color="light.text">
              成交明细
            </Heading>
            {tickData && (
              <Badge fontSize="xs" colorPalette="green">
                共 {tickData.total_records} 笔
              </Badge>
            )}
          </Flex>
        </Card.Header>
        <Card.Body>
          <TickDataTable
            data={tickData ?? null}
            loading={tickLoading}
            error={null}
          />
        </Card.Body>
      </Card.Root>

      {/* 所属板块 */}
      {boards.length > 0 && (
        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">所属板块</Heading>
          </Card.Header>
          <Card.Body>
            <SimpleGrid columns={[1, 2, 3]} gap={4}>
              {boards.map((board: BoardInfo) => (
                <Card.Root key={board.code || board.name} size="sm">
                  <Card.Body p={4}>
                    <VStack align="start" gap={2}>
                      <Text fontSize="xs" color="light.textSecondary">{board.board_type}</Text>
                      <Text fontSize="md" fontWeight="bold" color="light.text">{board.name}</Text>
                      <HStack gap={4}>
                        <Text fontSize="xs" color="light.textSecondary">
                          价格：{board.close_price?.toFixed(2) || '-'}
                        </Text>
                        <Badge colorPalette={board.change_pct && board.change_pct > 0 ? 'red' : 'green'}>
                          {board.change_pct?.toFixed(2) || 0}%
                        </Badge>
                      </HStack>
                    </VStack>
                  </Card.Body>
                </Card.Root>
              ))}
            </SimpleGrid>
          </Card.Body>
        </Card.Root>
      )}

      {/* 资金流向 */}
      {capitalFlows.length > 0 && (
        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">资金流向</Heading>
          </Card.Header>
          <Card.Body>
            <Box>
              <Table.Root size="sm" >
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">日期</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >收盘价</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >涨跌幅</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >主力净流入</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >主力净流入率</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >超大单</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >大单</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >中单</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >小单</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {capitalFlows.slice(-10).reverse().map((item: CapitalFlow) => (
                    <Table.Row key={item.trade_date} _hover={{ bg: 'light.bgSecondary' }}>
                      <Table.Cell borderColor="light.border" color="light.text">{item.trade_date}</Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        {item.close_price?.toFixed(2) || '-'}
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        <Badge colorPalette={item.change_pct && item.change_pct > 0 ? 'red' : 'green'}>
                          {item.change_pct?.toFixed(2) || 0}%
                        </Badge>
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        <Badge colorPalette={item.main_net_amount && item.main_net_amount > 0 ? 'red' : 'green'}>
                          {(item.main_net_amount / 10000).toFixed(0)}万
                        </Badge>
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        {item.main_net_amount_rate?.toFixed(2) || 0}%
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        {(item.buy_elg_amount / 10000).toFixed(0)}万
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        {(item.buy_lg_amount / 10000).toFixed(0)}万
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        {(item.buy_md_amount / 10000).toFixed(0)}万
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        {(item.buy_sm_amount / 10000).toFixed(0)}万
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          </Card.Body>
        </Card.Root>
      )}

      {/* 前十大股东 */}
      {shareholders.length > 0 && (
        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">前十大股东</Heading>
          </Card.Header>
          <Card.Body>
            <Box>
              <Table.Root size="sm" >
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">股东名称</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >持股数 (股)</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >持股比例</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >持股变化</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">报告期</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {shareholders.map((item: Shareholder) => (
                    <Table.Row key={item.shareholder_name} _hover={{ bg: 'light.bgSecondary' }}>
                      <Table.Cell borderColor="light.border" color="light.text">{item.shareholder_name}</Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        {item.hold_amount?.toLocaleString() || '-'}
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        {item.hold_ratio?.toFixed(2) || 0}%
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">
                        <Badge colorPalette={item.change_amount && item.change_amount > 0 ? 'red' : 'green'}>
                          {item.change_amount?.toLocaleString() || 0}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.text">{item.report_date}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          </Card.Body>
        </Card.Root>
      )}

      {/* 技术指标图表 - 暂时未实现
      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="light.text">技术指标</Heading>
        </Card.Header>
        <Card.Body>
          <IndicatorChart
            data={indicators}
            loading={indicatorLoading}
            height="300px"
          />
        </Card.Body>
      </Card.Root>
      */}

      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="light.text">指标数据</Heading>
        </Card.Header>
        <Card.Body>
          <Box>
            <Table.Root size="sm" >
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">日期</Table.ColumnHeader>
                  <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >MA5</Table.ColumnHeader>
                  <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >MA20</Table.ColumnHeader>
                  <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >RSI6</Table.ColumnHeader>
                  <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >MACD</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {indicators.slice(-20).reverse().map((item: TechnicalIndicator) => (
                  <Table.Row key={item.date} _hover={{ bg: 'light.bgSecondary' }}>
                    <Table.Cell borderColor="light.border" color="light.text">{item.date}</Table.Cell>
                    <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">{item.ma5?.toFixed(2)}</Table.Cell>
                    <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">{item.ma20?.toFixed(2)}</Table.Cell>
                    <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">{item.rsi6?.toFixed(2)}</Table.Cell>
                    <Table.Cell borderColor="light.border" fontFamily="mono" color="light.text">{item.macd?.toFixed(4)}</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
        </Card.Body>
      </Card.Root>
    </VStack>
  )
}

export default StockDetail
