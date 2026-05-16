import React, { useMemo } from 'react'
import { Box, Flex, Text, Button, Spinner, VStack } from '@chakra-ui/react'
import { useKLine } from '@/hooks/useKLine'
import { CanvasChart } from './CanvasChart'
import { VolumeChart } from './VolumeChart'
import type { KType, IndicatorType } from '@/types/chart'

interface KLineChartProps {
  code: string
  kType?: KType
  indicators?: IndicatorType[]
  height?: string
  showVolume?: boolean
  showIndicators?: boolean
  useWorker?: boolean
  onZoom?: (scale: number) => void
  onPan?: (offset: number) => void
}

export const KLineChart: React.FC<KLineChartProps> = ({
  code,
  kType = 'daily',
  indicators = ['MA', 'MACD', 'RSI'],
  height = '500px',
  showVolume = true,
  showIndicators = true,
  useWorker = true,
  onZoom,
  onPan
}) => {
  const {
    data,
    indicators: indicatorData,
    loading,
    error,
    refresh,
    calculating,
    rendering
  } = useKLine({
    code,
    kType,
    indicators,
    useWorker
  })

  const renderData = useMemo(() => {
    if (!data) return null

    return {
      kline: data,
      indicators: indicatorData || undefined,
      config: {
        width: 800,
        height: 400,
        candleWidth: 10,
        candleSpacing: 2,
        colors: {
          up: '#ef232a',
          down: '#14cf1a',
          ma5: '#ff9800',
          ma10: '#2196f3',
          ma20: '#9c27b0',
          ma60: '#795548',
          grid: '#e0e0e0',
          text: '#333333',
          axis: '#999999'
        },
        margins: {
          top: 20,
          right: 60,
          bottom: 30,
          left: 10
        }
      }
    }
  }, [data, indicatorData])

  if (error) {
    return (
      <Flex
        h={height}
        align="center"
        justify="center"
        border="1px solid"
        borderColor="border"
        borderRadius="md"
      >
        <VStack gap={2} textAlign="center">
          <Text color="red.500" fontWeight="600">图表加载失败</Text>
          <Text fontSize="xs" color="fg.muted">{error.message}</Text>
          <Button size="sm" colorPalette="blue" onClick={() => refresh()}>重试</Button>
        </VStack>
      </Flex>
    )
  }

  if (loading || !renderData) {
    return (
      <Flex
        h={height}
        align="center"
        justify="center"
        border="1px solid"
        borderColor="border"
        borderRadius="md"
      >
        <VStack gap={3}>
          <Spinner size="lg" color="brand.500" />
          <Text fontSize="sm" color="fg.muted">
            {calculating ? '计算指标中...' : rendering ? '渲染图表中...' : '加载数据中...'}
          </Text>
        </VStack>
      </Flex>
    )
  }

  return (
    <Box
      h={height}
      border="1px solid"
      borderColor="border"
      borderRadius="md"
      overflow="hidden"
      bg="bg.panel"
    >
      <Flex
        px={3}
        py={2}
        borderBottom="1px solid"
        borderColor="border"
        justify="space-between"
        align="center"
        bg="bg.subtle"
      >
        <Flex gap={2}>
          <Text fontSize="xs" color="fg.muted">{code}</Text>
          <Text fontSize="xs" color="fg.subtle">
            {kType === 'daily' ? '日线' : kType === 'weekly' ? '周线' : '月线'}
          </Text>
        </Flex>
        <Button size="2xs" variant="outline" onClick={() => refresh()}>刷新</Button>
      </Flex>

      <Box h="300px">
        <CanvasChart data={renderData} onZoom={onZoom} onPan={onPan} />
      </Box>

      {showVolume && (
        <Box h="100px" borderTop="1px solid" borderColor="border">
          <VolumeChart data={data} />
        </Box>
      )}

      {showIndicators && indicatorData && (
        <>
          {indicatorData.MACD && (
            <Box h="150px" borderTop="1px solid" borderColor="border">
              MACD Chart Placeholder
            </Box>
          )}
          {indicatorData.RSI && (
            <Box h="120px" borderTop="1px solid" borderColor="border">
              RSI Chart Placeholder
            </Box>
          )}
        </>
      )}
    </Box>
  )
}

export default KLineChart
