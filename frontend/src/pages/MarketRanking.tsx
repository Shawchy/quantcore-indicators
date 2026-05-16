/**
 * 市场排行榜页面
 * 显示实时涨跌幅排名、市场情绪等
 */
import React, { useState } from 'react'
import { Alert, Badge, Box, Button, Flex, Grid, HStack, NativeSelect, Spinner, Stat, Text, GridItem } from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { marketApi } from '../services/api'
import MarketQuotes from './MarketQuotes'
import type { MarketRankingData, MarketOverviewData } from '../types'
import MarketSentimentCard from '../components/MarketSentimentCard'
import StockRankingTable from '../components/StockRankingTable'

const MarketRankingPage: React.FC = () => {
  const [dataSource, setDataSource] = useState('sina')
  const [topN, setTopN] = useState(50)

  // 使用 React Query 获取市场排行榜数据（自动缓存和去重）
  const { 
    data: marketData, 
    isLoading: loading, 
    error: rankingError,
    refetch: refetchRanking 
  } = useQuery({
    queryKey: ['marketRanking', dataSource, topN],
    queryFn: () => marketApi.getRanking(topN, dataSource),
    staleTime: 30000,  // 30 秒内使用缓存
    gcTime: 120000,    // 缓存 2 分钟
    refetchOnWindowFocus: false,
  })

  // 使用 React Query 获取市场概览数据（自动缓存和去重）
  const { 
    data: overviewData, 
    isLoading: loadingOverview
  } = useQuery<MarketOverviewData>({
    queryKey: ['marketOverview'],
    queryFn: async () => {
      const response = await marketApi.getOverview()
      return response.data as MarketOverviewData
    },
    staleTime: 30000,  // 30 秒内使用缓存
    gcTime: 120000,    // 缓存 2 分钟
    refetchOnWindowFocus: false,
    refetchInterval: 30000, // 30 秒轮询一次
  })

  // 手动刷新
  const handleRefresh = () => {
    refetchRanking()
  }

  // 获取数据
  const rankingData = marketData as MarketRankingData | undefined
  const overview = overviewData as MarketOverviewData | undefined
  const lastUpdateTime = new Date().toLocaleTimeString()

  // 渲染加载状态
  if (loading && !marketData) {
    return (
      <Flex justify="center" align="center" h="400px">
        <Spinner size="xl" borderWidth="4px"  color="blue.500" />
      </Flex>
    )
  }

  // 渲染错误状态
  if (rankingError && !marketData) {
    return (
      <Alert.Root status="error" borderRadius="lg" p={6}>
        <Alert.Indicator />
        <Alert.Title mr={2}>获取数据失败</Alert.Title>
        {rankingError instanceof Error ? rankingError.message : '未知错误'}
        <Button size="sm" colorPalette="red" ml={4} onClick={handleRefresh}>
          重试
        </Button>
      </Alert.Root>
    )
  }

  return (
    <Box>
      {/* 顶部控制栏 */}
      <Flex justify="space-between" align="center" mb={4} bg="white" p={4} borderRadius="lg" boxShadow="sm">
        <Flex align="center" gap={4}>
          <Text fontWeight="bold" fontSize="xl" color="gray.700">
            📊 市场排行榜
          </Text>
          <Badge colorPalette="blue" fontSize="xs" px={2} py={1}>
            最后更新：{lastUpdateTime || '--:--:--'}
          </Badge>
        </Flex>
        
        <Flex align="center" gap={3}>
          <NativeSelect.Root size="sm"><NativeSelect.Field
            value={dataSource}
            onChange={(e) => setDataSource(e.target.value)}
          >
            <option value="sina">新浪数据源</option>
            <option value="dc">东方财富 (备用)</option>
          </NativeSelect.Field></NativeSelect.Root>
          
          <NativeSelect.Root size="sm"><NativeSelect.Field
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
          >
            <option value={20}>前 20</option>
            <option value={50}>前 50</option>
            <option value={100}>前 100</option>
          </NativeSelect.Field></NativeSelect.Root>
          
          <Button
            size="sm"
            colorPalette="blue"
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Flex>
      </Flex>

      {/* 市场概览和情绪 */}
      <Grid templateColumns="repeat(2, 1fr)" gap={4} mb={4}>
        <GridItem>
          {loadingOverview ? (
            <Box bg="white" p={6} borderRadius="lg" textAlign="center">
              <Spinner size="md" />
            </Box>
          ) : overview ? (
            <Box bg="white" p={6} borderRadius="lg" boxShadow="md">
              <Text fontWeight="bold" fontSize="lg" mb={4} color="gray.700">
                📈 市场概览
              </Text>
              <Grid templateColumns="repeat(3, 1fr)" gap={4}>
                <Stat.Root>
                  <Stat.Label fontSize="sm" color="gray.600">平均涨跌幅</Stat.Label>
                  <Stat.ValueText 
                    fontSize="2xl" 
                    fontWeight="bold"
                    color={overview.statistics.avg_pct_change > 0 ? 'red.500' : 'green.500'}
                  >
                    {overview.statistics.avg_pct_change > 0 ? '+' : ''}
                    {overview.statistics.avg_pct_change.toFixed(2)}%
                  </Stat.ValueText>
                  <Stat.HelpText mb={0} fontSize="xs" color="gray.500">
                    中位数：{overview.statistics.median_pct_change.toFixed(2)}%
                  </Stat.HelpText>
                </Stat.Root>
                
                <Stat.Root>
                  <Stat.Label fontSize="sm" color="gray.600">总成交额</Stat.Label>
                  <Stat.ValueText fontSize="2xl" fontWeight="bold" color="blue.500">
                    {overview.statistics.total_amount.toFixed(2)}亿
                  </Stat.ValueText>
                  <Stat.HelpText mb={0} fontSize="xs" color="gray.500">
                    平均：{overview.statistics.avg_amount.toFixed(2)}百万
                  </Stat.HelpText>
                </Stat.Root>
                
                <Stat.Root>
                  <Stat.Label fontSize="sm" color="gray.600">股票数量</Stat.Label>
                  <Stat.ValueText fontSize="2xl" fontWeight="bold" color="gray.700">
                    {overview.total_stocks.toLocaleString()}
                  </Stat.ValueText>
                  <Stat.HelpText mb={0} fontSize="xs" color="gray.500">
                    全市场
                  </Stat.HelpText>
                </Stat.Root>
              </Grid>
              
              <Box mt={4} pt={4} borderTop="1px" borderColor="gray.200">
                <Text fontSize="xs" color="gray.600" mb={2}>涨跌幅分布:</Text>
                <HStack gap={2} flexWrap="wrap">
                  <Badge colorPalette="red" fontSize="xs" px={2} py={1}>
                    &gt;5%: {overview.distribution.pct_5_plus}家
                  </Badge>
                  <Badge colorPalette="orange" fontSize="xs" px={2} py={1}>
                    3-5%: {overview.distribution.pct_3_to_5}家
                  </Badge>
                  <Badge colorPalette="gray" fontSize="xs" px={2} py={1}>
                    -3~3%: {overview.distribution.pct_minus_3_to_3}家
                  </Badge>
                  <Badge colorPalette="orange" fontSize="xs" px={2} py={1}>
                    -5~-3%: {overview.distribution.pct_minus_5_to_minus_3}家
                  </Badge>
                  <Badge colorPalette="green" fontSize="xs" px={2} py={1}>
                    &lt;-5%: {overview.distribution.pct_minus_5}家
                  </Badge>
                </HStack>
              </Box>
            </Box>
          ) : null}
        </GridItem>
        
        <GridItem>
          {rankingData && (
            <MarketSentimentCard
              stats={rankingData.market_stats}
              sentiment={rankingData.sentiment}
              totalStocks={rankingData.total_stocks}
            />
          )}
        </GridItem>
      </Grid>

      {/* 市场排行榜 */}
      <Box bg="white" p={4} borderRadius="lg" boxShadow="md" mb={4}>
        <MarketQuotes />
      </Box>

      {/* 原有的排行榜表格作为备用 */}
      <Box bg="white" p={6} borderRadius="lg" boxShadow="md" display="none">
        <Grid templateColumns="repeat(2, 1fr)" gap={4}>
          <GridItem>
            {rankingData && rankingData.rankings.gainers.length > 0 && (
              <StockRankingTable
                data={rankingData.rankings.gainers}
                type="gainers"
                showRank={true}
                maxItems={topN}
              />
            )}
          </GridItem>
          
          <GridItem>
            {rankingData && rankingData.rankings.losers.length > 0 && (
              <StockRankingTable
                data={rankingData.rankings.losers}
                type="losers"
                showRank={true}
                maxItems={topN}
              />
            )}
          </GridItem>
        </Grid>
      </Box>

      {/* 成交额和换手率榜 */}
      <Grid templateColumns="repeat(2, 1fr)" gap={4} mt={4}>
        <GridItem>
          {rankingData && rankingData.rankings.amount.length > 0 && (
            <StockRankingTable
              data={rankingData.rankings.amount}
              type="amount"
              showRank={true}
              maxItems={20}
            />
          )}
        </GridItem>
        
        <GridItem>
          {rankingData && rankingData.rankings.turnover.length > 0 && (
            <StockRankingTable
              data={rankingData.rankings.turnover}
              type="turnover"
              showRank={true}
              maxItems={20}
            />
          )}
        </GridItem>
      </Grid>

      {/* 数据说明 */}
      <Box mt={6} p={4} bg="blue.50" borderRadius="lg" borderLeft="4px" borderColor="blue.500">
        <Text fontSize="xs" color="blue.800">
          <strong>💡 数据说明：</strong>
          数据来源于爬虫接口，实时更新。建议使用新浪数据源（更稳定）。
          采集全市场数据需要约 4 分钟，请耐心等待。
          数据仅供参考，不构成投资建议。
        </Text>
      </Box>
    </Box>
  )
}

export default MarketRankingPage
