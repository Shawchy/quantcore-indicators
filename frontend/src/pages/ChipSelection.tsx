import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Spinner,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Box,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { chipApi } from '../services/api'

const ChipSelection = () => {
  const [minControl, setMinControl] = useState(0.5)
  const [maxControl, setMaxControl] = useState(1.0)

  const { data: rankingData, isLoading: rankingLoading } = useQuery({
    queryKey: ['chipRanking'],
    queryFn: () => chipApi.getRanking('desc', 50),
  })

  const { data: screenData, isLoading: screenLoading } = useQuery({
    queryKey: ['chipScreen', minControl, maxControl],
    queryFn: () => chipApi.screen(minControl, maxControl, 50),
  })

  const ranking = rankingData?.data || []
  const screened = screenData?.data || []

  const getDistributionOption = () => {
    const bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    const counts = bins.slice(0, -1).map((_, i) => {
      return ranking.filter((s: any) => 
        s.control_degree >= bins[i] && s.control_degree < bins[i + 1]
      ).length
    })

    return {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: ['0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0'],
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: counts,
        itemStyle: { color: '#2196f3' },
      }],
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      <Heading size="lg">筹码选股</Heading>

      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>高控盘股票数</StatLabel>
              <StatNumber>{screened.length}</StatNumber>
              <StatHelpText>控盘度 > 50%</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>平均控盘度</StatLabel>
              <StatNumber>
                {ranking.length > 0
                  ? (ranking.reduce((sum: number, s: any) => sum + (s.control_degree || 0), 0) / ranking.length * 100).toFixed(1) + '%'
                  : '--'}
              </StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>最高控盘度</StatLabel>
              <StatNumber>
                {ranking.length > 0
                  ? (Math.max(...ranking.map((s: any) => s.control_degree || 0)) * 100).toFixed(1) + '%'
                  : '--'}
              </StatNumber>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader>
            <Heading size="sm">控盘度分布</Heading>
          </CardHeader>
          <CardBody>
            <ReactECharts option={getDistributionOption()} style={{ height: '300px' }} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <Heading size="sm">筛选条件</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={6} align="stretch">
              <Box>
                <Text mb={2}>最小控盘度: {(minControl * 100).toFixed(0)}%</Text>
                <Slider value={minControl * 100} onChange={(v) => setMinControl(v / 100)} min={0} max={100}>
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </Box>
              <Box>
                <Text mb={2}>最大控盘度: {(maxControl * 100).toFixed(0)}%</Text>
                <Slider value={maxControl * 100} onChange={(v) => setMaxControl(v / 100)} min={0} max={100}>
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </Box>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardHeader>
          <Heading size="sm">高控盘股票列表</Heading>
        </CardHeader>
        <CardBody>
          {screenLoading ? (
            <Spinner />
          ) : (
            <TableContainer>
              <Table size="sm">
                <Thead>
                  <Tr>
                    <Th>代码</Th>
                    <Th>名称</Th>
                    <Th isNumeric>控盘度</Th>
                    <Th isNumeric>股东人数</Th>
                    <Th>统计日期</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {screened.map((stock: any) => (
                    <Tr key={stock.code} _hover={{ bg: 'gray.50' }}>
                      <Td fontWeight="medium">{stock.code}</Td>
                      <Td>{stock.name}</Td>
                      <Td isNumeric>
                        <Badge colorScheme={stock.control_degree >= 0.7 ? 'red' : 'orange'}>
                          {(stock.control_degree * 100).toFixed(1)}%
                        </Badge>
                      </Td>
                      <Td isNumeric>{stock.shareholder_count?.toLocaleString() || '--'}</Td>
                      <Td>{stock.date || '--'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <Heading size="sm">控盘度排行</Heading>
        </CardHeader>
        <CardBody>
          {rankingLoading ? (
            <Spinner />
          ) : (
            <TableContainer maxH="400px" overflowY="auto">
              <Table size="sm">
                <Thead>
                  <Tr>
                    <Th>排名</Th>
                    <Th>代码</Th>
                    <Th>名称</Th>
                    <Th isNumeric>控盘度</Th>
                    <Th isNumeric>股东人数</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {ranking.map((stock: any, index: number) => (
                    <Tr key={stock.code} _hover={{ bg: 'gray.50' }}>
                      <Td>{index + 1}</Td>
                      <Td fontWeight="medium">{stock.code}</Td>
                      <Td>{stock.name}</Td>
                      <Td isNumeric>
                        <Badge colorScheme={stock.control_degree >= 0.7 ? 'red' : stock.control_degree >= 0.5 ? 'orange' : 'gray'}>
                          {(stock.control_degree * 100).toFixed(1)}%
                        </Badge>
                      </Td>
                      <Td isNumeric>{stock.shareholder_count?.toLocaleString() || '--'}</Td>
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

export default ChipSelection
