import { describe, it, expect, beforeEach } from 'vitest'
import authReducer, {
  login,
  logout,
  clearError,
  localLogout,
  setToken
} from '../authSlice'
import type { AuthState } from '../authSlice'

const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
}

describe('authSlice', () => {
  beforeEach(() => {
    // 清除 sessionStorage
    sessionStorage.clear()
  })

  describe('reducers', () => {
    it('should handle clearError', () => {
      const stateWithError = { ...initialState, error: 'Some error' }
      const state = authReducer(stateWithError, clearError())
      expect(state.error).toBeNull()
    })

    it('should handle localLogout', () => {
      const authenticatedState: AuthState = {
        ...initialState,
        user: { user_id: 1, username: 'test', role: 'user' },
        token: 'test-token',
        refreshToken: 'test-refresh',
        isAuthenticated: true,
      }
      const state = authReducer(authenticatedState, localLogout())
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.refreshToken).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })

    it('should handle setToken', () => {
      const state = authReducer(
        initialState,
        setToken({ access_token: 'new-token', refresh_token: 'new-refresh' })
      )
      expect(state.token).toBe('new-token')
      expect(state.refreshToken).toBe('new-refresh')
      expect(state.isAuthenticated).toBe(true)
    })
  })

  describe('extraReducers - login', () => {
    it('should set loading state when login is pending', () => {
      const state = authReducer(
        initialState,
        login.pending('', { username: 'test', password: 'test' })
      )
      expect(state.isLoading).toBe(true)
      expect(state.error).toBeNull()
    })

    it('should set auth state when login is fulfilled', () => {
      const payload = {
        access_token: 'test-token',
        refresh_token: 'test-refresh',
        token_type: 'bearer',
      }
      const state = authReducer(
        { ...initialState, isLoading: true },
        login.fulfilled(payload, '', { username: 'test', password: 'test' })
      )
      expect(state.isLoading).toBe(false)
      expect(state.token).toBe('test-token')
      expect(state.refreshToken).toBe('test-refresh')
      expect(state.isAuthenticated).toBe(true)
    })

    it('should set error state when login is rejected', () => {
      const error = 'Invalid credentials'
      const state = authReducer(
        { ...initialState, isLoading: true },
        login.rejected(new Error(error), '', { username: 'test', password: 'test' }, error)
      )
      expect(state.isLoading).toBe(false)
      expect(state.error).toBe(error)
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('extraReducers - logout', () => {
    it('should clear auth state when logout is fulfilled', () => {
      const authenticatedState: AuthState = {
        ...initialState,
        user: { user_id: 1, username: 'test', role: 'user' },
        token: 'test-token',
        refreshToken: 'test-refresh',
        isAuthenticated: true,
      }
      const state = authReducer(authenticatedState, logout.fulfilled(undefined, ''))
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.refreshToken).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })
})
