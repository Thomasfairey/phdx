"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { useAppStore } from "@/stores/app-store";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function ApiHealthCheck() {
  const setApiConnected = useAppStore((state) => state.setApiConnected);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/health`, {
          method: "GET",
          cache: "no-store",
        });
        setApiConnected(response.ok);
      } catch {
        setApiConnected(false);
      }
    };

    // Check immediately
    checkHealth();

    // Check every 30 seconds
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, [setApiConnected]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ApiHealthCheck />
      {children}
    </QueryClientProvider>
  );
}
