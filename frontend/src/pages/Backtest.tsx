import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Badge,
  Button,
  Spinner,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  FormControl,
  FormLabel,
  Input,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Flex,
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { backtestApi, strategyApi } from '../services/api'
import { FiPlay } from 'react-icons/fi'

const Backtest = () => {
  const queryClient = useQueryClient()
  const [config, setConfig] = useState({
    strategy_id: '',
    start_date: '',
    end_date: '',
    initial_capital: 1000000,
  })

  const { data: strategiesData } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => strategyApi.getList(),
  })

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['backtestHistory'],
    queryFn: () => backtestApi.getHistory(20),
  })

  const runMutation = useMutation({
    mutationFn: () => backtestApi.run(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backtestHistory'] })
    },
  })

  const strategies = strategiesData?.data || []
  const history = historyData?.data || []

  const handleRun = () => {
    runMutation.mutate()
  }

  // 获取最新回测结果的详细数据
  const latestBacktestId = history.length > 0 ? history[0].backtest_id : null
  const { data: performanceData } = useQuery({
    queryKey: ['backtestPerformance', latestBacktestId],
    queryFn: () => latestBacktestId ? backtestApi.getPerformance(latestBacktestId) : Promise.resolve(null),
    enabled: !!latestBacktestId,
  })

  const getEquityCurveOption = () => {
    // 使用真实回测数据
    const performance = performanceData?.data
    const equityCurve = performance?.equity_curve || []
    const benchmarkCurve = performance?.benchmark_curve || []
    
    const dates = equityCurve.map((item: any) => item.date?.slice(5) || '')
    const strategyValues = equityCurve.map((item: any) => item.value || 1)
    const benchmarkValues = benchmarkCurve.map((item: any) => item.value || 1)
    
    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      legend: { 
        data: ['策略净值', '基准净值'], 
        bottom: 0,
        textStyle: { color: '#64748b' },
      },
      grid: { left: '10%', right: '5%', bottom: '15%' },
      xAxis: { 
        type: 'category', 
        data: dates.length > 0 ? dates : [],
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b' },
      },
      yAxis: { 
        type: 'value',
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
      },
      series: [
        { 
          name: '策略净值', 
          type: 'line', 
          data: strategyValues.length > 0 ? strategyValues : [],
          smooth: true,
          lineStyle: { color: 'brand.500', width: 2 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(49, 151, 149, 0.3)' },
                { offset: 1, color: 'rgba(49, 151, 149, 0)' },
              ],
            },
          },
        },
        { 
          name: '基准净值', 
          type: 'line', 
          data: benchmarkValues.length > 0 ? benchmarkValues : [],
          smooth: true,
          lineStyle: { color: '#94a3b8', width: 2 },
        },
      ],
    }
  }

  const getDrawdownOption = () => {
    // 使用真实回测数据
    const performance = performanceData?.data
    const drawdownCurve = performance?.drawdown_curve || []
    
    const dates = drawdownCurve.map((item: any) => item.date?.slice(5) || '')
    const drawdowns = drawdownCurve.map((item: any) => item.value || 0)
    
    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      grid: { left: '10%', right: '5%', bottom: '10%' },
      xAxis: { 
        type: 'category', 
        data: dates.length > 0 ? dates : [],
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b' },
      },
      yAxis: { 
        type: 'value', 
        max: 0,
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b', formatter: '{value}%' },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
      },
      series: [{
        type: 'line',
        data: drawdowns.length > 0 ? drawdowns : [],
        smooth: true,
        itemStyle: { color: 'up.500' },
        areaStyle: { color: 'rgba(229, 62, 62, 0.2)' },
      }],
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      <Heading size="lg" color="light.text">
        策略回测
      </Heading>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">回测配置</Heading>
        </CardHeader>
        <CardBody pt={2}>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">选择策略</FormLabel>
              <Select
                value={config.strategy_id}
                onChange={(e) => setConfig({ ...config, strategy_id: e.target.value })}
                placeholder="选择策略"
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.400' }}
                _focus={{ borderColor: 'brand.500', bg: 'white' }}
              >
                {strategies.map((s: any) => (
                  <option key={s.strategy_id} value={s.strategy_id} style={{ background: '#fff' }}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">开始日期</FormLabel>
              <Input
                type="date"
                value={config.start_date}
                onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.400' }}
                _focus={{ borderColor: 'brand.500', bg: 'white' }}
              />
            </FormControl>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">结束日期</FormLabel>
              <Input
                type="date"
                value={config.end_date}
                onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.400' }}
                _focus={{ borderColor: 'brand.500', bg: 'white' }}
              />
            </FormControl>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">初始资金</FormLabel>
              <NumberInput
                value={config.initial_capital}
                onChange={(_, v) => setConfig({ ...config, initial_capital: v })}
                min={10000}
                bg="light.bgSecondary"
                borderColor="light.border"
              >
                <NumberInputField 
                  bg="light.bgSecondary"
                  borderColor="light.border"
                />
                <NumberInputStepper>
                  <NumberIncrementStepper borderColor="light.border" color="light.textSecondary" />
                  <NumberDecrementStepper borderColor="light.border" color="light.textSecondary" />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>
          </SimpleGrid>

          <HStack mt={6} justify="flex-end" spacing={3}>
            <Button
              variant="ghost"
              size="md"
              onClick={() => {
                setConfig({
                  strategy_id: '',
                  start_date: '',
                  end_date: '',
                  initial_capital: 1000000,
                })
              }}
            >
              重置
            </Button>
            <Button
              variant="primary"
              size="md"
              leftIcon={runMutation.isPending ? <Spinner size="sm" /> : <FiPlay />}
              onClick={handleRun}
              isLoading={runMutation.isPending}
              loadingText="回测中"
              isDisabled={!config.strategy_id || !config.start_date || !config.end_date}
              px={6}
            >
              开始回测
            </Button>
          </HStack>
        </CardBody>
      </Card>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel color="light.textSecondary" fontSize="xs" textTransform="uppercase">总收益率</StatLabel>
              <StatNumber color={performanceData?.data?.total_return >= 0 ? 'red.500' : 'green.500'} fontSize="2xl" fontWeight="bold" fontFamily="mono" mt={1}>
                {performanceData?.data?.total_return ? `${performanceData.data.total_return >= 0 ? '+' : ''}${performanceData.data.total_return.toFixed(2)}%` : '-'}
              </StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel color="light.textSecondary" fontSize="xs" textTransform="uppercase">年化收益</StatLabel>
              <StatNumber color="light.text" fontSize="2xl" fontWeight="bold" fontFamily="mono" mt={1}>
                {performanceData?.data?.annual_return ? `${performanceData.data.annual_return >= 0 ? '+' : ''}${performanceData.data.annual_return.toFixed(2)}%` : '-'}
              </StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel color="light.textSecondary" fontSize="xs" textTransform="uppercase">最大回撤</StatLabel>
              <StatNumber color="red.500" fontSize="2xl" fontWeight="bold" fontFamily="mono" mt={1}>
                {performanceData?.data?.max_drawdown ? `${performanceData.data.max_drawdown.toFixed(2)}%` : '-'}
              </StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel color="light.textSecondary" fontSize="xs" textTransform="uppercase">夏普比率</StatLabel>
              <StatNumber color="light.text" fontSize="2xl" fontWeight="bold" fontFamily="mono" mt={1}>
                {performanceData?.data?.sharpe_ratio || '-'}
              </StatNumber>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">净值曲线</Heading>
          </CardHeader>
          <CardBody pt={2}>
            <ReactECharts option={getEquityCurveOption()} style={{ height: '300px' }} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">回撤曲线</Heading>
          </CardHeader>
          <CardBody pt={2}>
            <ReactECharts option={getDrawdownOption()} style={{ height: '300px' }} />
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">回测历史</Heading>
        </CardHeader>
        <CardBody>
          {historyLoading ? (
            <Flex justify="center" align="center" h="200px">
              <Spinner color="brand.500" />
            </Flex>
          ) : (
            <TableContainer>
              <Table size="sm" variant="simple">
                <Thead>
                  <Tr>
                    <Th borderColor="light.border" color="light.textSecondary">回测ID</Th>
                    <Th borderColor="light.border" color="light.textSecondary">策略</Th>
                    <Th borderColor="light.border" color="light.textSecondary">开始日期</Th>
                    <Th borderColor="light.border" color="light.textSecondary">结束日期</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>总收益</Th>
                    <Th borderColor="light.border" color="light.textSecondary">状态</Th>
                    <Th borderColor="light.border" color="light.textSecondary">创建时间</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {history.map((record: any) => (
                    <Tr key={record.backtest_id} _hover={{ bg: 'light.bgSecondary' }}>
                      <Td borderColor="light.border" fontFamily="mono" fontSize="xs" color="light.text">{record.backtest_id}</Td>
                      <Td borderColor="light.border" color="light.textSecondary">{record.strategy_id}</Td>
                      <Td borderColor="light.border" color="light.textSecondary">{record.start_date}</Td>
                      <Td borderColor="light.border" color="light.textSecondary">{record.end_date}</Td>
                      <Td borderColor="light.border" isNumeric>
                        <Badge variant={record.total_return >= 0 ? 'up' : 'down'}>
                          {record.total_return >= 0 ? '+' : ''}{(record.total_return || 0).toFixed(2)}%
                        </Badge>
                      </Td>
                      <Td borderColor="light.border">
                        <Badge 
                          bg={record.status === 'completed' ? 'green.100' : 'orange.100'}
                          color={record.status === 'completed' ? 'green.700' : 'orange.700'}
                        >
                          {record.status}
                        </Badge>
                      </Td>
                      <Td borderColor="light.border" color="light.textSecondary">{record.created_at}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          )}
        </CardBody>
      </Card>
    </VStack>
  )
}

export default Backtest
