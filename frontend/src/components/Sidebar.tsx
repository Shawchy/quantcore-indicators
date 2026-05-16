import { Box, Drawer, Flex, Icon, Text, VStack } from '@chakra-ui/react'
import { Link, useLocation } from 'react-router-dom'
import { 
  FiHome, 
  FiStar, 
  FiGrid, 
  FiFilter, 
  FiSearch, 
  FiSettings, 
  FiActivity,
  FiCpu,
  FiTrendingUp,
  FiBarChart,
  FiSliders,
  FiList,
  FiDollarSign,
  FiFile,
  FiPieChart,
  FiShoppingCart,
} from 'react-icons/fi'

const menuItems = [
  { name: '首页概览', icon: FiHome, path: '/' },
  { name: '自选股', icon: FiStar, path: '/watchlist' },
  { name: '基金中心', icon: FiDollarSign, path: '/fund' },
  { name: '市场排行', icon: FiTrendingUp, path: '/market' },
  { name: '龙虎榜', icon: FiList, path: '/billboard' },
  { name: '日线行情', icon: FiBarChart, path: '/daily' },
  { name: '板块分析', icon: FiGrid, path: '/sector' },
  { name: '筹码选股', icon: FiFilter, path: '/chip' },
  { name: '智能选股', icon: FiSearch, path: '/screener' },
  { name: '策略管理', icon: FiSettings, path: '/strategy' },
  { name: '策略回测', icon: FiActivity, path: '/backtest' },
  { name: '东方财富', icon: FiCpu, path: '/akshare/zt-board' },
  { name: '盘口异动', icon: FiActivity, path: '/akshare/changes' },
  { name: '千股千评', icon: FiBarChart, path: '/akshare/stock-comment' },
  { name: '研报公告', icon: FiFile, path: '/akshare/research-notice' },
  { name: '财务分析', icon: FiPieChart, path: '/akshare/financial' },
  { name: '市场指标', icon: FiBarChart, path: '/akshare/legulegu-market-indicators' },
  { name: '估值指标', icon: FiTrendingUp, path: '/akshare/a-share-valuation' },
  { name: '市场统计', icon: FiList, path: '/akshare/market-statistics' },
  { name: '大宗交易', icon: FiShoppingCart, path: '/akshare/block-trade' },
  { name: '融资融券', icon: FiDollarSign, path: '/akshare/margin-trading' },
  { name: '系统设置', icon: FiSliders, path: '/settings' },
]

interface SidebarProps {
  open: boolean
  onOpenChange: (details: { open: boolean }) => void
}

const Sidebar = ({ open, onOpenChange }: SidebarProps) => {
  const location = useLocation()

  const SidebarContent = () => (
    <VStack align="stretch" gap={1} p={3} pt={4}>
      {menuItems.map((item) => {
        const isActive = location.pathname === item.path
        const IconComponent = item.icon
        
        return (
          <Link key={item.path} to={item.path} onClick={() => onOpenChange({ open: false })}>
            <Flex
              align="center"
              p={3}
              borderRadius="md"
              bg={isActive ? 'brand.50' : 'transparent'}
              color={isActive ? 'brand.600' : 'light.textSecondary'}
              fontWeight={isActive ? '600' : '500'}
              transition="all 0.15s"
              _hover={{
                bg: isActive ? 'brand.50' : 'light.bgSecondary',
                color: isActive ? 'brand.600' : 'light.text',
              }}
            >
              <Icon as={IconComponent} boxSize={4} mr={3} />
              <Text fontSize="sm">{item.name}</Text>
            </Flex>
          </Link>
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
        w="sidebar"
        bg="light.card"
        borderRight="1px solid"
        borderColor="light.border"
        zIndex={20}
      >
        <Flex h="14" align="center" px={5} borderBottom="1px solid" borderColor="light.border">
          <Flex align="center" gap={2}>
            <Box
              p={1.5}
              borderRadius="md"
              bg="brand.500"
            >
              <Icon as={FiCpu} color="white" boxSize={4} />
            </Box>
            <Text 
              fontSize="md" 
              fontWeight="bold" 
              color="brand.600"
            >
              Quant
            </Text>
          </Flex>
        </Flex>
        
        <SidebarContent />
      </Box>

      <Drawer.Root open={open} placement="start" onOpenChange={onOpenChange}>
        <Drawer.Backdrop />
        <Drawer.Content bg="light.card">
          <Drawer.CloseTrigger color="light.textSecondary" />
          <Drawer.Body p={0}>
            <Flex h="14" align="center" px={5} borderBottom="1px solid" borderColor="light.border">
              <Flex align="center" gap={2}>
                <Box p={1.5} borderRadius="md" bg="brand.500">
                  <Icon as={FiCpu} color="white" boxSize={4} />
                </Box>
                <Text fontSize="md" fontWeight="bold" color="brand.600">
                  量化分析系统
                </Text>
              </Flex>
            </Flex>
            <SidebarContent />
          </Drawer.Body>
        </Drawer.Content>
      </Drawer.Root>
    </>
  )
}

export default Sidebar
