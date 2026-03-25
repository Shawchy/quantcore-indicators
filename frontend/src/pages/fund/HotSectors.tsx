/**
 * 热门板块页面
 * 
 * 展示涨幅领先、资金流入、估值低位等热门板块
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardBody,
  Heading,
  Text,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Badge,
  HStack,
  VStack,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react';
import {
  FiTrendingUp,
  FiDollarSign,
  FiBarChart,
} from 'react-icons/fi';

interface SectorInfo {
  key: string;
  name: string;
  change_pct: number;
  fund_count: number;
  avg_scale: number;
  top_funds: Array<{ code: string; name: string; return_rate: number }>;
}

const HotSectors: React.FC = () => {
  const [loading, setLoading] = useState(false);

  // 模拟数据（实际应从 API 获取）
  const riseLeadingSectors: SectorInfo[] = [
    {
      key: '1',
      name: '白酒',
      change_pct: 5.67,
      fund_count: 45,
      avg_scale: 125.5,
      top_funds: [
        { code: '161725', name: '招商中证白酒', return_rate: 6.45 },
        { code: '005827', name: '易方达蓝筹精选', return_rate: 5.89 },
      ],
    },
    {
      key: '2',
      name: '新能源',
      change_pct: 4.32,
      fund_count: 78,
      avg_scale: 98.3,
      top_funds: [
        { code: '005918', name: '天弘中证 500', return_rate: 5.12 },
      ],
    },
    {
      key: '3',
      name: '医药',
      change_pct: 3.21,
      fund_count: 92,
      avg_scale: 67.8,
      top_funds: [],
    },
  ];

  const capitalInflowSectors: SectorInfo[] = [
    {
      key: '1',
      name: '科技',
      change_pct: 2.15,
      fund_count: 156,
      avg_scale: 234.5,
      top_funds: [],
    },
    {
      key: '2',
      name: '消费',
      change_pct: 1.87,
      fund_count: 123,
      avg_scale: 189.2,
      top_funds: [],
    },
  ];

  const lowValuationSectors: SectorInfo[] = [
    {
      key: '1',
      name: '银行',
      change_pct: -0.45,
      fund_count: 34,
      avg_scale: 456.7,
      top_funds: [],
    },
    {
      key: '2',
      name: '地产',
      change_pct: -1.23,
      fund_count: 28,
      avg_scale: 234.1,
      top_funds: [],
    },
  ];

  // 获取涨跌幅颜色
  const getReturnColor = (value: number) => {
    if (value > 0) return 'red.500';
    if (value < 0) return 'green.500';
    return 'blue.500';
  };

  // 获取涨跌幅文本
  const getReturnText = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // 板块表格列
  const renderSectorTable = (sectors: SectorInfo[]) => (
    <TableContainer>
      <Table variant="simple" size="sm">
        <Thead>
          <Tr>
            <Th w="150px">板块名称</Th>
            <Th w="120px" isNumeric>涨跌幅</Th>
            <Th w="100px" isNumeric>基金数量</Th>
            <Th w="120px" isNumeric>平均规模 (亿)</Th>
            <Th>代表基金</Th>
          </Tr>
        </Thead>
        <Tbody>
          {sectors.map((sector) => (
            <Tr key={sector.key}>
              <Td>
                <Text fontWeight="bold">{sector.name}</Text>
              </Td>
              <Td>
                <Text fontWeight="bold" color={getReturnColor(sector.change_pct)}>
                  {getReturnText(sector.change_pct)}
                </Text>
              </Td>
              <Td isNumeric>{sector.fund_count}只</Td>
              <Td isNumeric>{sector.avg_scale.toFixed(2)}</Td>
              <Td>
                <VStack align="start" spacing={2}>
                  {sector.top_funds.slice(0, 2).map((fund, idx) => (
                    <HStack key={idx} wrap="wrap">
                      <Badge colorScheme="blue" fontSize="xs">{fund.code}</Badge>
                      <Text fontSize="sm">{fund.name}</Text>
                      <Text fontSize="sm" fontWeight="bold" color={getReturnColor(fund.return_rate)}>
                        {getReturnText(fund.return_rate)}
                      </Text>
                    </HStack>
                  ))}
                </VStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  );

  return (
    <Box p={6}>
      <VStack spacing={8} align="stretch">
        {/* 标题 */}
        <Box>
          <Heading size="xl" mb={2}>
            热门板块
          </Heading>
          <Text color="gray.500">
            追踪市场热门板块，把握投资热点
          </Text>
        </Box>

        {/* Tab 切换 */}
        <Tabs variant="enclosed">
          <TabList>
            <Tab>
              <HStack>
                <FiTrendingUp size={20} />
                <span>涨幅领先</span>
              </HStack>
            </Tab>
            <Tab>
              <HStack>
                <FiDollarSign size={20} />
                <span>资金流入</span>
              </HStack>
            </Tab>
            <Tab>
              <HStack>
                <FiBarChart size={20} />
                <span>估值低位</span>
              </HStack>
            </Tab>
          </TabList>
          <TabPanels>
            {/* 涨幅领先 */}
            <TabPanel>
              <Card>
                <CardBody>
                  <Alert status="success" mb={4} borderRadius="md">
                    <AlertIcon />
                    <AlertTitle mr={2}>涨幅领先板块</AlertTitle>
                    <AlertDescription>
                      展示近期涨幅最大的行业板块
                    </AlertDescription>
                  </Alert>
                  {renderSectorTable(riseLeadingSectors)}
                </CardBody>
              </Card>
            </TabPanel>

            {/* 资金流入 */}
            <TabPanel>
              <Card>
                <CardBody>
                  <Alert status="info" mb={4} borderRadius="md">
                    <AlertIcon />
                    <AlertTitle mr={2}>资金流入板块</AlertTitle>
                    <AlertDescription>
                      展示主力资金净流入的行业板块
                    </AlertDescription>
                  </Alert>
                  {renderSectorTable(capitalInflowSectors)}
                </CardBody>
              </Card>
            </TabPanel>

            {/* 估值低位 */}
            <TabPanel>
              <Card>
                <CardBody>
                  <Alert status="warning" mb={4} borderRadius="md">
                    <AlertIcon />
                    <AlertTitle mr={2}>估值低位板块</AlertTitle>
                    <AlertDescription>
                      展示估值处于历史低位的行业板块
                    </AlertDescription>
                  </Alert>
                  {renderSectorTable(lowValuationSectors)}
                </CardBody>
              </Card>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
};

export default HotSectors;
