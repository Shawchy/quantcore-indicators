import { Badge, Button, Card, Field, Flex, HStack, Heading, Input, SimpleGrid, Spinner, Text, VStack } from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useState, useTransition } from 'react'
import { screenerApi } from '../services/api'
import { StatCard } from '../components/StatCard'
import { PresetCondition, MarketIndustryStats, ScreenerCondition } from '../types'

interface ScreenerFormState {
  industry: string
  market_cap_min: string
  market_cap_max: string
  pe_min: string
  pe_max: string
  control_degree_min: string
}

const toApiCondition = (form: ScreenerFormState): ScreenerCondition => ({
  industry: form.industry || undefined,
  market_cap_min: form.market_cap_min ? Number(form.market_cap_min) : undefined,
  market_cap_max: form.market_cap_max ? Number(form.market_cap_max) : undefined,
  pe_min: form.pe_min ? Number(form.pe_min) : undefined,
  pe_max: form.pe_max ? Number(form.pe_max) : undefined,
  control_degree_min: form.control_degree_min ? Number(form.control_degree_min) : undefined,
})

const Screener = () => {
  const [conditions, setConditions] = useState<ScreenerFormState>({
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
    queryFn: () => screenerApi.query(toApiCondition(conditions)),
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
    const next: ScreenerFormState = {
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
    <VStack gap={6} align="stretch">
      <Heading size="lg" color="fg">
        智能选股
      </Heading>

      <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
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

      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="fg">预设条件</Heading>
        </Card.Header>
        <Card.Body pt={2}>
          <HStack gap={3} wrap="wrap">
            {presets.map((preset: any) => (
              <Button
                key={preset.id}
                variant="ghost"
                size="sm"
                border="1px solid"
                borderColor="border"
                _hover={{ borderColor: 'brand.400', bg: 'bg.subtle' }}
                onClick={() => handlePresetSelect(preset)}
                loading={isPending}
              >
                {preset.name}
              </Button>
            ))}
          </HStack>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="fg">筛选条件</Heading>
        </Card.Header>
        <Card.Body pt={2}>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
            <Field.Root>
              <Field.Label color="fg.muted" fontSize="sm">行业</Field.Label>
              <Input
                placeholder="输入行业名称"
                value={conditions.industry}
                onChange={(e) => setConditions({ ...conditions, industry: e.target.value })}
                bg="bg.subtle"
                borderColor="border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'bg.subtle' }}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label color="fg.muted" fontSize="sm">市值下限 (亿)</Field.Label>
              <Input
                type="number"
                placeholder="最小市值"
                value={conditions.market_cap_min}
                onChange={(e) => setConditions({ ...conditions, market_cap_min: e.target.value })}
                bg="bg.subtle"
                borderColor="border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'bg.subtle' }}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label color="fg.muted" fontSize="sm">市值上限 (亿)</Field.Label>
              <Input
                type="number"
                placeholder="最大市值"
                value={conditions.market_cap_max}
                onChange={(e) => setConditions({ ...conditions, market_cap_max: e.target.value })}
                bg="bg.subtle"
                borderColor="border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'bg.subtle' }}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label color="fg.muted" fontSize="sm">PE 下限</Field.Label>
              <Input
                type="number"
                placeholder="最小 PE"
                value={conditions.pe_min}
                onChange={(e) => setConditions({ ...conditions, pe_min: e.target.value })}
                bg="bg.subtle"
                borderColor="border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'bg.subtle' }}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label color="fg.muted" fontSize="sm">PE 上限</Field.Label>
              <Input
                type="number"
                placeholder="最大 PE"
                value={conditions.pe_max}
                onChange={(e) => setConditions({ ...conditions, pe_max: e.target.value })}
                bg="bg.subtle"
                borderColor="border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'bg.subtle' }}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label color="fg.muted" fontSize="sm">最小控盘度</Field.Label>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="1"
                placeholder="0-1 之间"
                value={conditions.control_degree_min}
                onChange={(e) => setConditions({ ...conditions, control_degree_min: e.target.value })}
                bg="bg.subtle"
                borderColor="border"
                _hover={{ borderColor: 'brand.500' }}
                _focus={{ borderColor: 'brand.400', bg: 'bg.subtle' }}
              />
            </Field.Root>
          </SimpleGrid>

          <HStack mt={6} justify="flex-end">
            <Button variant="ghost" onClick={handleReset}>重置</Button>
            <Button variant="solid" onClick={handleSearch}>筛选</Button>
          </HStack>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Header pb={2}>
          <Heading size="sm" color="fg">筛选结果</Heading>
        </Card.Header>
        <Card.Body>
          {isLoading ? (
            <Flex justify="center" align="center" h="200px">
              <Spinner color="brand.400" />
            </Flex>
          ) : hasSearched ? (
            results.length > 0 ? (
              <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} gap={3}>
                {results.map((stock: any) => (
                  <Card.Root 
                    key={stock.code} 
                    size="sm" 
                    variant="outline"
                    cursor="pointer"
                    _hover={{ borderColor: 'brand.400', bg: 'bg.subtle', transform: 'translateY(-2px)' }}
                    transition="all 0.2s"
                  >
                    <Card.Body p={3}>
                      <VStack align="start" gap={1}>
                        <Text fontWeight="bold" color="fg" fontFamily="mono">{stock.code}</Text>
                        <Text fontSize="sm" color="fg.muted">{stock.name}</Text>
                        {stock.industry && (
                          <Badge size="sm" variant="solid" colorPalette="blue" fontSize="xs">{stock.industry}</Badge>
                        )}
                      </VStack>
                    </Card.Body>
                  </Card.Root>
                ))}
              </SimpleGrid>
            ) : (
              <Text color="fg.subtle">未找到符合条件的股票</Text>
            )
          ) : (
            <Text color="fg.subtle">请设置筛选条件后点击筛选按钮</Text>
          )}
        </Card.Body>
      </Card.Root>
    </VStack>
  )
}

export default Screener
