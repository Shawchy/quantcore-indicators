/**
 * 市场排行榜页面
 * 显示实时涨跌幅排名、市场情绪等
 */
import React, { useState, useEffect } from 'react'
import {
  Box, Flex, Grid, GridItem, Text, Select, Button, Spinner,
  Alert, AlertIcon, AlertTitle, Badge, HStack, Stat, StatLabel, StatNumber, StatHelpText
} from '@chakra-ui/react'
import { RepeatIcon } from '@chakra-ui/icons'
import { marketApi } from '../services/api'
import type { MarketRankingData, MarketOverviewData } from '../types'
import MarketSentimentCard from '../components/MarketSentimentCard'
import StockRankingTable from '../components/StockRankingTable'

const MarketRankingPage: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketRankingData | null>(null)
  const [overviewData, setOverviewData] = useState<MarketOverviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingOverview, setLoadingOverview] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dataSource, setDataSource] = useState('sina')
  const [topN, setTopN] = useState(50)
  const [lastUpdateTime, setLastUpdateTime] = useState<string>('')

  // 获取市场排行榜数据
  const fetchMarketRanking = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await marketApi.getRanking(topN, dataSource)
      
      if (response.success && response.data) {
        setMarketData(response.data)
        setLastUpdateTime(new Date().toLocaleTimeString())
      } else {
        setError(response.message || '获取数据失败')
      }
    } catch (err: any) {
      console.error('获取市场排行榜失败:', err)
      setError(err.message || '网络错误')
    } finally {
      setLoading(false)
    }
  }

  // 获取市场概览数据
  const fetchMarketOverview = async () => {
    try {
      setLoadingOverview(true)
      const response = await marketApi.getOverview()
      
      if (response.success && response.data) {
        setOverviewData(response.data)
      }
    } catch (err: any) {
      console.error('获取市场概览失败:', err)
    } finally {
      setLoadingOverview(false)
    }
  }

  // 初始加载
  useEffect(() => {
    fetchMarketRanking()
    fetchMarketOverview()
  }, [dataSource, topN])

  // 自动刷新（每 60 秒）
  useEffect(() => {
    const interval = setInterval(() => {
      fetchMarketOverview() // 只刷新概览数据
    }, 60000)
    
    return () => clearInterval(interval)
  }, [])

  // 渲染加载状态
  if (loading && !marketData) {
    return (
      <Flex justify="center" align="center" h="400px">
        <Spinner size="xl" thickness="4px" speed="0.65s" color="blue.500" />
      </Flex>
    )
  }

  // 渲染错误状态
  if (error && !marketData) {
    return (
      <Alert status="error" borderRadius="lg" p={6}>
        <AlertIcon />
        <AlertTitle mr={2}>获取数据失败</AlertTitle>
        {error}
        <Button size="sm" colorScheme="red" ml={4} onClick={fetchMarketRanking}>
          重试
        </Button>
      </Alert>
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
          <Badge colorScheme="blue" fontSize="xs" px={2} py={1}>
            最后更新：{lastUpdateTime || '--:--:--'}
          </Badge>
        </Flex>
        
        <Flex align="center" gap={3}>
          <Select
            value={dataSource}
            onChange={(e) => setDataSource(e.target.value)}
            size="sm"
            width="150px"
          >
            <option value="sina">新浪数据源</option>
            <option value="dc">东方财富 (备用)</option>
          </Select>
          
          <Select
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            size="sm"
            width="120px"
          >
            <option value={20}>前 20</option>
            <option value={50}>前 50</option>
            <option value={100}>前 100</option>
          </Select>
          
          <Button
            size="sm"
            colorScheme="blue"
            leftIcon={<RepeatIcon />}
            onClick={fetchMarketRanking}
            isLoading={loading}
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
          ) : overviewData ? (
            <Box bg="white" p={6} borderRadius="lg" boxShadow="md">
              <Text fontWeight="bold" fontSize="lg" mb={4} color="gray.700">
                📈 市场概览
              </Text>
              <Grid templateColumns="repeat(3, 1fr)" gap={4}>
                <Stat>
                  <StatLabel fontSize="sm" color="gray.600">平均涨跌幅</StatLabel>
                  <StatNumber 
                    fontSize="2xl" 
                    fontWeight="bold"
                    color={overviewData.statistics.avg_pct_change > 0 ? 'red.500' : 'green.500'}
                  >
                    {overviewData.statistics.avg_pct_change > 0 ? '+' : ''}
                    {overviewData.statistics.avg_pct_change.toFixed(2)}%
                  </StatNumber>
                  <StatHelpText mb={0} fontSize="xs" color="gray.500">
                    中位数：{overviewData.statistics.median_pct_change.toFixed(2)}%
                  </StatHelpText>
                </Stat>
                
                <Stat>
                  <StatLabel fontSize="sm" color="gray.600">总成交额</StatLabel>
                  <StatNumber fontSize="2xl" fontWeight="bold" color="blue.500">
                    {overviewData.statistics.total_amount.toFixed(2)}亿
                  </StatNumber>
                  <StatHelpText mb={0} fontSize="xs" color="gray.500">
                    平均：{overviewData.statistics.avg_amount.toFixed(2)}百万
                  </StatHelpText>
                </Stat>
                
                <Stat>
                  <StatLabel fontSize="sm" color="gray.600">股票数量</StatLabel>
                  <StatNumber fontSize="2xl" fontWeight="bold" color="gray.700">
                    {overviewData.total_stocks.toLocaleString()}
                  </StatNumber>
                  <StatHelpText mb={0} fontSize="xs" color="gray.500">
                    全市场
                  </StatHelpText>
                </Stat>
              </Grid>
              
              <Box mt={4} pt={4} borderTop="1px" borderColor="gray.200">
                <Text fontSize="xs" color="gray.600" mb={2}>涨跌幅分布:</Text>
                <HStack spacing={2} flexWrap="wrap">
                  <Badge colorScheme="red" fontSize="xs" px={2} py={1}>
                    &gt;5%: {overviewData.distribution.pct_5_plus}家
                  </Badge>
                  <Badge colorScheme="orange" fontSize="xs" px={2} py={1}>
                    3-5%: {overviewData.distribution.pct_3_to_5}家
                  </Badge>
                  <Badge colorScheme="gray" fontSize="xs" px={2} py={1}>
                    -3~3%: {overviewData.distribution.pct_minus_3_to_3}家
                  </Badge>
                  <Badge colorScheme="orange" fontSize="xs" px={2} py={1}>
                    -5~-3%: {overviewData.distribution.pct_minus_5_to_minus_3}家
                  </Badge>
                  <Badge colorScheme="green" fontSize="xs" px={2} py={1}>
                    &lt;-5%: {overviewData.distribution.pct_minus_5}家
                  </Badge>
                </HStack>
              </Box>
            </Box>
          ) : null}
        </GridItem>
        
        <GridItem>
          {marketData && (
            <MarketSentimentCard
              stats={marketData.market_stats}
              sentiment={marketData.sentiment}
              totalStocks={marketData.total_stocks}
            />
          )}
        </GridItem>
      </Grid>

      {/* 排行榜表格 */}
      <Grid templateColumns="repeat(2, 1fr)" gap={4}>
        <GridItem>
          {marketData && marketData.rankings.gainers.length > 0 && (
            <StockRankingTable
              data={marketData.rankings.gainers}
              type="gainers"
              showRank={true}
              maxItems={topN}
            />
          )}
        </GridItem>
        
        <GridItem>
          {marketData && marketData.rankings.losers.length > 0 && (
            <StockRankingTable
              data={marketData.rankings.losers}
              type="losers"
              showRank={true}
              maxItems={topN}
            />
          )}
        </GridItem>
      </Grid>

      {/* 成交额和换手率榜 */}
      <Grid templateColumns="repeat(2, 1fr)" gap={4} mt={4}>
        <GridItem>
          {marketData && marketData.rankings.amount.length > 0 && (
            <StockRankingTable
              data={marketData.rankings.amount}
              type="amount"
              showRank={true}
              maxItems={20}
            />
          )}
        </GridItem>
        
        <GridItem>
          {marketData && marketData.rankings.turnover.length > 0 && (
            <StockRankingTable
              data={marketData.rankings.turnover}
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
