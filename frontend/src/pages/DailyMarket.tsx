/**
 * A 股日线行情页面
 * 展示全市场 A 股的日线 K 线数据和行情信息
 */
import React, { useState } from 'react'
import {
  Box,
  Flex,
  Text,
  Input,
  Button,
  InputGroup,
  InputLeftElement,
  VStack,
  useToast,
  Card,
  CardBody,
  Badge,
  HStack,
} from '@chakra-ui/react'
import { SearchIcon } from '@chakra-ui/icons'
import { useQuery } from '@tanstack/react-query'
import { stockApi } from '../services/api'
import DailyKLine from '../components/DailyKLine'

const DailyMarketPage: React.FC = () => {
  const toast = useToast()
  const [searchCode, setSearchCode] = useState('')
  const [currentCode, setCurrentCode] = useState('000001') // 默认平安银行

  // 计算日期范围（近 3 年）
  const getEndDate = () => {
    const now = new Date()
    return now.toISOString().split('T')[0]
  }

  const getStartDate = () => {
    const now = new Date()
    now.setFullYear(now.getFullYear() - 3) // 3 年前
    return now.toISOString().split('T')[0]
  }

  // 获取 K 线数据
  const { data, isLoading, error } = useQuery({
    queryKey: ['kline', currentCode],
    queryFn: () => stockApi.getKline(currentCode, {
      startDate: getStartDate(),
      endDate: getEndDate(),
      adjust: 'qfq',
      priorityLoad: true,
    }),
    enabled: !!currentCode,
  })

  // 获取股票基本信息
  const { data: basicData } = useQuery({
    queryKey: ['stockBasic', currentCode],
    queryFn: () => stockApi.getBasic(currentCode),
    enabled: !!currentCode,
  })

  // 处理搜索
  const handleSearch = () => {
    const code = searchCode.trim()
    if (!/^\d{6}$/.test(code)) {
      toast({
        title: '请输入正确的股票代码',
        description: '股票代码为 6 位数字',
        status: 'warning',
        duration: 3000,
      })
      return
    }
    setCurrentCode(code)
  }

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  // 快速选择股票
  const quickStocks = [
    { code: '000001', name: '平安银行' },
    { code: '600000', name: '浦发银行' },
    { code: '600036', name: '招商银行' },
    { code: '000858', name: '五粮液' },
    { code: '600519', name: '贵州茅台' },
  ]

  return (
    <Box>
      {/* 顶部搜索栏 */}
      <Card mb={4}>
        <CardBody>
          <VStack align="stretch" spacing={4}>
            <Flex justify="space-between" align="center" flexWrap="wrap" gap={3}>
              <Text fontWeight="bold" fontSize="xl">
                📈 A 股日线行情
              </Text>

              <InputGroup width={{ base: '100%', md: '400px' }}>
                <InputLeftElement pointerEvents="none">
                  <SearchIcon color="gray.400" />
                </InputLeftElement>
                <Input
                  placeholder="输入股票代码（6 位数字）"
                  value={searchCode}
                  onChange={(e) => setSearchCode(e.target.value)}
                  onKeyPress={handleKeyPress}
                  size="md"
                />
              </InputGroup>
            </Flex>

            {/* 快速选择 */}
            <Flex gap={2} flexWrap="wrap">
              <Text fontSize="sm" color="gray.600" fontWeight="medium">
                热门股票:
              </Text>
              {quickStocks.map((stock) => (
                <Badge
                  key={stock.code}
                  role="button"
                  tabIndex={0}
                  colorScheme={currentCode === stock.code ? 'blue' : 'gray'}
                  fontSize="sm"
                  px={3}
                  py={2}
                  borderRadius="md"
                  cursor="pointer"
                  onClick={() => {
                    setCurrentCode(stock.code)
                    setSearchCode(stock.code)
                  }}
                  _hover={{ bg: 'blue.50' }}
                >
                  {stock.name} ({stock.code})
                </Badge>
              ))}
            </Flex>
          </VStack>
        </CardBody>
      </Card>

      {/* 错误提示 */}
      {error && (
        <Card mb={4} bg="red.50" borderColor="red.200" borderWidth="1px">
          <CardBody>
            <Text color="red.600">
              ❌ 加载失败：{(error as Error).message}
            </Text>
          </CardBody>
        </Card>
      )}

      {/* 日线行情组件 */}
      {data && (
        <Card>
          <CardBody>
            <DailyKLine
              data={data.data?.data || []}
              loading={isLoading}
              code={currentCode}
              name={basicData?.data?.name}
              onExport={(exportedData) => {
                console.log('导出数据:', exportedData)
              }}
            />
          </CardBody>
        </Card>
      )}

      {/* 使用说明 */}
      <Card mt={4} bg="blue.50" borderLeft="4px" borderColor="blue.500">
        <CardBody>
          <Text fontSize="sm" color="blue.800">
            <strong>💡 使用说明：</strong>
            <br />
            • 输入 6 位股票代码查询日线行情，或点击热门股票快速查看
            <br />
            • K 线图支持缩放和拖动，可查看不同时间段的数据
            <br />
            • 显示 MA5、MA10、MA20 三条均线
            <br />
            • 支持导出 CSV 格式数据
            <br />
            • 数据源：Tushare/AkShare（前复权）
          </Text>
        </CardBody>
      </Card>
    </Box>
  )
}

export default DailyMarketPage
