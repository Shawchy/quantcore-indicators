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
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { FiPlus, FiEdit, FiTrash2, FiPlay } from 'react-icons/fi'
import { strategyApi } from '../services/api'

const Strategy = () => {
  const queryClient = useQueryClient()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [selectedStrategy, setSelectedStrategy] = useState<any>(null)
  const [formData, setFormData] = useState({
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
    const data = {
      name: formData.name,
      type: formData.type,
      config: JSON.parse(formData.config),
    }
    createMutation.mutate(data)
  }

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'trend',
      config: '{}',
    })
  }

  const strategyTypes = [
    { value: 'trend', label: '趋势跟踪' },
    { value: 'mean_reversion', label: '均值回归' },
    { value: 'multi_factor', label: '多因子' },
    { value: 'ml', label: '机器学习' },
    { value: 'custom', label: '自定义' },
  ]

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Heading size="lg">策略管理</Heading>
        <Button leftIcon={<FiPlus />} colorScheme="brand" onClick={handleCreate}>
          新建策略
        </Button>
      </HStack>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
        {isLoading ? (
          <Spinner />
        ) : (
          strategies.map((strategy: any) => (
            <Card key={strategy.strategy_id}>
              <CardBody>
                <VStack align="stretch" spacing={3}>
                  <HStack justify="space-between">
                    <Heading size="sm">{strategy.name}</Heading>
                    <Badge colorScheme={strategy.is_active ? 'green' : 'gray'}>
                      {strategy.is_active ? '启用' : '禁用'}
                    </Badge>
                  </HStack>
                  <Text fontSize="sm" color="gray.500">
                    类型: {strategyTypes.find(t => t.value === strategy.strategy_type)?.label || strategy.strategy_type}
                  </Text>
                  <Text fontSize="xs" color="gray.400">
                    创建时间: {strategy.created_at}
                  </Text>
                  <HStack spacing={2}>
                    <Button size="sm" variant="outline" leftIcon={<FiEdit />} onClick={() => handleEdit(strategy)}>
                      编辑
                    </Button>
                    <Button size="sm" variant="ghost" colorScheme="red" leftIcon={<FiTrash2 />} onClick={() => handleDelete(strategy.strategy_id)}>
                      删除
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          ))
        )}
      </SimpleGrid>

      {!isLoading && strategies.length === 0 && (
        <Card>
          <CardBody>
            <Text color="gray.500" textAlign="center">暂无策略，点击上方按钮创建</Text>
          </CardBody>
        </Card>
      )}

      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{selectedStrategy ? '编辑策略' : '新建策略'}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>策略名称</FormLabel>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="输入策略名称"
                />
              </FormControl>
              <FormControl>
                <FormLabel>策略类型</FormLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                >
                  {strategyTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel>策略配置 (JSON)</FormLabel>
                <Input
                  as="textarea"
                  value={formData.config}
                  onChange={(e) => setFormData({ ...formData, config: e.target.value })}
                  placeholder='{"param1": "value1"}'
                  h="150px"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={onClose}>取消</Button>
            <Button colorScheme="brand" onClick={handleSubmit} ml={3}>
              {selectedStrategy ? '保存' : '创建'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  )
}

export default Strategy
