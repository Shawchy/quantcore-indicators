import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-redux'
import { ChakraProvider } from '@chakra-ui/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as Sentry from '@sentry/react'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import { store } from './store'
import theme from './theme'

// 初始化 Sentry 错误监控
const sentryDsn = import.meta.env.VITE_SENTRY_DSN

// 仅在配置了有效 DSN 时启用 Sentry
if (sentryDsn && sentryDsn !== 'https://your-dsn-key@o0.ingest.sentry.io/0' && sentryDsn.startsWith('https://')) {
  Sentry.init({
    dsn: sentryDsn,
    environment: import.meta.env.MODE || 'development',
    enabled: import.meta.env.PROD, // 仅在生产环境启用
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    tracesSampleRate: 0.1,        // 10% 性能监控
    replaysSessionSampleRate: 0.1, // 10% 会话回放
    replaysOnErrorSampleRate: 1.0, // 100% 错误回放
    beforeSend(event, hint) {
      // 在发送前过滤某些错误
      if (event.exception?.values?.[0]?.value?.includes('Network request failed')) {
        return null // 忽略网络错误
      }
      return event
    },
  })
} else {
  // eslint-disable-next-line no-console
  console.warn('[Sentry] 未配置有效的 DSN，错误监控已禁用')
}

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

// 全局错误处理（Sentry 会自动捕获）
window.addEventListener('error', (event) => {
  // eslint-disable-next-line no-console
  console.error('Global error:', event.error)
  // Sentry 会自动捕获并上报
})

window.addEventListener('unhandledrejection', (event) => {
  // eslint-disable-next-line no-console
  console.error('Unhandled promise rejection:', event.reason)
  // Sentry 会自动捕获并上报
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
