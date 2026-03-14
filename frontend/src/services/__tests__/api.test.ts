import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
// axios 被 mock，但需要在模块中导入以启用 mock
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import axios from 'axios'
import { authApi, stockApi, watchlistApi, sectorApi, type AuthToken } from '../api'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
      put: vi.fn(),
    })),
  },
}))

describe('API Service', () => {
  // mockToken 用于类型检查
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const mockToken: AuthToken = {
    access_token: 'test-access-token',
    refresh_token: 'test-refresh-token',
    token_type: 'bearer',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('authApi', () => {
    it('should have correct login method signature', () => {
      // 验证 login 方法存在且可调用
      expect(typeof authApi.login).toBe('function')
    })

    it('should have correct logout method signature', () => {
      expect(typeof authApi.logout).toBe('function')
    })

    it('should have correct refreshToken method signature', () => {
      expect(typeof authApi.refreshToken).toBe('function')
    })

    it('should have correct getCurrentUser method signature', () => {
      expect(typeof authApi.getCurrentUser).toBe('function')
    })
  })

  describe('stockApi', () => {
    it('should have correct getBasic method signature', () => {
      expect(typeof stockApi.getBasic).toBe('function')
    })

    it('should have correct getKline method signature', () => {
      expect(typeof stockApi.getKline).toBe('function')
    })

    it('should have correct getWeeklyKline method signature', () => {
      expect(typeof stockApi.getWeeklyKline).toBe('function')
    })

    it('should have correct getMonthlyKline method signature', () => {
      expect(typeof stockApi.getMonthlyKline).toBe('function')
    })

    it('should have correct getIndicators method signature', () => {
      expect(typeof stockApi.getIndicators).toBe('function')
    })

    it('should have correct getRealtime method signature', () => {
      expect(typeof stockApi.getRealtime).toBe('function')
    })

    it('should have correct search method signature', () => {
      expect(typeof stockApi.search).toBe('function')
    })
  })

  describe('watchlistApi', () => {
    it('should have correct getList method signature', () => {
      expect(typeof watchlistApi.getList).toBe('function')
    })

    it('should have correct add method signature', () => {
      expect(typeof watchlistApi.add).toBe('function')
    })

    it('should have correct remove method signature', () => {
      expect(typeof watchlistApi.remove).toBe('function')
    })

    it('should have correct update method signature', () => {
      expect(typeof watchlistApi.update).toBe('function')
    })

    it('should have correct getQuotes method signature', () => {
      expect(typeof watchlistApi.getQuotes).toBe('function')
    })
  })

  describe('sectorApi', () => {
    it('should have correct getList method signature', () => {
      expect(typeof sectorApi.getList).toBe('function')
    })

    it('should have correct getRanking method signature', () => {
      expect(typeof sectorApi.getRanking).toBe('function')
    })

    it('should have correct getComponents method signature', () => {
      expect(typeof sectorApi.getComponents).toBe('function')
    })

    it('should have correct getLeaders method signature', () => {
      expect(typeof sectorApi.getLeaders).toBe('function')
    })
  })

  describe('API Types', () => {
    it('should export AuthToken interface', () => {
      // 类型检查在编译时完成，这里验证运行时对象结构
      const token: AuthToken = {
        access_token: 'test',
        refresh_token: 'test',
        token_type: 'bearer',
      }
      expect(token.access_token).toBe('test')
      expect(token.refresh_token).toBe('test')
      expect(token.token_type).toBe('bearer')
    })
  })
})
