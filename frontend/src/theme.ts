import { createSystem, defaultConfig, defineConfig, defineRecipe, defineSlotRecipe } from '@chakra-ui/react'

const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        brand: {
          50: { value: '#e6fffa' },
          100: { value: '#b2f5ea' },
          200: { value: '#81e6d9' },
          300: { value: '#4fd1c5' },
          400: { value: '#38b2ac' },
          500: { value: '#319795' },
          600: { value: '#2c7a7b' },
          700: { value: '#285e61' },
          800: { value: '#234e52' },
          900: { value: '#1d4044' },
        },
        light: {
          bg: { value: '#f7fafc' },
          bgSecondary: { value: '#edf2f7' },
          card: { value: '#ffffff' },
          cardHover: { value: '#f7fafc' },
          border: { value: '#e2e8f0' },
          text: { value: '#1a202c' },
          textSecondary: { value: '#4a5568' },
          textMuted: { value: '#718096' },
        },
        dark: {
          bg: { value: '#1a202c' },
          bgSecondary: { value: '#2d3748' },
          card: { value: '#2d3748' },
          cardHover: { value: '#4a5568' },
          border: { value: '#4a5568' },
          text: { value: '#e2e8f0' },
          textSecondary: { value: '#a0aec0' },
          textMuted: { value: '#718096' },
        },
        up: {
          500: { value: '#e53e3e' },
          600: { value: '#c53030' },
        },
        down: {
          500: { value: '#38a169' },
          600: { value: '#2f855a' },
        },
      },
      fonts: {
        heading: { value: `'SF Pro Display', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` },
        body: { value: `'SF Pro Text', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` },
        mono: { value: `'SF Mono', 'JetBrains Mono', 'Fira Code', monospace` },
      },
      shadows: {
        card: { value: '0 1px 3px rgba(0, 0, 0, 0.05)' },
        cardHover: { value: '0 4px 12px rgba(0, 0, 0, 0.1)' },
      },
      spacing: {
        sidebar: { value: '220px' },
      },
    },
    recipes: {
      button: defineRecipe({
        base: {
          fontWeight: '600',
          borderRadius: 'md',
          transition: 'all 0.2s',
        },
        variants: {
          variant: {
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
              color: 'fg.muted',
              _hover: {
                bg: 'bg.subtle',
                color: 'fg',
              },
            },
          },
        },
        defaultVariants: {
          variant: 'primary',
        },
      }),
      badge: defineRecipe({
        variants: {
          variant: {
            up: {
              bg: 'red.100',
              color: 'red.700',
              fontWeight: '600',
              borderRadius: 'md',
              px: '2',
              py: '0.5',
              _dark: {
                bg: 'red.900',
                color: 'red.200',
              },
            },
            down: {
              bg: 'green.100',
              color: 'green.700',
              fontWeight: '600',
              borderRadius: 'md',
              px: '2',
              py: '0.5',
              _dark: {
                bg: 'green.900',
                color: 'green.200',
              },
            },
            subtle: {
              bg: 'bg.subtle',
              color: 'fg.muted',
              borderRadius: 'md',
            },
          },
        },
      }),
    },
    slotRecipes: {
      card: defineSlotRecipe({
        slots: ['root', 'header', 'body'],
        base: {
          root: {
            bg: 'bg.panel',
            borderRadius: 'lg',
            border: '1px solid',
            borderColor: 'border',
            boxShadow: 'sm',
            transition: 'all 0.2s ease',
            _hover: {
              boxShadow: 'md',
              borderColor: 'brand.200',
            },
          },
          header: {
            borderBottom: '1px solid',
            borderColor: 'border',
            pb: '2',
          },
          body: {
            pt: '3',
          },
        },
      }),
      table: defineSlotRecipe({
        slots: ['root', 'header', 'body', 'row', 'headerCell', 'cell'],
        variants: {
          variant: {
            simple: {
              headerCell: {
                borderColor: 'border',
                color: 'fg.muted',
                fontWeight: '600',
                fontSize: 'xs',
                textTransform: 'uppercase',
                letterSpacing: 'wider',
              },
              cell: {
                borderColor: 'border',
                fontSize: 'sm',
              },
              row: {
                _hover: {
                  bg: 'bg.subtle',
                },
              },
            },
          },
        },
        defaultVariants: {
          variant: 'simple',
        },
      }),
      tabs: defineSlotRecipe({
        slots: ['root', 'list', 'trigger', 'content', 'indicator'],
        variants: {
          variant: {
            line: {
              trigger: {
                color: 'fg.muted',
                fontWeight: '500',
                borderBottom: '2px solid transparent',
                _selected: {
                  color: 'brand.600',
                  borderColor: 'brand.500',
                },
                _hover: {
                  color: 'fg',
                },
              },
              list: {
                borderBottom: '1px solid',
                borderColor: 'border',
              },
            },
          },
        },
        defaultVariants: {
          variant: 'line',
        },
      }),
      menu: defineSlotRecipe({
        slots: ['root', 'trigger', 'content', 'item'],
        base: {
          content: {
            bg: 'bg.panel',
            border: '1px solid',
            borderColor: 'border',
            boxShadow: 'md',
            borderRadius: 'lg',
            py: '2',
          },
          item: {
            bg: 'transparent',
            borderRadius: 'md',
            mx: '2',
            px: '3',
            _hover: {
              bg: 'brand.50',
            },
            _focus: {
              bg: 'brand.50',
            },
          },
        },
      }),
      dialog: defineSlotRecipe({
        slots: ['root', 'trigger', 'content', 'header', 'body', 'footer', 'backdrop', 'closeTrigger'],
        base: {
          content: {
            bg: 'bg.panel',
            borderRadius: 'xl',
          },
          backdrop: {
            bg: 'blackAlpha.200',
          },
        },
      }),
    },
  },
  globalCss: {
    'html, body': {
      bg: 'bg',
      color: 'fg',
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
      bg: 'bg.subtle',
    },
    '::-webkit-scrollbar-thumb': {
      bg: 'brand.300',
      borderRadius: '3px',
    },
    '::-webkit-scrollbar-thumb:hover': {
      bg: 'brand.400',
    },
  },
})

export const system = createSystem(defaultConfig, config)
export default system
