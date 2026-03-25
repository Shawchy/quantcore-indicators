/**
 * 东方财富个股研报和公告页面
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
  Input,
  InputGroup,
  InputLeftAddon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Select,
  InputRightAddon,
  Link,
  useToast,
} from '@chakra-ui/react';
import {
  eastMoneyApi,
  type StockResearchReport,
  type StockNotice,
} from '@/services/akshare/index';
import { ExternalLinkIcon } from '@chakra-ui/icons';

const noticeTypes = [
  '全部',
  '重大事项',
  '财务报告',
  '融资公告',
  '风险提示',
  '资产重组',
  '信息变更',
  '持股变动',
];

const EastMoneyResearchNoticePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  
  // 研报相关状态
  const [researchCode, setResearchCode] = useState('');
  const [researchReports, setResearchReports] = useState<StockResearchReport[]>([]);
  
  // 公告相关状态
  const [noticeType, setNoticeType] = useState('全部');
  const [noticeDate, setNoticeDate] = useState(new Date().toISOString().split('T')[0].replace(/-/g, ''));
  const [notices, setNotices] = useState<StockNotice[]>([]);
  
  const toast = useToast();

  // 获取个股研报
  const fetchResearchReports = async (code: string) => {
    if (!code) {
      toast({
        title: '请输入股票代码',
        status: 'warning',
        duration: 2000,
        isClosable: true,
      });
      return;
    }
    
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockResearchReport(code);
      setResearchReports(result);
      toast({
        title: `获取成功，共${result.length}条研报`,
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (error) {
      console.error('获取个股研报失败:', error);
      toast({
        title: '获取研报失败',
        status: 'error',
        duration: 2000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  // 获取公告
  const fetchNotices = async () => {
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockNoticeReport(noticeType, noticeDate);
      setNotices(result);
      toast({
        title: `获取成功，共${result.length}条公告`,
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (error) {
      console.error('获取公告失败:', error);
      toast({
        title: '获取公告失败',
        status: 'error',
        duration: 2000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotices();
  }, []);

  // 处理研报搜索
  const handleResearchSearch = () => {
    fetchResearchReports(researchCode);
  };

  // 处理公告查询
  const handleNoticeSearch = () => {
    fetchNotices();
  };

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>东方财富研究报告与公告</Heading>

      <Tabs onChange={(index) => setActiveTab(index)} colorScheme="blue">
        <TabList>
          <Tab>个股研报</Tab>
          <Tab>沪深京公告</Tab>
        </TabList>

        <TabPanels>
          {/* 个股研报 */}
          <TabPanel>
            <Flex gap={4} mb={6} align="center">
              <InputGroup width="400px">
                <InputLeftAddon>股票代码</InputLeftAddon>
                <Input
                  value={researchCode}
                  onChange={(e) => setResearchCode(e.target.value)}
                  placeholder="输入股票代码，如：000001"
                  onKeyPress={(e) => e.key === 'Enter' && handleResearchSearch()}
                />
              </InputGroup>
              <Button onClick={handleResearchSearch} colorScheme="blue" isLoading={loading}>
                查询
              </Button>
            </Flex>

            {loading && researchReports.length === 0 ? (
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
                      <Th>报告名称</Th>
                      <Th>评级</Th>
                      <Th>机构</Th>
                      <Th>近一月研报数</Th>
                      <Th>行业</Th>
                      <Th>日期</Th>
                      <Th>操作</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {researchReports.map((report) => (
                      <Tr key={report.serial_no}>
                        <Td>{report.serial_no}</Td>
                        <Td>
                          <Text fontWeight="bold">{report.stock_code}</Text>
                        </Td>
                        <Td>{report.stock_name}</Td>
                        <Td maxWidth="300px" isTruncated title={report.report_name}>
                          {report.report_name}
                        </Td>
                        <Td>
                          <Badge colorScheme={
                            report.rating.includes('买入') ? 'green' :
                            report.rating.includes('增持') ? 'blue' :
                            'gray'
                          }>
                            {report.rating}
                          </Badge>
                        </Td>
                        <Td>{report.institution}</Td>
                        <Td>{report.recent_report_count}</Td>
                        <Td>
                          <Badge colorScheme="green">{report.industry}</Badge>
                        </Td>
                        <Td>{report.report_date}</Td>
                        <Td>
                          <Link
                            href={report.report_pdf_url}
                            isExternal
                            color="blue.500"
                          >
                            查看 <ExternalLinkIcon mx="2px" />
                          </Link>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                {researchReports.length === 0 && !loading && (
                  <Center h="200px">
                    <Text color="gray.500">请输入股票代码查询研报</Text>
                  </Center>
                )}
              </Box>
            )}
          </TabPanel>

          {/* 沪深京公告 */}
          <TabPanel>
            <Flex gap={4} mb={6} align="center">
              <InputGroup width="200px">
                <InputLeftAddon>公告类型</InputLeftAddon>
                <Select
                  value={noticeType}
                  onChange={(e) => setNoticeType(e.target.value)}
                >
                  {noticeTypes.map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </Select>
              </InputGroup>
              
              <InputGroup width="200px">
                <InputLeftAddon>公告日期</InputLeftAddon>
                <Input
                  type="date"
                  value={noticeDate.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}
                  onChange={(e) => setNoticeDate(e.target.value.replace(/-/g, ''))}
                />
              </InputGroup>
              
              <Button onClick={handleNoticeSearch} colorScheme="green" isLoading={loading}>
                查询
              </Button>
            </Flex>

            {loading && notices.length === 0 ? (
              <Center h="400px">
                <Spinner size="xl" />
              </Center>
            ) : (
              <Box overflowX="auto">
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>代码</Th>
                      <Th>名称</Th>
                      <Th>公告标题</Th>
                      <Th>公告类型</Th>
                      <Th>公告日期</Th>
                      <Th>操作</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {notices.map((notice, index) => (
                      <Tr key={`${notice.code}-${index}`}>
                        <Td>
                          <Text fontWeight="bold">{notice.code}</Text>
                        </Td>
                        <Td>{notice.name}</Td>
                        <Td maxWidth="500px" isTruncated title={notice.notice_title}>
                          {notice.notice_title}
                        </Td>
                        <Td>
                          <Badge colorScheme="blue">{notice.notice_type}</Badge>
                        </Td>
                        <Td>{notice.notice_date}</Td>
                        <Td>
                          <Link
                            href={notice.url}
                            isExternal
                            color="blue.500"
                          >
                            查看 <ExternalLinkIcon mx="2px" />
                          </Link>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                {notices.length === 0 && !loading && (
                  <Center h="200px">
                    <Text color="gray.500">暂无公告数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default EastMoneyResearchNoticePage;
