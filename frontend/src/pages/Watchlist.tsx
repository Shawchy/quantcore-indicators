import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  IconButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Spinner,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useDisclosure,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  FormControl,
  FormLabel,
} from '@chakra-ui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FiTrash2, FiEdit, FiPlus, FiRefreshCw } from 'react-icons/fi'
import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { watchlistApi } from '../services/api'

const Watchlist = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [selectedCode, setSelectedCode] = useState<string>('')
  const [noteValue, setNoteValue] = useState('')
  const [addCode, setAddCode] = useState('')
  const cancelRef = useRef<HTMLButtonElement>(null)
  
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure()
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure()
  const { isOpen: isAddOpen, onOpen: onAddOpen, onClose: onAddClose } = useDisclosure()

  const { data: watchlistData, isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => watchlistApi.getList(),
  })

  const { data: quotesData, isLoading: quotesLoading, refetch } = useQuery({
    queryKey: ['watchlistQuotes'],
    queryFn: () => watchlistApi.getQuotes(),
  })

  const deleteMutation = useMutation({
    mutationFn: (code: string) => watchlistApi.remove(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      queryClient.invalidateQueries({ queryKey: ['watchlistQuotes'] })
      onDeleteClose()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ code, note }: { code: string; note: string }) => watchlistApi.update(code, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      onEditClose()
    },
  })

  const addMutation = useMutation({
    mutationFn: ({ code, note }: { code: string; note?: string }) => watchlistApi.add(code, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      queryClient.invalidateQueries({ queryKey: ['watchlistQuotes'] })
      onAddClose()
      setAddCode('')
    },
  })

  const handleDelete = (code: string) => {
    setSelectedCode(code)
    onDeleteOpen()
  }

  const handleEdit = (code: string, note: string) => {
    setSelectedCode(code)
    setNoteValue(note || '')
    onEditOpen()
  }

  const confirmDelete = () => {
    deleteMutation.mutate(selectedCode)
  }

  const confirmEdit = () => {
    updateMutation.mutate({ code: selectedCode, note: noteValue })
  }

  const confirmAdd = () => {
    if (addCode.trim()) {
      addMutation.mutate({ code: addCode.trim() })
    }
  }

  const quotes = quotesData?.data || []

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Heading size="lg">自选股</Heading>
        <HStack>
          <Button leftIcon={<FiRefreshCw />} variant="outline" size="sm" onClick={() => refetch()}>
            刷新
          </Button>
          <Button leftIcon={<FiPlus />} colorScheme="brand" size="sm" onClick={onAddOpen}>
            添加
          </Button>
        </HStack>
      </HStack>

      <Card>
        <CardBody>
          {isLoading || quotesLoading ? (
            <VStack justify="center" h="200px">
              <Spinner />
              <Text>加载中...</Text>
            </VStack>
          ) : (
            <TableContainer>
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>代码</Th>
                    <Th>名称</Th>
                    <Th isNumeric>现价</Th>
                    <Th isNumeric>涨跌幅</Th>
                    <Th isNumeric>成交量</Th>
                    <Th>备注</Th>
                    <Th>操作</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {quotes.map((item: any) => (
                    <Tr
                      key={item.code}
                      _hover={{ bg: 'gray.50', cursor: 'pointer' }}
                      onClick={() => navigate(`/stock/${item.code}`)}
                    >
                      <Td fontWeight="medium">{item.code}</Td>
                      <Td>{item.name}</Td>
                      <Td isNumeric fontWeight="medium">{item.price?.toFixed(2)}</Td>
                      <Td isNumeric>
                        <Badge colorScheme={item.change_pct >= 0 ? 'red' : 'green'}>
                          {item.change_pct >= 0 ? '+' : ''}{item.change_pct?.toFixed(2)}%
                        </Badge>
                      </Td>
                      <Td isNumeric>{item.volume ? (item.volume / 10000).toFixed(0) + '万' : '--'}</Td>
                      <Td>{item.note || '-'}</Td>
                      <Td>
                        <HStack spacing={1} onClick={(e) => e.stopPropagation()}>
                          <IconButton
                            aria-label="编辑"
                            icon={<FiEdit />}
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(item.code, item.note)}
                          />
                          <IconButton
                            aria-label="删除"
                            icon={<FiTrash2 />}
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => handleDelete(item.code)}
                          />
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          )}
        </CardBody>
      </Card>

      <AlertDialog isOpen={isDeleteOpen} leastDestructiveRef={cancelRef} onClose={onDeleteClose}>
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader>确认删除</AlertDialogHeader>
            <AlertDialogBody>
              确定要从自选股中删除 {selectedCode} 吗？
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onDeleteClose}>取消</Button>
              <Button colorScheme="red" onClick={confirmDelete} ml={3}>删除</Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      <Modal isOpen={isEditOpen} onClose={onEditClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>编辑备注</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <FormControl>
              <FormLabel>备注内容</FormLabel>
              <Input value={noteValue} onChange={(e) => setNoteValue(e.target.value)} placeholder="输入备注..." />
            </FormControl>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={onEditClose}>取消</Button>
            <Button colorScheme="brand" onClick={confirmEdit} ml={3}>保存</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal isOpen={isAddOpen} onClose={onAddClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>添加自选股</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <FormControl>
              <FormLabel>股票代码</FormLabel>
              <Input value={addCode} onChange={(e) => setAddCode(e.target.value)} placeholder="输入股票代码..." />
            </FormControl>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={onAddClose}>取消</Button>
            <Button colorScheme="brand" onClick={confirmAdd} ml={3}>添加</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  )
}

export default Watchlist
