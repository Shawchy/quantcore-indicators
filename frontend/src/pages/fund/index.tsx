/**
 * 基金首页
 * 
 * 基金模块的入口页面，展示基金市场概览
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Card, HStack, Heading, SimpleGrid, Stat, Text, VStack } from '@chakra-ui/react'
import { useColorModeValue } from '../../components/ui/color-mode'
import { FiStar } from 'react-icons/fi'
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
      <VStack gap={8} align="stretch">
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
        <Card.Root>
          <Card.Body>
            <Heading size="md" mb={4}>市场概览</Heading>
            <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} gap={4}>
              <Stat.Root>
                <Stat.Label>基金总数</Stat.Label>
                <Stat.ValueText fontSize="2xl">{marketOverview.totalFunds}</Stat.ValueText>
                <Stat.HelpText>只</Stat.HelpText>
              </Stat.Root>
              
              <Stat.Root>
                <Stat.Label>上涨基金</Stat.Label>
                <Stat.ValueText fontSize="2xl" color="red.500">
                  <HStack>
                    <FiTrendingUp />
                    <span>{marketOverview.riseCount}</span>
                  </HStack>
                </Stat.ValueText>
                <Stat.HelpText>只</Stat.HelpText>
              </Stat.Root>
              
              <Stat.Root>
                <Stat.Label>下跌基金</Stat.Label>
                <Stat.ValueText fontSize="2xl" color="green.500">
                  <HStack>
                    <FiTrendingDown />
                    <span>{marketOverview.fallCount}</span>
                  </HStack>
                </Stat.ValueText>
                <Stat.HelpText>只</Stat.HelpText>
              </Stat.Root>
              
              <Stat.Root>
                <Stat.Label>平均收益</Stat.Label>
                <Stat.ValueText fontSize="2xl" color="red.500">
                  {marketOverview.avgReturn.toFixed(2)}%
                </Stat.ValueText>
              </Stat.Root>
            </SimpleGrid>
          </Card.Body>
        </Card.Root>

        {/* 功能入口 */}
        <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} gap={4}>
          <Card.Root
            _hover={{ bg: cardHoverBg }}
            cursor="pointer"
            onClick={() => navigate('/fund/ranking')}
          >
            <Card.Body textAlign="center">
              <VStack gap={3}>
                <FiStar color="yellow.500" />
                <Heading size="sm">基金排行榜</Heading>
                <Text color="gray.500" fontSize="sm">
                  按收益、规模、同类排名查看基金排行
                </Text>
                <Button colorPalette="blue" size="sm">进入</Button>
              </VStack>
            </Card.Body>
          </Card.Root>
          
          <Card.Root
            _hover={{ bg: cardHoverBg }}
            cursor="pointer"
            onClick={() => navigate('/fund/hot-sectors')}
          >
            <Card.Body textAlign="center">
              <VStack gap={3}>
                <FiDollarSign size={48} color="green.500" />
                <Heading size="sm">热门板块</Heading>
                <Text color="gray.500" fontSize="sm">
                  追踪市场热门板块，把握投资热点
                </Text>
                <Button colorPalette="blue" size="sm">进入</Button>
              </VStack>
            </Card.Body>
          </Card.Root>
          
          <Card.Root
            _hover={{ bg: cardHoverBg }}
            cursor="pointer"
            onClick={() => navigate('/fund/recommended')}
          >
            <Card.Body textAlign="center">
              <VStack gap={3}>
                <FiHeart size={48} color="blue.500" />
                <Heading size="sm">基金优选</Heading>
                <Text color="gray.500" fontSize="sm">
                  专业投研团队精选优质基金
                </Text>
                <Button colorPalette="blue" size="sm">进入</Button>
              </VStack>
            </Card.Body>
          </Card.Root>
          
          <Card.Root
            _hover={{ bg: cardHoverBg }}
            cursor="pointer"
            onClick={() => navigate('/watchlist')}
          >
            <Card.Body textAlign="center">
              <VStack gap={3}>
                <FiBarChart size={48} color="purple.500" />
                <Heading size="sm">我的自选</Heading>
                <Text color="gray.500" fontSize="sm">
                  管理您的自选基金，实时跟踪行情
                </Text>
                <Button colorPalette="blue" size="sm">进入</Button>
              </VStack>
            </Card.Body>
          </Card.Root>
        </SimpleGrid>

        {/* 投资小贴士 */}
        <Card.Root>
          <Card.Body>
            <Heading size="md" mb={4}>投资小贴士</Heading>
            <VStack align="stretch" gap={3}>
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
          </Card.Body>
        </Card.Root>
      </VStack>
    </Box>
  );
};

export default FundHome;
