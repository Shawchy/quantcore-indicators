import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Badge,
  SimpleGrid,
  Spinner,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Select,
  Flex,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { sectorApi } from '../services/api'
import { RankBadge } from '../components/RankBadge'
import { SectorRankingItem } from '../types'
import { getBarOption } from '../utils/chartConfig'

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
  const ranking = rankingData?.data || [] as SectorRankingItem[]

  const barChartOption = useMemo(() => {
    return getBarOption(ranking, 'change_pct', 'name', '板块涨幅排行')
  }, [ranking])

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between" flexWrap="wrap" gap={4}>
        <Heading size="lg" color="light.text">
          板块分析
        </Heading>
        <HStack spacing={3}>
          <Select 
            value={sectorType} 
            onChange={(e) => setSectorType(e.target.value)} 
            w="150px"
            bg="light.bgSecondary"
            borderColor="light.border"
            _hover={{ borderColor: 'brand.500' }}
          >
            <option value="industry" style={{ background: '#ffffff' }}>行业板块</option>
            <option value="concept" style={{ background: '#ffffff' }}>概念板块</option>
          </Select>
          <Select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)} 
            w="150px"
            bg="light.bgSecondary"
            borderColor="light.border"
            _hover={{ borderColor: 'brand.500' }}
          >
            <option value="change_pct" style={{ background: '#ffffff' }}>按涨跌幅</option>
            <option value="volume" style={{ background: '#ffffff' }}>按成交量</option>
            <option value="amount" style={{ background: '#ffffff' }}>按成交额</option>
          </Select>
        </HStack>
      </HStack>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">板块涨幅排行</Heading>
          </CardHeader>
          <CardBody pt={2}>
            {rankingLoading ? (
              <Flex justify="center" align="center" h="400px">
                <Spinner color="brand.400" />
              </Flex>
            ) : (
              <ReactECharts option={barChartOption} style={{ height: '400px' }} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">板块列表</Heading>
          </CardHeader>
          <CardBody pt={2}>
            {listLoading ? (
              <Flex justify="center" align="center" h="400px">
                <Spinner color="brand.400" />
              </Flex>
            ) : (
              <TableContainer maxH="400px" overflowY="auto">
                <Table size="sm" variant="simple">
                  <Thead>
                    <Tr>
                      <Th borderColor="light.border" color="light.textSecondary">板块名称</Th>
                      <Th borderColor="light.border" color="light.textSecondary" isNumeric>涨跌幅</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {sectors.slice(0, 20).map((sector: SectorRankingItem) => (
                      <Tr key={sector.code} _hover={{ bg: 'light.bgSecondary' }}>
                        <Td borderColor="light.border" color="light.text">{sector.name}</Td>
                        <Td borderColor="light.border" isNumeric>
                          <Badge variant={sector.change_pct && sector.change_pct >= 0 ? 'up' : 'down'}>
                            {sector.change_pct && sector.change_pct >= 0 ? '+' : ''}{(sector.change_pct || 0).toFixed(2)}%
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
          <CardHeader pb={2}>
            <Heading size="sm" color="light.text">板块详情排行</Heading>
          </CardHeader>
          <CardBody>
            <TableContainer>
              <Table size="sm" variant="simple">
                <Thead>
                  <Tr>
                    <Th borderColor="light.border" color="light.textSecondary">排名</Th>
                    <Th borderColor="light.border" color="light.textSecondary">板块名称</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>涨跌幅</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>成交量</Th>
                    <Th borderColor="light.border" color="light.textSecondary" isNumeric>成交额</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {ranking.map((sector: SectorRankingItem, index: number) => (
                    <Tr key={sector.code} _hover={{ bg: 'light.bgSecondary' }}>
                      <Td borderColor="light.border">
                        <RankBadge rank={index + 1} />
                      </Td>
                      <Td borderColor="light.border" fontWeight="medium" color="light.text">{sector.name}</Td>
                      <Td borderColor="light.border" isNumeric>
                        <Badge variant={sector.change_pct && sector.change_pct >= 0 ? 'up' : 'down'}>
                          {sector.change_pct && sector.change_pct >= 0 ? '+' : ''}{(sector.change_pct || 0).toFixed(2)}%
                        </Badge>
                      </Td>
                      <Td borderColor="light.border" isNumeric color="light.textSecondary">
                        {sector.volume ? (sector.volume / 100000000).toFixed(2) + '亿' : '--'}
                      </Td>
                      <Td borderColor="light.border" isNumeric color="light.textSecondary">
                        {sector.amount ? (sector.amount / 100000000).toFixed(2) + '亿' : '--'}
                      </Td>
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
