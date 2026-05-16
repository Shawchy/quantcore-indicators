import { Alert, Badge, Box, Button, Card, Flex, HStack, Heading, SimpleGrid, Spinner, Switch, Text, VStack } from '@chakra-ui/react'
import { toaster } from './ui/toaster'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dataSourceApi } from '../services/api'
import { FiWifi, FiWifiOff, FiRefreshCw } from 'react-icons/fi'

interface DataSourceStatus {
  mode: 'online' | 'offline'
  disabled_sources: string[]
  available_modes: string[]
}

const DataSourceControl: React.FC = () => {
  
  const queryClient = useQueryClient()

  const { data: status, isLoading, refetch, error } = useQuery<DataSourceStatus>({
    queryKey: ['dataSourceStatus'],
    queryFn: () => dataSourceApi.getStatus() as unknown as Promise<DataSourceStatus>,
    refetchInterval: 30000,
    staleTime: 5 * 60 * 1000, // 5 分钟
    retry: 2,
    retryDelay: 1000,
  })

  const setModeMutation = useMutation({
    mutationFn: (mode: 'online' | 'offline') =>
      dataSourceApi.setMode(mode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSourceStatus'] })
      toaster.create({
        title: '数据源模式已切换',
        type: 'success',
        duration: 2000,
      })
    },
    onError: (error: Error) => {
      toaster.create({
        title: '切换失败',
        description: error.message || '请稍后重试',
        type: 'error',
        duration: 3000,
      })
    },
  })

  const toggleSourceMutation = useMutation({
    mutationFn: ({ source, enabled }: { source: string; enabled: boolean }) =>
      dataSourceApi.toggleSource(source, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSourceStatus'] })
      toaster.create({
        title: '数据源状态已更新',
        type: 'success',
        duration: 2000,
      })
    },
    onError: (error: Error) => {
      toaster.create({
        title: '更新失败',
        description: error.message || '请稍后重试',
        type: 'error',
        duration: 3000,
      })
    },
  })

  const resetMutation = useMutation({
    mutationFn: () => dataSourceApi.reset(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSourceStatus'] })
      toaster.create({
        title: '数据源已重置',
        type: 'success',
        duration: 2000,
      })
    },
    onError: (error: Error) => {
      toaster.create({
        title: '重置失败',
        description: error.message || '请稍后重试',
        type: 'error',
        duration: 3000,
      })
    },
  })

  const getModeBadge = (mode: string) => {
    switch (mode) {
      case 'online':
        return <Badge colorPalette="green">在线模式</Badge>
      case 'offline':
        return <Badge colorPalette="orange">离线模式</Badge>
      default:
        return <Badge>未知</Badge>
    }
  }

  const getModeDescription = (mode: string) => {
    switch (mode) {
      case 'online':
        return '正常从外部数据源拉取数据'
      case 'offline':
        return '禁用所有外部数据源，只使用本地缓存/数据库'
      default:
        return ''
    }
  }

  const dataSources = [
    { name: 'Tushare', id: 'tushare', description: 'Tushare 数据源' },
    { name: 'AkShare', id: 'akshare', description: 'AkShare 数据源' },
    { name: 'Baostock', id: 'baostock', description: 'Baostock 数据源' },
    { name: 'YFinance', id: 'yfinance', description: 'YFinance 数据源' },
  ]

  if (isLoading) {
    return (
      <Card.Root>
        <Card.Body>
          <Flex justify="center" align="center" h="200px">
            <Spinner size="lg" color="brand.500" />
          </Flex>
        </Card.Body>
      </Card.Root>
    )
  }

  if (error) {
    return (
      <Card.Root>
        <Card.Body>
          <Alert.Root status="error" borderRadius="md">
            <Alert.Indicator />
            <Box>
              <Alert.Title>加载失败</Alert.Title>
              <Alert.Description>
                无法获取数据源状态，请检查网络连接或刷新页面重试。
              </Alert.Description>
            </Box>
          </Alert.Root>
          <Button
            mt={4}
            width="full"
            onClick={() => refetch()}
          >
            重试
          <FiRefreshCw /> 
          </Button>
        </Card.Body>
      </Card.Root>
    )
  }

  return (
    <VStack gap={4} align="stretch">
      <Card.Root>
        <Card.Header>
          <HStack justify="space-between">
            <Heading size="sm">数据源状态</Heading>
            <Button
              size="sm"
              onClick={() => refetch()}
              loading={isLoading}
            >
              刷新
            </Button>
          </HStack>
        </Card.Header>
        <Card.Body>
          <VStack gap={4} align="stretch">
            <HStack justify="space-between" align="center">
              <Text fontWeight="medium">当前模式</Text>
              {status && getModeBadge(status.mode)}
            </HStack>
            
            <Text fontSize="sm" color="light.textSecondary">
              {status && getModeDescription(status.mode)}
            </Text>

            {status?.mode === 'offline' && (
              <Alert.Root status="warning" borderRadius="md">
                <Alert.Indicator />
                <Box>
                  <Alert.Title fontSize="sm">离线模式</Alert.Title>
                  <Alert.Description fontSize="xs">
                    当前已禁用所有外部数据源，仅使用本地数据库中的数据。
                    如需获取最新数据，请切换到在线模式。
                  </Alert.Description>
                </Box>
              </Alert.Root>
            )}
          </VStack>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Heading size="sm">切换模式</Heading>
        </Card.Header>
        <Card.Body>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
            <Button
              colorPalette="green"
              variant={status?.mode === 'online' ? 'solid' : 'outline'}
              onClick={() => setModeMutation.mutate('online')}
              loading={setModeMutation.isPending}
            >
              在线模式
            <FiWifi /> 
            </Button>
            <Button
              colorPalette="orange"
              variant={status?.mode === 'offline' ? 'solid' : 'outline'}
              onClick={() => setModeMutation.mutate('offline')}
              loading={setModeMutation.isPending}
            >
              离线模式
            <FiWifiOff /> 
            </Button>
          </SimpleGrid>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Heading size="sm">数据源开关</Heading>
        </Card.Header>
        <Card.Body>
          <VStack gap={3} align="stretch">
            {dataSources.map((source) => {
              const isDisabled = status?.disabled_sources?.includes(source.id)
              return (
                <HStack
                  key={source.id}
                  justify="space-between"
                  align="center"
                  p={3}
                  bg="light.bgSecondary"
                  borderRadius="md"
                >
                  <VStack align="start" gap={1}>
                    <Text fontWeight="medium">{source.name}</Text>
                    <Text fontSize="xs" color="light.textSecondary">
                      {source.description}
                    </Text>
                  </VStack>
                  <Switch.Root
                    checked={!isDisabled}
                    onCheckedChange={(e) =>
                      toggleSourceMutation.mutate({
                        source: source.id,
                        enabled: e.checked,
                      })
                    }
                    disabled={toggleSourceMutation.isPending}
                  >
                    <Switch.Control>
                      <Switch.Thumb />
                    </Switch.Control>
                  </Switch.Root>
                </HStack>
              )
            })}
          </VStack>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Body>
          <Button
            width="full"
            variant="outline"
            onClick={() => resetMutation.mutate()}
            loading={resetMutation.isPending}
          >
            重置为默认设置
          </Button>
        </Card.Body>
      </Card.Root>
    </VStack>
  )
}

export default DataSourceControl
