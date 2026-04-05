/**
 * KLineChart 主组件
 * 现代化的 K 线图表组件（替代 ECharts）
 */

import React, { useMemo } from 'react'
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
  // 使用智能 Hook
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

  // 生成渲染数据
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

  // 错误处理
  if (error) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid #e0e0e0',
          borderRadius: '4px'
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#f44336', marginBottom: '8px' }}>
            图表加载失败
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '16px' }}>
            {error.message}
          </div>
          <button
            onClick={refresh}
            style={{
              padding: '8px 16px',
              backgroundColor: '#2196f3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  // 加载状态
  if (loading || !renderData) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid #e0e0e0',
          borderRadius: '4px'
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              border: '4px solid #e0e0e0',
              borderTop: '4px solid #2196f3',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 16px'
            }}
          />
          <div style={{ color: '#666' }}>
            {calculating ? '计算指标中...' : rendering ? '渲染图表中...' : '加载数据中...'}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      style={{
        height,
        border: '1px solid #e0e0e0',
        borderRadius: '4px',
        overflow: 'hidden',
        backgroundColor: '#fff'
      }}
    >
      {/* 工具栏 */}
      <div
        style={{
          padding: '8px 12px',
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#f5f5f5'
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: '#666' }}>
            {code}
          </span>
          <span style={{ fontSize: '12px', color: '#999' }}>
            {kType === 'daily' ? '日线' : kType === 'weekly' ? '周线' : '月线'}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={refresh}
            style={{
              padding: '4px 8px',
              fontSize: '12px',
              backgroundColor: '#fff',
              border: '1px solid #ddd',
              borderRadius: '2px',
              cursor: 'pointer'
            }}
          >
            刷新
          </button>
        </div>
      </div>

      {/* K 线主图 */}
      <div style={{ height: '300px' }}>
        <CanvasChart
          data={renderData}
          onZoom={onZoom}
          onPan={onPan}
        />
      </div>

      {/* 成交量图 */}
      {showVolume && (
        <div style={{ height: '100px', borderTop: '1px solid #e0e0e0' }}>
          <VolumeChart data={data} />
        </div>
      )}

      {/* 指标图 */}
      {showIndicators && indicatorData && (
        <>
          {indicatorData.MACD && (
            <div style={{ height: '150px', borderTop: '1px solid #e0e0e0' }}>
              MACD Chart Placeholder
            </div>
          )}
          {indicatorData.RSI && (
            <div style={{ height: '120px', borderTop: '1px solid #e0e0e0' }}>
              RSI Chart Placeholder
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default KLineChart
