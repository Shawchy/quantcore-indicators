import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Box, ColorModeScript } from '@chakra-ui/react'
import Layout from './components/Layout'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import StockDetail from './pages/StockDetail'
import Watchlist from './pages/Watchlist'
import SectorAnalysis from './pages/SectorAnalysis'
import ChipSelection from './pages/ChipSelection'
import Screener from './pages/Screener'
import Strategy from './pages/Strategy'
import Backtest from './pages/Backtest'
import MarketRanking from './pages/MarketRanking'
import DailyMarket from './pages/DailyMarket'
import Settings from './pages/Settings'
import Billboard from './pages/Billboard'
import MarketQuotes from './pages/MarketQuotes'
import theme from './theme'

function App() {
  return (
    <Box>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <BrowserRouter>
        <Routes>
          {/* 公开路由 */}
          <Route path="/login" element={<Login />} />
          
          {/* 受保护的路由 */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="stock/:code" element={<StockDetail />} />
            <Route path="watchlist" element={<Watchlist />} />
            <Route path="sector" element={<SectorAnalysis />} />
            <Route path="chip" element={<ChipSelection />} />
            <Route path="screener" element={<Screener />} />
            <Route path="strategy" element={<Strategy />} />
            <Route path="backtest" element={<Backtest />} />
            <Route path="market" element={<MarketRanking />} />
            <Route path="daily" element={<DailyMarket />} />
            <Route path="billboard" element={<Billboard />} />
            <Route path="market-quotes" element={<MarketQuotes />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </Box>
  )
}

export default App
