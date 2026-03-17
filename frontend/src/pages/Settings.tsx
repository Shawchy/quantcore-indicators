import { Container, Heading, VStack } from '@chakra-ui/react'
import DataSourceControl from '../components/DataSourceControl'

const Settings: React.FC = () => {
  return (
    <Container maxW="container.xl" py={6}>
      <VStack spacing={6} align="stretch">
        <Heading size="lg">系统设置</Heading>
        <DataSourceControl />
      </VStack>
    </Container>
  )
}

export default Settings
