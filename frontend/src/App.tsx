import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Box } from '@chakra-ui/react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import StockDetail from './pages/StockDetail'
import Watchlist from './pages/Watchlist'
import SectorAnalysis from './pages/SectorAnalysis'
import ChipSelection from './pages/ChipSelection'
import Screener from './pages/Screener'
import Strategy from './pages/Strategy'
import Backtest from './pages/Backtest'

function App() {
  return (
    <BrowserRouter>
      <Box minH="100vh" bg="gray.50">
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="stock/:code" element={<StockDetail />} />
            <Route path="watchlist" element={<Watchlist />} />
            <Route path="sector" element={<SectorAnalysis />} />
            <Route path="chip" element={<ChipSelection />} />
            <Route path="screener" element={<Screener />} />
            <Route path="strategy" element={<Strategy />} />
            <Route path="backtest" element={<Backtest />} />
          </Route>
        </Routes>
      </Box>
    </BrowserRouter>
  )
}

export default App
