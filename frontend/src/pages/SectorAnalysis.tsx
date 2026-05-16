import { Badge, Box, Card, Flex, HStack, Heading, NativeSelect, SimpleGrid, Spinner, Table, VStack } from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import EChartsReactCore from 'echarts-for-react/lib/core'
import echarts from '../lib/echarts'
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
    <VStack gap={6} align="stretch">
      <HStack justify="space-between" flexWrap="wrap" gap={4}>
        <Heading size="lg" color="light.text">
          板块分析
        </Heading>
        <HStack gap={3}>
          <NativeSelect.Root size="sm"><NativeSelect.Field 
            value={sectorType} 
            onChange={(e) => setSectorType(e.target.value)} 
            w="150px"
            bg="light.bgSecondary"
            borderColor="light.border"
            _hover={{ borderColor: 'brand.500' }}
          >
            <option value="industry" style={{ background: '#ffffff' }}>行业板块</option>
            <option value="concept" style={{ background: '#ffffff' }}>概念板块</option>
          </NativeSelect.Field></NativeSelect.Root>
          <NativeSelect.Root size="sm"><NativeSelect.Field 
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
          </NativeSelect.Field></NativeSelect.Root>
        </HStack>
      </HStack>

      <SimpleGrid columns={{ base: 1, lg: 2 }} gap={4}>
        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">板块涨幅排行</Heading>
          </Card.Header>
          <Card.Body pt={2}>
            {rankingLoading ? (
              <Flex justify="center" align="center" h="400px">
                <Spinner color="brand.400" />
              </Flex>
            ) : (
              <EChartsReactCore echarts={echarts} option={barChartOption} style={{ height: '400px' }} />
            )}
          </Card.Body>
        </Card.Root>

        <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">板块列表</Heading>
          </Card.Header>
          <Card.Body pt={2}>
            {listLoading ? (
              <Flex justify="center" align="center" h="400px">
                <Spinner color="brand.400" />
              </Flex>
            ) : (
              <Box maxH="400px" overflowY="auto">
                <Table.Root size="sm" >
                  <Table.Header>
                    <Table.Row>
                      <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">板块名称</Table.ColumnHeader>
                      <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >涨跌幅</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {sectors.slice(0, 20).map((sector: SectorRankingItem) => (
                      <Table.Row key={sector.code} _hover={{ bg: 'light.bgSecondary' }}>
                        <Table.Cell borderColor="light.border" color="light.text">{sector.name}</Table.Cell>
                        <Table.Cell borderColor="light.border" >
                          <Badge variant={sector.change_pct && sector.change_pct >= 0 ? 'solid' : 'subtle'}>
                            {sector.change_pct && sector.change_pct >= 0 ? '+' : ''}{(sector.change_pct || 0).toFixed(2)}%
                          </Badge>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
              </Box>
            )}
          </Card.Body>
        </Card.Root>
      </SimpleGrid>

      <Card.Root>
          <Card.Header pb={2}>
            <Heading size="sm" color="light.text">板块详情排行</Heading>
          </Card.Header>
          <Card.Body>
            <Box>
              <Table.Root size="sm" >
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">排名</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary">板块名称</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >涨跌幅</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >成交量</Table.ColumnHeader>
                    <Table.ColumnHeader borderColor="light.border" color="light.textSecondary" >成交额</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {ranking.map((sector: SectorRankingItem, index: number) => (
                    <Table.Row key={sector.code} _hover={{ bg: 'light.bgSecondary' }}>
                      <Table.Cell borderColor="light.border">
                        <RankBadge rank={index + 1} />
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" fontWeight="medium" color="light.text">{sector.name}</Table.Cell>
                      <Table.Cell borderColor="light.border" >
                        <Badge variant={sector.change_pct && sector.change_pct >= 0 ? 'solid' : 'subtle'}>
                          {sector.change_pct && sector.change_pct >= 0 ? '+' : ''}{(sector.change_pct || 0).toFixed(2)}%
                        </Badge>
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">
                        {sector.volume ? (sector.volume / 100000000).toFixed(2) + '亿' : '--'}
                      </Table.Cell>
                      <Table.Cell borderColor="light.border" color="light.textSecondary">
                        {sector.amount ? (sector.amount / 100000000).toFixed(2) + '亿' : '--'}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          </Card.Body>
        </Card.Root>
    </VStack>
  )
}

export default SectorAnalysis
