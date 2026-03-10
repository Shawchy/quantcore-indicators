import {
  Box,
  Flex,
  HStack,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  Text,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Avatar,
  Badge,
  Tooltip,
} from '@chakra-ui/react'
import { FiMenu, FiSearch, FiBell, FiUser, FiSettings, FiLogOut } from 'react-icons/fi'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../store/hooks'
import { logout } from '../store/slices/authSlice'

interface HeaderProps {
  onMenuClick: () => void
}

const Header = ({ onMenuClick }: HeaderProps) => {
  const [searchValue, setSearchValue] = useState('')
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { user, isAuthenticated } = useAppSelector((state) => state.auth)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchValue.trim()) {
      navigate(`/stock/${searchValue.trim()}`)
      setSearchValue('')
    }
  }

  const handleLogout = async () => {
    try {
      await dispatch(logout()).unwrap()
      navigate('/login')
    } catch (error) {
      console.error('登出失败:', error)
    }
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
        <HStack spacing={4}>
          <IconButton
            display={{ base: 'flex', lg: 'none' }}
            variant="ghost"
            aria-label="打开菜单"
            icon={<FiMenu />}
            onClick={onMenuClick}
            color="light.textSecondary"
            _hover={{ color: 'brand.500', bg: 'light.bgSecondary' }}
          />
          
          <form onSubmit={handleSearch}>
            <InputGroup size="md" w={{ base: '180px', md: '320px' }}>
              <InputLeftElement pointerEvents="none" h="full">
                <FiSearch color="var(--chakra-colors-light-textMuted)" />
              </InputLeftElement>
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

        <HStack spacing={2}>
          <Tooltip label="系统通知" placement="bottom">
            <Box position="relative">
              <IconButton
                variant="ghost"
                aria-label="通知"
                icon={<FiBell />}
                size="md"
                color="light.textSecondary"
                _hover={{ 
                  color: 'brand.500', 
                  bg: 'light.bgSecondary' 
                }}
              />
              <Badge
                position="absolute"
                top={1}
                right={1}
                colorScheme="red"
                borderRadius="full"
                boxSize={2}
                p={0}
              />
            </Box>
          </Tooltip>
          
          <Menu>
            <MenuButton>
              <Avatar 
                size="sm" 
                name={user?.username}
                icon={<FiUser />}
                bg="brand.500"
                color="white"
                cursor="pointer"
                _hover={{
                  boxShadow: '0 0 15px rgba(33, 150, 243, 0.4)',
                }}
                transition="all 0.2s"
              />
            </MenuButton>
            <MenuList>
              <MenuItem 
                icon={<FiUser />} 
                _hover={{ bg: 'light.bgSecondary' }}
              >
                {user?.username || '个人中心'}
              </MenuItem>
              <MenuItem 
                icon={<FiSettings />} 
                _hover={{ bg: 'light.bgSecondary' }}
              >
                系统设置
              </MenuItem>
              <MenuItem 
                icon={<FiLogOut />} 
                onClick={handleLogout}
                _hover={{ bg: 'light.bgSecondary' }}
                color="red.500"
              >
                退出登录
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>
      </Flex>
    </Box>
  )
}

export default Header
