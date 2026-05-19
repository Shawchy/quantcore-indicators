import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuthStore } from '../store/authStore'
import {
  Box,
  Button,
  Container,
  Field,
  Input,
  Heading,
  Text,
  Alert,
  VStack,
  InputGroup,
  IconButton,
  createToaster,
} from '@chakra-ui/react'
import { useColorModeValue } from '../components/ui/color-mode'
import { FiEye, FiEyeOff } from 'react-icons/fi'
import { useState } from 'react'

const loginSchema = z.object({
  username: z
    .string()
    .min(2, '用户名至少2个字符')
    .max(50, '用户名最多50个字符'),
  password: z
    .string()
    .min(4, '密码至少4个字符')
    .max(100, '密码最多100个字符'),
})

type LoginFormData = z.infer<typeof loginSchema>

const toaster = createToaster({
  placement: 'top-end',
  duration: 3000,
})

const Login = () => {
  const [showPassword, setShowPassword] = useState(false)
  const login = useAuthStore((s) => s.login)
  const getCurrentUser = useAuthStore((s) => s.getCurrentUser)
  const isLoading = useAuthStore((s) => s.isLoading)
  const error = useAuthStore((s) => s.error)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const navigate = useNavigate()
  const location = useLocation()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  })

  const from = location.state?.from?.pathname || '/'

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, navigate, from])

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.username, data.password)
      await getCurrentUser()
      navigate(from, { replace: true })
    } catch {
      toaster.create({
        title: '登录失败',
        description: error || '请检查用户名和密码',
        type: 'error',
      })
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
        <VStack gap={2} mb={8}>
          <Heading size="xl" color="blue.500">
            量化分析系统
          </Heading>
          <Text color="gray.500" fontSize="sm">
            登录以继续访问
          </Text>
        </VStack>

        {error && (
          <Alert.Root status="error" mb={6} borderRadius="lg">
            <Alert.Indicator />
            <Alert.Description>{error}</Alert.Description>
          </Alert.Root>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <Field.Root invalid={!!errors.username} mb={5}>
            <Field.Label fontWeight="medium">用户名</Field.Label>
            <Input
              {...register('username')}
              placeholder="请输入用户名（admin 或 user）"
              size="lg"
              borderRadius="lg"
              autoComplete="username"
            />
            <Field.ErrorText>{errors.username?.message}</Field.ErrorText>
          </Field.Root>

          <Field.Root invalid={!!errors.password} mb={6}>
            <Field.Label fontWeight="medium">密码</Field.Label>
            <InputGroup endAddon={
              <IconButton
                size="sm"
                variant="ghost"
                aria-label={showPassword ? '隐藏密码' : '显示密码'}
                onClick={handleTogglePassword}
                tabIndex={-1}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </IconButton>
            }>
              <Input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                placeholder="请输入密码（admin123 或 user123）"
                borderRadius="lg"
                autoComplete="current-password"
              />
            </InputGroup>
            <Field.ErrorText>{errors.password?.message}</Field.ErrorText>
          </Field.Root>

          <Button
            type="submit"
            colorPalette="blue"
            width="full"
            size="lg"
            borderRadius="lg"
            loading={isLoading}
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
          <VStack align="start" gap={1} fontSize="xs" color="gray.600">
            <Text>• 管理员：admin / admin123</Text>
            <Text>• 普通用户：user / user123</Text>
          </VStack>
        </Box>
      </Box>
    </Container>
  )
}

export default Login
