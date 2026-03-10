import { configureStore } from '@reduxjs/toolkit'
import stockReducer from './slices/stockSlice'
import watchlistReducer from './slices/watchlistSlice'
import sectorReducer from './slices/sectorSlice'
import strategyReducer from './slices/strategySlice'

export const store = configureStore({
  reducer: {
    stock: stockReducer,
    watchlist: watchlistReducer,
    sector: sectorReducer,
    strategy: strategyReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
