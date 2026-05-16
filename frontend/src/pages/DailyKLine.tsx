/**
 * A 股日线行情组件
 * 显示日线级别的 K 线数据和基本信息
 */
import React, { useState, useMemo } from 'react'
import { Badge, Box, Button, Dialog, Flex, HStack, Icon, NativeSelect, Separator, SimpleGrid, Spinner, Stat, Table, Text, VStack, useDisclosure } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import { KLineChart } from '../components/KLineChart'
import { FiDownload } from 'react-icons/fi'

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
  
  const { open, onOpen, setOpen } = useDisclosure()
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
  // const calculateMA = (data: KLineData[], period: number): (number | '-')[] => {
  //   const result: (number | '-')[] = []
  //   for (let i = 0; i < data.length; i++) {
  //     if (i < period - 1) {
  //       result.push('-')
  //       continue
  //     }
  //     const sum = data.slice(i - period + 1, i + 1).reduce((s, d) => s + d.close, 0)
  //     result.push(+(sum / period).toFixed(2))
  //   }
  //   return result
  // }

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
      toaster.create({
        title: '无数据可导出',
        description: '请先选择日期范围或等待数据加载完成',
        type: 'warning',
        duration: 3000,
        closable: true,
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
    <Dialog.Root open={open} onOpenChange={(details) => setOpen(details.open)} >
      <Dialog.Backdrop backdropFilter="blur(5px)" />
      <Dialog.Content borderRadius="xl" boxShadow="2xl">
        <Dialog.Header bg="green.50" borderTopRadius="xl" py={4}>
          <Flex align="center" gap={3}>
            <Icon as={FiDownload} boxSize={6} color="green.500" />
            <Text fontSize="xl" fontWeight="bold" color="green.700">
              导出成功
            </Text>
          </Flex>
        </Dialog.Header>
        <Dialog.CloseTrigger />
        <Dialog.Body py={6}>
          <VStack gap={4}>
            <Text fontSize="md" color="gray.700">
              已成功导出以下数据：
            </Text>
            
            <Stat.Root w="100%" bg="green.50" p={4} borderRadius="lg">
              <Stat.ValueText fontSize="4xl" fontWeight="bold" color="green.600">
                {exportCount}
              </Stat.ValueText>
              <Stat.HelpText fontSize="md" color="green.700" mb={0}>
                条 K 线数据
              </Stat.HelpText>
            </Stat.Root>

            <Separator />

            <VStack gap={2} align="start" w="100%">
              <Text fontSize="sm" color="gray.600" fontWeight="bold">
                📊 数据详情：
              </Text>
              <HStack gap={4} fontSize="sm" color="gray.600">
                <Text>• 日期范围：{filteredData.length > 0 ? formatDate(filteredData[0].date) : '-'} 至 {formatDate(filteredData[filteredData.length - 1]?.date)}</Text>
              </HStack>
              <HStack gap={4} fontSize="sm" color="gray.600">
                <Text>• 数据字段：开盘、最高、最低、收盘、成交量、成交额</Text>
              </HStack>
              <HStack gap={4} fontSize="sm" color="gray.600">
                <Text>• 文件格式：CSV</Text>
              </HStack>
            </VStack>
          </VStack>
        </Dialog.Body>

        <Dialog.Footer bg="gray.50" borderBottomRadius="xl" py={3}>
          <Button colorPalette="green" onClick={() => setOpen(false)} size="lg" w="full">
            确定
          </Button>
        </Dialog.Footer>
      </Dialog.Content>
    </Dialog.Root>
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
            <Badge colorPalette={stats.change >= 0 ? 'red' : 'green'} fontSize="sm">
              {formatPrice(stats.latest.close)} ({stats.change >= 0 ? '+' : ''}{stats.changePct.toFixed(2)}%)
            </Badge>
          )}
        </HStack>

        <HStack>
          <NativeSelect.Root size="sm" width="120px">
            <NativeSelect.Field
              value={dateRange}
              onChange={(e) => setDateRange((e.target.value || 'year') as 'all' | 'month' | 'week' | 'year')}
            >
              <option value="all">全部</option>
              <option value="year">近 1 年</option>
              <option value="month">近 1 月</option>
              <option value="week">近 1 周</option>
            </NativeSelect.Field>
          </NativeSelect.Root>

          <Button 
            size="sm" 
            onClick={handleExport}
            colorPalette="blue"
            variant="outline"
          >
            <FiDownload />
            导出数据
          </Button>
        </HStack>
      </Flex>

      {/* 统计卡片 */}
      {stats && (
        <SimpleGrid columns={{ base: 2, md: 4 }} gap={3} mb={4}>
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
        <Box maxH="400px" overflowY="auto">
          <Table.Root size="sm" >
            <Table.Header position="sticky" top={0} bg="white" zIndex={1}>
              <Table.Row>
                <Table.ColumnHeader fontSize="xs" color="gray.600">日期</Table.ColumnHeader>
                <Table.ColumnHeader fontSize="xs" color="gray.600" >开盘</Table.ColumnHeader>
                <Table.ColumnHeader fontSize="xs" color="gray.600" >最高</Table.ColumnHeader>
                <Table.ColumnHeader fontSize="xs" color="gray.600" >最低</Table.ColumnHeader>
                <Table.ColumnHeader fontSize="xs" color="gray.600" >收盘</Table.ColumnHeader>
                <Table.ColumnHeader fontSize="xs" color="gray.600" >成交量</Table.ColumnHeader>
                <Table.ColumnHeader fontSize="xs" color="gray.600" >成交额</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {filteredData.slice(-100).reverse().map((item, index) => {
                const prevItem = index > 0 ? filteredData[filteredData.length - 101 + index] : null
                return (
                <Table.Row key={item.date} _hover={{ bg: 'gray.50' }}>
                  <Table.Cell fontSize="xs" fontFamily="mono">{formatDate(item.date)}</Table.Cell>
                  <Table.Cell fontSize="xs" fontWeight="bold" fontFamily="mono" >
                    {formatPrice(item.open)}
                  </Table.Cell>
                  <Table.Cell fontSize="xs" color="red.500" fontWeight="bold" fontFamily="mono" >
                    {formatPrice(item.high)}
                  </Table.Cell>
                  <Table.Cell fontSize="xs" color="green.500" fontWeight="bold" fontFamily="mono" >
                    {formatPrice(item.low)}
                  </Table.Cell>
                  <Table.Cell 
                    fontSize="xs" 
                    fontWeight="bold" 
                    fontFamily="mono" 
                    color={prevItem && item.close >= prevItem.close ? 'red.500' : 'green.500'}
                  >
                    {formatPrice(item.close)}
                  </Table.Cell>
                  <Table.Cell fontSize="xs" fontFamily="mono" >
                    {formatVolume(item.volume)}
                  </Table.Cell>
                  <Table.Cell fontSize="xs" color="gray.600" fontFamily="mono" >
                    {formatAmount(item.amount ?? 0)}
                  </Table.Cell>
                </Table.Row>
                )
              })}
            </Table.Body>
          </Table.Root>
        </Box>
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
