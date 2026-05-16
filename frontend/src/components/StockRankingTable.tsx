/**
 * 股票排行榜表格组件
 * 显示涨幅榜、跌幅榜、成交额榜等
 */
import React, { useMemo, memo } from 'react'
import { Badge, Box, Table, Text } from '@chakra-ui/react'
import { useColorModeValue } from './ui/color-mode'
import type { StockRankingItem } from '../types'

interface StockRankingTableProps {
  data: StockRankingItem[]
  type?: 'gainers' | 'losers' | 'amount' | 'turnover'
  showRank?: boolean
  maxItems?: number
}

const StockRankingTable: React.FC<StockRankingTableProps> = memo(({ 
  data, 
  type = 'gainers',
  showRank = true,
  maxItems = 50
}) => {
  const hoverBg = useColorModeValue('gray.50', 'gray.700')
  
  // 使用 useMemo 缓存格式化函数
  const formatters = useMemo(() => ({
    formatPctChange: (pct: number) => {
      const sign = pct > 0 ? '+' : ''
      return `${sign}${pct.toFixed(2)}%`
    },
    formatAmount: (amount?: number) => {
      if (amount === undefined || amount === null) return '-'
      if (amount >= 100000000) {
        return `${(amount / 100000000).toFixed(2)}亿`
      }
      if (amount >= 10000) {
        return `${(amount / 10000).toFixed(2)}万`
      }
      return amount.toFixed(0)
    },
    formatVolume: (volume?: number) => {
      if (volume === undefined || volume === null) return '-'
      if (volume >= 10000) {
        return `${(volume / 10000).toFixed(1)}万`
      }
      return volume.toFixed(0)
    }
  }), [])
  
  // 使用 useMemo 缓存颜色获取函数
  const colorHelpers = useMemo(() => ({
    getPctChangeColor: (pct: number) => {
      if (pct > 0) return 'red.500'
      if (pct < 0) return 'green.500'
      return 'gray.500'
    },
    getRankBadgeColor: (rank: number) => {
      if (rank === 1) return 'red'
      if (rank === 2) return 'orange'
      if (rank === 3) return 'yellow'
      return 'gray'
    }
  }), [])
  
  // 使用 useMemo 缓存显示数据
  const displayData = useMemo(() => data.slice(0, maxItems), [data, maxItems])
  
  // 使用 useMemo 缓存表格标题
  const tableTitle = useMemo(() => {
    const titles = {
      gainers: '涨幅榜',
      losers: '跌幅榜',
      amount: '成交额榜',
      turnover: '换手率榜'
    }
    return titles[type]
  }, [type])
  
  return (
    <Box bg="white" borderRadius="lg" boxShadow="md" overflow="hidden">
      <Box px={4} py={3} bg="gray.50" borderBottom="1px" borderColor="gray.200">
        <Text fontWeight="bold" fontSize="lg" color="gray.700">
          {tableTitle}
        </Text>
      </Box>
      
      <Box>
        <Table.Root size="sm" >
          <Table.Header bg="gray.50">
            <Table.Row>
              {showRank && (
                <Table.ColumnHeader width="60px" textAlign="center">排名</Table.ColumnHeader>
              )}
              <Table.ColumnHeader>代码</Table.ColumnHeader>
              <Table.ColumnHeader>名称</Table.ColumnHeader>
              <Table.ColumnHeader >现价</Table.ColumnHeader>
              {type !== 'amount' && type !== 'turnover' && (
                <Table.ColumnHeader >涨跌幅</Table.ColumnHeader>
              )}
              {type !== 'turnover' && (
                <Table.ColumnHeader >成交量</Table.ColumnHeader>
              )}
              {(type === 'amount' || type === 'turnover') && (
                <Table.ColumnHeader >成交额</Table.ColumnHeader>
              )}
              {type === 'turnover' && (
                <Table.ColumnHeader >换手率</Table.ColumnHeader>
              )}
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {displayData.map((item, index) => (
              <Table.Row 
                key={item.ts_code} 
                _hover={{ bg: hoverBg }}
                cursor="pointer"
              >
                {showRank && (
                  <Table.Cell textAlign="center">
                    <Badge 
                      colorPalette={colorHelpers.getRankBadgeColor(index + 1)}
                      minWidth="24px"
                      textAlign="center"
                      fontSize="xs"
                      px={2}
                      py={1}
                      borderRadius="md"
                    >
                      {index + 1}
                    </Badge>
                  </Table.Cell>
                )}
                <Table.Cell>
                  <Text fontSize="xs" color="gray.600" fontFamily="mono">
                    {item.ts_code}
                  </Text>
                </Table.Cell>
                <Table.Cell fontWeight="medium" color="gray.700">
                  {item.name}
                </Table.Cell>
                <Table.Cell fontWeight="bold" color="gray.700">
                  {item.price?.toFixed(2) || '-'}
                </Table.Cell>
                {type !== 'amount' && type !== 'turnover' && (
                  <Table.Cell 
                    fontWeight="bold"
                    color={colorHelpers.getPctChangeColor(item.pct_change)}
                  >
                    {formatters.formatPctChange(item.pct_change)}
                  </Table.Cell>
                )}
                {type !== 'turnover' && (
                  <Table.Cell fontSize="xs" color="gray.600">
                    {formatters.formatVolume(item.volume)}
                  </Table.Cell>
                )}
                {(type === 'amount' || type === 'turnover') && (
                  <Table.Cell fontSize="xs" color="gray.600">
                    {formatters.formatAmount(item.amount)}
                  </Table.Cell>
                )}
                {type === 'turnover' && (
                  <Table.Cell fontSize="xs" color="gray.600">
                    {item.turnover_rate?.toFixed(2) || '-'}%
                  </Table.Cell>
                )}
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
      
      {data.length > maxItems && (
        <Box px={4} py={2} bg="gray.50" borderTop="1px" borderColor="gray.200">
          <Text fontSize="xs" color="gray.500" textAlign="center">
            共 {data.length} 只股票，仅显示前 {maxItems} 只
          </Text>
        </Box>
      )}
    </Box>
  )
})

StockRankingTable.displayName = 'StockRankingTable'

export default StockRankingTable
