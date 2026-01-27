import { describe, it, expect, beforeEach } from "vitest";
import { useAppStore } from "@/stores/app-store";

describe("useAppStore", () => {
  beforeEach(() => {
    // Reset store state before each test
    useAppStore.setState({
      sidebarCollapsed: false,
      activeModule: "writing",
      apiConnected: false,
    });
  });

  it("should initialize with sidebar expanded", () => {
    const { sidebarCollapsed } = useAppStore.getState();
    expect(sidebarCollapsed).toBe(false);
  });

  it("should toggle sidebar collapsed state", () => {
    expect(useAppStore.getState().sidebarCollapsed).toBe(false);
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarCollapsed).toBe(true);
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarCollapsed).toBe(false);
  });

  it("should set sidebar collapsed directly", () => {
    useAppStore.getState().setSidebarCollapsed(true);
    expect(useAppStore.getState().sidebarCollapsed).toBe(true);
  });

  it("should initialize with writing as active module", () => {
    const { activeModule } = useAppStore.getState();
    expect(activeModule).toBe("writing");
  });

  it("should change active module", () => {
    useAppStore.getState().setActiveModule("data");
    expect(useAppStore.getState().activeModule).toBe("data");

    useAppStore.getState().setActiveModule("auditor");
    expect(useAppStore.getState().activeModule).toBe("auditor");
  });

  it("should track API connection status", () => {
    expect(useAppStore.getState().apiConnected).toBe(false);
    useAppStore.getState().setApiConnected(true);
    expect(useAppStore.getState().apiConnected).toBe(true);
  });
});
