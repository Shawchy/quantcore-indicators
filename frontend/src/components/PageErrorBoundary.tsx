import { Component, ErrorInfo, ReactNode } from 'react'
import { Box, Button, Text, VStack, Icon } from '@chakra-ui/react'
import { FiAlertTriangle } from 'react-icons/fi'

interface Props {
  children: ReactNode
  name?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class PageErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`[PageErrorBoundary] ${this.props.name || 'Page'} error:`, error, errorInfo)
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError) {
      return (
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          minH="400px"
          p={8}
        >
          <VStack spacing={4} textAlign="center">
            <Icon as={FiAlertTriangle} boxSize={10} color="orange.500" />
            <Text fontSize="lg" fontWeight="bold" color="gray.700">
              {this.props.name || '页面'}加载失败
            </Text>
            <Text color="gray.500" fontSize="sm">
              {this.state.error?.message || '发生了未知错误'}
            </Text>
            <Button colorScheme="brand" size="sm" onClick={this.handleRetry}>
              重试
            </Button>
          </VStack>
        </Box>
      )
    }

    return this.props.children
  }
}
