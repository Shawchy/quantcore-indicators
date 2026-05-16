/**
 * 东方财富个股研报和公告页面
 */
import React, { useState, useEffect } from 'react';
import { Badge, Box, Button, Center, Flex, Heading, Input, InputGroup, Link, NativeSelect, Spinner, Table, Tabs, Text } from '@chakra-ui/react'
import { toaster } from '../components/ui/toaster'
import {
  eastMoneyApi,
  type StockResearchReport,
  type StockNotice,
} from '@/services/akshare/index';
import { FiExternalLink } from 'react-icons/fi'

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
  const [, setActiveTab] = useState("个股研报");
  const [loading, setLoading] = useState(false);
  
  // 研报相关状态
  const [researchCode, setResearchCode] = useState('');
  const [researchReports, setResearchReports] = useState<StockResearchReport[]>([]);
  
  // 公告相关状态
  const [noticeType, setNoticeType] = useState('全部');
  const [noticeDate, setNoticeDate] = useState(new Date().toISOString().split('T')[0].replace(/-/g, ''));
  const [notices, setNotices] = useState<StockNotice[]>([]);
  
  ;

  // 获取个股研报
  const fetchResearchReports = async (code: string) => {
    if (!code) {
      toaster.create({
        title: '请输入股票代码',
        type: 'warning',
        duration: 2000,
        closable: true,
      });
      return;
    }
    
    setLoading(true);
    try {
      const result = await eastMoneyApi.getStockResearchReport(code);
      setResearchReports(result.data || []);
      toaster.create({
        title: `获取成功，共${result.data?.length || 0}条研报`,
        type: 'success',
        duration: 2000,
        closable: true,
      });
    } catch (error) {
      console.error('获取个股研报失败:', error);
      toaster.create({
        title: '获取研报失败',
        type: 'error',
        duration: 2000,
        closable: true,
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
      setNotices(result.data || []);
      toaster.create({
        title: `获取成功，共${result.data?.length || 0}条公告`,
        type: 'success',
        duration: 2000,
        closable: true,
      });
    } catch (error) {
      console.error('获取公告失败:', error);
      toaster.create({
        title: '获取公告失败',
        type: 'error',
        duration: 2000,
        closable: true,
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

      <Tabs.Root onValueChange={(e) => setActiveTab(e.value)} colorPalette="blue">
        <Tabs.List>
          <Tabs.Trigger value="个股研报">个股研报</Tabs.Trigger>
          <Tabs.Trigger value="沪深京公告">沪深京公告</Tabs.Trigger>
        </Tabs.List>

        <Tabs.ContentGroup>
          {/* 个股研报 */}
          <Tabs.Content value="沪深京公告">
            <Flex gap={4} mb={6} align="center">
              <InputGroup width="400px" startAddon="股票代码">
  <Input
                  value={researchCode}
                  onChange={(e) => setResearchCode(e.target.value)}
                  placeholder="输入股票代码，如：000001"
                  onKeyPress={(e) => e.key === 'Enter' && handleResearchSearch()}
                />
</InputGroup>
              <Button onClick={handleResearchSearch} colorPalette="blue" loading={loading}>
                查询
              </Button>
            </Flex>

            {loading && researchReports.length === 0 ? (
              <Center h="400px">
                <Spinner size="xl" />
              </Center>
            ) : (
              <Box overflowX="auto">
                <Table.Root  size="sm">
                  <Table.Header>
                    <Table.Row>
                      <Table.ColumnHeader>序号</Table.ColumnHeader>
                      <Table.ColumnHeader>代码</Table.ColumnHeader>
                      <Table.ColumnHeader>名称</Table.ColumnHeader>
                      <Table.ColumnHeader>报告名称</Table.ColumnHeader>
                      <Table.ColumnHeader>评级</Table.ColumnHeader>
                      <Table.ColumnHeader>机构</Table.ColumnHeader>
                      <Table.ColumnHeader>近一月研报数</Table.ColumnHeader>
                      <Table.ColumnHeader>行业</Table.ColumnHeader>
                      <Table.ColumnHeader>日期</Table.ColumnHeader>
                      <Table.ColumnHeader>操作</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {researchReports.map((report) => (
                      <Table.Row key={report.serial_no}>
                        <Table.Cell>{report.serial_no}</Table.Cell>
                        <Table.Cell>
                          <Text fontWeight="bold">{report.stock_code}</Text>
                        </Table.Cell>
                        <Table.Cell>{report.stock_name}</Table.Cell>
                        <Table.Cell maxWidth="300px" truncate title={report.report_name}>
                          {report.report_name}
                        </Table.Cell>
                        <Table.Cell>
                          <Badge colorPalette={
                            report.rating.includes('买入') ? 'green' :
                            report.rating.includes('增持') ? 'blue' :
                            'gray'
                          }>
                            {report.rating}
                          </Badge>
                        </Table.Cell>
                        <Table.Cell>{report.institution}</Table.Cell>
                        <Table.Cell>{report.recent_report_count}</Table.Cell>
                        <Table.Cell>
                          <Badge colorPalette="green">{report.industry}</Badge>
                        </Table.Cell>
                        <Table.Cell>{report.report_date}</Table.Cell>
                        <Table.Cell>
                          <Link
                            href={report.report_pdf_url} target="_blank" rel="noopener noreferrer" color="blue.500"
                          >
                            查看 <FiExternalLink />
                          </Link>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
                {researchReports.length === 0 && !loading && (
                  <Center h="200px">
                    <Text color="gray.500">请输入股票代码查询研报</Text>
                  </Center>
                )}
              </Box>
            )}
          </Tabs.Content>

          {/* 沪深京公告 */}
          <Tabs.Content value="个股研报">
            <Flex gap={4} mb={6} align="center">
              <InputGroup width="200px" startAddon="公告类型">
                <NativeSelect.Root><NativeSelect.Field
                  value={noticeType}
                  onChange={(e) => setNoticeType(e.target.value)}
                >
                  {noticeTypes.map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </NativeSelect.Field></NativeSelect.Root>
              </InputGroup>
              
              <InputGroup width="200px" startAddon="公告日期">
                <Input
                  type="date"
                  value={noticeDate.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}
                  onChange={(e) => setNoticeDate(e.target.value.replace(/-/g, ''))}
                />
              </InputGroup>
              
              <Button onClick={handleNoticeSearch} colorPalette="green" loading={loading}>
                查询
              </Button>
            </Flex>

            {loading && notices.length === 0 ? (
              <Center h="400px">
                <Spinner size="xl" />
              </Center>
            ) : (
              <Box overflowX="auto">
                <Table.Root  size="sm">
                  <Table.Header>
                    <Table.Row>
                      <Table.ColumnHeader>代码</Table.ColumnHeader>
                      <Table.ColumnHeader>名称</Table.ColumnHeader>
                      <Table.ColumnHeader>公告标题</Table.ColumnHeader>
                      <Table.ColumnHeader>公告类型</Table.ColumnHeader>
                      <Table.ColumnHeader>公告日期</Table.ColumnHeader>
                      <Table.ColumnHeader>操作</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {notices.map((notice, index) => (
                      <Table.Row key={`${notice.code}-${index}`}>
                        <Table.Cell>
                          <Text fontWeight="bold">{notice.code}</Text>
                        </Table.Cell>
                        <Table.Cell>{notice.name}</Table.Cell>
                        <Table.Cell maxWidth="500px" truncate title={notice.notice_title}>
                          {notice.notice_title}
                        </Table.Cell>
                        <Table.Cell>
                          <Badge colorPalette="blue">{notice.notice_type}</Badge>
                        </Table.Cell>
                        <Table.Cell>{notice.notice_date}</Table.Cell>
                        <Table.Cell>
                          <Link
                            href={notice.url} target="_blank" rel="noopener noreferrer" color="blue.500"
                          >
                            查看 <FiExternalLink />
                          </Link>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
                {notices.length === 0 && !loading && (
                  <Center h="200px">
                    <Text color="gray.500">暂无公告数据</Text>
                  </Center>
                )}
              </Box>
            )}
          </Tabs.Content>
        </Tabs.ContentGroup>
      </Tabs.Root>
    </Box>
  );
};

export default EastMoneyResearchNoticePage;
