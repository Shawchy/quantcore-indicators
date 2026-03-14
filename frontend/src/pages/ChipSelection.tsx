import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
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
  SimpleGrid,
  Flex,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { chipApi } from '../services/api'
import { StatCard } from '../components/StatCard'
import { RankBadge } from '../components/RankBadge'
import { ChipRankingItem } from '../types'

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

  const ranking = rankingData?.data || [] as ChipRankingItem[]
  const screened = screenData?.data || [] as ChipRankingItem[]

  const getDistributionOption = () => {
    const bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    const counts = bins.slice(0, -1).map((_, i) => {
      return ranking.filter((s: any) => 
        s.control_degree >= bins[i] && s.control_degree < bins[i + 1]
      ).length
    })

    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
      },
      xAxis: {
        type: 'category',
        data: ['0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0'],
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b', fontSize: 11 },
      },
      yAxis: { 
        type: 'value',
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      },
      series: [{
        type: 'bar',
        data: counts,
        itemStyle: { 
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#3b82f6' },
              { offset: 1, color: '#2563eb' },
            ],
          },
          borderRadius: [4, 4, 0, 0],
        },
        barWidth: '60%',
      }],
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      <Heading size="lg" color="light.text">
        筹码选股
      </Heading>

      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <StatCard
          label="高控盘股票数"
          value={screened.length}
          helpText="控盘度高于 50%"
          size="md"
        />
        <StatCard
          label="平均控盘度"
          value={ranking.length > 0
            ? (ranking.reduce((sum: number, s: any) => sum + (s.control_degree || 0), 0) / ranking.length * 100).toFixed(1) + '%'
            : '--'}
          size="md"
        />
        <StatCard
          label="最高控盘度"
          value={ranking.length > 0
            ? (Math.max(...ranking.map((s: any) => s.control_degree || 0)) * 100).toFixed(1) + '%'
            : '--'}
          size="md"
        />
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">控盘度分布</Heading>
          </CardHeader>
          <CardBody pt={2}>
            <ReactECharts option={getDistributionOption()} style={{ height: '300px' }} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">筛选条件</Heading>
          </CardHeader>
          <CardBody pt={4}>
            <VStack spacing={8} align="stretch">
              <Box>
                <Flex justify="space-between" mb={2}>
                  <Text color="light.textSecondary" fontSize="sm">最小控盘度</Text>
                  <Text color="brand.400" fontSize="sm" fontWeight="bold">{(minControl * 100).toFixed(0)}%</Text>
                </Flex>
                <Slider value={minControl * 100} onChange={(v) => setMinControl(v / 100)} min={0} max={100}>
                  <SliderTrack bg="light.bgSecondary">
                    <SliderFilledTrack bg="brand.400" />
                  </SliderTrack>
                  <SliderThumb boxSize={4} bg="brand.400" />
                </Slider>
              </Box>
              <Box>
                <Flex justify="space-between" mb={2}>
                  <Text color="light.textSecondary" fontSize="sm">最大控盘度</Text>
                  <Text color="brand.400" fontSize="sm" fontWeight="bold">{(maxControl * 100).toFixed(0)}%</Text>
                </Flex>
                <Slider value={maxControl * 100} onChange={(v) => setMaxControl(v / 100)} min={0} max={100}>
                  <SliderTrack bg="light.bgSecondary">
                    <SliderFilledTrack bg="brand.400" />
                  </SliderTrack>
                  <SliderThumb boxSize={4} bg="brand.400" />
                </Slider>
              </Box>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">高控盘股票列表</Heading>
        </CardHeader>
        <CardBody>
          {screenLoading ? (
            <Flex justify="center" align="center" h="200px">
              <Spinner color="brand.400" />
            </Flex>
          ) : (
            <TableContainer>
              <Table size="sm" variant="simple">
                <Thead>
                  <Tr>
                    <Th borderColor="light.border" color="light.textSecondary">代码</Th>
                    <Th borderColor="light.border" color="light.textSecondary">名称</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>控盘度</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>股东人数</Th>
                    <Th borderColor="light.border" color="light.textSecondary">统计日期</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {screened.map((stock: ChipRankingItem) => (
                    <Tr key={stock.code} _hover={{ bg: 'light.bgSecondary' }}>
                      <Td borderColor="light.border" fontWeight="medium" color="light.text">{stock.code}</Td>
                      <Td borderColor="light.border" color="light.textSecondary">{stock.name}</Td>
                      <Td borderColor="light.border" isNumeric>
                        <Badge variant={stock.control_degree && stock.control_degree >= 0.7 ? 'up' : 'subtle'}>
                          {(stock.control_degree ? stock.control_degree * 100 : 0).toFixed(1)}%
                        </Badge>
                      </Td>
                      <Td borderColor="light.border" isNumeric color="light.textSecondary">
                        {stock.shareholder_count?.toLocaleString() || '--'}
                      </Td>
                      <Td borderColor="light.border" color="light.textSecondary">{stock.date || '--'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">控盘度排行</Heading>
        </CardHeader>
        <CardBody>
          {rankingLoading ? (
            <Flex justify="center" align="center" h="200px">
              <Spinner color="brand.400" />
            </Flex>
          ) : (
            <TableContainer maxH="400px" overflowY="auto">
              <Table size="sm" variant="simple">
                <Thead>
                  <Tr>
                    <Th borderColor="light.border" color="light.textSecondary">排名</Th>
                    <Th borderColor="light.border" color="light.textSecondary">代码</Th>
                    <Th borderColor="light.border" color="light.textSecondary">名称</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>控盘度</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>股东人数</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {ranking.map((stock: ChipRankingItem, index: number) => (
                    <Tr key={stock.code} _hover={{ bg: 'light.bgSecondary' }}>
                      <Td borderColor="light.border">
                        <RankBadge rank={index + 1} />
                      </Td>
                      <Td borderColor="light.border" fontWeight="medium" color="light.text">{stock.code}</Td>
                      <Td borderColor="light.border" color="light.textSecondary">{stock.name}</Td>
                      <Td borderColor="light.border" isNumeric>
                        <Badge variant={stock.control_degree && stock.control_degree >= 0.7 ? 'up' : stock.control_degree && stock.control_degree >= 0.5 ? 'subtle' : 'subtle'}>
                          {(stock.control_degree ? stock.control_degree * 100 : 0).toFixed(1)}%
                        </Badge>
                      </Td>
                      <Td borderColor="light.border" isNumeric color="light.textSecondary">
                        {stock.shareholder_count?.toLocaleString() || '--'}
                      </Td>
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
