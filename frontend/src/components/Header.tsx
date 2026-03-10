import {
  Box,
  Flex,
  HStack,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  useColorModeValue,
  Text,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Avatar,
} from '@chakra-ui/react'
import { FiMenu, FiSearch, FiBell, FiUser } from 'react-icons/fi'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface HeaderProps {
  onMenuClick: () => void
}

const Header = ({ onMenuClick }: HeaderProps) => {
  const [searchValue, setSearchValue] = useState('')
  const navigate = useNavigate()
  const bgColor = useColorModeValue('white', 'gray.800')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchValue.trim()) {
      navigate(`/stock/${searchValue.trim()}`)
    }
  }

  return (
    <Box
      as="header"
      position="sticky"
      top={0}
      zIndex={5}
      bg={bgColor}
      borderBottom="1px"
      borderColor="gray.200"
    >
      <Flex h="16" px={4} align="center" justify="space-between">
        <HStack spacing={4}>
          <IconButton
            display={{ base: 'flex', lg: 'none' }}
            variant="ghost"
            aria-label="打开菜单"
            icon={<FiMenu />}
            onClick={onMenuClick}
          />
          
          <form onSubmit={handleSearch}>
            <InputGroup size="sm" w={{ base: '200px', md: '300px' }}>
              <InputLeftElement pointerEvents="none">
                <FiSearch color="gray" />
              </InputLeftElement>
              <Input
                placeholder="输入股票代码搜索..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                borderRadius="md"
              />
            </InputGroup>
          </form>
        </HStack>

        <HStack spacing={3}>
          <IconButton
            variant="ghost"
            aria-label="通知"
            icon={<FiBell />}
            size="sm"
          />
          
          <Menu>
            <MenuButton>
              <Avatar size="sm" icon={<FiUser />} />
            </MenuButton>
            <MenuList>
              <MenuItem>个人设置</MenuItem>
              <MenuItem>系统配置</MenuItem>
              <MenuItem>退出登录</MenuItem>
            </MenuList>
          </Menu>
        </HStack>
      </Flex>
    </Box>
  )
}

export default Header
