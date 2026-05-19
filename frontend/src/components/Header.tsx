import {
  Box,
  Flex,
  HStack,
  IconButton,
  Input,
  InputGroup,
  Menu,
  Avatar,
  Tooltip,
} from '@chakra-ui/react'
import { FiMenu, FiSearch, FiBell, FiUser } from 'react-icons/fi'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

interface HeaderProps {
  onMenuClick: () => void
}

const Header = ({ onMenuClick }: HeaderProps) => {
  const [searchValue, setSearchValue] = useState('')
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchValue.trim()) {
      navigate(`/stock/${searchValue.trim()}`)
      setSearchValue('')
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Box
      as="header"
      position="sticky"
      top={0}
      zIndex={15}
      bg="light.card"
      borderBottom="1px solid"
      borderColor="light.border"
    >
      <Flex 
        h="16" 
        px={{ base: 4, md: 6 }} 
        align="center" 
        justify="space-between"
        maxW="1800px"
        mx="auto"
      >
        <HStack gap={4}>
          <IconButton
              display={{ base: 'flex', lg: 'none' }}
              variant="ghost"
              aria-label="打开菜单"
              onClick={onMenuClick}
              color="light.textSecondary"
              _hover={{ color: 'brand.500', bg: 'light.bgSecondary' }}
            >
              <FiMenu />
            </IconButton>
          
          <form onSubmit={handleSearch}>
            <InputGroup w={{ base: '180px', md: '320px' }} startAddon={
              <Box pointerEvents="none" h="full" display="flex" alignItems="center" pl={3}>
                <FiSearch color="var(--chakra-colors-light-textMuted)" />
              </Box>
            }>
              <Input
                placeholder="搜索股票代码/名称..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                borderRadius="lg"
                bg="light.bgSecondary"
                border="1px solid"
                borderColor="light.border"
                color="light.text"
                fontSize="sm"
                _placeholder={{ color: 'light.textMuted' }}
                _hover={{
                  borderColor: 'brand.400',
                  bg: 'white',
                }}
                _focus={{
                  borderColor: 'brand.500',
                  bg: 'white',
                  boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
                }}
              />
            </InputGroup>
          </form>
        </HStack>

        <HStack gap={2}>
          <Tooltip.Root>
            <Tooltip.Trigger>
              <IconButton
                variant="ghost"
                aria-label="通知"
                size="md"
                color="light.textSecondary"
                _hover={{ 
                  color: 'brand.500', 
                  bg: 'light.bgSecondary' 
                }}
              >
                <FiBell />
              </IconButton>
            </Tooltip.Trigger>
            <Tooltip.Content>系统通知</Tooltip.Content>
          </Tooltip.Root>
          
          <Menu.Root>
            <Menu.Trigger>
              <Avatar.Root
                size="sm"
                bg="brand.500"
                color="white"
                cursor="pointer"
                _hover={{
                  boxShadow: '0 0 15px rgba(33, 150, 243, 0.4)',
                }}
                transition="all 0.2s"
              >
                <Avatar.Fallback name={user?.username}><FiUser /></Avatar.Fallback>
              </Avatar.Root>
            </Menu.Trigger>
            <Menu.Positioner>
              <Menu.Content>
                <Menu.Item 
                  value="profile"
                  _hover={{ bg: 'light.bgSecondary' }}
                >
                  {user?.username || '个人中心'}
                </Menu.Item>
                <Menu.Item 
                  value="settings"
                  _hover={{ bg: 'light.bgSecondary' }}
                >
                  系统设置
                </Menu.Item>
                <Menu.Item 
                  value="logout"
                  onClick={handleLogout}
                  _hover={{ bg: 'light.bgSecondary' }}
                  color="red.500"
                >
                  退出登录
                </Menu.Item>
              </Menu.Content>
            </Menu.Positioner>
          </Menu.Root>
        </HStack>
      </Flex>
    </Box>
  )
}

export default Header
