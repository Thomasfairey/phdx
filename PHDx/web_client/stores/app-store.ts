import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ModuleType =
  | "writing"
  | "data"
  | "narrative"
  | "library"
  | "auditor";

interface AppState {
  // Sidebar state
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Active module
  activeModule: ModuleType;
  setActiveModule: (module: ModuleType) => void;

  // Connection status
  apiConnected: boolean;
  setApiConnected: (connected: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Sidebar
      sidebarCollapsed: false,
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      // Active module
      activeModule: "writing",
      setActiveModule: (module) => set({ activeModule: module }),

      // Connection
      apiConnected: false,
      setApiConnected: (connected) => set({ apiConnected: connected }),
    }),
    {
      name: "phdx-app-store",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        activeModule: state.activeModule,
      }),
    }
  )
);
