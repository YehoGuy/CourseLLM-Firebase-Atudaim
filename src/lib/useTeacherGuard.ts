"use client";

import { useEffect, useState } from "react";

/**
 * ✅ Teacher-only protection (client-side).
 *
 * TODO (IMPORTANT):
 * Replace the DEV logic with your real auth source:
 * - If you have a user context/hook in src/hooks (e.g. useUser/useAuth),
 *   read role from there.
 */
export function useTeacherGuard() {
  const [loading, setLoading] = useState(true);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    // Replace with: const role = user.role
    const role = "TEACHER";

    setAllowed(role === "TEACHER");
    setLoading(false);
  }, []);

  return { loading, allowed };
}
