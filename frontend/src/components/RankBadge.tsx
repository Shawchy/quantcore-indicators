import { Flex, FlexProps } from '@chakra-ui/react'

interface RankBadgeProps extends FlexProps {
  rank: number
  size?: 'sm' | 'md' | 'lg'
}

const sizeConfig = {
  sm: {
    width: '20px',
    height: '20px',
    fontSize: 'xs',
  },
  md: {
    width: '24px',
    height: '24px',
    fontSize: 'xs',
  },
  lg: {
    width: '28px',
    height: '28px',
    fontSize: 'sm',
  },
}

export const RankBadge: React.FC<RankBadgeProps> = ({
  rank,
  size = 'md',
  ...props
}) => {
  const config = sizeConfig[size]
  const isTop3 = rank < 3
  
  return (
    <Flex
      w={config.width}
      h={config.height}
      align="center"
      justify="center"
      borderRadius="md"
      bg={isTop3 ? 'brand.500' : 'light.bgSecondary'}
      color={isTop3 ? 'white' : 'light.textMuted'}
      fontSize={config.fontSize}
      fontWeight="bold"
      {...props}
    >
      {rank}
    </Flex>
  )
}

export default RankBadge
