import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { sectorApi } from '../../services/api'
import { SectorInfo, SectorRankingItem, StockBasic } from '../../types'

interface SectorState {
  sectors: SectorInfo[]
  ranking: SectorRankingItem[]
  components: StockBasic[]
  leaders: SectorRankingItem[]
  loading: boolean
  error: string | null
}

const initialState: SectorState = {
  sectors: [],
  ranking: [],
  components: [],
  leaders: [],
  loading: false,
  error: null,
}

export const fetchSectorList = createAsyncThunk(
  'sector/fetchList',
  async (sectorType: string) => {
    const response = await sectorApi.getList(sectorType)
    return response.data
  }
)

export const fetchSectorRanking = createAsyncThunk(
  'sector/fetchRanking',
  async ({ sectorType, sortBy, limit }: { sectorType: string; sortBy?: string; limit?: number }) => {
    const response = await sectorApi.getRanking(sectorType, sortBy, limit)
    return response.data
  }
)

export const fetchSectorComponents = createAsyncThunk(
  'sector/fetchComponents',
  async (sectorCode: string) => {
    const response = await sectorApi.getComponents(sectorCode)
    return response.data
  }
)

export const fetchSectorLeaders = createAsyncThunk(
  'sector/fetchLeaders',
  async ({ sectorCode, topN }: { sectorCode: string; topN?: number }) => {
    const response = await sectorApi.getLeaders(sectorCode, topN)
    return response.data
  }
)

const sectorSlice = createSlice({
  name: 'sector',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSectorList.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchSectorList.fulfilled, (state, action) => {
        state.loading = false
        state.sectors = action.payload
      })
      .addCase(fetchSectorList.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取板块列表失败'
      })
      .addCase(fetchSectorRanking.fulfilled, (state, action) => {
        state.ranking = action.payload
      })
      .addCase(fetchSectorComponents.fulfilled, (state, action) => {
        state.components = action.payload
      })
      .addCase(fetchSectorLeaders.fulfilled, (state, action) => {
        state.leaders = action.payload
      })
  },
})

export default sectorSlice.reducer
