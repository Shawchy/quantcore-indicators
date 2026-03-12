import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { strategyApi } from '../../services/api'
import { Strategy } from '../../types'

interface StrategyState {
  strategies: Strategy[]
  currentStrategy: Strategy | null
  loading: boolean
  error: string | null
}

const initialState: StrategyState = {
  strategies: [],
  currentStrategy: null,
  loading: false,
  error: null,
}

export const fetchStrategies = createAsyncThunk(
  'strategy/fetchAll',
  async () => {
    const response = await strategyApi.getList()
    return response.data
  }
)

export const fetchStrategy = createAsyncThunk(
  'strategy/fetchOne',
  async (strategyId: string) => {
    const response = await strategyApi.get(strategyId)
    return response.data
  }
)

const strategySlice = createSlice({
  name: 'strategy',
  initialState,
  reducers: {
    clearCurrentStrategy: (state) => {
      state.currentStrategy = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStrategies.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchStrategies.fulfilled, (state, action) => {
        state.loading = false
        state.strategies = action.payload
      })
      .addCase(fetchStrategies.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取策略列表失败'
      })
      .addCase(fetchStrategy.fulfilled, (state, action) => {
        state.currentStrategy = action.payload
      })
  },
})

export const { clearCurrentStrategy } = strategySlice.actions
export default strategySlice.reducer
