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
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FiTrash2, FiEdit, FiPlus, FiRefreshCw, FiStar } from 'react-icons/fi'
import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { watchlistApi } from '../services/api'
import { fundApi } from '../services/fund'
import { FundInfo } from '../services/fund'

const Watchlist = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const toast = useToast()
  const [selectedCode, setSelectedCode] = useState<string>('')
  const [selectedType, setSelectedType] = useState<'stock' | 'fund'>('stock')
  const [noteValue, setNoteValue] = useState('')
  const [addCode, setAddCode] = useState('')
  const cancelRef = useRef<HTMLButtonElement>(null)
  
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure()
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure()
  const { isOpen: isAddOpen, onOpen: onAddOpen, onClose: onAddClose } = useDisclosure()

  // 股票自选列表
  const { data: stockWatchlistData, isLoading: stockLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => watchlistApi.getList(),
  })

  // 基金自选列表（从本地存储或 API 获取）
  const { data: fundWatchlistData, isLoading: fundLoading } = useQuery({
    queryKey: ['fundWatchlist'],
    queryFn: async () => {
      // 从本地存储获取基金自选代码
      const stored = localStorage.getItem('fundWatchlist')
      const codes = stored ? JSON.parse(stored) : []
      if (codes.length === 0) return []
      
      // 批量获取基金信息
      const infoRes = await fundApi.getFundBaseInfo(codes)
      return Array.isArray(infoRes.data) ? infoRes.data : [infoRes.data]
    },
  })

  // 股票行情数据
  const { data: quotesData, isLoading: quotesLoading, refetch } = useQuery({
    queryKey: ['watchlistQuotes'],
    queryFn: () => watchlistApi.getQuotes(),
  })

  // 基金行情数据
  const { data: fundQuotesData, isLoading: fundQuotesLoading } = useQuery({
    queryKey: ['fundWatchlistQuotes'],
    queryFn: async () => {
      const stored = localStorage.getItem('fundWatchlist')
      const codes = stored ? JSON.parse(stored) : []
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
      const stored = localStorage.getItem('fundWatchlist')
      const codes = stored ? JSON.parse(stored) : []
      const newCodes = codes.filter((c: string) => c !== code)
      localStorage.setItem('fundWatchlist', JSON.stringify(newCodes))
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
      // 股票添加逻辑（原有）
    } else {
      // 基金添加到自选
      const stored = localStorage.getItem('fundWatchlist')
      const codes = stored ? JSON.parse(stored) : []
      if (!codes.includes(addCode)) {
        codes.push(addCode)
        localStorage.setItem('fundWatchlist', JSON.stringify(codes))
        queryClient.invalidateQueries({ queryKey: ['fundWatchlist'] })
        queryClient.invalidateQueries({ queryKey: ['fundWatchlistQuotes'] })
        toast({
          title: '添加成功',
          description: `已添加基金 ${addCode}`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        })
      }
    }
    setAddCode('')
    onAddClose()
  }

  // 获取涨跌幅颜色
  const getReturnColor = (value?: number) => {
    if (value === undefined || value === null) return 'gray.500'
    if (value > 0) return 'red.500'
    if (value < 0) return 'green.500'
    return 'blue.500'
  }

  // 渲染股票列表
  const renderStockWatchlist = () => {
    if (stockLoading || quotesLoading) {
      return (
        <VStack py={8}>
          <Spinner size="xl" />
          <Text>加载中...</Text>
        </VStack>
      )
    }

    const watchlist = stockWatchlistData || []
    const quotes = quotesData || []

    if (watchlist.length === 0) {
      return (
        <VStack py={8}>
          <Text color="gray.500">暂无自选股，点击右上角添加</Text>
          <Button leftIcon={<FiPlus />} colorScheme="blue" onClick={handleAddToWatchlist}>
            添加自选股
          </Button>
        </VStack>
      )
    }

    return (
      <>
        <HStack mb={4}>
          <Button leftIcon={<FiPlus />} size="sm" colorScheme="blue" onClick={handleAddToWatchlist}>
            添加股票
          </Button>
          <IconButton
            aria-label="刷新"
            icon={<FiRefreshCw />}
            size="sm"
            onClick={() => refetch()}
          />
        </HStack>
        <TableContainer>
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>代码</Th>
                <Th>名称</Th>
                <Th isNumeric>最新价</Th>
                <Th isNumeric>涨跌幅</Th>
                <Th isNumeric>成交量</Th>
                <Th isNumeric>成交额</Th>
                <Th>操作</Th>
              </Tr>
            </Thead>
            <Tbody>
              {watchlist.map((code: string) => {
                const quote = quotes.find((q: any) => q.code === code)
                return (
                  <Tr key={code} _hover={{ bg: 'gray.50' }} cursor="pointer">
                    <Td>
                      <Text fontWeight="bold" color="blue.600">{code}</Text>
                    </Td>
                    <Td>{quote?.name || code}</Td>
                    <Td isNumeric>
                      <Text fontWeight="bold">{quote?.price?.toFixed(2) || '--'}</Text>
                    </Td>
                    <Td isNumeric>
                      <Badge colorScheme={quote?.changePercent && quote.changePercent > 0 ? 'red' : quote?.changePercent && quote.changePercent < 0 ? 'green' : 'gray'}>
                        {quote?.changePercent ? `${quote.changePercent > 0 ? '+' : ''}${quote.changePercent.toFixed(2)}%` : '--'}
                      </Badge>
                    </Td>
                    <Td isNumeric>{quote?.volume || '--'}</Td>
                    <Td isNumeric>{quote?.amount || '--'}</Td>
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
    if (fundLoading || fundQuotesLoading) {
      return (
        <VStack py={8}>
          <Spinner size="xl" />
          <Text>加载中...</Text>
        </VStack>
      )
    }

    const fundList = (fundWatchlistData || []) as FundInfo[]
    const fundRates = fundQuotesData || []

    if (fundList.length === 0) {
      return (
        <VStack py={8}>
          <Text color="gray.500">暂无自选基金，点击右上角添加</Text>
          <Button leftIcon={<FiPlus />} colorScheme="blue" onClick={handleAddToWatchlist}>
            添加自选基金
          </Button>
        </VStack>
      )
    }

    return (
      <>
        <HStack mb={4}>
          <Button leftIcon={<FiPlus />} size="sm" colorScheme="blue" onClick={handleAddToWatchlist}>
            添加基金
          </Button>
        </HStack>
        <TableContainer>
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>代码</Th>
                <Th>名称</Th>
                <Th isNumeric>最新净值</Th>
                <Th isNumeric>日涨跌</Th>
                <Th isNumeric>估算涨跌幅</Th>
                <Th>类型</Th>
                <Th>操作</Th>
              </Tr>
            </Thead>
            <Tbody>
              {fundList.map((fund: FundInfo) => {
                const rate = fundRates.find((r: any) => r.code === fund.code)
                return (
                  <Tr 
                    key={fund.code} 
                    _hover={{ bg: 'gray.50' }} 
                    cursor="pointer"
                    onClick={() => navigate(`/fund/detail/${fund.code}`)}
                  >
                    <Td>
                      <Text fontWeight="bold" color="blue.600">{fund.code}</Text>
                    </Td>
                    <Td>{fund.name}</Td>
                    <Td isNumeric>
                      <Text fontWeight="bold">{fund.net_asset_value?.toFixed(4) || '--'}</Text>
                    </Td>
                    <Td isNumeric>
                      <Badge colorScheme={fund.change_pct && fund.change_pct > 0 ? 'red' : fund.change_pct && fund.change_pct < 0 ? 'green' : 'gray'}>
                        {fund.change_pct ? `${fund.change_pct > 0 ? '+' : ''}${fund.change_pct.toFixed(2)}%` : '--'}
                      </Badge>
                    </Td>
                    <Td isNumeric>
                      <Badge colorScheme={rate?.estimate_change_pct && rate.estimate_change_pct > 0 ? 'red' : rate?.estimate_change_pct && rate.estimate_change_pct < 0 ? 'green' : 'gray'}>
                        {rate?.estimate_change_pct ? `${rate.estimate_change_pct > 0 ? '+' : ''}${rate.estimate_change_pct.toFixed(2)}%` : '--'}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge>{fund.type === 'stock' ? '股票型' : fund.type === 'bond' ? '债券型' : '混合型'}</Badge>
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
            <HStack justify="space-between">
              <Heading size="lg">我的自选</Heading>
            </HStack>

            <Tabs variant="enclosed-colored" onChange={(index) => {
              setSelectedType(index === 0 ? 'stock' : 'fund')
            }}>
              <TabList>
                <Tab>自选股</Tab>
                <Tab>自选基金</Tab>
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
                isLoading={deleteMutation.isLoading || deleteFundMutation.isLoading}
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
