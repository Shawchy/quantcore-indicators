import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
  type PaginationState,
} from '@tanstack/react-table'
import { useState } from 'react'
import { Box, HStack, IconButton, Input, NativeSelect, Table, Text } from '@chakra-ui/react'
import { useColorModeValue } from './ui/color-mode'
import { FiArrowUp, FiArrowDown } from 'react-icons/fi'

interface ColumnMeta {
  isNumeric?: boolean
}

interface DataTableProps<TData> {
  columns: ColumnDef<TData, unknown>[]
  data: TData[]
  pageSize?: number
  showPagination?: boolean
  showGlobalFilter?: boolean
  height?: string
}

function DataTable<TData>({
  columns,
  data,
  pageSize = 20,
  showPagination = true,
  showGlobalFilter = false,
  height,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize,
  })

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnFilters, globalFilter, pagination },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  })

  const hoverBg = useColorModeValue('gray.50', 'gray.700')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const headerBg = useColorModeValue('gray.50', 'gray.800')
  const textColor = useColorModeValue('gray.700', 'gray.200')
  const mutedColor = useColorModeValue('gray.500', 'gray.400')

  return (
    <Box>
      {showGlobalFilter && (
        <Box p={3}>
          <Input
            placeholder="全局搜索..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            size="sm"
            maxW="300px"
            borderRadius="md"
          />
        </Box>
      )}

      <Box overflowY={height ? 'auto' : undefined} maxH={height}>
        <Table.Root size="sm" >
          <Table.Header bg={headerBg} position="sticky" top={0} zIndex={1}>
            {table.getHeaderGroups().map((headerGroup) => (
              <Table.Row key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const meta = header.column.columnDef.meta as ColumnMeta | undefined
                  const isNumeric = meta?.isNumeric ?? false
                  return (
                    <Table.ColumnHeader
                      key={header.id}
                      cursor={header.column.getCanSort() ? 'pointer' : undefined}
                      onClick={header.column.getToggleSortingHandler()}
                      color={textColor}
                      fontSize="xs"
                      py={2}
                      textAlign={isNumeric ? 'right' : 'left'}
                    >
                      <HStack gap={1} justify={isNumeric ? 'flex-end' : 'flex-start'}>
                        <Text as="span" fontWeight="600">
                          {flexRender(header.column.columnDef.header, header.getContext())}
                        </Text>
                        {header.column.getIsSorted() === 'asc' && <FiArrowUp size={12} />}
                        {header.column.getIsSorted() === 'desc' && <FiArrowDown size={12} />}
                      </HStack>
                    </Table.ColumnHeader>
                  )
                })}
              </Table.Row>
            ))}
          </Table.Header>
          <Table.Body>
            {table.getRowModel().rows.map((row) => (
              <Table.Row key={row.id} _hover={{ bg: hoverBg }} borderColor={borderColor}>
                {row.getVisibleCells().map((cell) => {
                  const meta = cell.column.columnDef.meta as ColumnMeta | undefined
                  const isNumeric = meta?.isNumeric ?? false
                  return (
                    <Table.Cell
                      key={cell.id}
                      color={textColor}
                      fontSize="sm"
                      py={2}
                      textAlign={isNumeric ? 'right' : 'left'}
                      fontFamily={isNumeric ? 'mono' : undefined}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </Table.Cell>
                  )
                })}
              </Table.Row>
            ))}
            {table.getRowModel().rows.length === 0 && (
              <Table.Row>
                <Table.Cell colSpan={columns.length} textAlign="center" color={mutedColor} py={8}>
                  暂无数据
                </Table.Cell>
              </Table.Row>
            )}
          </Table.Body>
        </Table.Root>
      </Box>

      {showPagination && table.getPageCount() > 1 && (
        <HStack
          gap={1}
          justify="center"
          py={3}
          borderTop="1px solid"
          borderColor={borderColor}
        >
          <IconButton
            size="sm"
            variant="ghost"
            aria-label="首页"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          />
          <IconButton
            size="sm"
            variant="ghost"
            aria-label="上一页"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          />

          <Text fontSize="sm" color={mutedColor} px={2} minW="80px" textAlign="center">
            {table.getState().pagination.pageIndex + 1} / {table.getPageCount()}
          </Text>

          <IconButton
            size="sm"
            variant="ghost"
            aria-label="下一页"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          />
          <IconButton
            size="sm"
            variant="ghost"
            aria-label="末页"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
          />

          <NativeSelect.Root size="sm" w="70px" ml={4}>
            <NativeSelect.Field
              borderRadius="md"
              value={table.getState().pagination.pageSize}
              onChange={(e) => table.setPageSize(Number(e.target.value))}
            >
              {[10, 20, 30, 50].map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </NativeSelect.Field>
          </NativeSelect.Root>
        </HStack>
      )}
    </Box>
  )
}

export default DataTable
export type { ColumnDef, ColumnMeta }
