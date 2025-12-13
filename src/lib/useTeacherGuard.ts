"use client";

import { useEffect, useState } from "react";

export function useTeacherGuard() {
  const [loading, setLoading] = useState(true);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    const role = "TEACHER";

    setAllowed(role === "TEACHER");
    setLoading(false);
  }, []);

  return { loading, allowed };
}
