import { Card, CardBody, Stat, StatLabel, StatNumber, StatHelpText, Flex, Icon, BoxProps } from '@chakra-ui/react'
import type { ReactNode } from 'react'

interface StatCardProps extends BoxProps {
  label: string
  value: string | number | ReactNode
  helpText?: string
  size?: 'sm' | 'md' | 'lg'
  colorScheme?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
  icon?: React.ComponentType
  accentColor?: string
}

const sizeConfig = {
  sm: {
    numberFontSize: 'xl',
    labelFontSize: 'xs',
    helpTextFontSize: 'xs',
    padding: 3,
  },
  md: {
    numberFontSize: '2xl',
    labelFontSize: 'sm',
    helpTextFontSize: 'xs',
    padding: 4,
  },
  lg: {
    numberFontSize: '3xl',
    labelFontSize: 'md',
    helpTextFontSize: 'sm',
    padding: 5,
  },
}

const colorSchemeConfig = {
  default: {
    numberColor: 'light.text',
    labelColor: 'light.textSecondary',
    helpTextColor: 'light.textMuted',
  },
  primary: {
    numberColor: 'brand.500',
    labelColor: 'light.textSecondary',
    helpTextColor: 'light.textMuted',
  },
  success: {
    numberColor: 'green.600',
    labelColor: 'light.textSecondary',
    helpTextColor: 'light.textMuted',
  },
  warning: {
    numberColor: 'orange.600',
    labelColor: 'light.textSecondary',
    helpTextColor: 'light.textMuted',
  },
  danger: {
    numberColor: 'red.600',
    labelColor: 'light.textSecondary',
    helpTextColor: 'light.textMuted',
  },
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  helpText,
  size = 'md',
  colorScheme = 'default',
  icon,
  accentColor,
  ...props
}) => {
  const config = sizeConfig[size]
  const colors = colorSchemeConfig[colorScheme]
  const iconColor = accentColor ? `${accentColor}.500` : 'brand.500'
  const iconBg = accentColor ? `${accentColor}.50` : 'brand.50'

  return (
    <Card {...props}>
      <CardBody p={config.padding}>
        <Flex justify="space-between" align="flex-start">
          <Stat>
            <StatLabel color={colors.labelColor} fontSize={config.labelFontSize} textTransform="uppercase">
              {label}
            </StatLabel>
            <StatNumber
              color={colors.numberColor}
              fontSize={config.numberFontSize}
              fontWeight="bold"
              fontFamily="mono"
              mt={1}
            >
              {value}
            </StatNumber>
            {helpText && (
              <StatHelpText color={colors.helpTextColor} fontSize={config.helpTextFontSize} mb={0}>
                {helpText}
              </StatHelpText>
            )}
          </Stat>
          {icon && (
            <Flex
              p={3}
              borderRadius="lg"
              bg={iconBg}
              align="center"
              justify="center"
            >
              <Icon as={icon} boxSize={6} color={iconColor} />
            </Flex>
          )}
        </Flex>
      </CardBody>
    </Card>
  )
}

export default StatCard
