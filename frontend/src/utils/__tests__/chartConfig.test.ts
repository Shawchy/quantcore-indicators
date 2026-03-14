import { describe, it, expect } from 'vitest'
import {
  getBarOption,
  getKlineOption,
  getPieOption,
  getLineOption,
  getMoneyFlowOption,
} from '../chartConfig'

describe('chartConfig', () => {
  const mockBarData = [
    { name: '股票A', change_pct: 5.2 },
    { name: '股票B', change_pct: -3.1 },
    { name: '股票C', change_pct: 2.8 },
  ]

  describe('getBarOption', () => {
    it('should generate correct bar chart option', () => {
      const option = getBarOption(mockBarData, 'change_pct', 'name', '涨跌幅排名')

      expect(option).toHaveProperty('title')
      expect(option).toHaveProperty('tooltip')
      expect(option).toHaveProperty('xAxis')
      expect(option).toHaveProperty('yAxis')
      expect(option).toHaveProperty('series')

      expect(option.series).toHaveLength(1)
      expect(option.series[0].type).toBe('bar')
    })

    it('should handle empty data', () => {
      const option = getBarOption([])

      expect(option.series[0].data).toHaveLength(0)
    })
  })

  describe('getKlineOption', () => {
    it('should generate correct K-line chart option', () => {
      const dates = ['2024-01-01', '2024-01-02', '2024-01-03']
      const closes = [10.5, 11.2, 10.8]
      const volumes = [10000, 15000, 12000]

      const option = getKlineOption(dates, closes, volumes)

      expect(option).toHaveProperty('tooltip')
      expect(option).toHaveProperty('xAxis')
      expect(option).toHaveProperty('yAxis')
      expect(option).toHaveProperty('series')

      expect(option.series).toHaveLength(2)
      expect(option.series[0].type).toBe('line')
      expect(option.series[1].type).toBe('bar')
    })

    it('should handle empty data', () => {
      const option = getKlineOption([], [], [])

      expect(option.series[0].data).toHaveLength(0)
      expect(option.series[1].data).toHaveLength(0)
    })
  })

  describe('getPieOption', () => {
    it('should generate correct pie chart option', () => {
      const data = [
        { name: 'A', value: 30 },
        { name: 'B', value: 50 },
        { name: 'C', value: 20 },
      ]

      const option = getPieOption(data, '分布图')

      expect(option).toHaveProperty('title')
      expect(option).toHaveProperty('tooltip')
      expect(option).toHaveProperty('legend')
      expect(option).toHaveProperty('series')

      expect(option.series).toHaveLength(1)
      expect(option.series[0].type).toBe('pie')
    })
  })

  describe('getLineOption', () => {
    it('should generate correct line chart option', () => {
      const data = [
        { date: '2024-01-01', value: 100 },
        { date: '2024-01-02', value: 105 },
        { date: '2024-01-03', value: 103 },
      ]

      const option = getLineOption(data, 'value', 'date')

      expect(option).toHaveProperty('tooltip')
      expect(option).toHaveProperty('xAxis')
      expect(option).toHaveProperty('yAxis')
      expect(option).toHaveProperty('series')

      expect(option.series).toHaveLength(1)
      expect(option.series[0].type).toBe('line')
      expect(option.series[0].smooth).toBe(true)
    })
  })

  describe('getMoneyFlowOption', () => {
    it('should generate correct money flow chart option', () => {
      const data = {
        super: 1000,
        big: 2000,
        mid: 1500,
        small: 500,
      }

      const option = getMoneyFlowOption(data)

      expect(option).toHaveProperty('tooltip')
      expect(option).toHaveProperty('series')

      expect(option.series).toHaveLength(1)
      expect(option.series[0].type).toBe('pie')
      expect(option.series[0].data).toHaveLength(4)
    })

    it('should handle missing data', () => {
      const option = getMoneyFlowOption({})

      expect(option.series[0].data).toHaveLength(4)
      expect(option.series[0].data[0].value).toBe(0)
    })
  })
})
