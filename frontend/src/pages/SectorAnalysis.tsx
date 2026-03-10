import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  SimpleGrid,
  Spinner,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Select,
  Button,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { sectorApi } from '../services/api'

const SectorAnalysis = () => {
  const [sectorType, setSectorType] = useState('industry')
  const [sortBy, setSortBy] = useState('change_pct')

  const { data: sectorListData, isLoading: listLoading } = useQuery({
    queryKey: ['sectorList', sectorType],
    queryFn: () => sectorApi.getList(sectorType),
  })

  const { data: rankingData, isLoading: rankingLoading } = useQuery({
    queryKey: ['sectorRanking', sectorType, sortBy],
    queryFn: () => sectorApi.getRanking(sectorType, sortBy, 20),
  })

  const sectors = sectorListData?.data || []
  const ranking = rankingData?.data || []

  const getBarOption = () => {
    const top10 = ranking.slice(0, 10)
    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '15%', right: '5%', bottom: '10%', top: '5%' },
      xAxis: { type: 'value' },
      yAxis: {
        type: 'category',
        data: top10.map((s: any) => s.name).reverse(),
        axisLabel: { width: 80, overflow: 'truncate' },
      },
      series: [{
        type: 'bar',
        data: top10.map((s: any) => s.change_pct || 0).reverse(),
        itemStyle: {
          color: (params: any) => params.value >= 0 ? '#f44336' : '#4caf50',
        },
      }],
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Heading size="lg">板块分析</Heading>
        <HStack>
          <Select value={sectorType} onChange={(e) => setSectorType(e.target.value)} w="150px">
            <option value="industry">行业板块</option>
            <option value="concept">概念板块</option>
          </Select>
          <Select value={sortBy} onChange={(e) => setSortBy(e.target.value)} w="150px">
            <option value="change_pct">按涨跌幅</option>
            <option value="volume">按成交量</option>
            <option value="amount">按成交额</option>
          </Select>
        </HStack>
      </HStack>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader>
            <Heading size="sm">板块涨幅排行</Heading>
          </CardHeader>
          <CardBody>
            {rankingLoading ? (
              <Spinner />
            ) : (
              <ReactECharts option={getBarOption()} style={{ height: '400px' }} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <Heading size="sm">板块列表</Heading>
          </CardHeader>
          <CardBody>
            {listLoading ? (
              <Spinner />
            ) : (
              <TableContainer maxH="400px" overflowY="auto">
                <Table size="sm">
                  <Thead>
                    <Tr>
                      <Th>板块名称</Th>
                      <Th isNumeric>涨跌幅</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {sectors.slice(0, 20).map((sector: any) => (
                      <Tr key={sector.code} _hover={{ bg: 'gray.50' }}>
                        <Td>{sector.name}</Td>
                        <Td isNumeric>
                          <Badge colorScheme={sector.change_pct >= 0 ? 'red' : 'green'}>
                            {sector.change_pct >= 0 ? '+' : ''}{(sector.change_pct || 0).toFixed(2)}%
                          </Badge>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </TableContainer>
            )}
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardHeader>
          <Heading size="sm">板块详情排行</Heading>
        </CardHeader>
        <CardBody>
          <TableContainer>
            <Table size="sm">
              <Thead>
                <Tr>
                  <Th>排名</Th>
                  <Th>板块名称</Th>
                  <Th isNumeric>涨跌幅</Th>
                  <Th isNumeric>成交量</Th>
                  <Th isNumeric>成交额</Th>
                </Tr>
              </Thead>
              <Tbody>
                {ranking.map((sector: any, index: number) => (
                  <Tr key={sector.code} _hover={{ bg: 'gray.50' }}>
                    <Td>{index + 1}</Td>
                    <Td fontWeight="medium">{sector.name}</Td>
                    <Td isNumeric>
                      <Badge colorScheme={sector.change_pct >= 0 ? 'red' : 'green'}>
                        {sector.change_pct >= 0 ? '+' : ''}{(sector.change_pct || 0).toFixed(2)}%
                      </Badge>
                    </Td>
                    <Td isNumeric>{sector.volume ? (sector.volume / 100000000).toFixed(2) + '亿' : '--'}</Td>
                    <Td isNumeric>{sector.amount ? (sector.amount / 100000000).toFixed(2) + '亿' : '--'}</Td>
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

export default SectorAnalysis
