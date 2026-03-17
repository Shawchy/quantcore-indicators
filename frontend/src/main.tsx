import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-redux'
import { ChakraProvider } from '@chakra-ui/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import { store } from './store'
import theme from './theme'

// 将 store 挂载到 window 对象，避免循环依赖
declare global {
  interface Window {
    __store__: typeof store
  }
}
window.__store__ = store

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // 窗口聚焦时不自动刷新
      retry: 2, // 失败重试 2 次
      staleTime: 30 * 1000, // 30 秒内使用缓存（优化后）
      gcTime: 2 * 60 * 1000, // 缓存 2 分钟（优化后）
      timeout: 15000, // 15 秒超时
    },
  },
})

// 全局错误处理
window.addEventListener('error', (event) => {
  // 生产环境可以发送到错误监控服务
  // eslint-disable-next-line no-console
  console.error('Global error:', event.error)
})

window.addEventListener('unhandledrejection', (event) => {
  // 生产环境可以发送到错误监控服务
  // eslint-disable-next-line no-console
  console.error('Unhandled promise rejection:', event.reason)
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ChakraProvider theme={theme}>
          <ErrorBoundary>
            <App />
          </ErrorBoundary>
        </ChakraProvider>
      </QueryClientProvider>
    </Provider>
  </React.StrictMode>,
)
