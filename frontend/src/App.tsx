﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Box, ColorModeScript, Spinner, Flex } from '@chakra-ui/react'
import { Suspense, lazy } from 'react'
import Layout from './components/Layout'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import { PageErrorBoundary } from './components/PageErrorBoundary'
// 基金数据管理
import { FundDataManager } from './hooks/useFundDataManagement'
import fundStorage from './services/fundStorage'
import theme from './theme'

// 懒加载页面组件
const Dashboard = lazy(() => import('./pages/Dashboard'))
const StockDetail = lazy(() => import('./pages/StockDetail'))
const Watchlist = lazy(() => import('./pages/Watchlist'))
const SectorAnalysis = lazy(() => import('./pages/SectorAnalysis'))
const ChipSelection = lazy(() => import('./pages/ChipSelection'))
const Screener = lazy(() => import('./pages/Screener'))
const Strategy = lazy(() => import('./pages/Strategy'))
const Backtest = lazy(() => import('./pages/Backtest'))
const MarketRanking = lazy(() => import('./pages/MarketRanking'))
const DailyMarket = lazy(() => import('./pages/DailyMarket'))
const Settings = lazy(() => import('./pages/Settings'))
const Billboard = lazy(() => import('./pages/Billboard'))

// 东方财富模块 - 懒加载
const EastMoneyChangesPage = lazy(() => import('./pages/EastMoneyChangesPage'))
const EastMoneyZtBoardPage = lazy(() => import('./pages/EastMoneyZtBoardPage'))
const EastMoneyStockCommentPage = lazy(() => import('./pages/EastMoneyStockCommentPage'))
const EastMoneyResearchNoticePage = lazy(() => import('./pages/EastMoneyResearchNoticePage'))
const EastMoneyFinancialPage = lazy(() => import('./pages/EastMoneyFinancialPage'))
const SinaFinancialIndicatorPage = lazy(() => import('./pages/SinaFinancialIndicatorPage'))
const StockListPage = lazy(() => import('./pages/StockListPage'))
const IndustryClassificationPage = lazy(() => import('./pages/IndustryClassificationPage'))
const StockHolderPage = lazy(() => import('./pages/StockHolderPage'))
const StockPriceTargetPage = lazy(() => import('./pages/StockPriceTargetPage'))
const LeguleGuMarketIndicatorsPage = lazy(() => import('./pages/LeguleGuMarketIndicatorsPage'))
const AShareValuationPage = lazy(() => import('./pages/AShareValuationPage'))
const MarketStatisticsPage = lazy(() => import('./pages/MarketStatisticsPage'))
const BlockTradePage = lazy(() => import('./pages/BlockTradePage'))
const MarginTradingPage = lazy(() => import('./pages/MarginTradingPage'))

// 基金模块 - 懒加载
const FundHome = lazy(() => import('./pages/fund'))
const FundRanking = lazy(() => import('./pages/fund/Ranking'))
const HotSectors = lazy(() => import('./pages/fund/HotSectors'))
const FundRecommended = lazy(() => import('./pages/fund/Recommended'))
const FundDetail = lazy(() => import('./pages/fund/detail/[code]'))

// Loading 组件
const PageLoading = () => (
  <Flex justify="center" align="center" h="100vh" w="100%">
    <Spinner size="xl" color="brand.500" thickness="4px" />
  </Flex>
)

