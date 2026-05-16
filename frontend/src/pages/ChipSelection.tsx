import { Badge, Box, Card, Flex, Heading, SimpleGrid, Slider, Spinner, Table, Text, VStack } from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import EChartsReactCore from 'echarts-for-react/lib/core'
import echarts from '../lib/echarts'
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
    <VStack gap={6} align="stretch">
      <Heading size="lg" color="light.text">
        筹码选股
      </Heading>

      <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
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

      <SimpleGrid columns={{ base: 1, lg: 2 }} gap={4}>
        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">控盘度分布</Heading>
          </Card.Header>
          <Card.Body pt={2}>
            <EChartsReactCore echarts={echarts} option={getDistributionOption()} style={{ height: '300px' }} />
          </Card.Body>
        </Card.Root>

        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">筛选条件</Heading>
          </Card.Header>
          <Card.Body pt={4}>
            <VStack gap={8} align="stretch">
              <Box>
                <Flex justify="space-between" mb={2}>
                  <Text color="light.textSecondary" fontSize="sm">最小控盘度</Text>
                  <Text color="brand.400" fontSize="sm" fontWeight="bold">{(minControl * 100).toFixed(0)}%</Text>
                </Flex>
                <Slider.Root value={[minControl * 100]} onValueChange={(e) => setMinControl(e.value[0] / 100)} min={0} max={100}>
                  <Slider.Track bg="light.bgSecondary">
                    <Slider.Range bg="brand.400" />
                  </Slider.Track>
                  <Slider.Thumb index={0} boxSize={4} bg="brand.400" />
                </Slider.Root>
              </Box>
              <Box>
                <Flex justify="space-between" mb={2}>
                  <Text color="light.textSecondary" fontSize="sm">最大控盘度</Text>
                  <Text color="brand.400" fontSize="sm" fontWeight="bold">{(maxControl * 100).toFixed(0)}%</Text>
                </Flex>
              <Slider.Root value={[maxControl * 100]} onValueChange={(e) => setMaxControl(e.value[0] / 100)} min={0} max={100}>
                  <Slider.Track bg="light.bgSecondary">
                    <Slider.Range bg="brand.400" />
                  </Slider.Track>
                  <Slider.Thumb index={0} boxSize={4} bg="brand.400" />
                </Slider.Root>
              </Box>
            </VStack>
          </Card.Body>
        </Card.Root>
      </SimpleGrid>

      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="light.text">高控盘股票列表</Heading>
        </Card.Header>
        <Card.Body>
          {screenLoading ? (
            <Flex justify="center" align="center" h="200px">
              <Spinner color="brand.400" />
            </Flex>
          ) : (
            <Box>
              <Table.Root size="sm" >
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">代码</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">名称</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >控盘度</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >股东人数</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">统计日期</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {screened.map((stock: ChipRankingItem) => (
                    <Table.Row key={stock.code} _hover={{ bg: 'light.bgSecondary' }}>
                      <Table.Cell borderColor="light.border" fontWeight="medium" color="light.text">{stock.code}</Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">{stock.name}</Table.Cell>
                      <Table.Cell borderColor="light.border" >
                        <Badge variant={stock.control_degree && stock.control_degree >= 0.7 ? 'solid' : 'subtle'}>
                          {(stock.control_degree ? stock.control_degree * 100 : 0).toFixed(1)}%
                        </Badge>
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">
                        {stock.shareholder_count?.toLocaleString() || '--'}
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">{stock.date || '--'}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          )}
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="light.text">控盘度排行</Heading>
        </Card.Header>
        <Card.Body>
          {rankingLoading ? (
            <Flex justify="center" align="center" h="200px">
              <Spinner color="brand.400" />
            </Flex>
          ) : (
            <Box maxH="400px" overflowY="auto">
              <Table.Root size="sm" >
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">排名</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">代码</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">名称</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >控盘度</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >股东人数</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {ranking.map((stock: ChipRankingItem, index: number) => (
                    <Table.Row key={stock.code} _hover={{ bg: 'light.bgSecondary' }}>
                      <Table.Cell borderColor="light.border">
                        <RankBadge rank={index + 1} />
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontWeight="medium" color="light.text">{stock.code}</Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">{stock.name}</Table.Cell>
                      <Table.Cell borderColor="light.border" >
                        <Badge variant={stock.control_degree && stock.control_degree >= 0.7 ? 'solid' : stock.control_degree && stock.control_degree >= 0.5 ? 'subtle' : 'subtle'}>
                          {(stock.control_degree ? stock.control_degree * 100 : 0).toFixed(1)}%
                        </Badge>
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">
                        {stock.shareholder_count?.toLocaleString() || '--'}
                      </Table.Cell>
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

export default ChipSelection
