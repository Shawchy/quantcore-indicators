import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface AppState {
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  searchKeyword: string
}

const initialState: AppState = {
  sidebarCollapsed: false,
  theme: 'light',
  searchKeyword: '',
}

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload
    },
    setSearchKeyword: (state, action: PayloadAction<string>) => {
      state.searchKeyword = action.payload
    },
  },
})

export const { toggleSidebar, setTheme, setSearchKeyword } = appSlice.actions
export default appSlice.reducer