function App() {
  // 获取自选基金列表
  const watchlistCodes = fundStorage.getWatchlist();

  return (
    <Box>
      {/* 基金数据管理组件 - 自动检测路由并启用/禁用后台更新 */}
      <FundDataManager
        options={{
          enableCleanup: true,
          cleanupInterval: 60 * 60 * 1000, // 1 小时清理一次
          enableBackgroundUpdate: true,
          backgroundUpdateInterval: 5 * 60 * 1000, // 5 分钟更新一次
          watchlistCodes: watchlistCodes,
        }}
      />
      
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
            <Route index element={
              <Suspense fallback={<PageLoading />}>
                <PageErrorBoundary name="仪表盘">
                  <Dashboard />
                </PageErrorBoundary>
              </Suspense>
            } />
            <Route path="stock/:code" element={
              <Suspense fallback={<PageLoading />}>
                <PageErrorBoundary name="股票详情">
                  <StockDetail />
                </PageErrorBoundary>
              </Suspense>
            } />
            <Route path="watchlist" element={
              <Suspense fallback={<PageLoading />}>
                <PageErrorBoundary name="自选股">
                  <Watchlist />
                </PageErrorBoundary>
              </Suspense>
            } />
            <Route path="sector" element={
              <Suspense fallback={<PageLoading />}>
                <SectorAnalysis />
              </Suspense>
            } />
            <Route path="chip" element={
              <Suspense fallback={<PageLoading />}>
                <ChipSelection />
              </Suspense>
            } />
            <Route path="screener" element={
              <Suspense fallback={<PageLoading />}>
                <Screener />
              </Suspense>
            } />
            <Route path="strategy" element={
              <Suspense fallback={<PageLoading />}>
                <Strategy />
              </Suspense>
            } />
            <Route path="backtest" element={
              <Suspense fallback={<PageLoading />}>
                <PageErrorBoundary name="回测">
                  <Backtest />
                </PageErrorBoundary>
              </Suspense>
            } />
            <Route path="market" element={
              <Suspense fallback={<PageLoading />}>
                <MarketRanking />
              </Suspense>
            } />
            <Route path="daily" element={
              <Suspense fallback={<PageLoading />}>
                <DailyMarket />
              </Suspense>
            } />
            <Route path="billboard" element={
              <Suspense fallback={<PageLoading />}>
                <Billboard />
              </Suspense>
            } />
            <Route path="settings" element={
              <Suspense fallback={<PageLoading />}>
                <Settings />
              </Suspense>
            } />
            {/* 东方财富模块路由（使用 AkShare 数据源） */}
            <Route path="akshare/changes" element={
              <Suspense fallback={<PageLoading />}>
                <EastMoneyChangesPage />
              </Suspense>
            } />
            <Route path="akshare/zt-board" element={
              <Suspense fallback={<PageLoading />}>
                <EastMoneyZtBoardPage />
              </Suspense>
            } />
            <Route path="akshare/stock-comment" element={
              <Suspense fallback={<PageLoading />}>
                <EastMoneyStockCommentPage />
              </Suspense>
            } />
            <Route path="akshare/research-notice" element={
              <Suspense fallback={<PageLoading />}>
                <EastMoneyResearchNoticePage />
              </Suspense>
            } />
            <Route path="akshare/financial" element={
              <Suspense fallback={<PageLoading />}>
                <EastMoneyFinancialPage />
              </Suspense>
            } />
            <Route path="akshare/sina-financial-indicator" element={
              <Suspense fallback={<PageLoading />}>
                <SinaFinancialIndicatorPage />
              </Suspense>
            } />
            <Route path="akshare/stock-list" element={
              <Suspense fallback={<PageLoading />}>
                <StockListPage />
              </Suspense>
            } />
            <Route path="akshare/industry-classification" element={
              <Suspense fallback={<PageLoading />}>
                <IndustryClassificationPage />
              </Suspense>
            } />
            <Route path="akshare/stock-holder" element={
              <Suspense fallback={<PageLoading />}>
                <StockHolderPage />
              </Suspense>
            } />
            <Route path="akshare/stock-price-target" element={
              <Suspense fallback={<PageLoading />}>
                <StockPriceTargetPage />
              </Suspense>
            } />
            <Route path="akshare/legulegu-market-indicators" element={
              <Suspense fallback={<PageLoading />}>
                <LeguleGuMarketIndicatorsPage />
              </Suspense>
            } />
            <Route path="akshare/a-share-valuation" element={
              <Suspense fallback={<PageLoading />}>
                <AShareValuationPage />
              </Suspense>
            } />
            <Route path="akshare/market-statistics" element={
              <Suspense fallback={<PageLoading />}>
                <MarketStatisticsPage />
              </Suspense>
            } />
            <Route path="akshare/block-trade" element={
              <Suspense fallback={<PageLoading />}>
                <BlockTradePage />
              </Suspense>
            } />
            <Route path="akshare/margin-trading" element={
              <Suspense fallback={<PageLoading />}>
                <MarginTradingPage />
              </Suspense>
            } />
            {/* 基金模块路由 */}
            <Route path="fund" element={
              <Suspense fallback={<PageLoading />}>
                <FundHome />
              </Suspense>
            } />
            <Route path="fund/ranking" element={
              <Suspense fallback={<PageLoading />}>
                <FundRanking />
              </Suspense>
            } />
            <Route path="fund/hot-sectors" element={
              <Suspense fallback={<PageLoading />}>
                <HotSectors />
              </Suspense>
            } />
            <Route path="fund/recommended" element={
              <Suspense fallback={<PageLoading />}>
                <FundRecommended />
              </Suspense>
            } />
            <Route path="fund/detail/:code" element={
              <Suspense fallback={<PageLoading />}>
                <PageErrorBoundary name="基金详情">
                  <FundDetail />
                </PageErrorBoundary>
              </Suspense>
            } />
          </Route>
        </Routes>
      </BrowserRouter>
    </Box>
  )
}

export default App
