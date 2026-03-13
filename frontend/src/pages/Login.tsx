import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../store/hooks'
import { login, clearError, getCurrentUser } from '../store/slices/authSlice'
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Input,
  Heading,
  Text,
  Alert,
  AlertIcon,
  AlertDescription,
  VStack,
  InputGroup,
  InputRightElement,
  IconButton,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react'
import { FiEye, FiEyeOff } from 'react-icons/fi'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()
  const { isLoading, error, isAuthenticated } = useAppSelector((state) => state.auth)

  const from = location.state?.from?.pathname || '/'

  useEffect(() => {
    // 如果已经登录，直接跳转到首页
    if (isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, navigate, from])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!username.trim() || !password.trim()) {
      dispatch(clearError())
      toast({
        title: '请填写完整',
        description: '用户名和密码不能为空',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    try {
      const result = await dispatch(login({ username, password })).unwrap()
      // 登录成功后获取用户信息
      await dispatch(getCurrentUser()).unwrap()
      navigate(from, { replace: true })
    } catch (err) {
      // 错误已在 authSlice 中处理
    }
  }

  const handleTogglePassword = () => {
    setShowPassword(!showPassword)
  }

  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  return (
    <Container maxW="md" centerContent>
      <Box
        bg={bgColor}
        p={8}
        borderRadius="xl"
        boxShadow="xl"
        mt={20}
        w="full"
        border="1px solid"
        borderColor={borderColor}
      >
        <VStack spacing={2} mb={8}>
          <Heading size="xl" color="brand.500">
            量化分析系统
          </Heading>
          <Text color="gray.500" fontSize="sm">
            登录以继续访问
          </Text>
        </VStack>

        {error && (
          <Alert status="error" mb={6} borderRadius="lg" variant="left-accent">
            <AlertIcon />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <FormControl mb={5} isRequired>
            <FormLabel fontWeight="medium">用户名</FormLabel>
            <Input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名（admin 或 user）"
              size="lg"
              borderRadius="lg"
              autoComplete="username"
            />
          </FormControl>

          <FormControl mb={6} isRequired>
            <FormLabel fontWeight="medium">密码</FormLabel>
            <InputGroup size="lg">
              <Input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码（admin123 或 user123）"
                borderRadius="lg"
                autoComplete="current-password"
              />
              <InputRightElement>
                <IconButton
                  size="sm"
                  variant="ghost"
                  aria-label={showPassword ? '隐藏密码' : '显示密码'}
                  icon={showPassword ? <FiEyeOff /> : <FiEye />}
                  onClick={handleTogglePassword}
                  tabIndex={-1}
                />
              </InputRightElement>
            </InputGroup>
          </FormControl>

          <Button
            type="submit"
            colorScheme="blue"
            width="full"
            size="lg"
            borderRadius="lg"
            isLoading={isLoading}
            loadingText="登录中..."
            _hover={{
              transform: 'translateY(-1px)',
              boxShadow: 'lg',
            }}
            transition="all 0.2s"
          >
            登录
          </Button>
        </form>

        <Box mt={6} p={4} bg="blue.50" borderRadius="lg" fontSize="sm">
          <Text fontWeight="medium" mb={2}>
            测试账户：
          </Text>
          <VStack align="start" spacing={1} fontSize="xs" color="gray.600">
            <Text>• 管理员：admin / admin123</Text>
            <Text>• 普通用户：user / user123</Text>
          </VStack>
        </Box>
      </Box>
    </Container>
  )
}

export default Login
