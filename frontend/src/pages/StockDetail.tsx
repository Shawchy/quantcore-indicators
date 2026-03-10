import { useParams } from 'react-router-dom'
import {
  Box,
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
  StatHelpText,
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
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import ReactECharts from 'echarts-for-react'
import { stockApi } from '../services/api'

const StockDetail = () => {
  const { code } = useParams<{ code: string }>()

  const { data: basicData, isLoading: basicLoading } = useQuery({
    queryKey: ['stockBasic', code],
    queryFn: () => stockApi.getBasic(code!),
    enabled: !!code,
  })

  const { data: klineData, isLoading: klineLoading } = useQuery({
    queryKey: ['stockKline', code],
    queryFn: () => stockApi.getKline(code!),
    enabled: !!code,
  })

  const { data: indicatorData, isLoading: indicatorLoading } = useQuery({
    queryKey: ['stockIndicators', code],
    queryFn: () => stockApi.getIndicators(code!),
    enabled: !!code,
  })

  const { data: realtimeData, isLoading: realtimeLoading } = useQuery({
    queryKey: ['stockRealtime', code],
    queryFn: () => stockApi.getRealtime(code!),
    enabled: !!code,
    refetchInterval: 30000,
  })

  const stock = basicData?.data
  const quote = realtimeData?.data
  const klines = klineData?.data || []
  const indicators = indicatorData?.data || []

  const getKlineOption = () => {
    if (!klines.length) return {}

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

  const getIndicatorOption = () => {
    if (!indicators.length) return {}

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
              <StatArrow type={quote.change_pct >= 0 ? 'increase' : 'decrease'} color={quote.change_pct >= 0 ? 'up.500' : 'down.500'} />
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
              <Tab color="light.textSecondary">日K线</Tab>
              <Tab color="light.textSecondary">周K线</Tab>
              <Tab color="light.textSecondary">月K线</Tab>
            </TabList>
            <TabPanels>
              <TabPanel p={0} pt={4}>
                <ReactECharts
                  option={getKlineOption()}
                  style={{ height: '400px' }}
                  showLoading={klineLoading}
                />
              </TabPanel>
              <TabPanel>
                <Text color="light.textMuted">周K线数据</Text>
              </TabPanel>
              <TabPanel>
                <Text color="light.textMuted">月K线数据</Text>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </CardBody>
      </Card>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">技术指标</Heading>
        </CardHeader>
        <CardBody>
          <ReactECharts
            option={getIndicatorOption()}
            style={{ height: '300px' }}
            showLoading={indicatorLoading}
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
