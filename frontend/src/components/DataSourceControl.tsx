import { useState, useEffect } from 'react'
import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Button,
  Badge,
  SimpleGrid,
  Switch,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast,
  Divider,
  Box,
  Flex,
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dataSourceApi } from '../services/api'
import { FiDatabase, FiWifi, FiWifiOff, FiRefreshCw } from 'react-icons/fi'

interface DataSourceStatus {
  mode: 'online' | 'offline' | 'mock'
  disabled_sources: string[]
  mock_data_enabled: boolean
  available_modes: string[]
}

const DataSourceControl: React.FC = () => {
  const toast = useToast()
  const queryClient = useQueryClient()

  const { data: status, isLoading, refetch } = useQuery<DataSourceStatus>({
    queryKey: ['dataSourceStatus'],
    queryFn: () => dataSourceApi.getStatus().then(res => res.data),
    refetchInterval: 30000,
  })

  const setModeMutation = useMutation({
    mutationFn: (mode: 'online' | 'offline' | 'mock') =>
      dataSourceApi.setMode(mode),
    onSuccess: () => {
      queryClient.invalidateQueries(['dataSourceStatus'])
      toast({
        title: '数据源模式已切换',
        status: 'success',
        duration: 2000,
      })
    },
    onError: (error: any) => {
      toast({
        title: '切换失败',
        description: error.message || '请稍后重试',
        status: 'error',
        duration: 3000,
      })
    },
  })

  const toggleSourceMutation = useMutation({
    mutationFn: ({ source, enabled }: { source: string; enabled: boolean }) =>
      dataSourceApi.toggleSource(source, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries(['dataSourceStatus'])
      toast({
        title: '数据源状态已更新',
        status: 'success',
        duration: 2000,
      })
    },
    onError: (error: any) => {
      toast({
        title: '更新失败',
        description: error.message || '请稍后重试',
        status: 'error',
        duration: 3000,
      })
    },
  })

  const resetMutation = useMutation({
    mutationFn: () => dataSourceApi.reset(),
    onSuccess: () => {
      queryClient.invalidateQueries(['dataSourceStatus'])
      toast({
        title: '数据源已重置',
        status: 'success',
        duration: 2000,
      })
    },
    onError: (error: any) => {
      toast({
        title: '重置失败',
        description: error.message || '请稍后重试',
        status: 'error',
        duration: 3000,
      })
    },
  })

  const getModeBadge = (mode: string) => {
    switch (mode) {
      case 'online':
        return <Badge colorScheme="green">在线模式</Badge>
      case 'offline':
        return <Badge colorScheme="orange">离线模式</Badge>
      case 'mock':
        return <Badge colorScheme="blue">模拟数据</Badge>
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
      case 'mock':
        return '使用模拟测试数据进行开发调试'
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
      <Card>
        <CardBody>
          <Flex justify="center" align="center" h="200px">
            <Spinner size="lg" color="brand.500" />
          </Flex>
        </CardBody>
      </Card>
    )
  }

  return (
    <VStack spacing={4} align="stretch">
      <Card>
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="sm">数据源状态</Heading>
            <Button
              size="sm"
              leftIcon={<FiRefreshCw />}
              onClick={() => refetch()}
              isLoading={isLoading}
            >
              刷新
            </Button>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between" align="center">
              <Text fontWeight="medium">当前模式</Text>
              {status && getModeBadge(status.mode)}
            </HStack>
            
            <Text fontSize="sm" color="light.textSecondary">
              {status && getModeDescription(status.mode)}
            </Text>

            {status?.mode === 'offline' && (
              <Alert status="warning" borderRadius="md">
                <AlertIcon />
                <Box>
                  <AlertTitle fontSize="sm">离线模式</AlertTitle>
                  <AlertDescription fontSize="xs">
                    当前已禁用所有外部数据源，仅使用本地数据库中的数据。
                    如需获取最新数据，请切换到在线模式。
                  </AlertDescription>
                </Box>
              </Alert>
            )}

            {status?.mode === 'mock' && (
              <Alert status="info" borderRadius="md">
                <AlertIcon />
                <Box>
                  <AlertTitle fontSize="sm">模拟数据模式</AlertTitle>
                  <AlertDescription fontSize="xs">
                    当前使用模拟测试数据，仅用于开发调试。
                    生产环境请切换到在线模式。
                  </AlertDescription>
                </Box>
              </Alert>
            )}
          </VStack>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <Heading size="sm">切换模式</Heading>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={3}>
            <Button
              colorScheme="green"
              variant={status?.mode === 'online' ? 'solid' : 'outline'}
              onClick={() => setModeMutation.mutate('online')}
              isLoading={setModeMutation.isPending}
              leftIcon={<FiWifi />}
            >
              在线模式
            </Button>
            <Button
              colorScheme="orange"
              variant={status?.mode === 'offline' ? 'solid' : 'outline'}
              onClick={() => setModeMutation.mutate('offline')}
              isLoading={setModeMutation.isPending}
              leftIcon={<FiWifiOff />}
            >
              离线模式
            </Button>
            <Button
              colorScheme="blue"
              variant={status?.mode === 'mock' ? 'solid' : 'outline'}
              onClick={() => setModeMutation.mutate('mock')}
              isLoading={setModeMutation.isPending}
              leftIcon={<FiDatabase />}
            >
              模拟数据
            </Button>
          </SimpleGrid>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <Heading size="sm">数据源开关</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={3} align="stretch">
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
                  <VStack align="start" spacing={1}>
                    <Text fontWeight="medium">{source.name}</Text>
                    <Text fontSize="xs" color="light.textSecondary">
                      {source.description}
                    </Text>
                  </VStack>
                  <Switch
                    isChecked={!isDisabled}
                    onChange={(e) =>
                      toggleSourceMutation.mutate({
                        source: source.id,
                        enabled: e.target.checked,
                      })
                    }
                    isDisabled={toggleSourceMutation.isPending}
                  />
                </HStack>
              )
            })}
          </VStack>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <Button
            width="full"
            variant="outline"
            onClick={() => resetMutation.mutate()}
            isLoading={resetMutation.isPending}
          >
            重置为默认设置
          </Button>
        </CardBody>
      </Card>
    </VStack>
  )
}

export default DataSourceControl
