import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { authApi, type ApiUser, type AuthToken } from '../../services/api'

export type User = ApiUser

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

const getStoredToken = () => {
  if (typeof window === 'undefined') return null
  // 使用 sessionStorage 替代 localStorage，关闭浏览器后自动失效
  return sessionStorage.getItem('access_token')
}

const getStoredRefreshToken = () => {
  if (typeof window === 'undefined') return null
  return sessionStorage.getItem('refresh_token')
}

const initialState: AuthState = {
  user: null,
  token: getStoredToken(),
  refreshToken: getStoredRefreshToken(),
  isAuthenticated: !!getStoredToken(),
  isLoading: false,
  error: null,
}

export const login = createAsyncThunk<
  AuthToken,
  { username: string; password: string },
  { rejectValue: string }
>(
  'auth/login',
  async ({ username, password }, { rejectWithValue }) => {
    try {
      const response = await authApi.login(username, password)
      sessionStorage.setItem('access_token', response.access_token)
      sessionStorage.setItem('refresh_token', response.refresh_token)
      return response
    } catch (error: unknown) {
      return rejectWithValue(
        error instanceof Error ? error.message : '登录失败'
      )
    }
  }
)

export const getCurrentUser = createAsyncThunk<
  ApiUser,
  void,
  { rejectValue: string }
>(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      return await authApi.getCurrentUser()
    } catch (error: unknown) {
      return rejectWithValue(
        error instanceof Error ? error.message : '获取用户信息失败'
      )
    }
  }
)

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue: _rejectWithValue }) => {
    try {
      await authApi.logout()
    } catch (error: unknown) {
      // 即使登出接口失败，也要清除本地 token
      // eslint-disable-next-line no-console
      console.error('登出接口调用失败:', error)
    }
  }
)

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    localLogout: (state) => {
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
    },
    setToken: (state, action: PayloadAction<{ access_token: string; refresh_token: string }>) => {
      state.token = action.payload.access_token
      state.refreshToken = action.payload.refresh_token
      state.isAuthenticated = true
      sessionStorage.setItem('access_token', action.payload.access_token)
      sessionStorage.setItem('refresh_token', action.payload.refresh_token)
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false
        state.token = action.payload.access_token
        state.refreshToken = action.payload.refresh_token
        state.isAuthenticated = true
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string || '登录失败'
      })
      // Get Current User
      .addCase(getCurrentUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false
        state.user = action.payload
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string || '获取用户信息失败'
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
      })
  },
})

export const { clearError, localLogout, setToken } = authSlice.actions
export default authSlice.reducer
