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
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 分钟
      gcTime: 10 * 60 * 1000, // 10 分钟
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
