/**
 * 虚拟列表组件 - 用于优化长列表性能
 * 
 * 使用方式：
 * 1. 安装依赖：npm install @tanstack/react-virtual
 * 2. 导入组件：import { VirtualList } from './components/VirtualList'
 * 3. 使用示例：
 *    <VirtualList
 *      data={stockList}
 *      height={600}
 *      itemHeight={50}
 *      renderItem={(item, index) => <StockItem key={item.code} stock={item} />}
 *    />
 */

import React, { useRef, useMemo } from 'react'
import { Box, Flex, Text } from '@chakra-ui/react'
import { useVirtualizer } from '@tanstack/react-virtual'

interface VirtualListProps<T> {
  /** 数据数组 */
  data: T[]
  /** 列表容器高度 (px) */
  height?: number
  /** 每个项目的高度 (px) */
  itemHeight?: number
  /** 渲染单个项目的函数 */
  renderItem: (item: T, index: number) => React.ReactNode
  /** 空数据时的提示文字 */
  emptyText?: string
  /** 加载状态 */
  isLoading?: boolean
  /** 自定义加载组件 */
  loadingComponent?: React.ReactNode
  /** 额外的类名 */
  className?: string
}

export function VirtualList<T>({
  data,
  height = 500,
  itemHeight = 50,
  renderItem,
  emptyText = '暂无数据',
  isLoading = false,
  loadingComponent,
  className = '',
}: VirtualListProps<T>) {
  // 父元素引用
  const parentRef = useRef<HTMLDivElement>(null)

  // 虚拟列表实例
  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan: 5, // 预渲染前后各 5 个项目
  })

  const virtualItems = useMemo(() => virtualizer.getVirtualItems(), [virtualizer])

  // 空数据状态
  if (!isLoading && data.length === 0) {
    return (
      <Flex
        justify="center"
        align="center"
        h={height}
        w="100%"
        bg="gray.50"
        borderRadius="md"
      >
        <Text color="gray.500" fontSize="md">
          {emptyText}
        </Text>
      </Flex>
    )
  }

  // 加载状态
  if (isLoading) {
    return loadingComponent || (
      <Flex
        justify="center"
        align="center"
        h={height}
        w="100%"
        bg="gray.50"
        borderRadius="md"
      >
        <Text color="gray.500" fontSize="md">
          加载中...
        </Text>
      </Flex>
    )
  }

  return (
    <Box
      ref={parentRef}
      className={className}
      h={height}
      w="100%"
      overflow="auto"
      position="relative"
      css={{
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          width: '6px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: '#cbd5e0',
          borderRadius: '24px',
        },
      }}
    >
      {/* 占位元素，保持滚动条高度 */}
      <Box
        h={`${virtualizer.getTotalSize()}px`}
        w="100%"
        position="relative"
      >
        {/* 可见区域的项目 */}
        {virtualItems.map((virtualRow) => (
          <Box
            key={virtualRow.key}
            position="absolute"
            top={0}
            left={0}
            w="100%"
            transform={`translateY(${virtualRow.start}px)`}
          >
            {renderItem(data[virtualRow.index], virtualRow.index)}
          </Box>
        ))}
      </Box>
    </Box>
  )
}

/**
 * 表格形式的虚拟列表
 */
interface VirtualTableProps<T> {
  /** 数据数组 */
  data: T[]
  /** 表格列定义 */
  columns: Array<{
    key: string
    title: string
    width?: string | number
    render?: (item: T, index: number) => React.ReactNode
  }>
  /** 表格容器高度 (px) */
  height?: number
  /** 每行高度 (px) */
  rowHeight?: number
  /** 空数据提示 */
  emptyText?: string
  /** 加载状态 */
  isLoading?: boolean
}

export function VirtualTable<T>({
  data,
  columns,
  height = 500,
  rowHeight = 40,
  emptyText = '暂无数据',
  isLoading = false,
}: VirtualTableProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan: 5,
  })

  const virtualItems = useMemo(() => virtualizer.getVirtualItems(), [virtualizer])

  if (!isLoading && data.length === 0) {
    return (
      <Flex
        justify="center"
        align="center"
        h={height}
        w="100%"
        bg="gray.50"
        borderRadius="md"
      >
        <Text color="gray.500" fontSize="md">
          {emptyText}
        </Text>
      </Flex>
    )
  }

  if (isLoading) {
    return (
      <Flex
        justify="center"
        align="center"
        h={height}
        w="100%"
        bg="gray.50"
        borderRadius="md"
      >
        <Text color="gray.500" fontSize="md">
          加载中...
        </Text>
      </Flex>
    )
  }

  return (
    <Box
      ref={parentRef}
      h={height}
      w="100%"
      overflow="auto"
      position="relative"
      border="1px solid"
      borderColor="gray.200"
      borderRadius="md"
    >
      {/* 表头 */}
      <Flex
        h={`${rowHeight}px`}
        bg="gray.50"
        borderBottom="1px solid"
        borderColor="gray.200"
        fontWeight="bold"
        position="sticky"
        top={0}
        zIndex={1}
      >
        {columns.map((column) => (
          <Box
            key={column.key}
            px={3}
            display="flex"
            alignItems="center"
            w={column.width || 'auto'}
            flex={column.width ? undefined : 1}
            minW={column.width ? undefined : '100px'}
          >
            {column.title}
          </Box>
        ))}
      </Flex>

      {/* 表格内容 */}
      <Box h={`${virtualizer.getTotalSize()}px`} w="100%" position="relative">
        {virtualItems.map((virtualRow) => (
          <Flex
            key={virtualRow.key}
            h={`${rowHeight}px`}
            position="absolute"
            top={0}
            left={0}
            w="100%"
            transform={`translateY(${virtualRow.start}px)`}
            borderBottom="1px solid"
            borderColor="gray.100"
            _hover={{ bg: 'gray.50' }}
          >
            {columns.map((column) => (
              <Box
                key={column.key}
                px={3}
                display="flex"
                alignItems="center"
                w={column.width || 'auto'}
                flex={column.width ? undefined : 1}
                minW={column.width ? undefined : '100px'}
              >
                {column.render
                  ? column.render(data[virtualRow.index], virtualRow.index)
                  : String((data[virtualRow.index] as any)[column.key])}
              </Box>
            ))}
          </Flex>
        ))}
      </Box>
    </Box>
  )
}

export default VirtualList
