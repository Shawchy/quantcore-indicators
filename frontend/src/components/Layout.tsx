import { Outlet } from 'react-router-dom'
import {
  Box,
  Flex,
  useDisclosure,
} from '@chakra-ui/react'
import Sidebar from './Sidebar'
import Header from './Header'

const Layout = () => {
  const { isOpen, onOpen, onClose } = useDisclosure()

  return (
    <Flex minH="100vh" bg="light.bg">
      <Sidebar isOpen={isOpen} onClose={onClose} />
      
      <Flex 
        flexDir="column" 
        flex={1} 
        ml={{ base: 0, lg: 'sidebar' }}
        minW={0}
      >
        <Header onMenuClick={onOpen} />
        
        <Box 
          flex={1} 
          p={{ base: 3, md: 5, lg: 6 }}
          bg="light.bg"
          overflow="auto"
        >
          <Box maxW="1800px" mx="auto">
            <Outlet />
          </Box>
        </Box>
      </Flex>
    </Flex>
  )
}

export default Layout
