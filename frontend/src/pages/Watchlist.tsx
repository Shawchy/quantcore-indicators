import {
  Card,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  IconButton,
  Table,
  Spinner,
  Dialog,
  Input,
  Tabs,
  Box,
  Flex,
  Icon,
  Separator,
  createToaster,
} from '@chakra-ui/react'
import { useColorModeValue } from '../components/ui/color-mode'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FiTrash2, FiPlus, FiRefreshCw, FiStar, FiTrendingUp, FiTrendingDown, FiActivity } from 'react-icons/fi'
import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { watchlistApi } from '../services/api'
import { fundApi } from '../services/fund'
import fundStorage from '../services/fundStorage'
import { FundInfo } from '../services/fund'
import { getMarketColor } from '../utils/marketColors'

const toaster = createToaster({
  placement: 'bottom-end',
  max: 5,
})

const Watchlist = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [selectedCode, setSelectedCode] = useState<string>('')
  const [selectedType, setSelectedType] = useState<'stock' | 'fund'>('stock')
  const [addCode, setAddCode] = useState('')
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [isAddOpen, setIsAddOpen] = useState(false)
  const cancelRef = useRef<HTMLButtonElement>(null)

  const cardBg = useColorModeValue('white', 'gray.800')
  const cardHoverBg = useColorModeValue('gray.50', 'gray.700')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const rowAltBg = useColorModeValue('gray.50', 'gray.750')

  const { data: stockWatchlistData, isLoading: stockLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => watchlistApi.getList(),
  })

  const { data: fundWatchlistData, isLoading: fundLoading, refetch: refetchFundWatchlist } = useQuery({
    queryKey: ['fundWatchlist'],
    queryFn: async () => {
      const codes = fundStorage.getWatchlist()
      
      if (codes.length === 0) {
        return []
      }
      
      const infoRes = await fundApi.getFundBaseInfo(codes)
      return Array.isArray(infoRes.data) ? infoRes.data : [infoRes.data]
    },
  })

  const { data: quotesData, isLoading: quotesLoading, refetch } = useQuery({
    queryKey: ['watchlistQuotes'],
    queryFn: () => watchlistApi.getQuotes(),
  })

  const { data: fundQuotesData, isLoading: fundQuotesLoading, refetch: refetchFundQuotes } = useQuery({
    queryKey: ['fundWatchlistQuotes'],
    queryFn: async () => {
      const codes = fundStorage.getWatchlist()
      if (codes.length === 0) return []
      
      const rateRes = await fundApi.getFundRealtimeRate(codes)
      return Array.isArray(rateRes.data) ? rateRes.data : [rateRes.data]
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (code: string) => watchlistApi.remove(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      queryClient.invalidateQueries({ queryKey: ['watchlistQuotes'] })
      setIsDeleteOpen(false)
      toaster.create({
        title: '删除成功',
        description: `已删除股票 ${selectedCode}`,
        type: 'success',
      })
    },
    onError: (error: any) => {
      toaster.create({
        title: '删除失败',
        description: error.message,
        type: 'error',
      })
    },
  })

  const deleteFundMutation = useMutation({
    mutationFn: (code: string) => {
      fundStorage.removeFromWatchlist(code)
      return Promise.resolve()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fundWatchlist'] })
      queryClient.invalidateQueries({ queryKey: ['fundWatchlistQuotes'] })
      setIsDeleteOpen(false)
      toaster.create({
        title: '删除成功',
        description: `已删除基金 ${selectedCode}`,
        type: 'success',
      })
    },
  })

  const handleDelete = (code: string, type: 'stock' | 'fund' = 'stock') => {
    setSelectedCode(code)
    setSelectedType(type)
    setIsDeleteOpen(true)
  }

  const confirmDelete = () => {
    if (selectedType === 'stock') {
      deleteMutation.mutate(selectedCode)
    } else {
      deleteFundMutation.mutate(selectedCode)
    }
  }

  const handleAddToWatchlist = () => {
    setIsAddOpen(true)
  }

  const confirmAdd = () => {
    if (selectedType === 'stock') {
      watchlistApi.add(addCode)
        .then(() => {
          queryClient.invalidateQueries({ queryKey: ['watchlist'] })
          queryClient.invalidateQueries({ queryKey: ['watchlistQuotes'] })
          toaster.create({
            title: '添加成功',
            description: `已添加股票 ${addCode}`,
            type: 'success',
          })
          setAddCode('')
          setIsAddOpen(false)
        })
        .catch((err) => {
          toaster.create({
            title: '添加失败',
            description: err.message || '请重试',
            type: 'error',
          })
        })
    } else {
      const fundCode = addCode.trim()
      
      if (!/^\d{6}$/.test(fundCode)) {
        toaster.create({
          title: '添加失败',
          description: '请输入 6 位数字的基金代码',
          type: 'error',
        })
        return
      }
      
      fundStorage.addToWatchlist(fundCode)
      
      refetchFundWatchlist().catch((err) => {
        console.error('[Watchlist] 基金列表刷新失败:', err)
      })
      
      refetchFundQuotes().catch((err) => {
        console.error('[Watchlist] 行情数据刷新失败:', err)
      })
      
      toaster.create({
        title: '添加成功',
        description: `已添加基金 ${fundCode}`,
        type: 'success',
      })
      setAddCode('')
      setIsAddOpen(false)
    }
  }

  const renderStockWatchlist = () => {
    if (stockLoading || quotesLoading) {
      return (
        <VStack py={12}>
          <Spinner size="xl" color="blue.500" />
          <Text color="gray.500" fontSize="sm">加载自选股数据...</Text>
        </VStack>
      )
    }

    const watchlist = (stockWatchlistData?.data || []).map((item: any) => item.code || item)
    const quotes = (quotesData?.data || []).filter((q: any) => q !== null && q !== undefined)

    if (watchlist.length === 0) {
      return (
        <VStack py={16} gap={6}>
          <Icon as={FiStar} w={16} h={16} color="gray.300" />
          <VStack gap={2}>
            <Text color="gray.500" fontSize="lg">暂无自选股</Text>
            <Text color="gray.400" fontSize="sm">点击右上角添加您关注的股票</Text>
          </VStack>
          <Button 
            colorPalette="blue" 
            onClick={handleAddToWatchlist}
            size="md"
          >
            <FiPlus /> 添加自选股
          </Button>
        </VStack>
      )
    }

    const riseCount = quotes.filter((q: any) => q.change_percent !== null && q.change_percent !== undefined && q.change_percent > 0).length
    const fallCount = quotes.filter((q: any) => q.change_percent !== null && q.change_percent !== undefined && q.change_percent < 0).length
    const flatCount = quotes.filter((q: any) => q.change_percent !== null && q.change_percent !== undefined && q.change_percent === 0).length

    return (
      <>
        <Flex justify="space-between" align="center" mb={4}>
          <HStack gap={2}>
            <Button 
              size="sm" 
              colorPalette="blue" 
              onClick={handleAddToWatchlist}
              variant="solid"
            >
              <FiPlus /> 添加股票
            </Button>
            <IconButton
              aria-label="刷新"
              size="sm"
              onClick={() => refetch()}
              variant="outline"
              colorPalette="blue"
            >
              <FiRefreshCw />
            </IconButton>
          </HStack>
          
          <HStack gap={3} fontSize="xs">
            <Badge colorPalette="red" px={2} py={1} borderRadius="md">
              涨 {riseCount}
            </Badge>
            <Badge colorPalette="green" px={2} py={1} borderRadius="md">
              跌 {fallCount}
            </Badge>
            <Badge colorPalette="gray" px={2} py={1} borderRadius="md">
              平 {flatCount}
            </Badge>
          </HStack>
        </Flex>
        
        <Box borderRadius="lg" border="1px" borderColor={borderColor} overflowX="auto">
          <Table.Root size="sm">
            <Table.Header bg={cardBg}>
              <Table.Row>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium">代码</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium">名称</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium" textAlign="end">最新价</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium" textAlign="end">涨跌幅</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium" textAlign="end">成交量</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium" textAlign="end">成交额</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium">操作</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {watchlist.map((code: string, index: number) => {
                const quote = quotes.find((q: any) => q.code === code)
                const isRising = quote?.change_percent !== null && quote?.change_percent !== undefined && quote.change_percent > 0
                const isFalling = quote?.change_percent !== null && quote?.change_percent !== undefined && quote.change_percent < 0
                
                return (
                  <Table.Row 
                    key={code} 
                    _hover={{ bg: cardHoverBg }} 
                    cursor="pointer"
                    onClick={() => navigate(`/stock/${code}`)}
                    bg={index % 2 === 0 ? 'transparent' : rowAltBg}
                  >
                    <Table.Cell>
                      <VStack align="start" gap={1}>
                        <Text fontWeight="bold" color="blue.600" fontSize="sm">{code}</Text>
                      </VStack>
                    </Table.Cell>
                    <Table.Cell>
                      <Text fontSize="sm" fontWeight="medium">{quote?.name || code}</Text>
                    </Table.Cell>
                    <Table.Cell textAlign="end">
                      <Text fontWeight="bold" fontSize="sm">{quote?.price?.toFixed(2) || '--'}</Text>
                    </Table.Cell>
                    <Table.Cell textAlign="end">
                      {quote?.change_percent !== null && quote?.change_percent !== undefined ? (
                        <HStack justify="end" gap={1}>
                          <Icon 
                            as={isRising ? FiTrendingUp : isFalling ? FiTrendingDown : FiActivity} 
                            color={getMarketColor(quote.change_percent)}
                            w={4}
                            h={4}
                          />
                          <Badge 
                            colorPalette={isRising ? 'red' : isFalling ? 'green' : 'gray'}
                            fontSize="xs"
                            px={2}
                            py={1}
                          >
                            {isRising ? '+' : ''}{quote.change_percent.toFixed(2)}%
                          </Badge>
                        </HStack>
                      ) : (
                        <Text fontSize="sm" color="gray.400">--</Text>
                      )}
                    </Table.Cell>
                    <Table.Cell textAlign="end">
                      <Text fontSize="sm" color="gray.600">{quote?.volume || '--'}</Text>
                    </Table.Cell>
                    <Table.Cell textAlign="end">
                      <Text fontSize="sm" color="gray.600">{quote?.amount || '--'}</Text>
                    </Table.Cell>
                    <Table.Cell>
                      <HStack gap={2}>
                        <IconButton
                          aria-label="删除"
                          size="sm"
                          variant="ghost"
                          colorPalette="red"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(code, 'stock')
                          }}
                          _hover={{ bg: 'red.50' }}
                        >
                          <FiTrash2 />
                        </IconButton>
                      </HStack>
                    </Table.Cell>
                  </Table.Row>
                )
              })}
            </Table.Body>
          </Table.Root>
        </Box>
      </>
    )
  }

  const renderFundWatchlist = () => {
    if (fundLoading || fundQuotesLoading) {
      return (
        <VStack py={12}>
          <Spinner size="xl" color="blue.500" />
          <Text color="gray.500" fontSize="sm">加载自选基金数据...</Text>
        </VStack>
      )
    }

    const fundList = (fundWatchlistData || []).filter((f: any) => f !== null && f !== undefined) as FundInfo[]
    const fundRates = fundQuotesData || []

    if (fundList.length === 0) {
      return (
        <VStack py={16} gap={6}>
          <Icon as={FiStar} w={16} h={16} color="gray.300" />
          <VStack gap={2}>
            <Text color="gray.500" fontSize="lg">暂无自选基金</Text>
            <Text color="gray.400" fontSize="sm">点击右上角添加您关注的基金</Text>
          </VStack>
          <Button 
            colorPalette="blue" 
            onClick={handleAddToWatchlist}
            size="md"
          >
            <FiPlus /> 添加自选基金
          </Button>
        </VStack>
      )
    }

    const riseCount = fundList.filter((f: any) => f.change_pct !== null && f.change_pct !== undefined && f.change_pct > 0).length
    const fallCount = fundList.filter((f: any) => f.change_pct !== null && f.change_pct !== undefined && f.change_pct < 0).length

    return (
      <>
        <Flex justify="space-between" align="center" mb={4}>
          <HStack gap={2}>
            <Button 
              size="sm" 
              colorPalette="blue" 
              onClick={handleAddToWatchlist}
              variant="solid"
            >
              <FiPlus /> 添加基金
            </Button>
          </HStack>
          
          <HStack gap={3} fontSize="xs">
            <Badge colorPalette="red" px={2} py={1} borderRadius="md">
              涨 {riseCount}
            </Badge>
            <Badge colorPalette="green" px={2} py={1} borderRadius="md">
              跌 {fallCount}
            </Badge>
          </HStack>
        </Flex>
        
        <Box borderRadius="lg" border="1px" borderColor={borderColor} overflowX="auto">
          <Table.Root size="sm">
            <Table.Header bg={cardBg}>
              <Table.Row>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium">代码</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium">名称</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium" textAlign="end">最新净值</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium" textAlign="end">日涨跌</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium" textAlign="end">估算涨幅</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium">类型</Table.ColumnHeader>
                <Table.ColumnHeader color="gray.500" fontSize="xs" fontWeight="medium">操作</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {fundList.map((fund: FundInfo, index: number) => {
                const rate = fundRates.find((r: any) => r.code === fund.code)
                const isRising = fund.change_pct !== null && fund.change_pct !== undefined && fund.change_pct > 0
                const isEstimateRising = rate?.estimate_change_pct !== null && rate?.estimate_change_pct !== undefined && rate.estimate_change_pct > 0
                
                return (
                  <Table.Row 
                    key={fund.code} 
                    _hover={{ bg: cardHoverBg }} 
                    cursor="pointer"
                    onClick={() => navigate(`/fund/detail/${fund.code}`)}
                    bg={index % 2 === 0 ? 'transparent' : rowAltBg}
                  >
                    <Table.Cell>
                      <VStack align="start" gap={1}>
                        <Text fontWeight="bold" color="blue.600" fontSize="sm">{fund.code}</Text>
                      </VStack>
                    </Table.Cell>
                    <Table.Cell>
                      <Text fontSize="sm" fontWeight="medium">{fund.name}</Text>
                    </Table.Cell>
                    <Table.Cell textAlign="end">
                      <Text fontWeight="bold" fontSize="sm">{fund.net_asset_value?.toFixed(4) || '--'}</Text>
                    </Table.Cell>
                    <Table.Cell textAlign="end">
                      {fund.change_pct !== null && fund.change_pct !== undefined ? (
                        <HStack justify="end" gap={1}>
                          <Icon 
                            as={isRising ? FiTrendingUp : FiTrendingDown} 
                            color={getMarketColor(fund.change_pct)}
                            w={4}
                            h={4}
                          />
                          <Badge 
                            colorPalette={isRising ? 'red' : 'green'}
                            fontSize="xs"
                            px={2}
                            py={1}
                          >
                            {isRising ? '+' : ''}{fund.change_pct.toFixed(2)}%
                          </Badge>
                        </HStack>
                      ) : (
                        <Text fontSize="sm" color="gray.400">--</Text>
                      )}
                    </Table.Cell>
                    <Table.Cell textAlign="end">
                      {rate?.estimate_change_pct !== null && rate?.estimate_change_pct !== undefined ? (
                        <HStack justify="end" gap={1}>
                          <Icon 
                            as={isEstimateRising ? FiTrendingUp : FiTrendingDown} 
                            color={getMarketColor(rate.estimate_change_pct)}
                            w={4}
                            h={4}
                          />
                          <Badge 
                            colorPalette={isEstimateRising ? 'red' : 'green'}
                            fontSize="xs"
                            px={2}
                            py={1}
                          >
                            {isEstimateRising ? '+' : ''}{rate.estimate_change_pct.toFixed(2)}%
                          </Badge>
                        </HStack>
                      ) : (
                        <Text fontSize="sm" color="gray.400">--</Text>
                      )}
                    </Table.Cell>
                    <Table.Cell>
                      <Badge 
                        colorPalette={fund.type === 'stock' ? 'red' : fund.type === 'bond' ? 'blue' : 'orange'}
                        fontSize="xs"
                        px={2}
                        py={1}
                      >
                        {fund.type === 'stock' ? '股票型' : fund.type === 'bond' ? '债券型' : '混合型'}
                      </Badge>
                    </Table.Cell>
                    <Table.Cell>
                      <HStack gap={2}>
                        <IconButton
                          aria-label="删除"
                          size="sm"
                          variant="ghost"
                          colorPalette="red"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(fund.code, 'fund')
                          }}
                          _hover={{ bg: 'red.50' }}
                        >
                          <FiTrash2 />
                        </IconButton>
                      </HStack>
                    </Table.Cell>
                  </Table.Row>
                )
              })}
            </Table.Body>
          </Table.Root>
        </Box>
      </>
    )
  }

  return (
    <VStack gap={6} align="stretch">
      <Card.Root>
        <Card.Body>
          <VStack gap={4}>
            <Flex justify="space-between" align="center" w="full">
              <HStack gap={3}>
                <Box 
                  p={2} 
                  bg="blue.500" 
                  borderRadius="lg"
                  boxShadow="md"
                >
                  <Icon as={FiStar} w={6} h={6} color="white" />
                </Box>
                <VStack align="start" gap={0}>
                  <Heading size="lg" fontWeight="bold">我的自选</Heading>
                  <Text fontSize="xs" color="gray.500">实时跟踪您关注的股票和基金</Text>
                </VStack>
              </HStack>
            </Flex>

            <Separator />

            <Tabs.Root variant="enclosed" w="full" onValueChange={(details) => {
              setSelectedType(details.value === '0' ? 'stock' : 'fund')
            }}>
              <Tabs.List>
                <Tabs.Trigger value="0">
                  <HStack gap={2}>
                    <Icon as={FiActivity} w={4} h={4} />
                    <Text>自选股</Text>
                  </HStack>
                </Tabs.Trigger>
                <Tabs.Trigger value="1">
                  <HStack gap={2}>
                    <Icon as={FiTrendingUp} w={4} h={4} />
                    <Text>自选基金</Text>
                  </HStack>
                </Tabs.Trigger>
                <Tabs.Indicator />
              </Tabs.List>
              <Tabs.Content value="0" p={0} pt={4}>
                {renderStockWatchlist()}
              </Tabs.Content>
              <Tabs.Content value="1" p={0} pt={4}>
                {renderFundWatchlist()}
              </Tabs.Content>
            </Tabs.Root>
          </VStack>
        </Card.Body>
      </Card.Root>

      <Dialog.Root open={isDeleteOpen} onOpenChange={(details) => setIsDeleteOpen(details.open)}>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header fontSize="lg" fontWeight="bold">
              删除确认
            </Dialog.Header>
            <Dialog.Body>
              确定要删除{selectedType === 'stock' ? '股票' : '基金'} {selectedCode} 吗？
            </Dialog.Body>
            <Dialog.Footer>
              <Button variant="outline" ref={cancelRef} onClick={() => setIsDeleteOpen(false)}>
                取消
              </Button>
              <Button
                colorPalette="red"
                onClick={confirmDelete}
                ml={3}
                loading={deleteMutation.isPending || deleteFundMutation.isPending}
              >
                删除
              </Button>
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Dialog.Root>

      <Dialog.Root open={isAddOpen} onOpenChange={(details) => setIsAddOpen(details.open)}>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>添加{selectedType === 'stock' ? '股票' : '基金'}</Dialog.Header>
            <Dialog.CloseTrigger />
            <Dialog.Body>
              <Box mb={4}>
                <Text fontSize="sm" fontWeight="medium" mb={2}>
                  {selectedType === 'stock' ? '股票代码' : '基金代码'}
                </Text>
                <Input
                  placeholder={`请输入${selectedType === 'stock' ? '6 位股票代码' : '6 位基金代码'}`}
                  value={addCode}
                  onChange={(e) => setAddCode(e.target.value)}
                  maxLength={6}
                />
              </Box>
            </Dialog.Body>
            <Dialog.Footer>
              <Button variant="outline" onClick={() => setIsAddOpen(false)}>取消</Button>
              <Button colorPalette="blue" onClick={confirmAdd} ml={3}>
                添加
              </Button>
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Dialog.Root>
    </VStack>
  )
}

export default Watchlist
