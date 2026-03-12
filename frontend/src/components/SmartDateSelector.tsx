import { Box, Flex, Text, Button, HStack, Badge, Tooltip, useColorModeValue, Slider, SliderTrack, SliderFilledTrack, SliderThumb, Input, Popover, PopoverTrigger, PopoverContent, PopoverBody, PopoverArrow, useToast } from '@chakra-ui/react'
import { useState, useEffect, useCallback, useRef } from 'react'
import { screenerApi } from '../services/api'
import { FiCalendar, FiClock, FiCheck, FiRefreshCw, FiChevronLeft, FiChevronRight } from 'react-icons/fi'

interface TradingDay {
  date: string
  display: string
  is_today: boolean
  is_latest: boolean
  is_selected: boolean
}

interface EffectiveDateInfo {
  effective_date: string
  is_today: boolean
  is_market_open: boolean
  latest_trading_day: string
  previous_trading_day: string
  current_time: string
}

interface SmartDateSelectorProps {
  onDateChange?: (date: string) => void
  enableAutoRefresh?: boolean  // 是否启用自动刷新
  showSlider?: boolean  // 是否显示滑块
}

const CACHE_KEY = 'trading_days_cache'
const CACHE_TIMESTAMP_KEY = 'trading_days_cache_timestamp'
const CACHE_EXPIRY = 5 * 60 * 1000 // 5 分钟缓存过期

