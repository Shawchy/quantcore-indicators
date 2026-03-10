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
  FormControl,
  FormLabel,
  Input,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { screenerApi } from '../services/api'

const Screener = () => {
  const [conditions, setConditions] = useState({
    industry: '',
    market_cap_min: '',
    market_cap_max: '',
    pe_min: '',
    pe_max: '',
    control_degree_min: '',
  })
  const [hasSearched, setHasSearched] = useState(false)

  const { data: presetsData } = useQuery({
    queryKey: ['presetConditions'],
    queryFn: () => screenerApi.getPresetConditions(),
  })

  const { data: marketStatsData } = useQuery({
    queryKey: ['marketStats'],
    queryFn: () => screenerApi.getMarketStats(),
  })

  const { data: resultsData, isLoading, refetch } = useQuery({
    queryKey: ['screenerQuery', conditions],
    queryFn: () => screenerApi.query(conditions),
    enabled: false,
  })

  const presets = presetsData?.data || []
  const marketStats = marketStatsData?.data
  const results = resultsData?.data || []

  const handleSearch = () => {
    setHasSearched(true)
    refetch()
  }

  const handlePresetSelect = (preset: any) => {
    setConditions({ ...conditions, ...preset.conditions })
    setHasSearched(true)
    setTimeout(() => refetch(), 100)
  }

  const handleReset = () => {
    setConditions({
      industry: '',
      market_cap_min: '',
      market_cap_max: '',
      pe_min: '',
      pe_max: '',
      control_degree_min: '',
    })
    setHasSearched(false)
  }

  return (
    <VStack spacing={6} align="stretch">
      <Heading size="lg">智能选股</Heading>

      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>市场股票总数</StatLabel>
              <StatNumber>{marketStats?.total_stocks || '--'}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>筛选结果</StatLabel>
              <StatNumber>{results.length}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>行业数量</StatLabel>
              <StatNumber>{Object.keys(marketStats?.industry_distribution || {}).length}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="sm">预设条件</Heading>
          </HStack>
        </CardHeader>
        <CardBody>
          <HStack spacing={4} wrap="wrap">
            {presets.map((preset: any) => (
              <Button
                key={preset.id}
                variant="outline"
                size="sm"
                onClick={() => handlePresetSelect(preset)}
              >
                {preset.name}
              </Button>
            ))}
          </HStack>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <Heading size="sm">筛选条件</Heading>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
            <FormControl>
              <FormLabel>行业</FormLabel>
              <Input
                placeholder="输入行业名称"
                value={conditions.industry}
                onChange={(e) => setConditions({ ...conditions, industry: e.target.value })}
              />
            </FormControl>
            <FormControl>
              <FormLabel>市值下限(亿)</FormLabel>
              <Input
                type="number"
                placeholder="最小市值"
                value={conditions.market_cap_min}
                onChange={(e) => setConditions({ ...conditions, market_cap_min: e.target.value })}
              />
            </FormControl>
            <FormControl>
              <FormLabel>市值上限(亿)</FormLabel>
              <Input
                type="number"
                placeholder="最大市值"
                value={conditions.market_cap_max}
                onChange={(e) => setConditions({ ...conditions, market_cap_max: e.target.value })}
              />
            </FormControl>
            <FormControl>
              <FormLabel>PE下限</FormLabel>
              <Input
                type="number"
                placeholder="最小PE"
                value={conditions.pe_min}
                onChange={(e) => setConditions({ ...conditions, pe_min: e.target.value })}
              />
            </FormControl>
            <FormControl>
              <FormLabel>PE上限</FormLabel>
              <Input
                type="number"
                placeholder="最大PE"
                value={conditions.pe_max}
                onChange={(e) => setConditions({ ...conditions, pe_max: e.target.value })}
              />
            </FormControl>
            <FormControl>
              <FormLabel>最小控盘度</FormLabel>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="1"
                placeholder="0-1之间"
                value={conditions.control_degree_min}
                onChange={(e) => setConditions({ ...conditions, control_degree_min: e.target.value })}
              />
            </FormControl>
          </SimpleGrid>

          <HStack mt={6} justify="flex-end">
            <Button variant="ghost" onClick={handleReset}>重置</Button>
            <Button colorScheme="brand" onClick={handleSearch}>筛选</Button>
          </HStack>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <Heading size="sm">筛选结果</Heading>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <VStack justify="center" h="200px">
              <Spinner />
              <Text>筛选中...</Text>
            </VStack>
          ) : hasSearched ? (
            results.length > 0 ? (
              <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={4}>
                {results.map((stock: any) => (
                  <Card key={stock.code} size="sm" variant="outline">
                    <CardBody>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="bold">{stock.code}</Text>
                        <Text fontSize="sm" color="gray.500">{stock.name}</Text>
                        {stock.industry && (
                          <Badge size="sm" variant="subtle">{stock.industry}</Badge>
                        )}
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            ) : (
              <Text color="gray.500">未找到符合条件的股票</Text>
            )
          ) : (
            <Text color="gray.500">请设置筛选条件后点击筛选按钮</Text>
          )}
        </CardBody>
      </Card>
    </VStack>
  )
}

export default Screener
