import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  sidebarCollapsed: boolean
  searchKeyword: string

  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setSearchKeyword: (keyword: string) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      searchKeyword: '',

      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setSearchKeyword: (keyword) => set({ searchKeyword: keyword }),
    }),
    {
      name: 'app-settings',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
)