import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Box, ColorModeScript } from '@chakra-ui/react'
import { useEffect } from 'react'
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
// 基金模块
import FundHome from './pages/fund'
import FundRanking from './pages/fund/Ranking'
import HotSectors from './pages/fund/HotSectors'
import FundRecommended from './pages/fund/Recommended'
import FundDetail from './pages/fund/detail/[code]'
// 基金数据管理
import { useFundDataManagement } from './hooks/useFundDataManagement'
import fundStorage from './services/fundStorage'
import theme from './theme'

function App() {
  // 初始化基金数据管理
  const { getStorageStats } = useFundDataManagement({
    enableCleanup: true,
    cleanupInterval: 60 * 60 * 1000, // 1 小时清理一次
    enableBackgroundUpdate: true,
    backgroundUpdateInterval: 5 * 60 * 1000, // 5 分钟更新一次
    watchlistCodes: fundStorage.getWatchlist(),
  });

  // 打印存储统计信息
  useEffect(() => {
    const printStats = async () => {
      const stats = await getStorageStats();
      console.log('[基金数据] 存储统计:', stats);
    };
    
    // 延迟打印统计信息
    const timer = setTimeout(printStats, 5000);
    
    return () => clearTimeout(timer);
  }, [getStorageStats]);

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
            {/* 基金模块路由 */}
            <Route path="fund" element={<FundHome />} />
            <Route path="fund/ranking" element={<FundRanking />} />
            <Route path="fund/hot-sectors" element={<HotSectors />} />
            <Route path="fund/recommended" element={<FundRecommended />} />
            <Route path="fund/detail/:code" element={<FundDetail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </Box>
  )
}

export default App
