import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { stockApi } from '../../services/api'
import { StockBasic, KLineData, TechnicalIndicator, RealtimeQuote } from '../../types'

interface StockState {
  currentStock: StockBasic | null
  klineData: KLineData[]
  indicators: TechnicalIndicator[]
  realtimeQuote: RealtimeQuote | null
  searchResults: StockBasic[]
  loading: boolean
  error: string | null
}

const initialState: StockState = {
  currentStock: null,
  klineData: [],
  indicators: [],
  realtimeQuote: null,
  searchResults: [],
  loading: false,
  error: null,
}

export const fetchStockBasic = createAsyncThunk(
  'stock/fetchBasic',
  async (code: string) => {
    const response = await stockApi.getBasic(code)
    return response.data
  }
)

export const fetchKline = createAsyncThunk(
  'stock/fetchKline',
  async ({ code, startDate, endDate, adjust }: { code: string; startDate?: string; endDate?: string; adjust?: string }) => {
    const response = await stockApi.getKline(code, startDate, endDate, adjust)
    return response.data
  }
)

export const fetchIndicators = createAsyncThunk(
  'stock/fetchIndicators',
  async ({ code, startDate, endDate }: { code: string; startDate?: string; endDate?: string }) => {
    const response = await stockApi.getIndicators(code, startDate, endDate)
    return response.data
  }
)

export const fetchRealtimeQuote = createAsyncThunk(
  'stock/fetchRealtime',
  async (code: string) => {
    const response = await stockApi.getRealtime(code)
    return response.data
  }
)

export const searchStocks = createAsyncThunk(
  'stock/search',
  async (keyword: string) => {
    const response = await stockApi.search(keyword)
    return response.data
  }
)

const stockSlice = createSlice({
  name: 'stock',
  initialState,
  reducers: {
    clearCurrentStock: (state) => {
      state.currentStock = null
      state.klineData = []
      state.indicators = []
      state.realtimeQuote = null
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStockBasic.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchStockBasic.fulfilled, (state, action) => {
        state.loading = false
        state.currentStock = action.payload
      })
      .addCase(fetchStockBasic.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取股票信息失败'
      })
      .addCase(fetchKline.fulfilled, (state, action) => {
        state.klineData = action.payload
      })
      .addCase(fetchIndicators.fulfilled, (state, action) => {
        state.indicators = action.payload
      })
      .addCase(fetchRealtimeQuote.fulfilled, (state, action) => {
        state.realtimeQuote = action.payload
      })
      .addCase(searchStocks.fulfilled, (state, action) => {
        state.searchResults = action.payload
      })
  },
})

export const { clearCurrentStock, clearError } = stockSlice.actions
export default stockSlice.reducer
