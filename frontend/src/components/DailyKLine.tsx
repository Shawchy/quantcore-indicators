/**
 * A 股日线行情组件
 * 显示日线级别的 K 线数据和基本信息
 */
import React, { useState, useMemo } from 'react'
import {
  Box,
  Flex,
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Button,
  Select,
  HStack,
  VStack,
  SimpleGrid,
  Spinner,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Icon,
  Stat,
  StatNumber,
  StatHelpText,
  Divider,
} from '@chakra-ui/react'
import { KLineChart } from './KLineChart'
import { DownloadIcon } from '@chakra-ui/icons'

interface KLineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount?: number
  turnover_rate?: number
}

interface DailyKLineProps {
  data: KLineData[]
  loading?: boolean
  code?: string
  name?: string
  onExport?: (data: KLineData[]) => void
}

const DailyKLine: React.FC<DailyKLineProps> = ({
  data,
  loading = false,
  code = '',
  name = '',
  onExport,
}) => {
  const toast = useToast()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [dateRange, setDateRange] = useState<'all' | 'year' | 'month' | 'week'>('year')
  const [exportCount, setExportCount] = useState(0)
  // 自定义日期范围功能预留
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_customStart, _setCustomStart] = useState('')
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_customEnd, _setCustomEnd] = useState('')

  // 根据日期范围过滤数据
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return []

    const now = new Date()
    let startDate: Date

    switch (dateRange) {
      case 'week':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      case 'month':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        break
      case 'year':
        startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
        break
      case 'all':
      default:
        return data
    }

    return data.filter((item) => new Date(item.date) >= startDate)
  }, [data, dateRange])

  // 计算统计数据
  const stats = useMemo(() => {
    if (filteredData.length === 0) return null

    const latest = filteredData[filteredData.length - 1]
    const prev = filteredData.length > 1 ? filteredData[filteredData.length - 2] : null
    const change = prev ? latest.close - prev.close : 0
    const changePct = prev ? (change / prev.close) * 100 : 0

    // 期间统计
    const periodHigh = Math.max(...filteredData.map((d) => d.high))
    const periodLow = Math.min(...filteredData.map((d) => d.low))
    const avgVolume = filteredData.reduce((sum, d) => sum + d.volume, 0) / filteredData.length
    const totalAmount = filteredData.reduce((sum, d) => sum + (d.amount || 0), 0)

    return {
      latest,
      change,
      changePct,
      periodHigh,
      periodLow,
      avgVolume,
      totalAmount,
    }
  }, [filteredData])

  // 格式化日期（移除时分秒）
  const formatDate = (dateStr: string) => {
    if (!dateStr) return ''
    // 如果包含时分秒，只取日期部分
    if (dateStr.includes(' ')) {
      return dateStr.split(' ')[0]
    }
    if (dateStr.includes('T')) {
      return dateStr.split('T')[0]
    }
    return dateStr
  }


  // 计算移动平均线
  const calculateMA = (data: KLineData[], period: number): (number | '-')[] => {
    const result: (number | '-')[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push('-')
        continue
      }
      const sum = data.slice(i - period + 1, i + 1).reduce((s, d) => s + d.close, 0)
      result.push(+(sum / period).toFixed(2))
    }
    return result
  }

  // 格式化数据
  const formatPrice = (price: number) => price.toFixed(2)
  const formatVolume = (volume: number) => {
    if (volume >= 100000000) return `${(volume / 100000000).toFixed(2)}亿手`
    if (volume >= 10000) return `${(volume / 10000).toFixed(1)}万手`
    return volume.toFixed(0)
  }
  const formatAmount = (amount: number) => {
    if (!amount) return '-'
    if (amount >= 100000000) return `${(amount / 100000000).toFixed(2)}亿`
    if (amount >= 10000) return `${(amount / 10000).toFixed(0)}万`
    return amount.toFixed(0)
  }

  // 导出数据
  const handleExport = () => {
    if (!filteredData || filteredData.length === 0) {
      toast({
        title: '无数据可导出',
        description: '请先选择日期范围或等待数据加载完成',
        status: 'warning',
        duration: 3000,
        isClosable: true,
        position: 'top',
      })
      return
    }

    const csv = [
      ['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额'].join(','),
      ...filteredData.map((d) =>
        [
          formatDate(d.date),
          d.open,
          d.high,
          d.low,
          d.close,
          d.volume,
          d.amount || 0,
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${code || 'stock'}_daily_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    URL.revokeObjectURL(url)

    setExportCount(filteredData.length)
    onOpen() // 打开导出成功提示框

    if (onExport) {
      onExport(filteredData)
    }
  }

  // 导出成功确认框
  const ExportSuccessModal = () => (
    <Modal isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay backdropFilter="blur(5px)" />
      <ModalContent borderRadius="xl" boxShadow="2xl">
        <ModalHeader bg="green.50" borderTopRadius="xl" py={4}>
          <Flex align="center" gap={3}>
            <Icon as={DownloadIcon} boxSize={6} color="green.500" />
            <Text fontSize="xl" fontWeight="bold" color="green.700">
              导出成功
            </Text>
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody py={6}>
          <VStack spacing={4}>
            <Text fontSize="md" color="gray.700">
              已成功导出以下数据：
            </Text>
            
            <Stat w="100%" bg="green.50" p={4} borderRadius="lg">
              <StatNumber fontSize="4xl" fontWeight="bold" color="green.600">
                {exportCount}
              </StatNumber>
              <StatHelpText fontSize="md" color="green.700" mb={0}>
                条 K 线数据
              </StatHelpText>
            </Stat>

            <Divider />

            <VStack spacing={2} align="start" w="100%">
              <Text fontSize="sm" color="gray.600" fontWeight="bold">
                📊 数据详情：
              </Text>
              <HStack spacing={4} fontSize="sm" color="gray.600">
                <Text>• 日期范围：{filteredData.length > 0 ? formatDate(filteredData[0].date) : '-'} 至 {formatDate(filteredData[filteredData.length - 1]?.date)}</Text>
              </HStack>
              <HStack spacing={4} fontSize="sm" color="gray.600">
                <Text>• 数据字段：开盘、最高、最低、收盘、成交量、成交额</Text>
              </HStack>
              <HStack spacing={4} fontSize="sm" color="gray.600">
                <Text>• 文件格式：CSV</Text>
              </HStack>
            </VStack>
          </VStack>
        </ModalBody>

        <ModalFooter bg="gray.50" borderBottomRadius="xl" py={3}>
          <Button colorScheme="green" onClick={onClose} size="lg" w="full">
            确定
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )

  if (loading) {
    return (
      <Flex justify="center" align="center" h="400px">
        <Spinner size="xl" />
      </Flex>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Text fontSize="lg" color="gray.500">暂无日线数据</Text>
      </Box>
    )
  }

  return (
    <Box>
      {/* 导出成功提示框 */}
      <ExportSuccessModal />

      {/* 头部控制栏 */}
      <Flex justify="space-between" align="center" mb={4} flexWrap="wrap" gap={3}>
        <HStack>
          <Text fontWeight="bold" fontSize="lg">
            {name || code} - 日线行情
          </Text>
          {stats && (
            <Badge colorScheme={stats.change >= 0 ? 'red' : 'green'} fontSize="sm">
              {formatPrice(stats.latest.close)} ({stats.change >= 0 ? '+' : ''}{stats.changePct.toFixed(2)}%)
            </Badge>
          )}
        </HStack>

        <HStack>
          <Select
            value={dateRange}
            onChange={(e) => setDateRange((e.target.value || 'year') as 'all' | 'month' | 'week' | 'year')}
            size="sm"
            width="120px"
          >
            <option value="all">全部</option>
            <option value="year">近 1 年</option>
            <option value="month">近 1 月</option>
            <option value="week">近 1 周</option>
          </Select>

          <Button 
            size="sm" 
            leftIcon={<DownloadIcon />} 
            onClick={handleExport}
            colorScheme="blue"
            variant="outline"
          >
            导出数据
          </Button>
        </HStack>
      </Flex>

      {/* 统计卡片 */}
      {stats && (
        <SimpleGrid columns={{ base: 2, md: 4 }} spacing={3} mb={4}>
          <StatCard label="最新价" value={formatPrice(stats.latest.close)} />
          <StatCard 
            label="期间最高" 
            value={formatPrice(stats.periodHigh)} 
            color="red.500" 
          />
          <StatCard 
            label="期间最低" 
            value={formatPrice(stats.periodLow)} 
            color="green.500" 
          />
          <StatCard 
            label="平均成交量" 
            value={formatVolume(stats.avgVolume)} 
          />
        </SimpleGrid>
      )}

      {/* K 线图 */}
      <Box
        bg="white"
        borderRadius="lg"
        p={4}
        boxShadow="sm"
        mb={4}
        borderWidth="1px"
        borderColor="gray.200"
      >
        <KLineChart
          data={filteredData}
          loading={loading}
          type="daily"
          height="500px"
        />
      </Box>

      {/* 数据表格 */}
      <Box bg="white" borderRadius="lg" overflow="hidden">
        <Box px={4} py={3} bg="gray.50" borderBottom="1px" borderColor="gray.200">
          <Text fontWeight="bold" fontSize="md">日线数据明细</Text>
        </Box>
        <TableContainer maxH="400px" overflowY="auto">
          <Table size="sm" variant="simple">
            <Thead position="sticky" top={0} bg="white" zIndex={1}>
              <Tr>
                <Th fontSize="xs" color="gray.600">日期</Th>
                <Th fontSize="xs" color="gray.600" isNumeric>开盘</Th>
                <Th fontSize="xs" color="gray.600" isNumeric>最高</Th>
                <Th fontSize="xs" color="gray.600" isNumeric>最低</Th>
                <Th fontSize="xs" color="gray.600" isNumeric>收盘</Th>
                <Th fontSize="xs" color="gray.600" isNumeric>成交量</Th>
                <Th fontSize="xs" color="gray.600" isNumeric>成交额</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredData.slice(-100).reverse().map((item, index) => {
                const prevItem = index > 0 ? filteredData[filteredData.length - 101 + index] : null
                return (
                <Tr key={item.date} _hover={{ bg: 'gray.50' }}>
                  <Td fontSize="xs" fontFamily="mono">{formatDate(item.date)}</Td>
                  <Td fontSize="xs" fontWeight="bold" fontFamily="mono" isNumeric>
                    {formatPrice(item.open)}
                  </Td>
                  <Td fontSize="xs" color="red.500" fontWeight="bold" fontFamily="mono" isNumeric>
                    {formatPrice(item.high)}
                  </Td>
                  <Td fontSize="xs" color="green.500" fontWeight="bold" fontFamily="mono" isNumeric>
                    {formatPrice(item.low)}
                  </Td>
                  <Td 
                    fontSize="xs" 
                    fontWeight="bold" 
                    fontFamily="mono" 
                    isNumeric
                    color={prevItem && item.close >= prevItem.close ? 'red.500' : 'green.500'}
                  >
                    {formatPrice(item.close)}
                  </Td>
                  <Td fontSize="xs" fontFamily="mono" isNumeric>
                    {formatVolume(item.volume)}
                  </Td>
                  <Td fontSize="xs" color="gray.600" fontFamily="mono" isNumeric>
                    {formatAmount(item.amount ?? 0)}
                  </Td>
                </Tr>
                )
              })}
            </Tbody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  )
}

// 统计卡片组件
const StatCard: React.FC<{
  label: string
  value: string
  color?: string
}> = ({ label, value, color }) => (
  <Box bg="gray.50" p={3} borderRadius="md">
    <Text fontSize="xs" color="gray.600" mb={1}>{label}</Text>
    <Text fontSize="lg" fontWeight="bold" color={color || 'gray.700'} fontFamily="mono">
      {value}
    </Text>
  </Box>
)

export default DailyKLine
