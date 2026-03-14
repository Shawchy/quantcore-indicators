import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Progress,
  Badge,
  IconButton,
  Tooltip,
  Flex,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  Divider,
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { loadingProgressApi } from '../services/api'
import { FiRefreshCw, FiTrash2, FiCheckCircle, FiXCircle, FiClock, FiDatabase } from 'react-icons/fi'
import { useState } from 'react'

interface LoadingTask {
  task_id: string
  task_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial'
  data_type: string
  data_source: string
  code?: string
  start_date?: string
  end_date?: string
  progress_percent: number
  total: number
  current: number
  loaded_count: number
  failed_count: number
  message: string
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
  updated_at: string
}

const LoadingProgressPanel: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('')
  const queryClient = useQueryClient()

  const { data: tasks, isLoading, refetch } = useQuery<LoadingTask[]>({
    queryKey: ['loadingTasks', filterStatus],
    queryFn: () => loadingProgressApi.getTasks(filterStatus || undefined, undefined),
    refetchInterval: 3000, // 3 秒轮询一次
  })

  const removeMutation = useMutation({
    mutationFn: (taskId: string) => loadingProgressApi.removeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loadingTasks'] })
    },
  })

  const cleanupMutation = useMutation({
    mutationFn: () => loadingProgressApi.cleanupTasks(24),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loadingTasks'] })
    },
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <Badge colorScheme="blue">运行中</Badge>
      case 'completed':
        return <Badge colorScheme="green">已完成</Badge>
      case 'failed':
        return <Badge colorScheme="red">失败</Badge>
      case 'partial':
        return <Badge colorScheme="orange">部分完成</Badge>
      case 'pending':
        return <Badge colorScheme="gray">等待中</Badge>
      default:
        return <Badge>未知</Badge>
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Spinner size="sm" color="blue.500" />
      case 'completed':
        return <FiCheckCircle color="green" />
      case 'failed':
        return <FiXCircle color="red" />
      default:
        return <FiClock color="gray" />
    }
  }

  const getDataTypeDisplay = (dataType: string) => {
    const typeMap: Record<string, string> = {
      kline: 'K 线数据',
      stock_info: '股票信息',
      sector: '板块数据',
      chip: '筹码数据',
      moneyflow: '资金流向',
      index: '指数数据',
      realtime: '实时数据',
    }
    return typeMap[dataType] || dataType
  }

  const getDataSourceDisplay = (dataSource: string) => {
    const sourceMap: Record<string, string> = {
      tushare: 'Tushare',
      akshare: 'AkShare',
      baostock: 'Baostock',
      yfinance: 'YFinance',
      mixed: '混合数据源',
    }
    return sourceMap[dataSource] || dataSource
  }

  const getProgressColor = (status: string, progress: number) => {
    if (status === 'failed') return 'red'
    if (status === 'completed') return 'green'
    if (status === 'partial') return 'orange'
    if (progress < 30) return 'blue'
    if (progress < 70) return 'yellow'
    return 'green'
  }

  const bg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  return (
    <Card>
      <CardHeader>
        <HStack justify="space-between">
          <HStack>
            <FiDatabase />
            <Heading size="sm">数据加载进度</Heading>
          </HStack>
          <HStack spacing={2}>
            <IconButton
              size="sm"
              aria-label="刷新"
              icon={<FiRefreshCw />}
              onClick={() => refetch()}
              isLoading={isLoading}
            />
            <Tooltip label="清理 24 小时前的任务">
              <IconButton
                size="sm"
                aria-label="清理旧任务"
                icon={<FiTrash2 />}
                onClick={() => cleanupMutation.mutate()}
                isLoading={cleanupMutation.isPending}
              />
            </Tooltip>
          </HStack>
        </HStack>
      </CardHeader>
      <CardBody>
        {isLoading ? (
          <Flex justify="center" align="center" h="200px">
            <Spinner size="lg" color="brand.500" />
          </Flex>
        ) : tasks && tasks.length > 0 ? (
          <VStack spacing={4} align="stretch">
            {tasks.map((task) => (
              <Card
                key={task.task_id}
                variant="outline"
                borderColor={borderColor}
              >
                <CardBody>
                  <VStack spacing={3} align="stretch">
                    {/* 标题行 */}
                    <HStack justify="space-between">
                      <HStack spacing={2}>
                        {getStatusIcon(task.status)}
                        <Text fontWeight="medium">{task.task_name}</Text>
                        {task.code && (
                          <Badge colorScheme="purple">{task.code}</Badge>
                        )}
                      </HStack>
                      <HStack spacing={2}>
                        {getStatusBadge(task.status)}
                        {task.status === 'completed' || task.status === 'failed' ? (
                          <IconButton
                            size="xs"
                            aria-label="移除"
                            icon={<FiTrash2 />}
                            onClick={() => removeMutation.mutate(task.task_id)}
                            isLoading={removeMutation.isPending}
                          />
                        ) : null}
                      </HStack>
                    </HStack>

                    {/* 数据类型和来源 */}
                    <HStack spacing={4}>
                      <Badge colorScheme="teal">
                        {getDataTypeDisplay(task.data_type)}
                      </Badge>
                      <Badge colorScheme="cyan">
                        {getDataSourceDisplay(task.data_source)}
                      </Badge>
                      {task.start_date && task.end_date && (
                        <Text fontSize="xs" color="gray.500">
                          {task.start_date} - {task.end_date}
                        </Text>
                      )}
                    </HStack>

                    {/* 进度条 */}
                    <Box>
                      <Progress
                        value={task.progress_percent}
                        colorScheme={getProgressColor(task.status, task.progress_percent)}
                        size="sm"
                        borderRadius="md"
                        hasStripe={task.status === 'running'}
                        isAnimated={task.status === 'running'}
                      />
                      <HStack justify="space-between" mt={1}>
                        <Text fontSize="xs" color="gray.500">
                          进度：{task.current} / {task.total}
                        </Text>
                        <Text fontSize="xs" fontWeight="bold" color="gray.600">
                          {task.progress_percent.toFixed(1)}%
                        </Text>
                      </HStack>
                    </Box>

                    {/* 统计信息 */}
                    <HStack spacing={4} justify="space-between">
                      <HStack spacing={3}>
                        <Text fontSize="xs" color="gray.600">
                          已加载：{task.loaded_count} 条
                        </Text>
                        {task.failed_count > 0 && (
                          <Text fontSize="xs" color="red.500">
                            失败：{task.failed_count} 次
                          </Text>
                        )}
                      </HStack>
                      <Text fontSize="xs" color="gray.500">
                        更新时间：{new Date(task.updated_at).toLocaleString('zh-CN')}
                      </Text>
                    </HStack>

                    {/* 状态消息 */}
                    {task.message && (
                      <Alert
                        status={task.status === 'failed' ? 'error' : 'info'}
                        borderRadius="md"
                        fontSize="sm"
                      >
                        <AlertIcon />
                        {task.message}
                      </Alert>
                    )}

                    {/* 错误信息 */}
                    {task.error_message && (
                      <Alert status="error" borderRadius="md" fontSize="sm">
                        <AlertIcon />
                        <Text fontSize="xs">{task.error_message}</Text>
                      </Alert>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </VStack>
        ) : (
          <Flex
            justify="center"
            align="center"
            h="200px"
            flexDirection="column"
            color="gray.500"
          >
            <FiDatabase size={48} opacity={0.3} />
            <Text mt={4}>暂无加载任务</Text>
          </Flex>
        )}

        {/* 筛选按钮 */}
        {tasks && tasks.length > 0 && (
          <Flex mt={4} gap={2} flexWrap="wrap">
            <Badge
              cursor="pointer"
              colorScheme={filterStatus === '' ? 'blue' : 'gray'}
              onClick={() => setFilterStatus('')}
              px={3}
              py={1}
            >
              全部
            </Badge>
            <Badge
              cursor="pointer"
              colorScheme={filterStatus === 'running' ? 'blue' : 'gray'}
              onClick={() => setFilterStatus('running')}
              px={3}
              py={1}
            >
              运行中
            </Badge>
            <Badge
              cursor="pointer"
              colorScheme={filterStatus === 'completed' ? 'green' : 'gray'}
              onClick={() => setFilterStatus('completed')}
              px={3}
              py={1}
            >
              已完成
            </Badge>
            <Badge
              cursor="pointer"
              colorScheme={filterStatus === 'failed' ? 'red' : 'gray'}
              onClick={() => setFilterStatus('failed')}
              px={3}
              py={1}
            >
              失败
            </Badge>
          </Flex>
        )}
      </CardBody>
    </Card>
  )
}

export default LoadingProgressPanel
