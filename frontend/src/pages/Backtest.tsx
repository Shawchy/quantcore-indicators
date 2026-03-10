import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Spinner,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
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
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import ReactECharts from 'echarts-for-react'
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

  const getEquityCurveOption = () => {
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['策略净值', '基准净值'], bottom: 0 },
      grid: { left: '10%', right: '5%', bottom: '15%' },
      xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      yAxis: { type: 'value' },
      series: [
        { name: '策略净值', type: 'line', data: [1, 1.1, 1.05, 1.2, 1.15, 1.3] },
        { name: '基准净值', type: 'line', data: [1, 1.02, 1.01, 1.05, 1.03, 1.08] },
      ],
    }
  }

  const getDrawdownOption = () => {
    return {
      tooltip: { trigger: 'axis' },
      grid: { left: '10%', right: '5%', bottom: '10%' },
      xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      yAxis: { type: 'value', max: 0 },
      series: [{
        type: 'line',
        data: [0, -2, -5, -3, -8, -4],
        itemStyle: { color: '#f44336' },
        areaStyle: { color: 'rgba(244, 67, 54, 0.2)' },
      }],
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      <Heading size="lg">策略回测</Heading>

      <Card>
        <CardHeader>
          <Heading size="sm">回测配置</Heading>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
            <FormControl>
              <FormLabel>选择策略</FormLabel>
              <Select
                value={config.strategy_id}
                onChange={(e) => setConfig({ ...config, strategy_id: e.target.value })}
                placeholder="选择策略"
              >
                {strategies.map((s: any) => (
                  <option key={s.strategy_id} value={s.strategy_id}>{s.name}</option>
                ))}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel>开始日期</FormLabel>
              <Input
                type="date"
                value={config.start_date}
                onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
              />
            </FormControl>
            <FormControl>
              <FormLabel>结束日期</FormLabel>
              <Input
                type="date"
                value={config.end_date}
                onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
              />
            </FormControl>
            <FormControl>
              <FormLabel>初始资金</FormLabel>
              <NumberInput
                value={config.initial_capital}
                onChange={(_, v) => setConfig({ ...config, initial_capital: v })}
                min={10000}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>
          </SimpleGrid>

          <HStack mt={4} justify="flex-end">
            <Button
              colorScheme="brand"
              onClick={handleRun}
              isLoading={runMutation.isPending}
              isDisabled={!config.strategy_id || !config.start_date || !config.end_date}
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
              <StatLabel>总收益率</StatLabel>
              <StatNumber>
                <StatArrow type="increase" />
                +30.0%
              </StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>年化收益</StatLabel>
              <StatNumber>+25.5%</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>最大回撤</StatLabel>
              <StatNumber color="red.500">-8.0%</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>夏普比率</StatLabel>
              <StatNumber>1.85</StatNumber>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader>
            <Heading size="sm">净值曲线</Heading>
          </CardHeader>
          <CardBody>
            <ReactECharts option={getEquityCurveOption()} style={{ height: '300px' }} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <Heading size="sm">回撤曲线</Heading>
          </CardHeader>
          <CardBody>
            <ReactECharts option={getDrawdownOption()} style={{ height: '300px' }} />
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardHeader>
          <Heading size="sm">回测历史</Heading>
        </CardHeader>
        <CardBody>
          {historyLoading ? (
            <Spinner />
          ) : (
            <TableContainer>
              <Table size="sm">
                <Thead>
                  <Tr>
                    <Th>回测ID</Th>
                    <Th>策略</Th>
                    <Th>开始日期</Th>
                    <Th>结束日期</Th>
                    <Th isNumeric>总收益</Th>
                    <Th>状态</Th>
                    <Th>创建时间</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {history.map((record: any) => (
                    <Tr key={record.backtest_id}>
                      <Td>{record.backtest_id}</Td>
                      <Td>{record.strategy_id}</Td>
                      <Td>{record.start_date}</Td>
                      <Td>{record.end_date}</Td>
                      <Td isNumeric>
                        <Badge colorScheme={record.total_return >= 0 ? 'red' : 'green'}>
                          {record.total_return >= 0 ? '+' : ''}{(record.total_return || 0).toFixed(2)}%
                        </Badge>
                      </Td>
                      <Td>
                        <Badge colorScheme={record.status === 'completed' ? 'green' : 'yellow'}>
                          {record.status}
                        </Badge>
                      </Td>
                      <Td>{record.created_at}</Td>
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
