import { Component, ErrorInfo, ReactNode } from 'react'
import { Box, Button, Heading, Text, VStack } from '@chakra-ui/react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 生产环境可以发送到错误监控服务
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/'
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          minH="100vh"
          p={4}
        >
          <VStack gap={4} textAlign="center">
            <Heading size="lg" color="red.500">
              出错了
            </Heading>
            <Text color="gray.500">
              {this.state.error?.message || '发生了未知错误'}
            </Text>
            <Button colorPalette="brand" onClick={this.handleReset}>
              返回首页
            </Button>
          </VStack>
        </Box>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
