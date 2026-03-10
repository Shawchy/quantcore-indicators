import { configureStore } from '@reduxjs/toolkit'
import appReducer from './slices/appSlice'
import authReducer from './slices/authSlice'
import stockReducer from './slices/stockSlice'
import watchlistReducer from './slices/watchlistSlice'
import sectorReducer from './slices/sectorSlice'
import strategyReducer from './slices/strategySlice'

export const store = configureStore({
  reducer: {
    app: appReducer,
    auth: authReducer,
    stock: stockReducer,
    watchlist: watchlistReducer,
    sector: sectorReducer,
    strategy: strategyReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
