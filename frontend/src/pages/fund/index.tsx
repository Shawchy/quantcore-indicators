/**
 * 基金首页
 * 
 * 基金模块的入口页面，展示基金市场概览
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardBody,
  Heading,
  Text,
  SimpleGrid,
  HStack,
  VStack,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Button,
  useColorModeValue,
} from '@chakra-ui/react';
import { StarIcon } from '@chakra-ui/icons';
import {
  FiTrendingUp,
  FiTrendingDown,
  FiDollarSign,
  FiBarChart,
  FiHeart,
} from 'react-icons/fi';

const FundHome: React.FC = () => {
  const navigate = useNavigate();
  const cardHoverBg = useColorModeValue('gray.50', 'gray.700');

  // 模拟市场概览数据
  const marketOverview = {
    totalFunds: 24708,
    riseCount: 12345,
    fallCount: 11234,
    avgReturn: 2.34,
    topSector: '白酒',
    topSectorReturn: 5.67,
  };

  return (
    <Box p={6}>
      <VStack spacing={8} align="stretch">
        {/* 标题 */}
        <Box>
          <Heading size="xl" mb={2}>
            基金中心
          </Heading>
          <Text color="gray.500">
            全面的基金数据，专业的分析工具，助您做出明智的投资决策
          </Text>
        </Box>

        {/* 市场概览 */}
        <Card>
          <CardBody>
            <Heading size="md" mb={4}>市场概览</Heading>
            <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={4}>
              <Stat>
                <StatLabel>基金总数</StatLabel>
                <StatNumber fontSize="2xl">{marketOverview.totalFunds}</StatNumber>
                <StatHelpText>只</StatHelpText>
              </Stat>
              
              <Stat>
                <StatLabel>上涨基金</StatLabel>
                <StatNumber fontSize="2xl" color="red.500">
                  <HStack>
                    <FiTrendingUp />
                    <span>{marketOverview.riseCount}</span>
                  </HStack>
                </StatNumber>
                <StatHelpText>只</StatHelpText>
              </Stat>
              
              <Stat>
                <StatLabel>下跌基金</StatLabel>
                <StatNumber fontSize="2xl" color="green.500">
                  <HStack>
                    <FiTrendingDown />
                    <span>{marketOverview.fallCount}</span>
                  </HStack>
                </StatNumber>
                <StatHelpText>只</StatHelpText>
              </Stat>
              
              <Stat>
                <StatLabel>平均收益</StatLabel>
                <StatNumber fontSize="2xl" color="red.500">
                  {marketOverview.avgReturn.toFixed(2)}%
                </StatNumber>
              </Stat>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* 功能入口 */}
        <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={4}>
          <Card
            _hover={{ bg: cardHoverBg }}
            cursor="pointer"
            onClick={() => navigate('/fund/ranking')}
          >
            <CardBody textAlign="center">
              <VStack spacing={3}>
                <StarIcon w={12} h={12} color="yellow.500" />
                <Heading size="sm">基金排行榜</Heading>
                <Text color="gray.500" fontSize="sm">
                  按收益、规模、同类排名查看基金排行
                </Text>
                <Button colorScheme="blue" size="sm">进入</Button>
              </VStack>
            </CardBody>
          </Card>
          
          <Card
            _hover={{ bg: cardHoverBg }}
            cursor="pointer"
            onClick={() => navigate('/fund/hot-sectors')}
          >
            <CardBody textAlign="center">
              <VStack spacing={3}>
                <FiDollarSign size={48} color="green.500" />
                <Heading size="sm">热门板块</Heading>
                <Text color="gray.500" fontSize="sm">
                  追踪市场热门板块，把握投资热点
                </Text>
                <Button colorScheme="blue" size="sm">进入</Button>
              </VStack>
            </CardBody>
          </Card>
          
          <Card
            _hover={{ bg: cardHoverBg }}
            cursor="pointer"
            onClick={() => navigate('/fund/recommended')}
          >
            <CardBody textAlign="center">
              <VStack spacing={3}>
                <FiHeart size={48} color="blue.500" />
                <Heading size="sm">基金优选</Heading>
                <Text color="gray.500" fontSize="sm">
                  专业投研团队精选优质基金
                </Text>
                <Button colorScheme="blue" size="sm">进入</Button>
              </VStack>
            </CardBody>
          </Card>
          
          <Card
            _hover={{ bg: cardHoverBg }}
            cursor="pointer"
            onClick={() => navigate('/watchlist')}
          >
            <CardBody textAlign="center">
              <VStack spacing={3}>
                <FiBarChart size={48} color="purple.500" />
                <Heading size="sm">我的自选</Heading>
                <Text color="gray.500" fontSize="sm">
                  管理您的自选基金，实时跟踪行情
                </Text>
                <Button colorScheme="blue" size="sm">进入</Button>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* 投资小贴士 */}
        <Card>
          <CardBody>
            <Heading size="md" mb={4}>投资小贴士</Heading>
            <VStack align="stretch" spacing={3}>
              <Box>
                <Text as="span" fontWeight="bold">💡 分散投资：</Text>
                <Text as="span">不要把所有资金投入到单只基金，分散投资可以降低风险。</Text>
              </Box>
              <Box>
                <Text as="span" fontWeight="bold">📈 长期持有：</Text>
                <Text as="span">基金投资适合长期持有，短期波动不必过于担心。</Text>
              </Box>
              <Box>
                <Text as="span" fontWeight="bold">🎯 定投策略：</Text>
                <Text as="span">定期定额投资可以平摊成本，降低择时风险。</Text>
              </Box>
              <Box>
                <Text as="span" fontWeight="bold">📊 关注业绩：</Text>
                <Text as="span">关注基金的长期业绩，而不仅仅是短期表现。</Text>
              </Box>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
};

export default FundHome;
