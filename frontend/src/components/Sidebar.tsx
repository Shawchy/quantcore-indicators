import {
  Box,
  Flex,
  Text,
  IconButton,
  Drawer,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  DrawerHeader,
  DrawerBody,
  VStack,
  useColorModeValue,
  Link as ChakraLink,
} from '@chakra-ui/react'
import { Link, useLocation } from 'react-router-dom'
import { FiHome, FiTrendingUp, FiStar, FiGrid, FiFilter, FiSearch, FiSettings, FiActivity } from 'react-icons/fi'

const menuItems = [
  { name: '首页概览', icon: FiHome, path: '/' },
  { name: '自选股', icon: FiStar, path: '/watchlist' },
  { name: '板块分析', icon: FiGrid, path: '/sector' },
  { name: '筹码选股', icon: FiFilter, path: '/chip' },
  { name: '智能选股', icon: FiSearch, path: '/screener' },
  { name: '策略管理', icon: FiSettings, path: '/strategy' },
  { name: '策略回测', icon: FiActivity, path: '/backtest' },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  const location = useLocation()
  const bgColor = useColorModeValue('white', 'gray.800')
  const activeBg = useColorModeValue('brand.50', 'brand.900')
  const activeColor = useColorModeValue('brand.600', 'brand.200')

  const SidebarContent = () => (
    <VStack align="stretch" spacing={1} p={2}>
      {menuItems.map((item) => {
        const isActive = location.pathname === item.path
        const Icon = item.icon
        
        return (
          <ChakraLink
            key={item.path}
            as={Link}
            to={item.path}
            onClick={onClose}
            _hover={{ textDecoration: 'none' }}
          >
            <Flex
              align="center"
              p={3}
              borderRadius="md"
              bg={isActive ? activeBg : 'transparent'}
              color={isActive ? activeColor : 'gray.600'}
              fontWeight={isActive ? 'semibold' : 'normal'}
              _hover={{ bg: activeBg }}
              transition="all 0.2s"
            >
              <Icon size={18} style={{ marginRight: '12px' }} />
              <Text fontSize="sm">{item.name}</Text>
            </Flex>
          </ChakraLink>
        )
      })}
    </VStack>
  )

  return (
    <>
      <Box
        display={{ base: 'none', lg: 'block' }}
        position="fixed"
        left={0}
        top={0}
        bottom={0}
        w="250px"
        bg={bgColor}
        borderRight="1px"
        borderColor="gray.200"
        zIndex={10}
      >
        <Flex h="16" align="center" px={6} borderBottom="1px" borderColor="gray.200">
          <Text fontSize="xl" fontWeight="bold" color="brand.600">
            量化分析系统
          </Text>
        </Flex>
        <SidebarContent />
      </Box>

      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>量化分析系统</DrawerHeader>
          <DrawerBody>
            <SidebarContent />
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </>
  )
}

export default Sidebar
