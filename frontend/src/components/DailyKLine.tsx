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
  SimpleGrid,
  Spinner,
} from '@chakra-ui/react'
import ReactECharts from 'echarts-for-react'
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
  const [dateRange, setDateRange] = useState<'all' | 'year' | 'month' | 'week'>('year')
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

  // K 线图配置
  const getKLineOption = () => {
    if (filteredData.length === 0) return {}

    const dates = filteredData.map((d) => formatDate(d.date))
    const ohlc = filteredData.map((d) => [d.open, d.close, d.low, d.high])
    const volumes = filteredData.map((d) => d.volume)
    const ma5 = calculateMA(filteredData, 5)
    const ma10 = calculateMA(filteredData, 10)
    const ma20 = calculateMA(filteredData, 20)

    return {
      backgroundColor: 'transparent',
      animation: true,
      animationDuration: 800,
      animationEasing: 'cubicOut',
      tooltip: {
        trigger: 'axis',
        axisPointer: { 
          type: 'cross',
          crossStyle: {
            color: '#999',
            width: 1,
            type: 'dashed',
          },
        },
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        textStyle: { 
          color: '#1e293b',
          fontSize: 12,
        },
        extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border-radius: 8px; padding: 12px;',
        formatter: (params: { axisValue: string; dataIndex: number }[]) => {
          const item = formatDate(params[0].axisValue)
          const data = filteredData[params[0].dataIndex]
          const change = data.close - data.open
          const changePct = (change / data.open) * 100
          return `
            <div style="padding: 4px 0;">
              <div style="font-weight: 600; margin-bottom: 8px; font-size: 13px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">${item}</div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                <div><span style="color: #64748b;">开盘：</span><span style="font-weight: 500;">${data.open.toFixed(2)}</span></div>
                <div><span style="color: #64748b;">收盘：</span><span style="font-weight: 500; color: ${change >= 0 ? '#ef4444' : '#10b981'};">${data.close.toFixed(2)}</span></div>
                <div><span style="color: #64748b;">最低：</span><span style="font-weight: 500; color: #10b981;">${data.low.toFixed(2)}</span></div>
                <div><span style="color: #64748b;">最高：</span><span style="font-weight: 500; color: #ef4444;">${data.high.toFixed(2)}</span></div>
                <div><span style="color: #64748b;">涨跌：</span><span style="font-weight: 500; color: ${change >= 0 ? '#ef4444' : '#10b981'};">${change >= 0 ? '+' : ''}${change.toFixed(2)}</span></div>
                <div><span style="color: #64748b;">幅度：</span><span style="font-weight: 500; color: ${change >= 0 ? '#ef4444' : '#10b981'};">${change >= 0 ? '+' : ''}${changePct.toFixed(2)}%</span></div>
                <div><span style="color: #64748b;">成交量：</span><span style="font-weight: 500;">${(data.volume / 10000).toFixed(1)}万手</span></div>
                ${data.amount ? `<div><span style="color: #64748b;">成交额：</span><span style="font-weight: 500;">${(data.amount / 10000).toFixed(0)}万</span></div>` : ''}
              </div>
            </div>
          `
        },
      },
      legend: {
        data: ['K 线', 'MA5', 'MA10', 'MA20'],
        bottom: 8,
        itemWidth: 12,
        itemHeight: 8,
        textStyle: { 
          color: '#64748b',
          fontSize: 11,
        },
        icon: 'roundRect',
      },
      grid: [
        { 
          left: '8%', 
          right: '8%', 
          height: '55%',
          top: '8%',
          borderColor: '#f1f5f9',
          borderWidth: 1,
        },
        { 
          left: '8%', 
          right: '8%', 
          top: '72%', 
          height: '18%',
          borderColor: '#f1f5f9',
          borderWidth: 1,
        },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          gridIndex: 0,
          axisLine: { 
            lineStyle: { 
              color: '#e2e8f0',
              width: 1,
            } 
          },
          axisLabel: { 
            color: '#64748b',
            fontSize: 10,
            margin: 8,
            rotate: 0,
          },
          axisTick: {
            show: false,
          },
          splitLine: {
            show: false,
          },
        },
        {
          type: 'category',
          data: dates,
          gridIndex: 1,
          axisLine: { 
            lineStyle: { 
              color: '#e2e8f0',
              width: 1,
            } 
          },
          axisLabel: { 
            color: '#64748b',
            fontSize: 10,
            margin: 8,
            rotate: 0,
          },
          axisTick: {
            show: false,
          },
          splitLine: {
            show: false,
          },
        },
      ],
      yAxis: [
        {
          scale: true,
          gridIndex: 0,
          axisLine: { 
            lineStyle: { 
              color: '#e2e8f0',
              width: 1,
            } 
          },
          axisLabel: { 
            color: '#64748b',
            fontSize: 10,
            formatter: (value: number) => value.toFixed(2),
            margin: 8,
          },
          axisTick: {
            show: false,
          },
          splitLine: { 
            lineStyle: { 
              color: '#f1f5f9',
              width: 1,
              type: 'dashed',
            } 
          },
        },
        {
          scale: true,
          gridIndex: 1,
          splitLine: { show: false },
          axisLine: { 
            lineStyle: { 
              color: '#e2e8f0',
              width: 1,
            } 
          },
          axisLabel: { 
            color: '#64748b',
            fontSize: 10,
            formatter: (value: number) => {
              if (value >= 100000000) {
                return (value / 100000000).toFixed(0) + '亿'
              }
              if (value >= 10000) {
                return (value / 10000).toFixed(0) + '万'
              }
              return value.toFixed(0)
            },
            margin: 8,
          },
          axisTick: {
            show: false,
          },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 50,
          end: 100,
          zoomOnMouseWheel: true,
          moveOnMouseMove: true,
          zoomLock: false,
          roam: true,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          bottom: 8,
          height: 16,
          backgroundColor: '#f1f5f9',
          fillerColor: 'rgba(59, 130, 246, 0.2)',
          borderColor: '#e2e8f0',
          textStyle: { 
            color: '#64748b',
            fontSize: 10,
          },
          handleIcon: 'path://M10.56,5.05c0.16-0.09,0.35-0.09,0.51,0l3.69,2.03c0.46,0.25,0.46,0.92,0,1.17l-3.69,2.03c-0.16,0.09-0.35,0.09-0.51,0l-3.69-2.03C6.42,8.1,6.42,7.43,6.87,7.18L10.56,5.05z M10.56,12.95c-0.16,0.09-0.35,0.09-0.51,0l-3.69-2.03c-0.46-0.25-0.46-0.92,0-1.17l3.69-2.03c0.16-0.09,0.35-0.09,0.51,0l3.69,2.03c0.46,0.25,0.46,0.92,0,1.17L10.56,12.95z',
          handleSize: '100%',
          handleStyle: {
            color: '#94a3b8',
            shadowBlur: 4,
            shadowColor: 'rgba(0, 0, 0, 0.2)',
            shadowOffsetX: 0,
            shadowOffsetY: 2,
          },
          selectedDataBackground: {
            lineStyle: {
              color: '#3b82f6',
            },
            areaStyle: {
              color: 'rgba(59, 130, 246, 0.1)',
            },
          },
          zoomLock: false,
          roam: true,
        },
      ],
      series: [
        {
          name: 'K 线',
          type: 'candlestick',
          data: ohlc,
          barWidth: '60%',
          barMaxWidth: 20,
          itemStyle: {
            color: '#ef4444',
            color0: '#10b981',
            borderColor: '#ef4444',
            borderColor0: '#10b981',
            borderWidth: 1.5,
          },
          markLine: {
            symbol: 'none',
            label: {
              show: false,
            },
            lineStyle: {
              color: '#f59e0b',
              width: 1,
              type: 'dashed',
            },
          },
        },
        {
          name: 'MA5',
          type: 'line',
          data: ma5,
          smooth: true,
          lineStyle: { 
            color: '#f59e0b',
            width: 1.5,
            type: 'solid',
          },
          itemStyle: { 
            color: '#f59e0b',
            borderWidth: 2,
          },
          showSymbol: false,
        },
        {
          name: 'MA10',
          type: 'line',
          data: ma10,
          smooth: true,
          lineStyle: { 
            color: '#3b82f6',
            width: 1.5,
            type: 'solid',
          },
          itemStyle: { 
            color: '#3b82f6',
            borderWidth: 2,
          },
          showSymbol: false,
        },
        {
          name: 'MA20',
          type: 'line',
          data: ma20,
          smooth: true,
          lineStyle: { 
            color: '#8b5cf6',
            width: 1.5,
            type: 'solid',
          },
          itemStyle: { 
            color: '#8b5cf6',
            borderWidth: 2,
          },
          showSymbol: false,
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          barWidth: '60%',
          barMaxWidth: 20,
          itemStyle: {
            color: (params: { dataIndex: number }) => {
              const idx = params.dataIndex
              const open = ohlc[idx][0]
              const close = ohlc[idx][1]
              return close >= open
                ? 'rgba(239, 68, 68, 0.7)'
                : 'rgba(16, 185, 129, 0.7)'
            },
          },
        },
      ],
    }
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
      alert('无数据可导出')
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

    alert(`已导出 ${filteredData.length} 条数据`)

    if (onExport) {
      onExport(filteredData)
    }
  }

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

          <Button size="sm" leftIcon={<DownloadIcon />} onClick={handleExport}>
            导出
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
        mb={4}
        borderWidth="1px"
        borderColor="gray.200"
      >
        <ReactECharts
          option={getKLineOption()}
          style={{ height: '500px' }}
          showLoading={loading}
          notMerge={true}
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
