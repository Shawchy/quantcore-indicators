import { Badge, Box, Button, Card, Field, Flex, HStack, Heading, Input, NumberInput, NativeSelect, SimpleGrid, Spinner, Stat, Table, VStack } from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import EChartsReactCore from 'echarts-for-react/lib/core'
import echarts from '../lib/echarts'
import { backtestApi, strategyApi } from '../services/api'

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
    <VStack gap={6} align="stretch">
      <Heading size="lg" color="light.text">
        策略回测
      </Heading>

      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="light.text">回测配置</Heading>
        </Card.Header>
        <Card.Body pt={2}>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4}>
            <Field.Root>
              <Field.Label color="light.textSecondary" fontSize="sm">选择策略</Field.Label>
              <NativeSelect.Root><NativeSelect.Field
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
              </NativeSelect.Field></NativeSelect.Root>
            </Field.Root>
            <Field.Root>
              <Field.Label color="light.textSecondary" fontSize="sm">开始日期</Field.Label>
              <Input
                type="date"
                value={config.start_date}
                onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.400' }}
                _focus={{ borderColor: 'brand.500', bg: 'white' }}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label color="light.textSecondary" fontSize="sm">结束日期</Field.Label>
              <Input
                type="date"
                value={config.end_date}
                onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.400' }}
                _focus={{ borderColor: 'brand.500', bg: 'white' }}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label color="light.textSecondary" fontSize="sm">初始资金</Field.Label>
              <NumberInput.Root
                value={String(config.initial_capital)}
                onValueChange={(e) => setConfig({ ...config, initial_capital: Number(e.value) })}
                min={10000}
                bg="light.bgSecondary"
                borderColor="light.border"
              >
                <NumberInput.Input 
                  bg="light.bgSecondary"
                  borderColor="light.border"
                />
                <NumberInput.Control>
                  <NumberInput.IncrementTrigger borderColor="light.border" color="light.textSecondary" />
                  <NumberInput.DecrementTrigger borderColor="light.border" color="light.textSecondary" />
                </NumberInput.Control>
              </NumberInput.Root>
            </Field.Root>
          </SimpleGrid>

          <HStack mt={6} justify="flex-end" gap={3}>
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
              variant="solid"
              size="md"
              
              onClick={handleRun}
              loading={runMutation.isPending}
              loadingText="回测中"
              disabled={!config.strategy_id || !config.start_date || !config.end_date}
              px={6}
            >
              开始回测
            </Button>
          </HStack>
        </Card.Body>
      </Card.Root>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4}>
        <Card.Root>
          <Card.Body>
            <Stat.Root>
              <Stat.Label color="light.textSecondary" fontSize="xs" textTransform="uppercase">总收益率</Stat.Label>
              <Stat.ValueText color={performanceData?.data?.total_return >= 0 ? 'red.500' : 'green.500'} fontSize="2xl" fontWeight="bold" fontFamily="mono" mt={1}>
                {performanceData?.data?.total_return ? `${performanceData.data.total_return >= 0 ? '+' : ''}${performanceData.data.total_return.toFixed(2)}%` : '-'}
              </Stat.ValueText>
            </Stat.Root>
          </Card.Body>
        </Card.Root>
        <Card.Root>
          <Card.Body>
            <Stat.Root>
              <Stat.Label color="light.textSecondary" fontSize="xs" textTransform="uppercase">年化收益</Stat.Label>
              <Stat.ValueText color="light.text" fontSize="2xl" fontWeight="bold" fontFamily="mono" mt={1}>
                {performanceData?.data?.annual_return ? `${performanceData.data.annual_return >= 0 ? '+' : ''}${performanceData.data.annual_return.toFixed(2)}%` : '-'}
              </Stat.ValueText>
            </Stat.Root>
          </Card.Body>
        </Card.Root>
        <Card.Root>
          <Card.Body>
            <Stat.Root>
              <Stat.Label color="light.textSecondary" fontSize="xs" textTransform="uppercase">最大回撤</Stat.Label>
              <Stat.ValueText color="red.500" fontSize="2xl" fontWeight="bold" fontFamily="mono" mt={1}>
                {performanceData?.data?.max_drawdown ? `${performanceData.data.max_drawdown.toFixed(2)}%` : '-'}
              </Stat.ValueText>
            </Stat.Root>
          </Card.Body>
        </Card.Root>
        <Card.Root>
          <Card.Body>
            <Stat.Root>
              <Stat.Label color="light.textSecondary" fontSize="xs" textTransform="uppercase">夏普比率</Stat.Label>
              <Stat.ValueText color="light.text" fontSize="2xl" fontWeight="bold" fontFamily="mono" mt={1}>
                {performanceData?.data?.sharpe_ratio || '-'}
              </Stat.ValueText>
            </Stat.Root>
          </Card.Body>
        </Card.Root>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} gap={4}>
        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">净值曲线</Heading>
          </Card.Header>
          <Card.Body pt={2}>
            <EChartsReactCore echarts={echarts} option={getEquityCurveOption()} style={{ height: '300px' }} />
          </Card.Body>
        </Card.Root>

        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">回撤曲线</Heading>
          </Card.Header>
          <Card.Body pt={2}>
            <EChartsReactCore echarts={echarts} option={getDrawdownOption()} style={{ height: '300px' }} />
          </Card.Body>
        </Card.Root>
      </SimpleGrid>

      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="light.text">回测历史</Heading>
        </Card.Header>
        <Card.Body>
          {historyLoading ? (
            <Flex justify="center" align="center" h="200px">
              <Spinner color="brand.500" />
            </Flex>
          ) : (
            <Box>
              <Table.Root size="sm" >
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">回测ID</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">策略</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">开始日期</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">结束日期</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >总收益</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">状态</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">创建时间</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {history.map((record: any) => (
                    <Table.Row key={record.backtest_id} _hover={{ bg: 'light.bgSecondary' }}>
                      <Table.Cell borderColor="light.border" fontFamily="mono" fontSize="xs" color="light.text">{record.backtest_id}</Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">{record.strategy_id}</Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">{record.start_date}</Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">{record.end_date}</Table.Cell>
                      <Table.Cell borderColor="light.border" >
                        <Badge variant={record.total_return >= 0 ? 'solid' : 'subtle'}>
                          {record.total_return >= 0 ? '+' : ''}{(record.total_return || 0).toFixed(2)}%
                        </Badge>
                      </Table.Cell>
                      <Table.Cell borderColor="light.border">
                        <Badge 
                          bg={record.status === 'completed' ? 'green.100' : 'orange.100'}
                          color={record.status === 'completed' ? 'green.700' : 'orange.700'}
                        >
                          {record.status}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">{record.created_at}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          )}
        </Card.Body>
      </Card.Root>
    </VStack>
  )
}

export default Backtest
