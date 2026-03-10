import { extendTheme } from '@chakra-ui/react'

const config = {
  initialColorMode: 'light',
  useSystemColorMode: false,
}

const theme = extendTheme({
  config,
  colors: {
    brand: {
      50: '#e3f2fd',
      100: '#bbdefb',
      200: '#90caf9',
      300: '#64b5f6',
      400: '#42a5f5',
      500: '#2196f3',
      600: '#1e88e5',
      700: '#1976d2',
      800: '#1565c0',
      900: '#0d47a1',
    },
    up: {
      500: '#f44336',
      600: '#d32f2f',
    },
    down: {
      500: '#4caf50',
      600: '#388e3c',
    },
  },
  fonts: {
    heading: `'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif`,
    body: `'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif`,
  },
  styles: {
    global: {
      body: {
        bg: 'gray.50',
      },
    },
  },
  components: {
    Button: {
      defaultProps: {
        colorScheme: 'brand',
      },
    },
    Card: {
      baseStyle: {
        container: {
          borderRadius: 'lg',
          boxShadow: 'sm',
          bg: 'white',
        },
      },
    },
  },
})

export default theme
