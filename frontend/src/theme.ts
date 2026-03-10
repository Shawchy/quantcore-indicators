import { extendTheme, type ThemeConfig } from '@chakra-ui/react'

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
}

const colors = {
  brand: {
    50: '#e6fffa',
    100: '#b2f5ea',
    200: '#81e6d9',
    300: '#4fd1c5',
    400: '#38b2ac',
    500: '#319795',
    600: '#2c7a7b',
    700: '#285e61',
    800: '#234e52',
    900: '#1d4044',
  },
  light: {
    bg: '#f7fafc',
    bgSecondary: '#edf2f7',
    card: '#ffffff',
    cardHover: '#f7fafc',
    border: '#e2e8f0',
    text: '#1a202c',
    textSecondary: '#4a5568',
    textMuted: '#718096',
  },
  up: {
    500: '#e53e3e',
    600: '#c53030',
  },
  down: {
    500: '#38a169',
    600: '#2f855a',
  },
}

const fonts = {
  heading: `'SF Pro Display', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`,
  body: `'SF Pro Text', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`,
  mono: `'SF Mono', 'JetBrains Mono', 'Fira Code', monospace`,
}

const styles = {
  global: {
    'html, body': {
      bg: 'light.bg',
      color: 'light.text',
      minHeight: '100vh',
    },
    '*::selection': {
      bg: 'brand.100',
      color: 'brand.900',
    },
    '::-webkit-scrollbar': {
      width: '6px',
      height: '6px',
    },
    '::-webkit-scrollbar-track': {
      bg: 'light.bgSecondary',
    },
    '::-webkit-scrollbar-thumb': {
      bg: 'brand.300',
      borderRadius: '3px',
    },
    '::-webkit-scrollbar-thumb:hover': {
      bg: 'brand.400',
    },
  },
}

const components = {
  Button: {
    baseStyle: {
      fontWeight: '600',
      borderRadius: 'md',
      transition: 'all 0.2s',
    },
    variants: {
      primary: {
        bg: 'brand.500',
        color: 'white',
        _hover: {
          bg: 'brand.600',
          transform: 'translateY(-1px)',
          boxShadow: 'sm',
        },
        _active: {
          bg: 'brand.700',
          transform: 'translateY(0)',
        },
      },
      secondary: {
        bg: 'transparent',
        color: 'brand.600',
        border: '1px solid',
        borderColor: 'brand.300',
        _hover: {
          bg: 'brand.50',
          borderColor: 'brand.400',
        },
      },
      ghost: {
        color: 'light.textSecondary',
        _hover: {
          bg: 'light.bgSecondary',
          color: 'light.text',
        },
      },
    },
    defaultProps: {
      variant: 'primary',
    },
  },
  Card: {
    baseStyle: {
      container: {
        bg: 'light.card',
        borderRadius: 'lg',
        border: '1px solid',
        borderColor: 'light.border',
        boxShadow: 'sm',
        transition: 'all 0.2s ease',
        _hover: {
          boxShadow: 'md',
          borderColor: 'brand.200',
        },
      },
      header: {
        borderBottom: '1px solid',
        borderColor: 'light.border',
        pb: 2,
      },
      body: {
        pt: 3,
      },
    },
  },
  Input: {
    variants: {
      filled: {
        field: {
          bg: 'light.bgSecondary',
          borderRadius: 'md',
          _hover: {
            bg: 'light.bgSecondary',
            borderColor: 'brand.300',
          },
          _focus: {
            bg: 'white',
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
          },
        },
      },
    },
    defaultProps: {
      variant: 'filled',
    },
  },
  Select: {
    variants: {
      filled: {
        field: {
          bg: 'light.bgSecondary',
          borderRadius: 'md',
          _hover: {
            bg: 'light.bgSecondary',
            borderColor: 'brand.300',
          },
          _focus: {
            bg: 'white',
            borderColor: 'brand.500',
          },
        },
      },
    },
    defaultProps: {
      variant: 'filled',
    },
  },
  Table: {
    variants: {
      simple: {
        th: {
          borderColor: 'light.border',
          color: 'light.textSecondary',
          fontWeight: '600',
          fontSize: 'xs',
          textTransform: 'uppercase',
          letterSpacing: 'wider',
        },
        td: {
          borderColor: 'light.border',
          fontSize: 'sm',
        },
        tr: {
          _hover: {
            bg: 'light.bgSecondary',
          },
        },
      },
    },
  },
  Badge: {
    variants: {
      up: {
        bg: 'red.100',
        color: 'red.700',
        fontWeight: '600',
        borderRadius: 'md',
        px: 2,
        py: 0.5,
      },
      down: {
        bg: 'green.100',
        color: 'green.700',
        fontWeight: '600',
        borderRadius: 'md',
        px: 2,
        py: 0.5,
      },
      subtle: {
        bg: 'light.bgSecondary',
        color: 'light.textSecondary',
        borderRadius: 'md',
      },
    },
  },
  Tabs: {
    variants: {
      line: {
        tab: {
          color: 'light.textSecondary',
          fontWeight: '500',
          borderBottom: '2px solid transparent',
          _selected: {
            color: 'brand.600',
            borderColor: 'brand.500',
          },
          _hover: {
            color: 'light.text',
          },
        },
        tablist: {
          borderBottom: '1px solid',
          borderColor: 'light.border',
        },
      },
    },
  },
  Menu: {
    baseStyle: {
      list: {
        bg: 'light.card',
        border: '1px solid',
        borderColor: 'light.border',
        boxShadow: 'md',
        borderRadius: 'lg',
        py: 2,
      },
      item: {
        bg: 'transparent',
        borderRadius: 'md',
        mx: 2,
        px: 3,
        _hover: {
          bg: 'brand.50',
        },
        _focus: {
          bg: 'brand.50',
        },
      },
    },
  },
  Modal: {
    baseStyle: {
      dialog: {
        bg: 'light.card',
        borderRadius: 'xl',
      },
      overlay: {
        bg: 'blackAlpha.200',
      },
    },
  },
}

const shadows = {
  card: '0 1px 3px rgba(0, 0, 0, 0.05)',
  cardHover: '0 4px 12px rgba(0, 0, 0, 0.1)',
}

const theme = extendTheme({
  config,
  colors,
  fonts,
  styles,
  components,
  shadows,
  space: {
    sidebar: '220px',
  },
})

export default theme