export const SmartDateSelector = ({ 
  onDateChange,
  enableAutoRefresh = true,
  showSlider = true 
}: SmartDateSelectorProps) => {
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [tradingDays, setTradingDays] = useState<TradingDay[]>([])
  const [effectiveInfo, setEffectiveInfo] = useState<EffectiveDateInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)
  const [sliderValue, setSliderValue] = useState(0)
  const [customDate, setCustomDate] = useState<string>('')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null)
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null)

  const bgColor = useColorModeValue('white', 'gray.800')
  const hoverBg = useColorModeValue('gray.50', 'gray.700')
  const toast = useToast()

  // 从缓存加载数据
  const loadFromCache = useCallback(() => {
    try {
      const cachedData = localStorage.getItem(CACHE_KEY)
      const cachedTimestamp = localStorage.getItem(CACHE_TIMESTAMP_KEY)
      
      if (cachedData && cachedTimestamp) {
        const timestamp = parseInt(cachedTimestamp)
        const now = Date.now()
        
        // 检查缓存是否过期
        if (now - timestamp < CACHE_EXPIRY) {
          const parsed = JSON.parse(cachedData)
          setTradingDays(parsed.tradingDays)
          setEffectiveInfo(parsed.effectiveInfo)
          setSelectedDate(parsed.selectedDate)
          setLastRefreshTime(new Date(timestamp))
          return true
        }
      }
    } catch (error) {
      console.warn('加载缓存失败:', error)
    }
    return false
  }, [])

  // 保存到缓存
  const saveToCache = useCallback((data: { tradingDays: TradingDay[], effectiveInfo: EffectiveDateInfo, selectedDate: string }) => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(data))
      localStorage.setItem(CACHE_TIMESTAMP_KEY, Date.now().toString())
    } catch (error) {
      console.warn('保存缓存失败:', error)
    }
  }, [])

  // 加载交易日数据
  const loadTradingDays = useCallback(async (forceRefresh = false) => {
    try {
      setIsLoading(true)
      setIsRefreshing(forceRefresh)
      
      // 尝试从缓存加载（非强制刷新）
      if (!forceRefresh && loadFromCache()) {
        if (onDateChange) {
          onDateChange(selectedDate)
        }
        setIsLoading(false)
        setIsRefreshing(false)
        return
      }
      
      // 从服务器加载（带超时处理）
      try {
        const effectiveResult = await Promise.race([
          screenerApi.getEffectiveDate(),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('请求超时')), 10000)
          )
        ]) as any
        const effectiveData = effectiveResult.data
        setEffectiveInfo(effectiveData)
        
        const tradingDaysResult = await Promise.race([
          screenerApi.getTradingDays(20),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('请求超时')), 10000)
          )
        ]) as any
        const tradingDaysData = tradingDaysResult.data
        
        // 标记选中的日期
        const updatedDays = tradingDaysData.map((day: TradingDay, index: number) => ({
          ...day,
          is_selected: index === 0
        }))
        
        setTradingDays(updatedDays)
        setSelectedDate(effectiveData.effective_date)
        setSliderValue(0)
        
        // 保存到缓存
        saveToCache({
          tradingDays: updatedDays,
          effectiveInfo: effectiveData,
          selectedDate: effectiveData.effective_date
        })
        
        // 通知父组件
        if (onDateChange) {
          onDateChange(effectiveData.effective_date)
        }
        
        if (forceRefresh) {
          toast({
            title: '数据已刷新',
            status: 'success',
            duration: 2000,
            position: 'top-right',
            isClosable: true
          })
        }
      } catch (apiError: any) {
        // API 失败时不估算，显示错误提示
        console.error('API 加载失败:', apiError.message)
        
        toast({
          title: '数据加载失败',
          description: `无法获取交易日数据：${apiError.message || '请求超时'}`,
          status: 'error',
          duration: 5000,
          position: 'top-right',
          isClosable: true
        })
        
        // 尝试从缓存加载旧数据
        loadFromCache()
      }
    } catch (error) {
      console.error('加载交易日失败:', error)
      toast({
        title: '加载失败',
        description: '无法加载交易日数据',
        status: 'error',
        duration: 3000,
        position: 'top-right',
        isClosable: true
      })
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [loadFromCache, saveToCache, onDateChange, toast, selectedDate])

  // 初始加载
  useEffect(() => {
    loadTradingDays()
  }, [loadTradingDays])

  // 自动刷新（盘中）
  useEffect(() => {
    if (!enableAutoRefresh || !effectiveInfo?.is_market_open) {
      return
    }

    // 30 秒刷新一次
    refreshTimerRef.current = setInterval(() => {
      loadTradingDays(false)
    }, 30000)

    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current)
      }
    }
  }, [enableAutoRefresh, effectiveInfo?.is_market_open, loadTradingDays])

  const handleDateSelect = (date: string) => {
    setSelectedDate(date)
    setShowAll(false)
    
    // 通知父组件
    if (onDateChange) {
      onDateChange(date)
    }
  }

  const handleSliderChange = (value: number) => {
    setSliderValue(value)
    if (tradingDays[value]) {
      handleDateSelect(tradingDays[value].date)
    }
  }

  const handleCustomDateSelect = () => {
    if (customDate) {
      const formattedDate = customDate.replace(/-/g, '')
      handleDateSelect(formattedDate)
    }
  }

  const handleManualRefresh = () => {
    loadTradingDays(true)
  }

  const navigateDate = (direction: 'prev' | 'next') => {
    const currentIndex = tradingDays.findIndex(day => day.date === selectedDate)
    if (currentIndex === -1) return
    
    const newIndex = direction === 'prev' 
      ? Math.min(currentIndex + 1, tradingDays.length - 1)
      : Math.max(currentIndex - 1, 0)
    
    if (newIndex !== currentIndex && tradingDays[newIndex]) {
      handleDateSelect(tradingDays[newIndex].date)
      setSliderValue(newIndex)
    }
  }

  const getStatusBadge = () => {
    if (!effectiveInfo) return null

    if (effectiveInfo.is_market_open) {
      return (
        <Badge colorScheme="green" variant="subtle" fontSize="xs" px={2} py={1} borderRadius="full">
          <Flex align="center" gap={1}>
            <Box w={1.5} h={1.5} borderRadius="full" bg="green.500" />
            交易中
          </Flex>
        </Badge>
      )
    } else if (effectiveInfo.is_today) {
      return (
        <Badge colorScheme="orange" variant="subtle" fontSize="xs" px={2} py={1} borderRadius="full">
          <Flex align="center" gap={1}>
            <FiClock size={10} />
            未开盘
          </Flex>
        </Badge>
      )
    } else {
      return (
        <Badge colorScheme="blue" variant="subtle" fontSize="xs" px={2} py={1} borderRadius="full">
          历史数据
        </Badge>
      )
    }
  }

  const formatDateLabel = (date: string) => {
    try {
      const [year, month, day] = date.match(/(\d{4})(\d{2})(\d{2})/)!.slice(1)
      return `${year}年${parseInt(month)}月${parseInt(day)}日`
    } catch {
      return date
    }
  }

  const displayedDays = showAll ? tradingDays : tradingDays.slice(0, 5)

  if (isLoading) {
    return (
      <Flex align="center" gap={2} px={3} py={2}>
        <FiCalendar size={16} />
        <Text fontSize="sm">加载中...</Text>
      </Flex>
    )
  }

  return (
    <Flex direction="column" gap={3} w="100%">
      {/* 日期选择器头部 */}
      <Flex 
        align="center" 
        gap={3} 
        px={3} 
        py={2}
        bg={bgColor}
        borderRadius="lg"
        border="1px solid"
        borderColor="gray.200"
        _hover={{ borderColor: 'brand.500' }}
        transition="all 0.2s"
        wrap="wrap"
      >
        <FiCalendar size={16} color="#6b7280" />
        
        <Flex direction="column" flex={1} minW="150px">
          <Flex align="center" gap={2} wrap="wrap">
            <Text fontSize="sm" fontWeight="medium" color="gray.700">
              {formatDateLabel(selectedDate)}
            </Text>
            {getStatusBadge()}
          </Flex>
          
          {effectiveInfo && !effectiveInfo.is_today && (
            <Text fontSize="xs" color="gray.500">
              显示 {effectiveInfo.latest_trading_day === selectedDate ? '最新' : '历史'} 交易日数据
            </Text>
          )}
        </Flex>

        {/* 刷新按钮 */}
        <Tooltip label={lastRefreshTime ? `上次刷新：${lastRefreshTime.toLocaleTimeString()}` : '刷新数据'}>
          <Button
            size="sm"
            variant="ghost"
            colorScheme="blue"
            onClick={handleManualRefresh}
            isLoading={isRefreshing}
            minW="auto"
            p={2}
          >
            <FiRefreshCw size={16} />
          </Button>
        </Tooltip>

        {/* 日期导航 */}
        <Flex align="center" gap={1}>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigateDate('next')}
            disabled={sliderValue === 0}
            minW="auto"
            p={2}
          >
            <FiChevronLeft size={16} />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigateDate('prev')}
            disabled={sliderValue >= tradingDays.length - 1}
            minW="auto"
            p={2}
          >
            <FiChevronRight size={16} />
          </Button>
        </Flex>

        {/* 自定义日期选择 */}
        <Popover>
          <PopoverTrigger>
            <Button size="sm" variant="outline" colorScheme="gray">
              <FiCalendar size={14} />
            </Button>
          </PopoverTrigger>
          <PopoverContent w="auto">
            <PopoverArrow />
            <PopoverBody>
              <Flex gap={2} align="center">
                <Input
                  type="date"
                  value={customDate}
                  onChange={(e) => setCustomDate(e.target.value)}
                  size="sm"
                  max={new Date().toISOString().split('T')[0]}
                />
                <Button size="sm" colorScheme="blue" onClick={handleCustomDateSelect}>
                  确定
                </Button>
              </Flex>
            </PopoverBody>
          </PopoverContent>
        </Popover>
      </Flex>

      {/* 日期滑块 */}
      {showSlider && tradingDays.length > 0 && (
        <Box px={2} py={1}>
          <Slider
            value={sliderValue}
            onChange={handleSliderChange}
            min={0}
            max={tradingDays.length - 1}
            step={1}
            colorScheme="brand"
            focusThumbOnChange={false}
          >
            <SliderTrack>
              <SliderFilledTrack />
            </SliderTrack>
            <SliderThumb boxSize={6}>
              <Box color="brand.500" as={FiCalendar} />
            </SliderThumb>
          </Slider>
          
          {/* 滑块标签 */}
          <Flex justify="space-between" mt={1} px={1}>
            {tradingDays.slice(0, 5).map((day, index) => (
              <Text 
                key={day.date} 
                fontSize="xs" 
                color={sliderValue === index ? 'brand.500' : 'gray.400'}
                fontWeight={sliderValue === index ? 'bold' : 'normal'}
                cursor="pointer"
                onClick={() => handleSliderChange(index)}
              >
                {day.display.split('月')[1]}
              </Text>
            ))}
          </Flex>
        </Box>
      )}

      {/* 日期选择列表 */}
      {showAll && (
        <Box 
          bg={bgColor}
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          p={3}
          animation="slideDown 0.2s ease-out"
        >
          <HStack spacing={2} wrap="wrap">
            {displayedDays.map((day) => (
              <Tooltip
                key={day.date}
                label={
                  <Flex direction="column" gap={1}>
                    <Text fontWeight="bold">{day.display}</Text>
                    {day.is_latest && <Text fontSize="xs">最新交易日</Text>}
                    {day.is_today && <Text fontSize="xs">今天</Text>}
                    {day.is_selected && <Text fontSize="xs">已选择</Text>}
                  </Flex>
                }
              >
                <Button
                  size="sm"
                  variant={selectedDate === day.date ? 'solid' : 'outline'}
                  colorScheme={day.is_latest ? 'brand' : 'gray'}
                  onClick={() => handleDateSelect(day.date)}
                  minW="80px"
                  position="relative"
                  _hover={{
                    transform: 'translateY(-1px)',
                    boxShadow: 'md'
                  }}
                  transition="all 0.2s"
                >
                  <Flex direction="column" align="center" gap={0.5}>
                    <Text fontSize="xs">{day.display.split('月')[0]}月</Text>
                    <Text fontSize="sm" fontWeight="bold">{day.display.split('月')[1]}</Text>
                  </Flex>
                  
                  {selectedDate === day.date && (
                    <Box
                      position="absolute"
                      top="-2px"
                      right="-2px"
                      bg="green.500"
                      color="white"
                      borderRadius="full"
                      p={0.5}
                    >
                      <FiCheck size={8} />
                    </Box>
                  )}
                </Button>
              </Tooltip>
            ))}
          </HStack>
          
          {effectiveInfo && (
            <Flex justify="space-between" align="center" mt={3} pt={2} borderTop="1px solid" borderColor="gray.100">
              <Text fontSize="xs" color="gray.500">
                当前时间：{effectiveInfo.current_time}
              </Text>
              <Text fontSize="xs" color="gray.500">
                {effectiveInfo.is_market_open ? '已开盘' : '未开盘'}
              </Text>
            </Flex>
          )}
        </Box>
      )}

      <style>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </Flex>
  )
}
