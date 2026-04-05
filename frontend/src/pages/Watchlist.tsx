import {
  Card,
  CardBody,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  IconButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Spinner,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useDisclosure,
  useToast,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  FormControl,
  FormLabel,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Box,
  Flex,
  Icon,
  useColorModeValue,
  Divider,
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FiTrash2, FiPlus, FiRefreshCw, FiStar, FiTrendingUp, FiTrendingDown, FiActivity } from 'react-icons/fi'
import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { watchlistApi } from '../services/api'
import { fundApi } from '../services/fund'
import fundStorage from '../services/fundStorage'
import { FundInfo } from '../services/fund'
import { getMarketColor } from '../utils/marketColors'

const Watchlist = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const toast = useToast()
  const [selectedCode, setSelectedCode] = useState<string>('')
  const [selectedType, setSelectedType] = useState<'stock' | 'fund'>('stock')
  const [addCode, setAddCode] = useState('')
  const cancelRef = useRef<HTMLButtonElement>(null)
  
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure()
  const { isOpen: isAddOpen, onOpen: onAddOpen, onClose: onAddClose } = useDisclosure()

  // 股票自选列表
  const { data: stockWatchlistData, isLoading: stockLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => watchlistApi.getList(),
  })

  // 基金自选列表（从本地存储或 API 获取）
  const { data: fundWatchlistData, isLoading: fundLoading, refetch: refetchFundWatchlist } = useQuery({
    queryKey: ['fundWatchlist'],
    queryFn: async () => {
      console.log('[Watchlist Query] 开始获取基金自选列表...')
      // 从本地存储获取基金自选代码（使用 fundStorage 的验证方法）
      const codes = fundStorage.getWatchlist()
      console.log('[Watchlist Query] 从本地存储获取到基金代码:', codes)
      
      if (codes.length === 0) {
        console.log('[Watchlist Query] 自选列表为空，返回空数组')
        return []
      }
      
      // 批量获取基金信息
      console.log('[Watchlist Query] 开始批量获取基金信息...')
      const infoRes = await fundApi.getFundBaseInfo(codes)
      console.log('[Watchlist Query] 获取基金信息结果:', infoRes)
      return Array.isArray(infoRes.data) ? infoRes.data : [infoRes.data]
    },
  })

  // 股票行情数据
  const { data: quotesData, isLoading: quotesLoading, refetch } = useQuery({
    queryKey: ['watchlistQuotes'],
    queryFn: () => watchlistApi.getQuotes(),
  })

  // 基金行情数据
  const { data: fundQuotesData, isLoading: fundQuotesLoading, refetch: refetchFundQuotes } = useQuery({
    queryKey: ['fundWatchlistQuotes'],
    queryFn: async () => {
      // 从本地存储获取基金自选代码（使用 fundStorage 的验证方法）
      const codes = fundStorage.getWatchlist()
      if (codes.length === 0) return []
      
      // 批量获取实时估算涨跌幅
      const rateRes = await fundApi.getFundRealtimeRate(codes)
      return Array.isArray(rateRes.data) ? rateRes.data : [rateRes.data]
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (code: string) => watchlistApi.remove(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      queryClient.invalidateQueries({ queryKey: ['watchlistQuotes'] })
      onDeleteClose()
      toast({
        title: '删除成功',
        description: `已删除股票 ${selectedCode}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    },
    onError: (error: any) => {
      toast({
        title: '删除失败',
        description: error.message,
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    },
  })

  // 删除基金
  const deleteFundMutation = useMutation({
    mutationFn: (code: string) => {
      // 使用 fundStorage 的删除方法
      fundStorage.removeFromWatchlist(code)
      return Promise.resolve()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fundWatchlist'] })
      queryClient.invalidateQueries({ queryKey: ['fundWatchlistQuotes'] })
      onDeleteClose()
      toast({
        title: '删除成功',
        description: `已删除基金 ${selectedCode}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    },
  })

  const handleDelete = (code: string, type: 'stock' | 'fund' = 'stock') => {
    setSelectedCode(code)
    setSelectedType(type)
    onDeleteOpen()
  }

  const confirmDelete = () => {
    if (selectedType === 'stock') {
      deleteMutation.mutate(selectedCode)
    } else {
      deleteFundMutation.mutate(selectedCode)
    }
  }

  const handleAddToWatchlist = () => {
    onAddOpen()
  }

  const confirmAdd = () => {
    if (selectedType === 'stock') {
      // 股票添加到自选 - 调用 API
      watchlistApi.add(addCode)
        .then(() => {
          queryClient.invalidateQueries({ queryKey: ['watchlist'] })
          queryClient.invalidateQueries({ queryKey: ['watchlistQuotes'] })
          toast({
            title: '添加成功',
            description: `已添加股票 ${addCode}`,
            status: 'success',
            duration: 3000,
            isClosable: true,
          })
          setAddCode('')
          onAddClose()
        })
        .catch((err) => {
          toast({
            title: '添加失败',
            description: err.message || '请重试',
            status: 'error',
            duration: 3000,
            isClosable: true,
          })
        })
    } else {
      // 基金添加到自选 - 使用 fundStorage 的验证方法
      const fundCode = addCode.trim()
      
      // 先验证代码格式
      if (!/^\d{6}$/.test(fundCode)) {
        toast({
          title: '添加失败',
          description: '请输入 6 位数字的基金代码',
          status: 'error',
          duration: 3000,
          isClosable: true,
        })
        return
      }
      
      // 使用 fundStorage 的添加方法（会自动验证）
      fundStorage.addToWatchlist(fundCode)
      
      // 调试日志
      console.log('[Watchlist] 添加基金后，当前自选列表:', fundStorage.getWatchlist())
      
      // 手动刷新基金列表和行情数据
      console.log('[Watchlist] 开始刷新基金列表...')
      refetchFundWatchlist().then((result) => {
        console.log('[Watchlist] 基金列表刷新完成:', result)
      }).catch((err) => {
        console.error('[Watchlist] 基金列表刷新失败:', err)
      })
      
      console.log('[Watchlist] 开始刷新行情数据...')
      refetchFundQuotes().then((result) => {
        console.log('[Watchlist] 行情数据刷新完成:', result)
      }).catch((err) => {
        console.error('[Watchlist] 行情数据刷新失败:', err)
      })
      
      toast({
        title: '添加成功',
        description: `已添加基金 ${fundCode}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      setAddCode('')
      onAddClose()
    }
  }

  // 渲染股票列表
  const renderStockWatchlist = () => {
    const cardBg = useColorModeValue('white', 'gray.800')
    const cardHoverBg = useColorModeValue('gray.50', 'gray.700')
    const borderColor = useColorModeValue('gray.200', 'gray.700')
    
    if (stockLoading || quotesLoading) {
      return (
        <VStack py={12}>
          <Spinner size="xl" color="blue.500" thickness="3px" />
          <Text color="gray.500" fontSize="sm">加载自选股数据...</Text>
        </VStack>
      )
    }

    const watchlist = (stockWatchlistData?.data || []).map((item: any) => item.code || item)
    const quotes = (quotesData?.data || []).filter((q: any) => q !== null && q !== undefined)

    if (watchlist.length === 0) {
      return (
        <VStack py={16} spacing={6}>
          <Icon as={FiStar} w={16} h={16} color="gray.300" />
          <VStack spacing={2}>
            <Text color="gray.500" fontSize="lg">暂无自选股</Text>
            <Text color="gray.400" fontSize="sm">点击右上角添加您关注的股票</Text>
          </VStack>
          <Button 
            leftIcon={<FiPlus />} 
            colorScheme="blue" 
            onClick={handleAddToWatchlist}
            size="md"
          >
            添加自选股
          </Button>
        </VStack>
      )
    }

    // 统计涨跌家数
    const riseCount = quotes.filter((q: any) => q.change_percent !== null && q.change_percent !== undefined && q.change_percent > 0).length
    const fallCount = quotes.filter((q: any) => q.change_percent !== null && q.change_percent !== undefined && q.change_percent < 0).length
    const flatCount = quotes.filter((q: any) => q.change_percent !== null && q.change_percent !== undefined && q.change_percent === 0).length

    return (
      <>
        {/* 工具栏 */}
        <Flex justify="space-between" align="center" mb={4}>
          <HStack spacing={2}>
            <Button 
              leftIcon={<FiPlus />} 
              size="sm" 
              colorScheme="blue" 
              onClick={handleAddToWatchlist}
              variant="solid"
            >
              添加股票
            </Button>
            <IconButton
              aria-label="刷新"
              icon={<FiRefreshCw />}
              size="sm"
              onClick={() => refetch()}
              variant="outline"
              colorScheme="blue"
            />
          </HStack>
          
          {/* 涨跌统计 */}
          <HStack spacing={3} fontSize="xs">
            <Badge colorScheme="red" px={2} py={1} borderRadius="md">
              涨 {riseCount}
            </Badge>
            <Badge colorScheme="green" px={2} py={1} borderRadius="md">
              跌 {fallCount}
            </Badge>
            <Badge colorScheme="gray" px={2} py={1} borderRadius="md">
              平 {flatCount}
            </Badge>
          </HStack>
        </Flex>
        
        {/* 表格 */}
        <TableContainer borderRadius="lg" border="1px" borderColor={borderColor}>
          <Table variant="simple" size="sm">
            <Thead bg={cardBg}>
              <Tr>
                <Th color="gray.500" fontSize="xs" fontWeight="medium">代码</Th>
                <Th color="gray.500" fontSize="xs" fontWeight="medium">名称</Th>
                <Th isNumeric color="gray.500" fontSize="xs" fontWeight="medium">最新价</Th>
                <Th isNumeric color="gray.500" fontSize="xs" fontWeight="medium">涨跌幅</Th>
                <Th isNumeric color="gray.500" fontSize="xs" fontWeight="medium">成交量</Th>
                <Th isNumeric color="gray.500" fontSize="xs" fontWeight="medium">成交额</Th>
                <Th color="gray.500" fontSize="xs" fontWeight="medium">操作</Th>
              </Tr>
            </Thead>
            <Tbody>
              {watchlist.map((code: string, index: number) => {
                const quote = quotes.find((q: any) => q.code === code)
                const isRising = quote?.change_percent !== null && quote?.change_percent !== undefined && quote.change_percent > 0
                const isFalling = quote?.change_percent !== null && quote?.change_percent !== undefined && quote.change_percent < 0
                
                return (
                  <Tr 
                    key={code} 
                    _hover={{ bg: cardHoverBg }} 
                    cursor="pointer"
                    onClick={() => navigate(`/stock/${code}`)}
                    bg={index % 2 === 0 ? 'transparent' : useColorModeValue('gray.50', 'gray.750')}
                  >
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="bold" color="blue.600" fontSize="sm">{code}</Text>
                      </VStack>
                    </Td>
                    <Td>
                      <Text fontSize="sm" fontWeight="medium">{quote?.name || code}</Text>
                    </Td>
                    <Td isNumeric>
                      <Text fontWeight="bold" fontSize="sm">{quote?.price?.toFixed(2) || '--'}</Text>
                    </Td>
                    <Td isNumeric>
                      {quote?.change_percent !== null && quote?.change_percent !== undefined ? (
                        <HStack justify="end" spacing={1}>
                          <Icon 
                            as={isRising ? FiTrendingUp : isFalling ? FiTrendingDown : FiActivity} 
                            color={getMarketColor(quote.change_percent)}
                            w={4}
                            h={4}
                          />
                          <Badge 
                            colorScheme={isRising ? 'red' : isFalling ? 'green' : 'gray'}
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
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" color="gray.600">{quote?.volume || '--'}</Text>
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" color="gray.600">{quote?.amount || '--'}</Text>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <IconButton
                          aria-label="删除"
                          icon={<FiTrash2 />}
                          size="sm"
                          variant="ghost"
                          colorScheme="red"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(code, 'stock')
                          }}
                          _hover={{ bg: 'red.50' }}
                        />
                      </HStack>
                    </Td>
                  </Tr>
                )
              })}
            </Tbody>
          </Table>
        </TableContainer>
      </>
    )
  }

  // 渲染基金列表
  const renderFundWatchlist = () => {
    const cardBg = useColorModeValue('white', 'gray.800')
    const cardHoverBg = useColorModeValue('gray.50', 'gray.700')
    const borderColor = useColorModeValue('gray.200', 'gray.700')
    
    if (fundLoading || fundQuotesLoading) {
      return (
        <VStack py={12}>
          <Spinner size="xl" color="blue.500" thickness="3px" />
          <Text color="gray.500" fontSize="sm">加载自选基金数据...</Text>
        </VStack>
      )
    }

    const fundList = (fundWatchlistData || []).filter((f: any) => f !== null && f !== undefined) as FundInfo[]
    const fundRates = fundQuotesData || []

    if (fundList.length === 0) {
      return (
        <VStack py={16} spacing={6}>
          <Icon as={FiStar} w={16} h={16} color="gray.300" />
          <VStack spacing={2}>
            <Text color="gray.500" fontSize="lg">暂无自选基金</Text>
            <Text color="gray.400" fontSize="sm">点击右上角添加您关注的基金</Text>
          </VStack>
          <Button 
            leftIcon={<FiPlus />} 
            colorScheme="blue" 
            onClick={handleAddToWatchlist}
            size="md"
          >
            添加自选基金
          </Button>
        </VStack>
      )
    }

    // 统计涨跌家数
    const riseCount = fundList.filter((f: any) => f.change_pct !== null && f.change_pct !== undefined && f.change_pct > 0).length
    const fallCount = fundList.filter((f: any) => f.change_pct !== null && f.change_pct !== undefined && f.change_pct < 0).length

    return (
      <>
        {/* 工具栏 */}
        <Flex justify="space-between" align="center" mb={4}>
          <HStack spacing={2}>
            <Button 
              leftIcon={<FiPlus />} 
              size="sm" 
              colorScheme="blue" 
              onClick={handleAddToWatchlist}
              variant="solid"
            >
              添加基金
            </Button>
          </HStack>
          
          {/* 涨跌统计 */}
          <HStack spacing={3} fontSize="xs">
            <Badge colorScheme="red" px={2} py={1} borderRadius="md">
              涨 {riseCount}
            </Badge>
            <Badge colorScheme="green" px={2} py={1} borderRadius="md">
              跌 {fallCount}
            </Badge>
          </HStack>
        </Flex>
        
        {/* 表格 */}
        <TableContainer borderRadius="lg" border="1px" borderColor={borderColor}>
          <Table variant="simple" size="sm">
            <Thead bg={cardBg}>
              <Tr>
                <Th color="gray.500" fontSize="xs" fontWeight="medium">代码</Th>
                <Th color="gray.500" fontSize="xs" fontWeight="medium">名称</Th>
                <Th isNumeric color="gray.500" fontSize="xs" fontWeight="medium">最新净值</Th>
                <Th isNumeric color="gray.500" fontSize="xs" fontWeight="medium">日涨跌</Th>
                <Th isNumeric color="gray.500" fontSize="xs" fontWeight="medium">估算涨幅</Th>
                <Th color="gray.500" fontSize="xs" fontWeight="medium">类型</Th>
                <Th color="gray.500" fontSize="xs" fontWeight="medium">操作</Th>
              </Tr>
            </Thead>
            <Tbody>
              {fundList.map((fund: FundInfo, index: number) => {
                const rate = fundRates.find((r: any) => r.code === fund.code)
                const isRising = fund.change_pct !== null && fund.change_pct !== undefined && fund.change_pct > 0
                const isEstimateRising = rate?.estimate_change_pct !== null && rate?.estimate_change_pct !== undefined && rate.estimate_change_pct > 0
                
                return (
                  <Tr 
                    key={fund.code} 
                    _hover={{ bg: cardHoverBg }} 
                    cursor="pointer"
                    onClick={() => navigate(`/fund/detail/${fund.code}`)}
                    bg={index % 2 === 0 ? 'transparent' : useColorModeValue('gray.50', 'gray.750')}
                  >
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="bold" color="blue.600" fontSize="sm">{fund.code}</Text>
                      </VStack>
                    </Td>
                    <Td>
                      <Text fontSize="sm" fontWeight="medium">{fund.name}</Text>
                    </Td>
                    <Td isNumeric>
                      <Text fontWeight="bold" fontSize="sm">{fund.net_asset_value?.toFixed(4) || '--'}</Text>
                    </Td>
                    <Td isNumeric>
                      {fund.change_pct !== null && fund.change_pct !== undefined ? (
                        <HStack justify="end" spacing={1}>
                          <Icon 
                            as={isRising ? FiTrendingUp : FiTrendingDown} 
                            color={getMarketColor(fund.change_pct)}
                            w={4}
                            h={4}
                          />
                          <Badge 
                            colorScheme={isRising ? 'red' : 'green'}
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
                    </Td>
                    <Td isNumeric>
                      {rate?.estimate_change_pct !== null && rate?.estimate_change_pct !== undefined ? (
                        <HStack justify="end" spacing={1}>
                          <Icon 
                            as={isEstimateRising ? FiTrendingUp : FiTrendingDown} 
                            color={getMarketColor(rate.estimate_change_pct)}
                            w={4}
                            h={4}
                          />
                          <Badge 
                            colorScheme={isEstimateRising ? 'red' : 'green'}
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
                    </Td>
                    <Td>
                      <Badge 
                        colorScheme={fund.type === 'stock' ? 'red' : fund.type === 'bond' ? 'blue' : 'orange'}
                        fontSize="xs"
                        px={2}
                        py={1}
                      >
                        {fund.type === 'stock' ? '股票型' : fund.type === 'bond' ? '债券型' : '混合型'}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <IconButton
                          aria-label="删除"
                          icon={<FiTrash2 />}
                          size="sm"
                          variant="ghost"
                          colorScheme="red"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(fund.code, 'fund')
                          }}
                          _hover={{ bg: 'red.50' }}
                        />
                      </HStack>
                    </Td>
                  </Tr>
                )
              })}
            </Tbody>
          </Table>
        </TableContainer>
      </>
    )
  }

  return (
    <VStack spacing={6} align="stretch">
      <Card>
        <CardBody>
          <VStack spacing={4}>
            {/* 头部标题 */}
            <Flex justify="space-between" align="center" w="full">
              <HStack spacing={3}>
                <Box 
                  p={2} 
                  bg="blue.500" 
                  borderRadius="lg"
                  boxShadow="md"
                >
                  <Icon as={FiStar} w={6} h={6} color="white" />
                </Box>
                <VStack align="start" spacing={0}>
                  <Heading size="lg" fontWeight="bold">我的自选</Heading>
                  <Text fontSize="xs" color="gray.500">实时跟踪您关注的股票和基金</Text>
                </VStack>
              </HStack>
            </Flex>

            {/* 分隔线 */}
            <Divider />

            {/* Tab 切换 */}
            <Tabs variant="enclosed-colored" w="full" onChange={(index) => {
              setSelectedType(index === 0 ? 'stock' : 'fund')
            }}>
              <TabList>
                <Tab _selected={{ color: 'blue.500', bg: 'blue.50' }}>
                  <HStack spacing={2}>
                    <Icon as={FiActivity} w={4} h={4} />
                    <Text>自选股</Text>
                  </HStack>
                </Tab>
                <Tab _selected={{ color: 'blue.500', bg: 'blue.50' }}>
                  <HStack spacing={2}>
                    <Icon as={FiTrendingUp} w={4} h={4} />
                    <Text>自选基金</Text>
                  </HStack>
                </Tab>
              </TabList>
              <TabPanels>
                <TabPanel p={0} pt={4}>
                  {renderStockWatchlist()}
                </TabPanel>
                <TabPanel p={0} pt={4}>
                  {renderFundWatchlist()}
                </TabPanel>
              </TabPanels>
            </Tabs>
          </VStack>
        </CardBody>
      </Card>

      {/* 删除确认对话框 */}
      <AlertDialog
        isOpen={isDeleteOpen}
        leastDestructiveRef={cancelRef}
        onClose={onDeleteClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              删除确认
            </AlertDialogHeader>
            <AlertDialogBody>
              确定要删除{selectedType === 'stock' ? '股票' : '基金'} {selectedCode} 吗？
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onDeleteClose}>
                取消
              </Button>
              <Button
                colorScheme="red"
                onClick={confirmDelete}
                ml={3}
                isLoading={deleteMutation.isPending || deleteFundMutation.isPending}
              >
                删除
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      {/* 添加对话框 */}
      <Modal isOpen={isAddOpen} onClose={onAddClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>添加{selectedType === 'stock' ? '股票' : '基金'}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <FormControl>
              <FormLabel>{selectedType === 'stock' ? '股票代码' : '基金代码'}</FormLabel>
              <Input
                placeholder={`请输入${selectedType === 'stock' ? '6 位股票代码' : '6 位基金代码'}`}
                value={addCode}
                onChange={(e) => setAddCode(e.target.value)}
                maxLength={6}
              />
            </FormControl>
          </ModalBody>
          <ModalFooter>
            <Button onClick={onAddClose}>取消</Button>
            <Button colorScheme="blue" onClick={confirmAdd} ml={3}>
              添加
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  )
}

export default Watchlist
