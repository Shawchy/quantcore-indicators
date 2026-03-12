import {
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Spinner,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  FormControl,
  FormLabel,
  Input,
  Select,
  useDisclosure,
  SimpleGrid,
  Flex,
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { FiPlus, FiEdit, FiTrash2, FiPlay, FiSettings } from 'react-icons/fi'
import { strategyApi } from '../services/api'
import { Strategy as StrategyType } from '../types'

interface StrategyFormData {
  name: string
  type: string
  config: string
}

const Strategy = () => {
  const queryClient = useQueryClient()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyType | null>(null)
  const [formData, setFormData] = useState<StrategyFormData>({
    name: '',
    type: 'trend',
    config: '{}',
  })

  const { data: strategiesData, isLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => strategyApi.getList(),
  })

  const strategies = strategiesData?.data || []

  const createMutation = useMutation({
    mutationFn: (data: any) => strategyApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] })
      onClose()
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => strategyApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] })
    },
  })

  const handleCreate = () => {
    setSelectedStrategy(null)
    resetForm()
    onOpen()
  }

  const handleEdit = (strategy: any) => {
    setSelectedStrategy(strategy)
    setFormData({
      name: strategy.name,
      type: strategy.strategy_type,
      config: JSON.stringify(strategy.config || {}, null, 2),
    })
    onOpen()
  }

  const handleDelete = (strategyId: string) => {
    if (confirm('确定要删除该策略吗？')) {
      deleteMutation.mutate(strategyId)
    }
  }

  const handleSubmit = () => {
    try {
      const config = JSON.parse(formData.config)
      const data = {
        name: formData.name,
        type: formData.type,
        config,
      }
      createMutation.mutate(data)
    } catch (error) {
      toast({
        title: '配置格式错误',
        description: '请输入有效的 JSON 格式',
        status: 'error',
      })
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'trend',
      config: '{}',
    })
  }

  const strategyTypes = [
    { value: 'trend', label: '趋势跟踪', color: 'brand.500' },
    { value: 'mean_reversion', label: '均值回归', color: 'purple.500' },
    { value: 'multi_factor', label: '多因子', color: 'green.500' },
    { value: 'ml', label: '机器学习', color: 'orange.500' },
    { value: 'custom', label: '自定义', color: 'gray.500' },
  ]

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Heading size="lg" color="light.text">
          策略管理
        </Heading>
        <Button leftIcon={<FiPlus />} variant="primary" onClick={handleCreate}>
          新建策略
        </Button>
      </HStack>

      {isLoading ? (
        <Flex justify="center" align="center" h="200px">
          <Spinner color="brand.400" />
        </Flex>
      ) : strategies.length > 0 ? (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
          {strategies.map((strategy: StrategyType) => {
            const typeInfo = strategyTypes.find(t => t.value === strategy.strategy_type) || strategyTypes[4]
            return (
              <Card 
                key={strategy.strategy_id}
                position="relative"
                overflow="hidden"
                _before={{ 
                  content: '""', 
                  position: 'absolute', 
                  top: 0, 
                  left: 0, 
                  right: 0, 
                  height: '3px', 
                  bg: typeInfo.color 
                }}
              >
                <CardBody>
                  <VStack align="stretch" spacing={3}>
                    <HStack justify="space-between">
                      <Heading size="sm" color="light.text">{strategy.name}</Heading>
                      <Badge 
                        bg={strategy.is_active ? 'rgba(16, 185, 129, 0.15)' : 'light.bgSecondary'}
                        color={strategy.is_active ? 'green.600' : 'light.textMuted'}
                        variant="subtle"
                      >
                        {strategy.is_active ? '启用' : '禁用'}
                      </Badge>
                    </HStack>
                    <HStack>
                      <Badge 
                        bg="light.bgSecondary" 
                        color={typeInfo.color}
                        border="1px solid"
                        borderColor={typeInfo.color}
                        fontSize="xs"
                      >
                        {typeInfo.label}
                      </Badge>
                    </HStack>
                    <Text fontSize="xs" color="light.textMuted">
                      创建时间：{strategy.created_at}
                    </Text>
                    <HStack spacing={2}>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        leftIcon={<FiEdit />}
                        _hover={{ color: 'brand.400', bg: 'light.bgSecondary' }}
                        onClick={() => handleEdit(strategy)}
                      >
                        编辑
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        color="light.textSecondary"
                        _hover={{ color: 'down.500', bg: 'light.bgSecondary' }}
                        leftIcon={<FiTrash2 />} 
                        onClick={() => handleDelete(strategy.strategy_id)}
                      >
                        删除
                      </Button>
                    </HStack>
                  </VStack>
                </CardBody>
              </Card>
            )
          })}
        </SimpleGrid>
      ) : (
        <Card>
          <CardBody>
            <VStack py={10}>
              <Flex
                p={4}
                borderRadius="full"
                bg="light.bgSecondary"
              >
                <FiSettings size={40} color="var(--chakra-colors-light-textMuted)" />
              </Flex>
              <Text color="light.textMuted" textAlign="center">暂无策略，点击上方按钮创建</Text>
            </VStack>
          </CardBody>
        </Card>
      )}

      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(4px)" />
        <ModalContent bg="light.bg" border="1px solid" borderColor="light.border">
          <ModalHeader color="light.text">{selectedStrategy ? '编辑策略' : '新建策略'}</ModalHeader>
          <ModalCloseButton color="light.textSecondary" />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel color="light.textSecondary" fontSize="sm">策略名称</FormLabel>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="输入策略名称"
                  bg="light.bgSecondary"
                  borderColor="light.border"
                  _hover={{ borderColor: 'brand.500' }}
                  _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
                />
              </FormControl>
              <FormControl>
                <FormLabel color="light.textSecondary" fontSize="sm">策略类型</FormLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  bg="light.bgSecondary"
                  borderColor="light.border"
                  _hover={{ borderColor: 'brand.500' }}
                  _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
                >
                  {strategyTypes.map(type => (
                    <option key={type.value} value={type.value} style={{ background: '#ffffff' }}>
                      {type.label}
                    </option>
                  ))}
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel color="light.textSecondary" fontSize="sm">策略配置 (JSON)</FormLabel>
                <Input
                  as="textarea"
                  value={formData.config}
                  onChange={(e) => setFormData({ ...formData, config: e.target.value })}
                  placeholder='{"param1": "value1"}'
                  h="150px"
                  bg="light.bgSecondary"
                  borderColor="light.border"
                  _hover={{ borderColor: 'brand.500' }}
                  _focus={{ borderColor: 'brand.400', bg: 'light.bgSecondary' }}
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={onClose} color="light.textSecondary" ml={3}>
              {selectedStrategy ? '保存' : '创建'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  )
}

export default Strategy
