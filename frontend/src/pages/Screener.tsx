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
  Flex,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState, useTransition } from 'react'
import { screenerApi } from '../services/api'
import { StatCard } from '../components/StatCard'
import { PresetCondition, MarketIndustryStats } from '../types'

interface ScreenerConditions {
  industry: string
  market_cap_min: string
  market_cap_max: string
  pe_min: string
  pe_max: string
  control_degree_min: string
}

const Screener = () => {
  const [conditions, setConditions] = useState<ScreenerConditions>({
    industry: '',
    market_cap_min: '',
    market_cap_max: '',
    pe_min: '',
    pe_max: '',
    control_degree_min: '',
  })
  const [hasSearched, setHasSearched] = useState(false)
  const [isPending, startTransition] = useTransition()

  const { data: presetsData } = useQuery({
    queryKey: ['presetConditions'],
    queryFn: () => screenerApi.getPresetConditions(),
  })

  const { data: marketStatsData } = useQuery({
    queryKey: ['marketStats'],
    queryFn: () => screenerApi.getMarketStats(),
    refetchInterval: false, // 禁用自动轮询
    staleTime: 5 * 60 * 1000, // 5 分钟内使用缓存
    gcTime: 10 * 60 * 1000, // 缓存 10 分钟
  })

  const { data: resultsData, isLoading, refetch } = useQuery({
    queryKey: ['screenerQuery', conditions],
    queryFn: () => screenerApi.query(conditions),
    enabled: false,
  })

  const presets = presetsData?.data || []
  const marketStats = (marketStatsData as { data?: MarketIndustryStats } | undefined)?.data
  const results = resultsData?.data || []

  const handleSearch = () => {
    setHasSearched(true)
    refetch()
  }

  const handlePresetSelect = (preset: PresetCondition) => {
    const raw = preset.conditions as Record<string, string | number | undefined>
    const next: ScreenerConditions = {
      ...conditions,
      industry: String(raw.industry ?? ''),
      market_cap_min: String(raw.market_cap_min ?? ''),
      market_cap_max: String(raw.market_cap_max ?? ''),
      pe_min: String(raw.pe_min ?? ''),
      pe_max: String(raw.pe_max ?? ''),
      control_degree_min: String(raw.control_degree_min ?? ''),
    }
    // 使用 startTransition 优化非紧急更新
    startTransition(() => {
      setConditions(next)
      setHasSearched(true)
    })
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
      <Heading size="lg" color="light.text">
        智能选股
      </Heading>

      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <StatCard
          label="市场股票总数"
          value={marketStats?.total_stocks || '--'}
          size="md"
        />
        <StatCard
          label="筛选结果"
          value={results.length}
          size="md"
        />
        <StatCard
          label="行业数量"
          value={Object.keys(marketStats?.industry_distribution || {}).length}
          size="md"
        />
      </SimpleGrid>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">预设条件</Heading>
        </CardHeader>
        <CardBody pt={2}>
          <HStack spacing={3} wrap="wrap">
            {presets.map((preset: any) => (
              <Button
                key={preset.id}
                variant="ghost"
                size="sm"
                border="1px solid"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
                onClick={() => handlePresetSelect(preset)}
                isLoading={isPending}
              >
                {preset.name}
              </Button>
            ))}
          </HStack>
        </CardBody>
      </Card>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">筛选条件</Heading>
        </CardHeader>
        <CardBody pt={2}>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">行业</FormLabel>
              <Input
                placeholder="输入行业名称"
                value={conditions.industry}
                onChange={(e) => setConditions({ ...conditions, industry: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
              />
            </FormControl>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">市值下限 (亿)</FormLabel>
              <Input
                type="number"
                placeholder="最小市值"
                value={conditions.market_cap_min}
                onChange={(e) => setConditions({ ...conditions, market_cap_min: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
              />
            </FormControl>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">市值上限 (亿)</FormLabel>
              <Input
                type="number"
                placeholder="最大市值"
                value={conditions.market_cap_max}
                onChange={(e) => setConditions({ ...conditions, market_cap_max: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
              />
            </FormControl>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">PE 下限</FormLabel>
              <Input
                type="number"
                placeholder="最小 PE"
                value={conditions.pe_min}
                onChange={(e) => setConditions({ ...conditions, pe_min: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
              />
            </FormControl>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">PE 上限</FormLabel>
              <Input
                type="number"
                placeholder="最大 PE"
                value={conditions.pe_max}
                onChange={(e) => setConditions({ ...conditions, pe_max: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
              />
            </FormControl>
            <FormControl>
              <FormLabel color="light.textSecondary" fontSize="sm">最小控盘度</FormLabel>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="1"
                placeholder="0-1 之间"
                value={conditions.control_degree_min}
                onChange={(e) => setConditions({ ...conditions, control_degree_min: e.target.value })}
                bg="light.bgSecondary"
                borderColor="light.border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
              />
            </FormControl>
          </SimpleGrid>

          <HStack mt={6} justify="flex-end">
            <Button variant="ghost" onClick={handleReset}>重置</Button>
            <Button variant="primary" onClick={handleSearch}>筛选</Button>
          </HStack>
        </CardBody>
      </Card>

      <Card>
        <CardHeader pb={2}>
          <Heading size="sm" color="light.text">筛选结果</Heading>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <Flex justify="center" align="center" h="200px">
              <Spinner color="brand.400" />
            </Flex>
          ) : hasSearched ? (
            results.length > 0 ? (
              <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={3}>
                {results.map((stock: any) => (
                  <Card 
                    key={stock.code} 
                    size="sm" 
                    variant="outline"
                    cursor="pointer"
                    _hover={{ borderColor: 'brand.400', bg: 'light.bgSecondary', transform: 'translateY(-2px)' }}
                    transition="all 0.2s"
                  >
                    <CardBody p={3}>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="bold" color="light.text" fontFamily="mono">{stock.code}</Text>
                        <Text fontSize="sm" color="light.textSecondary">{stock.name}</Text>
                        {stock.industry && (
                          <Badge size="sm" variant="solid" colorScheme="blue" fontSize="xs">{stock.industry}</Badge>
                        )}
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            ) : (
              <Text color="light.textMuted">未找到符合条件的股票</Text>
            )
          ) : (
            <Text color="light.textMuted">请设置筛选条件后点击筛选按钮</Text>
          )}
        </CardBody>
      </Card>
    </VStack>
  )
}

export default Screener
