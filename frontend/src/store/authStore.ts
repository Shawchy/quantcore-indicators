import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, type AuthToken, type ApiUser } from '../services/api'

interface AuthState {
  token: string | null
  refreshToken: string | null
  user: ApiUser | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  setAuth: (auth: AuthToken) => void
  setUser: (user: ApiUser) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  getCurrentUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setAuth: (auth) => set({
        token: auth.access_token,
        refreshToken: auth.refresh_token,
        isAuthenticated: true,
        error: null,
      }),

      setUser: (user) => set({ user }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      login: async (username, password) => {
        set({ isLoading: true, error: null })
        try {
          const auth = await authApi.login(username, password)
          set({
            token: auth.access_token,
            refreshToken: auth.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          const message = error instanceof Error ? error.message : '登录失败'
          set({ error: message, isLoading: false, isAuthenticated: false })
          throw error
        }
      },

      logout: async () => {
        try {
          await authApi.logout()
        } catch {
          // 静默处理登出 API 失败
        }
        set({
          token: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
          error: null,
        })
      },

      getCurrentUser: async () => {
        try {
          const user = await authApi.getCurrentUser()
          set({ user })
        } catch {
          // 静默处理
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    }
  )
)