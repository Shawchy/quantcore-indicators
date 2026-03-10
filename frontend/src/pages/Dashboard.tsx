import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Text,
  VStack,
  HStack,
  Badge,
  Spinner,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import ReactECharts from 'echarts-for-react'
import { stockApi, screenerApi, sectorApi } from '../services/api'

const Dashboard = () => {
  const { data: marketStats, isLoading: statsLoading } = useQuery({
    queryKey: ['marketStats'],
    queryFn: () => screenerApi.getMarketStats(),
  })

  const { data: sectorRanking, isLoading: sectorLoading } = useQuery({
    queryKey: ['sectorRanking'],
    queryFn: () => sectorApi.getRanking('industry', 'change_pct', 10),
  })

  const getKlineOption = () => {
    return {
      title: {
        text: 'K线图示例',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['K线', 'MA5', 'MA20'],
        bottom: 0,
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%',
      },
      xAxis: {
        type: 'category',
        data: ['周一', '周二', '周三', '周四', '周五'],
      },
      yAxis: {
        type: 'value',
        scale: true,
      },
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: [
            [2320.26, 2320.26, 2287.3, 2362.94],
            [2300, 2291.3, 2288.26, 2308.38],
            [2295.35, 2346.5, 2295.35, 2346.92],
            [2347.22, 2358.98, 2337.35, 2363.8],
            [2360.75, 2382.48, 2347.89, 2383.76],
          ],
        },
      ],
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      <Heading size="lg">首页概览</Heading>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>市场股票数</Stat>
              <StatNumber>
                {statsLoading ? <Spinner size="sm" /> : marketStats?.data?.total_stocks || 0}
              </StatNumber>
              <StatHelpText>A股市场</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>行业板块数</Stat>
              <StatNumber>--
              </StatNumber>
              <StatHelpText>申万一级行业</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>今日涨跌比</Stat>
              <StatNumber>--</StatNumber>
              <StatHelpText>上涨 / 下跌</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>市场成交额</Stat>
              <StatNumber>--</StatNumber>
              <StatHelpText>亿元</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardHeader>
            <Heading size="sm">板块涨幅排行</Heading>
          </CardHeader>
          <CardBody>
            {sectorLoading ? (
              <Spinner />
            ) : (
              <VStack align="stretch" spacing={2}>
                {sectorRanking?.data?.slice(0, 8).map((sector: any, index: number) => (
                  <HStack key={sector.code} justify="space-between">
                    <HStack>
                      <Text color="gray.500" w="20px">{index + 1}</Text>
                      <Text fontWeight="medium">{sector.name}</Text>
                    </HStack>
                    <Badge
                      colorScheme={sector.change_pct >= 0 ? 'red' : 'green'}
                      variant="subtle"
                    >
                      {sector.change_pct >= 0 ? '+' : ''}
                      {(sector.change_pct || 0).toFixed(2)}%
                    </Badge>
                  </HStack>
                ))}
              </VStack>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <Heading size="sm">K线图表示例</Heading>
          </CardHeader>
          <CardBody>
            <ReactECharts option={getKlineOption()} style={{ height: '300px' }} />
          </CardBody>
        </Card>
      </SimpleGrid>
    </VStack>
  )
}

export default Dashboard
