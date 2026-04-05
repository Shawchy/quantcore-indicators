/**
 * 基金优选页面
 * 
 * 展示精选优质基金推荐
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardBody,
  Heading,
  Text,
  HStack,
  VStack,
  SimpleGrid,
  Badge,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  StarIcon,
  WarningIcon,
  CheckCircleIcon,
  InfoOutlineIcon,
} from '@chakra-ui/icons';
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
    <SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 4 }} spacing={4}>
      {funds.map((fund) => (
        <VStack key={fund.code} align="stretch">
          <FundCard
            fund={fund}
            showRank={false}
            showActions={true}
            compact={false}
          />
          <Card
            size="sm"
            borderTopWidth="4px"
            borderTopColor="blue.500"
          >
            <CardBody>
              <VStack spacing={2} align="stretch">
                <HStack>
                  {[...Array(5)].map((_, i) => (
                    <Icon
                      key={i}
                      as={StarIcon}
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
                    <Badge key={idx} colorScheme="blue" fontSize="xs">
                      {tag}
                    </Badge>
                  ))}
                </HStack>
              </VStack>
            </CardBody>
          </Card>
        </VStack>
      ))}
    </SimpleGrid>
  );

  return (
    <Box p={6}>
      <VStack spacing={8} align="stretch">
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
        <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={4}>
          <Card _hover={{ bg: cardHoverBg }}>
            <CardBody>
              <VStack spacing={2}>
                <HStack>
                  <Icon as={WarningIcon} w={6} h={6} color="yellow.500" />
                  <Heading size="sm">明星基金</Heading>
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  长期业绩优秀，市场公认的优质基金
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card _hover={{ bg: cardHoverBg }}>
            <CardBody>
              <VStack spacing={2}>
                <HStack>
                  <Icon as={CheckCircleIcon} w={6} h={6} color="green.500" />
                  <Heading size="sm">稳健增长</Heading>
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  波动小，稳定增长，适合风险偏好较低的投资者
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card _hover={{ bg: cardHoverBg }}>
            <CardBody>
              <VStack spacing={2}>
                <HStack>
                  <Icon as={InfoOutlineIcon} w={6} h={6} color="blue.500" />
                  <Heading size="sm">高弹性</Heading>
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  高收益、高波动，适合风险偏好较高的投资者
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card _hover={{ bg: cardHoverBg }}>
            <CardBody>
              <VStack spacing={2}>
                <HStack>
                  <Icon as={StarIcon} w={6} h={6} color="purple.500" />
                  <Heading size="sm">价值投资</Heading>
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  专注低估值价值股，安全边际高
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Tab 切换 */}
        <Tabs variant="enclosed">
          <TabList>
            <Tab>
              <HStack>
                <Icon as={WarningIcon} />
                <span>明星基金</span>
              </HStack>
            </Tab>
            <Tab>
              <HStack>
                <Icon as={CheckCircleIcon} />
                <span>稳健增长</span>
              </HStack>
            </Tab>
            <Tab>
              <HStack>
                <Icon as={InfoOutlineIcon} />
                <span>高弹性</span>
              </HStack>
            </Tab>
            <Tab>
              <HStack>
                <Icon as={StarIcon} />
                <span>价值投资</span>
              </HStack>
            </Tab>
          </TabList>
          <TabPanels>
            <TabPanel>
              {renderFundCards(starFunds)}
            </TabPanel>
            <TabPanel>
              {renderFundCards(steadyFunds)}
            </TabPanel>
            <TabPanel>
              {renderFundCards(highElasticFunds)}
            </TabPanel>
            <TabPanel>
              {renderFundCards(valueFunds)}
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
};

export default FundRecommended;
