import { Outlet } from 'react-router-dom'
import {
  Box,
  Flex,
  HStack,
  IconButton,
  useDisclosure,
  VStack,
  Text,
  Container,
} from '@chakra-ui/react'
import { HamburgerIcon } from '@chakra-ui/icons'
import Sidebar from './Sidebar'
import Header from './Header'

const Layout = () => {
  const { isOpen, onOpen, onClose } = useDisclosure()

  return (
    <Flex minH="100vh">
      <Sidebar isOpen={isOpen} onClose={onClose} />
      
      <Flex flexDir="column" flex={1} ml={{ base: 0, lg: '250px' }}>
        <Header onMenuClick={onOpen} />
        
        <Box flex={1} p={4} bg="gray.50">
          <Container maxW="container.xl">
            <Outlet />
          </Container>
        </Box>
      </Flex>
    </Flex>
  )
}

export default Layout
