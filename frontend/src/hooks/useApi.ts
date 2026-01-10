"use client";

import { useSession } from "next-auth/react";
import { useEffect, useMemo } from "react";
import { api } from "@/lib/api";

export function useApi() {
  const { data: session } = useSession();

  useEffect(() => {
    // Set JWT token from session
    const token = session?.accessToken || null;
    api.setToken(token);
  }, [session]);

  return useMemo(
    () => ({
      api,
      userId: session?.user?.id,
      isAuthenticated: !!session?.user?.id,
    }),
    [session?.user?.id]
  );
}
