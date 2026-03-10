import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { authApi } from '../../services/api'

interface User {
  user_id: number
  username: string
  email?: string
  role: string
  is_active?: boolean
}

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
  return localStorage.getItem('access_token')
}

const getStoredRefreshToken = () => {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('refresh_token')
}

const initialState: AuthState = {
  user: null,
  token: getStoredToken(),
  refreshToken: getStoredRefreshToken(),
  isAuthenticated: !!getStoredToken(),
  isLoading: false,
  error: null,
}

export const login = createAsyncThunk(
  'auth/login',
  async ({ username, password }: { username: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await authApi.login(username, password)
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || '登录失败')
    }
  }
)

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authApi.getCurrentUser()
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || '获取用户信息失败')
    }
  }
)

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authApi.logout()
    } catch (error: any) {
      // 即使登出接口失败，也要清除本地 token
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
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
    },
    setToken: (state, action: PayloadAction<{ access_token: string; refresh_token: string }>) => {
      state.token = action.payload.access_token
      state.refreshToken = action.payload.refresh_token
      state.isAuthenticated = true
      localStorage.setItem('access_token', action.payload.access_token)
      localStorage.setItem('refresh_token', action.payload.refresh_token)
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
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
      })
  },
})

export const { clearError, localLogout, setToken } = authSlice.actions
export default authSlice.reducer
