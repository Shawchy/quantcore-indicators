import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { watchlistApi } from '../../services/api'
import { WatchlistItem, RealtimeQuote } from '../../types'

interface WatchlistState {
  items: WatchlistItem[]
  quotes: RealtimeQuote[]
  loading: boolean
  error: string | null
}

const initialState: WatchlistState = {
  items: [],
  quotes: [],
  loading: false,
  error: null,
}

export const fetchWatchlist = createAsyncThunk(
  'watchlist/fetchAll',
  async () => {
    const response = await watchlistApi.getList()
    return response.data
  }
)

export const fetchWatchlistQuotes = createAsyncThunk(
  'watchlist/fetchQuotes',
  async () => {
    const response = await watchlistApi.getQuotes()
    return response.data
  }
)

const watchlistSlice = createSlice({
  name: 'watchlist',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchWatchlist.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchWatchlist.fulfilled, (state, action) => {
        state.loading = false
        state.items = action.payload
      })
      .addCase(fetchWatchlist.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取自选股失败'
      })
      .addCase(fetchWatchlistQuotes.fulfilled, (state, action) => {
        state.quotes = action.payload
      })
  },
})

export default watchlistSlice.reducer
