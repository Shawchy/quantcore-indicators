/**
 * 东方财富千股千评页面
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Flex,
  Text,
  Badge,
  Spinner,
  Center,
  Button,
  Grid,
  Stat,
  StatLabel,
  StatNumber,
  Input,
  InputGroup,
  InputLeftAddon,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  SimpleGrid,
  useDisclosure,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockComment,
  type StockCommentDetailInstitution,
  type StockCommentDetailScore,
} from '../../services/eastmoney';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const EastMoneyStockCommentPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [comments, setComments] = useState<StockComment[]>([]);
  const [searchCode, setSearchCode] = useState('');
  const [selectedStock, setSelectedStock] = useState<StockComment | null>(null);
  const [institutionData, setInstitutionData] = useState<StockCommentDetailInstitution[]>([]);
  const [scoreData, setScoreData] = useState<StockCommentDetailScore[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  
  const { isOpen, onOpen, onClose } = useDisclosure();

  // 获取千股千评数据
  const fetchComments = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockComment();
      setComments(result);
    } catch (error) {
      console.error('获取千股千评数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取个股详情
  const fetchStockDetail = async (code: string) => {
    setDetailLoading(true);
    try {
      const [institutionRes, scoreRes] = await Promise.all([
        eastMoneyApi.getStockCommentDetailInstitution(code),
        eastMoneyApi.getStockCommentDetailScore(code),
      ]);
      setInstitutionData(institutionRes);
      setScoreData(scoreRes);
    } catch (error) {
      console.error('获取个股详情失败:', error);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, []);

  // 刷新数据
  const handleRefresh = () => {
    fetchComments();
  };

  // 查看详情
  const handleViewDetail = (stock: StockComment) => {
    setSelectedStock(stock);
    fetchStockDetail(stock.code);
    onOpen();
  };

  // 搜索股票
  const handleSearch = () => {
    if (!searchCode) {
      fetchComments();
      return;
    }
    const filtered = comments.filter(c => c.code.includes(searchCode) || c.name.includes(searchCode));
    setComments(filtered);
  };

  // 统计数据
  const stats = {
    total: comments.length,
    positive: comments.filter(c => c.change_pct > 0).length,
    negative: comments.filter(c => c.change_pct < 0).length,
    avgScore: comments.length > 0 
      ? comments.reduce((sum, c) => sum + c.comprehensive_score, 0) / comments.length 
      : 0,
  };

  return (
    <Box p={6}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">东方财富千股千评</Heading>
        <Flex gap={4} align="center">
          <InputGroup width="300px">
            <InputLeftAddon>股票代码/名称</InputLeftAddon>
            <Input
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              placeholder="输入股票代码或名称"
            />
          </InputGroup>
          <Button onClick={handleSearch} colorScheme="blue">
            搜索
          </Button>
          <Button onClick={handleRefresh} colorScheme="green" isLoading={loading}>
            刷新
          </Button>
        </Flex>
      </Flex>

      {/* 统计信息 */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
        <Stat>
          <StatLabel>股票总数</StatLabel>
          <StatNumber color="blue.500">{stats.total}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>上涨</StatLabel>
          <StatNumber color="red.500">{stats.positive}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>下跌</StatLabel>
          <StatNumber color="green.500">{stats.negative}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>平均综合得分</StatLabel>
          <StatNumber color="purple.500">{stats.avgScore.toFixed(2)}</StatNumber>
        </Stat>
      </Grid>

      {/* 千股千评表格 */}
      {loading ? (
        <Center h="400px">
          <Spinner size="xl" />
        </Center>
      ) : (
        <Box overflowX="auto">
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>序号</Th>
                <Th>代码</Th>
                <Th>名称</Th>
                <Th>最新价</Th>
                <Th>涨跌幅</Th>
                <Th>换手率</Th>
                <Th>市盈率</Th>
                <Th>主力成本</Th>
                <Th>机构参与度</Th>
                <Th>综合得分</Th>
                <Th>上升</Th>
                <Th>目前排名</Th>
                <Th>关注指数</Th>
                <Th>操作</Th>
              </Tr>
            </Thead>
            <Tbody>
              {comments.map((stock) => (
                <Tr key={stock.serial_no}>
                  <Td>{stock.serial_no}</Td>
                  <Td>
                    <Text fontWeight="bold">{stock.code}</Text>
                  </Td>
                  <Td>{stock.name}</Td>
                  <Td>{stock.latest_price.toFixed(2)}</Td>
                  <Td color={stock.change_pct > 0 ? 'red.500' : 'green.500'}>
                    {stock.change_pct.toFixed(2)}%
                  </Td>
                  <Td>{stock.turnover_rate.toFixed(2)}%</Td>
                  <Td>{stock.pe_ratio.toFixed(2)}</Td>
                  <Td>{stock.main_force_cost.toFixed(2)}</Td>
                  <Td>
                    <Badge colorScheme={stock.institution_participation > 30 ? 'red' : 'blue'}>
                      {stock.institution_participation.toFixed(2)}%
                    </Badge>
                  </Td>
                  <Td>
                    <Badge colorScheme={stock.comprehensive_score > 60 ? 'green' : 'orange'}>
                      {stock.comprehensive_score.toFixed(2)}
                    </Badge>
                  </Td>
                  <Td>
                    <Badge colorScheme={stock.rise > 0 ? 'red' : 'green'}>
                      {stock.rise > 0 ? '+' : ''}{stock.rise}
                    </Badge>
                  </Td>
                  <Td>{stock.current_rank}</Td>
                  <Td>{stock.attention_index.toFixed(1)}</Td>
                  <Td>
                    <Button 
                      size="sm" 
                      colorScheme="blue"
                      onClick={() => handleViewDetail(stock)}
                    >
                      详情
                    </Button>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
          {comments.length === 0 && (
            <Center h="200px">
              <Text color="gray.500">暂无数据</Text>
            </Center>
          )}
        </Box>
      )}

      {/* 详情弹窗 */}
      <Modal isOpen={isOpen} onClose={onClose} size="6xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {selectedStock?.code} - {selectedStock?.name} 详情
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {detailLoading ? (
              <Center h="400px">
                <Spinner size="xl" />
              </Center>
            ) : (
              <Tabs colorScheme="blue">
                <TabList>
                  <Tab>机构参与度</Tab>
                  <Tab>历史评分</Tab>
                </TabList>
                <TabPanels>
                  {/* 机构参与度 */}
                  <TabPanel>
                    <Box h="400px">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={institutionData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="trading_day" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line 
                            type="monotone" 
                            dataKey="institution_participation" 
                            name="机构参与度" 
                            stroke="#8884d8" 
                            activeDot={{ r: 8 }} 
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </TabPanel>

                  {/* 历史评分 */}
                  <TabPanel>
                    <Box h="400px">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={scoreData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="trading_day" />
                          <YAxis domain={[0, 100]} />
                          <Tooltip />
                          <Legend />
                          <Line 
                            type="monotone" 
                            dataKey="score" 
                            name="综合评分" 
                            stroke="#82ca9d" 
                            activeDot={{ r: 8 }} 
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </TabPanel>
                </TabPanels>
              </Tabs>
            )}
          </ModalBody>
          <ModalFooter>
            <Button onClick={onClose}>关闭</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default EastMoneyStockCommentPage;
