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
import { useState, useMemo } from 'react'
import {
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Box,
  Text,
  HStack,
  IconButton,
  Select,
  Input,
  useColorModeValue,
} from '@chakra-ui/react'
import { FiChevronLeft, FiChevronRight, FiChevronsLeft, FiChevronsRight, FiArrowUp, FiArrowDown } from 'react-icons/fi'

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

      <TableContainer overflowY={height ? 'auto' : undefined} maxH={height}>
        <Table size="sm" variant="simple">
          <Thead bg={headerBg} position="sticky" top={0} zIndex={1}>
            {table.getHeaderGroups().map((headerGroup) => (
              <Tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <Th
                    key={header.id}
                    isNumeric={header.column.columnDef.meta?.isNumeric as boolean}
                    cursor={header.column.getCanSort() ? 'pointer' : undefined}
                    onClick={header.column.getToggleSortingHandler()}
                    color={textColor}
                    fontSize="xs"
                    py={2}
                  >
                    <HStack spacing={1} justify={header.column.columnDef.meta?.isNumeric as boolean ? 'flex-end' : 'flex-start'}>
                      <Text as="span" fontWeight="600">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                      </Text>
                      {header.column.getIsSorted() === 'asc' && <FiArrowUp size={12} />}
                      {header.column.getIsSorted() === 'desc' && <FiArrowDown size={12} />}
                    </HStack>
                  </Th>
                ))}
              </Tr>
            ))}
          </Thead>
          <Tbody>
            {table.getRowModel().rows.map((row) => (
              <Tr key={row.id} _hover={{ bg: hoverBg }} borderColor={borderColor}>
                {row.getVisibleCells().map((cell) => (
                  <Td
                    key={cell.id}
                    isNumeric={cell.column.columnDef.meta?.isNumeric as boolean}
                    color={textColor}
                    fontSize="sm"
                    py={2}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </Td>
                ))}
              </Tr>
            ))}
            {table.getRowModel().rows.length === 0 && (
              <Tr>
                <Td colSpan={columns.length} textAlign="center" color={mutedColor} py={8}>
                  暂无数据
                </Td>
              </Tr>
            )}
          </Tbody>
        </Table>
      </TableContainer>

      {showPagination && table.getPageCount() > 1 && (
        <HStack
          spacing={1}
          justify="center"
          py={3}
          borderTop="1px solid"
          borderColor={borderColor}
        >
          <IconButton
            size="xs"
            variant="ghost"
            aria-label="首页"
            icon={<FiChevronsLeft />}
            onClick={() => table.setPageIndex(0)}
            isDisabled={!table.getCanPreviousPage()}
          />
          <IconButton
            size="xs"
            variant="ghost"
            aria-label="上一页"
            icon={<FiChevronLeft />}
            onClick={() => table.previousPage()}
            isDisabled={!table.getCanPreviousPage()}
          />

          <Text fontSize="sm" color={mutedColor} px={2} minW="80px" textAlign="center">
            {table.getState().pagination.pageIndex + 1} / {table.getPageCount()}
          </Text>

          <IconButton
            size="xs"
            variant="ghost"
            aria-label="下一页"
            icon={<FiChevronRight />}
            onClick={() => table.nextPage()}
            isDisabled={!table.getCanNextPage()}
          />
          <IconButton
            size="xs"
            variant="ghost"
            aria-label="末页"
            icon={<FiChevronsRight />}
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            isDisabled={!table.getCanNextPage()}
          />

          <Select
            size="xs"
            w="70px"
            ml={4}
            borderRadius="md"
            value={table.getState().pagination.pageSize}
            onChange={(e) => table.setPageSize(Number(e.target.value))}
          >
            {[10, 20, 30, 50].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </Select>
        </HStack>
      )}
    </Box>
  )
}

export default DataTable
export type { ColumnDef }