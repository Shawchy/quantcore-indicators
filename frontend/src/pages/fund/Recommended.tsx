/**
 * 基金优选页面
 * 
 * 展示精选优质基金推荐
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Card, HStack, Heading, Icon, SimpleGrid, Tabs, Text, VStack } from '@chakra-ui/react'
import { useColorModeValue } from '../../components/ui/color-mode'
import { FiAlertTriangle, FiCheckCircle, FiInfo, FiStar } from 'react-icons/fi'
import FundCard from '@/components/fund/FundCard';
import { FundInfo } from '@/services/fund';

interface RecommendedFund extends FundInfo {
  reason: string;
  rating: number;
  tags: string[];
}

const FundRecommended: React.FC = () => {
  const [starFunds, setStarFunds] = useState<RecommendedFund[]>([])
  const [steadyFunds, setSteadyFunds] = useState<RecommendedFund[]>([])
  const [highElasticFunds, setHighElasticFunds] = useState<RecommendedFund[]>([])
  const [valueFunds, setValueFunds] = useState<RecommendedFund[]>([])
  const cardHoverBg = useColorModeValue('gray.50', 'gray.700')

  // 模拟数据（实际应从 API 获取）
  useEffect(() => {
    // 明星基金
    setStarFunds([
      {
        code: '161725',
        name: '招商中证白酒指数 (LOF)A',
        type: 'index',
        net_asset_value: 2.8856,
        change_pct: 0.64,
        fund_scale: 310.21,
        fund_company: '招商基金',
        reason: '近五年收益 519.44%，同类排名第 1，白酒行业龙头基金',
        rating: 5,
        tags: ['行业龙头', '长期优秀', '高收益'],
      },
      {
        code: '005827',
        name: '易方达蓝筹精选混合',
        type: 'mix',
        net_asset_value: 2.3908,
        change_pct: -0.23,
        fund_scale: 310.21,
        fund_company: '易方达基金',
        reason: '张坤管理，专注蓝筹股投资，长期业绩稳定',
        rating: 5,
        tags: ['明星经理', '蓝筹股', '稳健增长'],
      },
    ]);

    // 稳健增长
    setSteadyFunds([
      {
        code: '000001',
        name: '华夏成长混合',
        type: 'mix',
        net_asset_value: 1.5678,
        change_pct: 0.12,
        fund_scale: 156.78,
        fund_company: '华夏基金',
        reason: '成立 20 余年，穿越多轮牛熊，年化收益 15%+',
        rating: 4,
        tags: ['老牌基金', '稳健', '长期投资'],
      },
    ]);

    // 高弹性
    setHighElasticFunds([
      {
        code: '005918',
        name: '天弘中证 500 指数增强 A',
        type: 'index',
        net_asset_value: 1.8765,
        change_pct: 1.23,
        fund_scale: 98.45,
        fund_company: '天弘基金',
        reason: '中证 500 指数增强，弹性大，适合风险偏好较高的投资者',
        rating: 4,
        tags: ['指数增强', '高弹性', '中小盘'],
      },
    ]);

    // 价值投资
    setValueFunds([
      {
        code: '000002',
        name: '嘉实价值优势混合',
        type: 'mix',
        net_asset_value: 1.3456,
        change_pct: -0.45,
        fund_scale: 234.56,
        fund_company: '嘉实基金',
        reason: '专注低估值价值股，安全边际高，适合长期配置',
        rating: 4,
        tags: ['价值投资', '低估值', '安全边际'],
      },
    ]);
  }, []);

  // 渲染基金卡片
  const renderFundCards = (funds: RecommendedFund[]) => (
    <SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 4 }} gap={4}>
      {funds.map((fund) => (
        <VStack key={fund.code} align="stretch">
          <FundCard
            fund={fund}
            showRank={false}
            showActions={true}
            compact={false}
          />
          <Card.Root
            size="sm"
            borderTopWidth="4px"
            borderTopColor="blue.500"
          >
            <Card.Body>
              <VStack gap={2} align="stretch">
                <HStack>
                  {[...Array(5)].map((_, i) => (
                    <Icon
                      key={i}
                      as={FiStar}
                      color={i < fund.rating ? 'yellow.400' : 'gray.300'}
                      fill={i < fund.rating ? 'yellow.400' : 'none'}
                      w={4}
                      h={4}
                    />
                  ))}
                </HStack>
                <Text fontSize="xs" color="gray.600">
                  {fund.reason}
                </Text>
                <HStack wrap="wrap">
                  {fund.tags.map((tag, idx) => (
                    <Badge key={idx} colorPalette="blue" fontSize="xs">
                      {tag}
                    </Badge>
                  ))}
                </HStack>
              </VStack>
            </Card.Body>
          </Card.Root>
        </VStack>
      ))}
    </SimpleGrid>
  );

  return (
    <Box p={6}>
      <VStack gap={8} align="stretch">
        {/* 标题 */}
        <Box>
          <Heading size="xl" mb={2}>
            基金优选
          </Heading>
          <Text color="gray.500">
            专业投研团队精选优质基金，助您轻松投资
          </Text>
        </Box>

        {/* 分类说明卡片 */}
        <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} gap={4}>
          <Card.Root _hover={{ bg: cardHoverBg }}>
            <Card.Body>
              <VStack gap={2}>
                <HStack>
                  <Icon as={FiAlertTriangle} w={6} h={6} color="yellow.500" />
                  <Heading size="sm">明星基金</Heading>
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  长期业绩优秀，市场公认的优质基金
                </Text>
              </VStack>
            </Card.Body>
          </Card.Root>
          <Card.Root _hover={{ bg: cardHoverBg }}>
            <Card.Body>
              <VStack gap={2}>
                <HStack>
                  <Icon as={FiCheckCircle} w={6} h={6} color="green.500" />
                  <Heading size="sm">稳健增长</Heading>
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  波动小，稳定增长，适合风险偏好较低的投资者
                </Text>
              </VStack>
            </Card.Body>
          </Card.Root>
          <Card.Root _hover={{ bg: cardHoverBg }}>
            <Card.Body>
              <VStack gap={2}>
                <HStack>
                  <Icon as={FiInfo} w={6} h={6} color="blue.500" />
                  <Heading size="sm">高弹性</Heading>
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  高收益、高波动，适合风险偏好较高的投资者
                </Text>
              </VStack>
            </Card.Body>
          </Card.Root>
          <Card.Root _hover={{ bg: cardHoverBg }}>
            <Card.Body>
              <VStack gap={2}>
                <HStack>
                  <Icon as={FiStar} w={6} h={6} color="purple.500" />
                  <Heading size="sm">价值投资</Heading>
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  专注低估值价值股，安全边际高
                </Text>
              </VStack>
            </Card.Body>
          </Card.Root>
        </SimpleGrid>

        {/* Tab 切换 */}
        <Tabs.Root variant="enclosed" defaultValue="star">
          <Tabs.List>
            <Tabs.Trigger value="star">
              <HStack>
                <Icon as={FiAlertTriangle} />
                <span>明星基金</span>
              </HStack>
            </Tabs.Trigger>
            <Tabs.Trigger value="steady">
              <HStack>
                <Icon as={FiCheckCircle} />
                <span>稳健增长</span>
              </HStack>
            </Tabs.Trigger>
            <Tabs.Trigger value="elastic">
              <HStack>
                <Icon as={FiInfo} />
                <span>高弹性</span>
              </HStack>
            </Tabs.Trigger>
            <Tabs.Trigger value="value">
              <HStack>
                <Icon as={FiStar} />
                <span>价值投资</span>
              </HStack>
            </Tabs.Trigger>
          </Tabs.List>
          <Tabs.ContentGroup>
            <Tabs.Content value="star">
              {renderFundCards(starFunds)}
            </Tabs.Content>
            <Tabs.Content value="steady">
              {renderFundCards(steadyFunds)}
            </Tabs.Content>
            <Tabs.Content value="elastic">
              {renderFundCards(highElasticFunds)}
            </Tabs.Content>
            <Tabs.Content value="value">
              {renderFundCards(valueFunds)}
            </Tabs.Content>
          </Tabs.ContentGroup>
        </Tabs.Root>
      </VStack>
    </Box>
  );
};

export default FundRecommended;
