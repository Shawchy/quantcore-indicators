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
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
      },
      legend: { data: ['K线', 'MA5', 'MA20'], bottom: 0 },
      grid: [
        { left: '10%', right: '8%', height: '50%' },
        { left: '10%', right: '8%', top: '65%', height: '20%' },
      ],
      xAxis: [
        { type: 'category', data: dates, gridIndex: 0 },
        { type: 'category', data: dates, gridIndex: 1 },
      ],
      yAxis: [
        { scale: true, gridIndex: 0 },
        { scale: true, gridIndex: 1, splitLine: { show: false } },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
        { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: '5%' },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: ohlc,
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
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
      tooltip: { trigger: 'axis' },
      legend: { data: ['MACD', 'Signal', 'Hist'], bottom: 0 },
      grid: { left: '10%', right: '8%', bottom: '15%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value' },
      series: [
        { name: 'MACD', type: 'line', data: macd },
        { name: 'Signal', type: 'line', data: macdSignal },
        { name: 'Hist', type: 'bar', data: macdHist },
      ],
    }
  }

  if (basicLoading) {
    return (
      <VStack justify="center" h="400px">
        <Spinner size="xl" />
        <Text>加载中...</Text>
      </VStack>
    )
  }

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <VStack align="start" spacing={1}>
          <Heading size="lg">
            {stock?.name || code}
            <Text as="span" fontSize="md" color="gray.500" ml={2}>
              {code}
            </Text>
          </Heading>
          <HStack>
            <Badge colorScheme={stock?.market === 'SH' ? 'red' : 'blue'}>
              {stock?.market}
            </Badge>
            {stock?.industry && <Badge variant="outline">{stock.industry}</Badge>}
          </HStack>
        </VStack>

        {quote && (
          <VStack align="end" spacing={1}>
            <Text fontSize="2xl" fontWeight="bold" color={quote.change_pct >= 0 ? 'red.500' : 'green.500'}>
              {quote.price?.toFixed(2)}
            </Text>
            <HStack>
              <StatArrow type={quote.change_pct >= 0 ? 'increase' : 'decrease'} />
              <Text color={quote.change_pct >= 0 ? 'red.500' : 'green.500'}>
                {quote.change_pct >= 0 ? '+' : ''}{quote.change_pct?.toFixed(2)}%
              </Text>
            </HStack>
          </VStack>
        )}
      </HStack>

      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
        <Card size="sm">
          <CardBody>
            <Stat size="sm">
              <StatLabel>今开</StatLabel>
              <StatNumber fontSize="md">{quote?.open?.toFixed(2) || '--'}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card size="sm">
          <CardBody>
            <Stat size="sm">
              <StatLabel>最高</StatLabel>
              <StatNumber fontSize="md">{quote?.high?.toFixed(2) || '--'}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card size="sm">
          <CardBody>
            <Stat size="sm">
              <StatLabel>最低</StatLabel>
              <StatNumber fontSize="md">{quote?.low?.toFixed(2) || '--'}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card size="sm">
          <CardBody>
            <Stat size="sm">
              <StatLabel>成交量</StatLabel>
              <StatNumber fontSize="md">{quote?.volume ? (quote.volume / 10000).toFixed(0) + '万' : '--'}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardBody>
          <Tabs>
            <TabList>
              <Tab>日K线</Tab>
              <Tab>周K线</Tab>
              <Tab>月K线</Tab>
            </TabList>
            <TabPanels>
              <TabPanel>
                <ReactECharts
                  option={getKlineOption()}
                  style={{ height: '400px' }}
                  showLoading={klineLoading}
                />
              </TabPanel>
              <TabPanel>
                <Text>周K线数据</Text>
              </TabPanel>
              <TabPanel>
                <Text>月K线数据</Text>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <Heading size="sm">技术指标</Heading>
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
        <CardHeader>
          <Heading size="sm">指标数据</Heading>
        </CardHeader>
        <CardBody>
          <TableContainer>
            <Table size="sm">
              <Thead>
                <Tr>
                  <Th>日期</Th>
                  <Th isNumeric>MA5</Th>
                  <Th isNumeric>MA20</Th>
                  <Th isNumeric>RSI6</Th>
                  <Th isNumeric>MACD</Th>
                </Tr>
              </Thead>
              <Tbody>
                {indicators.slice(-20).reverse().map((item: any, index: number) => (
                  <Tr key={index}>
                    <Td>{item.date}</Td>
                    <Td isNumeric>{item.ma5?.toFixed(2)}</Td>
                    <Td isNumeric>{item.ma20?.toFixed(2)}</Td>
                    <Td isNumeric>{item.rsi6?.toFixed(2)}</Td>
                    <Td isNumeric>{item.macd?.toFixed(4)}</Td>
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
